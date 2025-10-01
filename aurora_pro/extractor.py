"""
Content extraction using trafilatura and newspaper3k with fallback.
"""
from typing import Optional, Dict, Any

import httpx
import trafilatura
from newspaper import Article


class ContentExtractor:
    """Extract and parse content from HTML."""

    def extract(self, html: str, url: str) -> Dict[str, Any]:
        """
        Extract content using trafilatura with newspaper3k fallback.

        Returns:
            Dict with 'text', 'title', and 'method' keys
        """
        # Try trafilatura first (fast and clean)
        text = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False
        )

        if text and len(text.strip()) > 100:
            # Extract metadata for title
            metadata = trafilatura.extract_metadata(html)
            title = metadata.title if metadata and metadata.title else None

            return {
                "text": text,
                "title": title,
                "method": "trafilatura"
            }

        # Fallback to newspaper3k
        try:
            article = Article(url)
            article.download(input_html=html)
            article.parse()

            if article.text and len(article.text.strip()) > 100:
                return {
                    "text": article.text,
                    "title": article.title or None,
                    "method": "newspaper3k"
                }
        except Exception as e:
            print(f"Newspaper3k extraction failed: {e}")

        # Last resort: return empty
        return {
            "text": "",
            "title": None,
            "method": "failed"
        }