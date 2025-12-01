import unittest
from unittest.mock import MagicMock, patch
import os
from src.google_service_manager import GoogleServiceManager

class TestGoogleServiceManager(unittest.TestCase):
    def test_interactive_false_no_token(self):
        # Ensure that initializing with interactive=False and no token raises an Exception

        # Mock os.path.exists to return False for token file
        with patch('os.path.exists') as mock_exists:
            # We want to simulate token file NOT existing, but client_secret existing
            # We also need to handle the recursive check inside authenticate
            def side_effect(path):
                if path == "dummy_token.json":
                    return False
                if path == "dummy_secret.json":
                    return True
                return False

            mock_exists.side_effect = side_effect

            with self.assertRaises(Exception) as context:
                GoogleServiceManager(
                    client_secret_file="dummy_secret.json",
                    token_file="dummy_token.json",
                    services=["gmail"],
                    interactive=False
                )

            self.assertIn("Authentication required but interactive mode is disabled", str(context.exception))

if __name__ == '__main__':
    unittest.main()
