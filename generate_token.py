import os
from google_auth_oauthlib.flow import InstalledAppFlow

def generate_admin_token():
    """
    Generates the 'tokens/token_admin.json' file using the Installed App Flow.
    This script must be run on a machine with a web browser.
    """

    # Define the scopes required for Gmail
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    CLIENT_SECRET_FILE = 'client_secret.json'
    TOKEN_FILE = 'tokens/token_admin.json'

    # Check if client_secret.json exists
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"Error: '{CLIENT_SECRET_FILE}' not found.")
        print("Please download your OAuth 2.0 Client Secret from the Google Cloud Console.")
        return

    # Create the tokens directory if it doesn't exist
    tokens_dir = os.path.dirname(TOKEN_FILE)
    if tokens_dir and not os.path.exists(tokens_dir):
        os.makedirs(tokens_dir)

    print("Initiating authentication for Admin (Gmail)...")
    print("A browser window should open shortly for you to log in.")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRET_FILE, SCOPES
        )
        creds = flow.run_local_server(port=0)

        # Save the credentials
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

        print(f"\nSuccess! Token saved to '{TOKEN_FILE}'.")
        print("You can now transfer this file to your headless machine.")

    except Exception as e:
        print(f"\nAn error occurred during authentication: {e}")

if __name__ == '__main__':
    generate_admin_token()
