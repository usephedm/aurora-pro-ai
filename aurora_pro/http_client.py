"""
SSRF-safe HTTP client with rate limiting and retry logic.
"""
import asyncio
import urllib.robotparser
from typing import Optional
from urllib.parse import urljoin, urlparse

import httpx
from aiolimiter import AsyncLimiter
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from ssrf_protection import SSRFProtection


class SafeHTTPClient:
    """HTTP client with SSRF protection, rate limiting, and robots.txt respect."""

    def __init__(self):
        self.ssrf = SSRFProtection()
        # Rate limiter: 5 requests per second per domain
        self.rate_limiters = {}
        self.robots_cache = {}
        self.client = httpx.AsyncClient(
            follow_redirects=False,  # We validate redirects manually
            timeout=30.0
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def _get_rate_limiter(self, domain: str) -> AsyncLimiter:
        """Get or create rate limiter for domain."""
        if domain not in self.rate_limiters:
            # 5 requests per second, max burst of 10
            self.rate_limiters[domain] = AsyncLimiter(5, 1.0)
        return self.rate_limiters[domain]

    async def _check_robots_txt(self, url: str) -> bool:
        """Check if URL is allowed by robots.txt."""
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        robots_url = urljoin(base_url, "/robots.txt")

        if base_url not in self.robots_cache:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)

            try:
                # Fetch robots.txt without SSRF check (same domain)
                response = await self.client.get(robots_url, timeout=5.0)
                if response.status_code == 200:
                    rp.parse(response.text.splitlines())
                else:
                    # No robots.txt or error - allow by default
                    rp.parse([])
            except Exception:
                # Error fetching robots.txt - allow by default
                rp.parse([])

            self.robots_cache[base_url] = rp

        rp = self.robots_cache[base_url]
        return rp.can_fetch("Aurora-Bot", url)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError))
    )
    async def _fetch_with_retry(self, url: str) -> httpx.Response:
        """Fetch URL with retry logic."""
        return await self.client.get(url, follow_redirects=False)

    async def fetch(self, url: str, max_redirects: int = 5) -> Optional[httpx.Response]:
        """
        Safely fetch URL with SSRF protection, robots.txt respect, and rate limiting.

        Returns:
            Response object or None if blocked/failed
        """
        current_url = url
        redirect_count = 0

        while redirect_count <= max_redirects:
            # SSRF validation
            is_valid, error_msg = self.ssrf.validate_url(current_url)
            if not is_valid:
                print(f"SSRF check failed for {current_url}: {error_msg}")
                return None

            # Check robots.txt
            if not await self._check_robots_txt(current_url):
                print(f"Blocked by robots.txt: {current_url}")
                return None

            # Rate limiting
            parsed = urlparse(current_url)
            limiter = self._get_rate_limiter(parsed.netloc)
            async with limiter:
                try:
                    response = await self._fetch_with_retry(current_url)

                    # Handle redirects manually for SSRF validation
                    if response.status_code in (301, 302, 303, 307, 308):
                        location = response.headers.get("Location")
                        if not location:
                            return None

                        # Make absolute URL
                        next_url = urljoin(current_url, location)

                        # Validate redirect target
                        is_valid, error_msg = self.ssrf.validate_redirect(current_url, next_url)
                        if not is_valid:
                            print(f"Redirect blocked: {next_url}: {error_msg}")
                            return None

                        current_url = next_url
                        redirect_count += 1
                        continue

                    return response

                except Exception as e:
                    print(f"Fetch failed for {current_url}: {e}")
                    return None

        print(f"Too many redirects for {url}")
        return None