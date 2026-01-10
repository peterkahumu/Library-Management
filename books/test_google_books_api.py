import unittest
from unittest.mock import patch, Mock
import requests
from books.google_books import GoogleBooksAPI, GoogleBooksAPIError

class GoogleBooksAPITests(unittest.TestCase):
    """Test the GoogleBooksAPI wrapper class."""

    def setUp(self):
        self.api = GoogleBooksAPI()
        # Ensure API key is set for testing logic (though mocked)
        self.api.api_key = "test_key"

    @patch("requests.get")
    def test_make_request_success(self, mock_get):
        """Test successful API request."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_get.return_value = mock_response

        result = self.api._make_request("http://test.url", {"q": "test"})
        self.assertEqual(result, {"key": "value"})
        mock_get.assert_called_with("http://test.url", params={"q": "test", "key": "test_key"}, timeout=10)

    @patch("requests.get")
    def test_make_request_timeout(self, mock_get):
        """Test timeout handling."""
        mock_get.side_effect = requests.exceptions.Timeout
        
        with self.assertRaises(GoogleBooksAPIError) as cm:
            self.api._make_request("http://url", {})
        self.assertIn("timed out", str(cm.exception))

    @patch("requests.get")
    def test_make_request_429(self, mock_get):
        """Test rate limit handling."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_get.return_value = mock_response
        
        with self.assertRaises(GoogleBooksAPIError) as cm:
            self.api._make_request("http://url", {})
        self.assertIn("Rate limit", str(cm.exception))

    @patch.object(GoogleBooksAPI, "_make_request")
    def test_search_books_empty_query(self, mock_request):
        """Test search with empty query returns empty structure."""
        result = self.api.search_books("")
        self.assertEqual(result["total_items"], 0)
        self.assertEqual(result["items"], [])
        mock_request.assert_not_called()

    @patch.object(GoogleBooksAPI, "_make_request")
    def test_search_books_success(self, mock_request):
        """Test search calls make_request correctly."""
        mock_data = {"totalItems": 1, "items": [{"id": "1"}]}
        mock_request.return_value = mock_data
        
        result = self.api.search_books("python")
        self.assertEqual(result["total_items"], 1)
        # Verify params
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], self.api.BASE_URL)
        self.assertEqual(args[1]["q"], "python")
        self.assertEqual(args[1]["printType"], "books")

    @patch.object(GoogleBooksAPI, "_make_request")
    def test_get_book_details_success(self, mock_request):
        """Test fetching details."""
        mock_request.return_value = {"id": "vol1"}
        result = self.api.get_book_details("vol1")
        self.assertEqual(result, {"id": "vol1"})
        mock_request.assert_called_with(f"{self.api.BASE_URL}/vol1", {})

    # Static Method Tests

    def test_extract_isbn(self):
        """Test ISBN extraction prefers 13 over 10."""
        vol_info = {
            "industryIdentifiers": [
                {"type": "ISBN_10", "identifier": "1234567890"},
                {"type": "ISBN_13", "identifier": "9781234567890"}
            ]
        }
        self.assertEqual(GoogleBooksAPI.extract_isbn(vol_info), "9781234567890")
        
        # Fallback
        vol_info_10 = {
            "industryIdentifiers": [{"type": "ISBN_10", "identifier": "1234567890"}]
        }
        self.assertEqual(GoogleBooksAPI.extract_isbn(vol_info_10), "1234567890")
        
        # None
        self.assertIsNone(GoogleBooksAPI.extract_isbn({}))

    def test_extract_authors(self):
        """Test author formatting."""
        self.assertEqual(GoogleBooksAPI.extract_authors({"authors": ["A", "B"]}), "A, B")
        self.assertEqual(GoogleBooksAPI.extract_authors({}), "Unknown Author")

    def test_extract_cover_url(self):
        """Test cover URL selection and HTTPS normalization."""
        vol_info = {
            "imageLinks": {
                "thumbnail": "http://img.com/thumb.jpg",
                "small": "https://img.com/small.jpg"
            }
        }
        # It prefers small over thumbnail? Check implementation list order.
        # Implementation: extraLarge, large, medium, small, thumbnail...
        # So "small" should be picked over "thumbnail".
        
        url = GoogleBooksAPI.extract_cover_url(vol_info)
        self.assertEqual(url, "https://img.com/small.jpg")
        
        # HTTPS enforcement
        vol_info_http = {
            "imageLinks": {"thumbnail": "http://insecure.com/img.jpg"}
        }
        self.assertEqual(
            GoogleBooksAPI.extract_cover_url(vol_info_http), 
            "https://insecure.com/img.jpg"
        )

    def test_extract_publication_date(self):
        """Test date normalization."""
        self.assertEqual(GoogleBooksAPI.extract_publication_date({"publishedDate": "2020"}), "2020-01-01")
        self.assertEqual(GoogleBooksAPI.extract_publication_date({"publishedDate": "2020-05"}), "2020-05-01")
        self.assertEqual(GoogleBooksAPI.extract_publication_date({"publishedDate": "2020-05-20"}), "2020-05-20")
        self.assertIsNone(GoogleBooksAPI.extract_publication_date({}))

    def test_normalize_image_links(self):
        """Test batch normalization."""
        vol_info = {
            "imageLinks": {
                "a": "http://a.com",
                "b": "https://b.com"
            }
        }
        normalized = GoogleBooksAPI.normalize_image_links(vol_info)
        self.assertEqual(normalized["imageLinks"]["a"], "https://a.com")
        self.assertEqual(normalized["imageLinks"]["b"], "https://b.com")
