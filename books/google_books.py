"""
Google Books API integration module.

This module provides a Python interface to the Google Books API,
enabling search and retrieval of book information.
"""

import requests
from typing import Dict, Optional
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class GoogleBooksAPIError(Exception):
    """Custom exception for Google Books API errors."""

    pass


class GoogleBooksAPI:
    """
    Client for interacting with the Google Books API.

    This class provides methods to search for books and retrieve
    detailed book information from Google Books.
    """

    BASE_URL = "https://www.googleapis.com/books/v1/volumes"

    def __init__(self):
        """Initialize the Google Books API client."""
        self.api_key = settings.GOOGLE_BOOKS_API_KEY
        if not self.api_key:
            logger.warning("Google Books API key not configured")

    def _make_request(self, url: str, params: Dict) -> Optional[Dict]:
        """
        Make a GET request to the Google Books API.

        Args:
            url: The API endpoint URL
            params: Query parameters for the request

        Returns:
            JSON response data or None if request fails

        Raises:
            GoogleBooksAPIError: If the API request fails
        """
        if self.api_key:
            params["key"] = self.api_key

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error("Google Books API request timed out")
            raise GoogleBooksAPIError("Request timed out. Please try again.")
        except requests.exceptions.HTTPError as e:
            logger.error(f"Google Books API HTTP error: {e}")
            if response.status_code == 429:
                raise GoogleBooksAPIError(
                    "Rate limit exceeded. Please try again later."
                )
            raise GoogleBooksAPIError(f"API request failed: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Google Books API request error: {e}")
            raise GoogleBooksAPIError("Failed to connect to Google Books API.")

    def search_books(
        self, query: str, start_index: int = 0, max_results: int = 20
    ) -> Dict:
        """
        Search for books using the Google Books API.

        Args:
            query: Search query string
            start_index: Starting index for pagination (default: 0)
            max_results: Maximum number of results to return (default: 20, max: 40)

        Returns:
            Dictionary containing search results with structure:
            {
                'total_items': int,
                'items': [list of book volumes],
                'start_index': int,
                'items_per_page': int
            }

        Raises:
            GoogleBooksAPIError: If the search fails
        """
        if not query or not query.strip():
            return {
                "total_items": 0,
                "items": [],
                "start_index": 0,
                "items_per_page": max_results,
            }

        # Limit max_results to prevent excessive API usage
        max_results = min(max_results, 40)

        params = {
            "q": query.strip(),
            "startIndex": start_index,
            "maxResults": max_results,
            "printType": "books",  # Only return books, not magazines
        }

        try:
            data = self._make_request(self.BASE_URL, params)

            return {
                "total_items": data.get("totalItems", 0),
                "items": data.get("items", []),
                "start_index": start_index,
                "items_per_page": max_results,
            }
        except GoogleBooksAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during book search: {e}")
            raise GoogleBooksAPIError("An unexpected error occurred during search.")

    def get_book_details(self, volume_id: str) -> Optional[Dict]:
        """
        Get detailed information about a specific book.

        Args:
            volume_id: The Google Books volume ID

        Returns:
            Dictionary containing detailed book information or None if not found

        Raises:
            GoogleBooksAPIError: If the request fails
        """
        if not volume_id:
            return None

        url = f"{self.BASE_URL}/{volume_id}"
        params = {}

        try:
            return self._make_request(url, params)
        except GoogleBooksAPIError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error retrieving book details: {e}")
            raise GoogleBooksAPIError("Failed to retrieve book details.")

    @staticmethod
    def extract_isbn(volume_info: Dict) -> Optional[str]:
        """
        Extract ISBN-13 or ISBN-10 from volume info.

        Args:
            volume_info: The volumeInfo dictionary from Google Books API

        Returns:
            ISBN string (preferring ISBN-13) or None if not found
        """
        identifiers = volume_info.get("industryIdentifiers", [])

        # Prefer ISBN-13
        for identifier in identifiers:
            if identifier.get("type") == "ISBN_13":
                return identifier.get("identifier")

        # Fall back to ISBN-10
        for identifier in identifiers:
            if identifier.get("type") == "ISBN_10":
                return identifier.get("identifier")

        return None

    @staticmethod
    def extract_authors(volume_info: Dict) -> str:
        """
        Extract and format authors from volume info.

        Args:
            volume_info: The volumeInfo dictionary from Google Books API

        Returns:
            Comma-separated string of authors or "Unknown Author"
        """
        authors = volume_info.get("authors", [])
        return ", ".join(authors) if authors else "Unknown Author"

    @staticmethod
    def extract_cover_url(volume_info: Dict) -> Optional[str]:
        """
        Extract the best available cover image URL.

        Args:
            volume_info: The volumeInfo dictionary from Google Books API

        Returns:
            URL string for the cover image or None if not available
        """
        image_links = volume_info.get("imageLinks", {})

        # Prefer larger images
        for size in [
            "extraLarge",
            "large",
            "medium",
            "small",
            "thumbnail",
            "smallThumbnail",
        ]:
            if size in image_links:
                # Use HTTPS for secure connections
                url = image_links[size]
                return url.replace("http://", "https://")

        return None

    @staticmethod
    def normalize_image_links(volume_info: Dict) -> Dict:
        """
        Convert all image links in volumeInfo to HTTPS.

        Args:
            volume_info: The volumeInfo dictionary from Google Books API

        Returns:
            Modified volumeInfo with HTTPS image links
        """
        if "imageLinks" in volume_info:
            image_links = volume_info["imageLinks"]
            for key, url in image_links.items():
                if url and isinstance(url, str):
                    image_links[key] = url.replace("http://", "https://")
        return volume_info

    @staticmethod
    def extract_publication_date(volume_info: Dict) -> Optional[str]:
        """
        Extract and normalize publication date.

        Args:
            volume_info: The volumeInfo dictionary from Google Books API

        Returns:
            ISO format date string (YYYY-MM-DD) or None if not available
        """
        date_str = volume_info.get("publishedDate", "")

        if not date_str:
            return None

        # Handle different date formats from Google Books
        # Formats: YYYY, YYYY-MM, or YYYY-MM-DD
        parts = date_str.split("-")

        if len(parts) == 1:  # YYYY
            return f"{parts[0]}-01-01"
        elif len(parts) == 2:  # YYYY-MM
            return f"{parts[0]}-{parts[1]}-01"
        else:  # YYYY-MM-DD
            return date_str
