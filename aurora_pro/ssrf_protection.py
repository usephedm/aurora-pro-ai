"""
SSRF Protection Module
Implements domain allowlisting and private IP blocking per OWASP SSRF guidelines.
"""
import ipaddress
import socket
from urllib.parse import urlparse
from typing import Set, Tuple


class SSRFProtection:
    """Validates URLs against SSRF attacks by checking domains and resolved IPs."""

    ALLOWED_DOMAINS = {
        "github.com",
        "api.github.com",
        "huggingface.co",
        "arxiv.org",
        "export.arxiv.org",
        "docs.python.org"
    }

    BLOCKED_IP_RANGES = [
        ipaddress.ip_network("127.0.0.0/8"),      # Loopback
        ipaddress.ip_network("10.0.0.0/8"),       # Private
        ipaddress.ip_network("172.16.0.0/12"),    # Private
        ipaddress.ip_network("192.168.0.0/16"),   # Private
        ipaddress.ip_network("169.254.0.0/16"),   # Link-local
        ipaddress.ip_network("224.0.0.0/4"),      # Multicast
        ipaddress.ip_network("::1/128"),          # IPv6 loopback
        ipaddress.ip_network("fc00::/7"),         # IPv6 private
        ipaddress.ip_network("fe80::/10"),        # IPv6 link-local
    ]

    def __init__(self, allowed_domains: Set[str] = None):
        """Initialize with optional custom allowed domains."""
        self.allowed_domains = allowed_domains or self.ALLOWED_DOMAINS

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Validate URL for SSRF safety.

        Returns:
            (is_valid, error_message)
        """
        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in ("http", "https"):
                return False, f"Invalid scheme: {parsed.scheme}. Only http/https allowed."

            # Check domain allowlist
            hostname = parsed.hostname
            if not hostname:
                return False, "No hostname in URL"

            if hostname not in self.allowed_domains:
                return False, f"Domain {hostname} not in allowlist"

            # Resolve DNS and check IPs
            try:
                addr_info = socket.getaddrinfo(hostname, None)
            except socket.gaierror as e:
                return False, f"DNS resolution failed: {e}"

            for family, _, _, _, sockaddr in addr_info:
                ip_str = sockaddr[0]
                try:
                    ip_obj = ipaddress.ip_address(ip_str)

                    # Check against blocked ranges
                    for blocked_range in self.BLOCKED_IP_RANGES:
                        if ip_obj in blocked_range:
                            return False, f"IP {ip_str} is in blocked range {blocked_range}"

                except ValueError:
                    return False, f"Invalid IP address: {ip_str}"

            return True, ""

        except Exception as e:
            return False, f"Validation error: {e}"

    def validate_redirect(self, original_url: str, redirect_url: str) -> Tuple[bool, str]:
        """Validate redirect target using same SSRF rules."""
        return self.validate_url(redirect_url)