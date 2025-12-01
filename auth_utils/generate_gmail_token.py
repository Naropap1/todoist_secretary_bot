import os
from google_auth_oauthlib.flow import InstalledAppFlow

def generate_admin_token():
    """
    Generates the 'tokens/token_admin.json' file using the Installed App Flow.
    This script must be run on a machine with a web browser.
    """

    # Define the scopes required for Gmail
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    # Get the absolute path of the directory containing this script
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

    # Path to client_secret.json (expected in the same directory as this script)
    CLIENT_SECRET_FILE = os.path.join(SCRIPT_DIR, 'client_secret.json')

    # Determine the target path for the token file
    # Check for the existence of the root 'tokens' directory relative to this script
    ROOT_TOKENS_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, '..', 'tokens'))

    if os.path.exists(ROOT_TOKENS_DIR) and os.path.isdir(ROOT_TOKENS_DIR):
        TOKEN_FILE = os.path.join(ROOT_TOKENS_DIR, 'token_admin.json')
    else:
        # Fallback to the current directory if root/tokens is not found
        TOKEN_FILE = os.path.join(SCRIPT_DIR, 'token_admin.json')

    # Check if client_secret.json exists
    if not os.path.exists(CLIENT_SECRET_FILE):
        print(f"Error: '{CLIENT_SECRET_FILE}' not found.")
        print("Please download your OAuth 2.0 Client Secret (Desktop App type) from the Google Cloud Console")
        print(f"and save it as '{CLIENT_SECRET_FILE}'.")
        return

    print("Initiating authentication for Admin (Gmail)...")
    print(f"Token will be saved to: {TOKEN_FILE}")
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
        if TOKEN_FILE.startswith(ROOT_TOKENS_DIR):
             print("The token is in the correct location for main.py to use.")
        else:
            print("Please move this file to the 'tokens/' directory in the project root so main.py can find it.")

    except Exception as e:
        print(f"\nAn error occurred during authentication: {e}")

if __name__ == '__main__':
    generate_admin_token()
