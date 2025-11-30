import unittest
from unittest.mock import MagicMock, patch, mock_open
import datetime
import base64
from src.google_service_manager import GoogleServiceManager

class TestGoogleServiceManager(unittest.TestCase):

    def setUp(self):
        # Mock credentials and build
        self.mock_creds = MagicMock()
        self.mock_creds.valid = True

        self.patcher_creds = patch('src.google_service_manager.Credentials')
        self.mock_creds_cls = self.patcher_creds.start()
        self.mock_creds_cls.from_authorized_user_file.return_value = self.mock_creds

        self.patcher_build = patch('src.google_service_manager.build')
        self.mock_build = self.patcher_build.start()

        self.patcher_os = patch('os.path.exists')
        self.mock_exists = self.patcher_os.start()
        self.mock_exists.return_value = True

    def tearDown(self):
        self.patcher_creds.stop()
        self.patcher_build.stop()
        self.patcher_os.stop()

    def test_init_calendar_only(self):
        """Test initialization with only Calendar service."""
        manager = GoogleServiceManager(services=["calendar"])

        # Check scopes
        self.assertIn("https://www.googleapis.com/auth/calendar", manager.scopes)
        self.assertNotIn("https://www.googleapis.com/auth/gmail.readonly", manager.scopes)

        # Check services initialized
        self.assertIn("calendar", manager.services)
        self.assertNotIn("gmail", manager.services)

    def test_init_gmail_only(self):
        """Test initialization with only Gmail service."""
        manager = GoogleServiceManager(services=["gmail"])

        # Check scopes
        self.assertNotIn("https://www.googleapis.com/auth/calendar", manager.scopes)
        self.assertIn("https://www.googleapis.com/auth/gmail.readonly", manager.scopes)

        # Check services initialized
        self.assertNotIn("calendar", manager.services)
        self.assertIn("gmail", manager.services)

    def test_get_emails_parsing(self):
        """Test fetching and parsing of emails."""
        manager = GoogleServiceManager(services=["gmail"])
        mock_gmail_service = manager.services["gmail"]

        # Mock List Messages
        mock_list = mock_gmail_service.users().messages().list.return_value
        mock_list.execute.return_value = {
            "messages": [{"id": "123"}]
        }

        # Mock Get Message Detail
        mock_get = mock_gmail_service.users().messages().get.return_value

        # Sample Payload with Headers and Body
        email_body = "This is a test email body."
        encoded_body = base64.urlsafe_b64encode(email_body.encode("utf-8")).decode("utf-8")

        mock_get.execute.return_value = {
            "id": "123",
            "snippet": "Snippet text",
            "payload": {
                "headers": [
                    {"name": "From", "value": "Sender Name <sender@example.com>"},
                    {"name": "Date", "value": "Mon, 01 Jan 2024 10:00:00 +0000"},
                    {"name": "Subject", "value": "[TODOBOT] Test Task"}
                ],
                "body": {
                    "data": encoded_body
                }
            }
        }

        emails = manager.get_emails_from_last_days(3)

        self.assertEqual(len(emails), 1)
        email = emails[0]
        self.assertEqual(email["sender"], "sender@example.com")
        self.assertEqual(email["subject"], "[TODOBOT] Test Task")
        self.assertEqual(email["content"], "This is a test email body.")

    def test_get_emails_parsing_nested_parts(self):
        """Test parsing of emails with nested parts (multipart/alternative)."""
        manager = GoogleServiceManager(services=["gmail"])
        mock_gmail_service = manager.services["gmail"]

        mock_list = mock_gmail_service.users().messages().list.return_value
        mock_list.execute.return_value = {"messages": [{"id": "456"}]}

        email_text = "Plain text content."
        encoded_text = base64.urlsafe_b64encode(email_text.encode("utf-8")).decode("utf-8")

        mock_get = mock_gmail_service.users().messages().get.return_value
        mock_get.execute.return_value = {
            "id": "456",
            "payload": {
                "headers": [
                    {"name": "From", "value": "sender@example.com"}
                ],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {"data": encoded_text}
                    },
                    {
                        "mimeType": "text/html",
                        "body": {"data": "PGh0bWw+...html content..."}
                    }
                ]
            }
        }

        emails = manager.get_emails_from_last_days(3)
        self.assertEqual(emails[0]["content"], "Plain text content.")

if __name__ == '__main__':
    unittest.main()
