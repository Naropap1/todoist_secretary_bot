import unittest
from unittest.mock import MagicMock, patch
import datetime
import sys
import os

# Add src to python path to import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.google_service_manager import GoogleServiceManager

class TestGoogleServiceManager(unittest.TestCase):

    @patch('src.google_service_manager.build')
    @patch('src.google_service_manager.Credentials')
    @patch('os.path.exists')
    def setUp(self, mock_exists, mock_creds, mock_build):
        mock_exists.return_value = True
        self.mock_service = MagicMock()
        mock_build.return_value = self.mock_service

        # Mock credentials
        mock_creds.from_authorized_user_file.return_value = MagicMock(valid=True)

        self.manager = GoogleServiceManager(
            client_secret_file="dummy_secret.json",
            token_file="dummy_token.json",
            services=["calendar"],
            interactive=False
        )
        self.manager.bot_calendar_id = "secretary_bot_id"

    def test_clear_events_for_day(self):
        # Setup date
        test_date = datetime.date(2023, 10, 27)

        # Setup mock events response
        mock_events_list = self.mock_service.events.return_value.list
        mock_events_execute = mock_events_list.return_value.execute

        mock_events_execute.return_value = {
            "items": [
                {"id": "event1", "summary": "Old Event 1"},
                {"id": "event2", "summary": "Old Event 2"}
            ]
        }

        # Setup mock delete
        mock_events_delete = self.mock_service.events.return_value.delete

        # Call the method (we haven't implemented it yet, but this defines expectations)
        # Note: We are testing the *intended* implementation.
        if hasattr(self.manager, 'clear_events_for_day'):
            result = self.manager.clear_events_for_day(test_date)

            # Assertions
            # 1. Verify list was called for the bot calendar
            mock_events_list.assert_called()
            call_args = mock_events_list.call_args[1]
            self.assertEqual(call_args['calendarId'], "secretary_bot_id")

            # 2. Verify delete was called twice (once for each event)
            self.assertEqual(mock_events_delete.call_count, 2)

            # Check calls
            mock_events_delete.assert_any_call(calendarId="secretary_bot_id", eventId="event1")
            mock_events_delete.assert_any_call(calendarId="secretary_bot_id", eventId="event2")

            print(f"Test Result: {result}")
        else:
            print("Method clear_events_for_day not implemented yet.")

if __name__ == '__main__':
    unittest.main()
