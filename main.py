import argparse
import json
import os
import sys
from src.todoist_manager import TodoistManager
from src.google_service_manager import GoogleServiceManager
from src.gemini_manager import GeminiManager


def load_config(config_path="credentials.json"):
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found.")
        print(
            "Please create a 'credentials.json' file based on 'credentials_template.json'."
        )
        sys.exit(1)

    with open(config_path, "r") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Personal Assistant Script")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run in test mode (process only the first user)",
    )
    parser.add_argument(
        "--no_export",
        action="store_true",
        help="Turns off export to google calendar",
    )
    args = parser.parse_args()

    print("Starting Personal Assistant Script...")

    # 1. Load Credentials
    config = load_config()

    gemini_api_key = config.get("gemini", {}).get("api_key")
    calendar_config = config.get("google_calendar", {})
    admin_email = config.get("admin_email")
    users = config.get("users", [])

    if not gemini_api_key:
        print("Error: Missing Gemini API key in credentials.json")
        sys.exit(1)

    if not users:
        print("Error: No users found in credentials.json")
        sys.exit(1)

    if not admin_email:
        print("Warning: 'admin_email' not found in credentials.json. Email processing will be skipped.")

    # 2. Admin Context: Fetch all emails if admin email is present
    all_recent_emails = []
    if admin_email:
        print(f"\n=== Admin: Fetching Emails for {admin_email} ===")
        try:
            client_secret = calendar_config.get(
                "client_secret_file", "client_secret.json"
            )
            tokens_dir = "tokens"
            os.makedirs(tokens_dir, exist_ok=True)
            admin_token_file = os.path.join(tokens_dir, "token_admin.json")

            admin_service_manager = GoogleServiceManager(
                client_secret_file=client_secret,
                token_file=admin_token_file,
                services=["gmail"]
            )
            all_recent_emails = admin_service_manager.get_emails_from_last_days(3)
            print(f"Fetched {len(all_recent_emails)} emails from the last 3 days.")
        except Exception as e:
            print(f"Failed to fetch admin emails: {e}")

    print(f"\nFound {len(users)} users to process.")

    if args.test:
        print("TEST MODE ENABLED: Only the first user will be processed.")
        users = users[:1]

    for user in users:
        user_id = user.get("user_id", "unknown_user")
        user_email = user.get("email")

        # Sanitize user_id to ensure safe filename
        safe_user_id = "".join(
            c for c in user_id if c.isalnum() or c in ("-", "_")
        ).strip()
        if not safe_user_id:
            safe_user_id = "unknown_user"

        print(f"\n=== Processing User: {user_id} ===")

        todoist_api_key = user.get("todoist_api_key")
        personal_scheduling_preferences = user.get("personal_scheduling_preferences")

        if not todoist_api_key:
            print(f"Skipping user {user_id}: Missing Todoist API key.")
            continue

        if not personal_scheduling_preferences:
            print(f"Warning: User {user_id} has no personal scheduling preferences.")
            personal_scheduling_preferences = ""

        # Filter emails for this user
        recent_user_input = ""
        if user_email and all_recent_emails:
            print(f"Filtering emails for {user_email}...")
            user_emails = [
                email for email in all_recent_emails
                if user_email.lower() in email.get("sender", "").lower()
            ]
            if user_emails:
                for email in user_emails:
                    recent_user_input += f"Date: {email['date']}\nContent: {email['content']}\n\n"
                print(f"Found {len(user_emails)} relevant emails.")
            else:
                print("No relevant emails found for this user.")
        elif not user_email:
            print(f"No email configured for user {user_id}, skipping email context.")

        # 3. Initialize Managers for this user
        print(f"Initializing services for {user_id}...")
        try:
            todoist_manager = TodoistManager(todoist_api_key)

            # Helper to get client secret file path
            client_secret = calendar_config.get(
                "client_secret_file", "client_secret.json"
            )
            # Unique token file for each user
            tokens_dir = "tokens"
            os.makedirs(tokens_dir, exist_ok=True)
            token_file = os.path.join(tokens_dir, f"token_{safe_user_id}.json")

            # User only needs Calendar access
            calendar_manager = GoogleServiceManager(
                client_secret_file=client_secret,
                token_file=token_file,
                services=["calendar"]
            )

            gemini_manager = GeminiManager(gemini_api_key, calendar_manager)
        except Exception as e:
            print(f"Initialization failed for user {user_id}: {e}")
            continue

        # 4. Get Tasks from Todoist
        print(f"Fetching tasks from Todoist for {user_id}...")
        potential_tasks = todoist_manager.get_potential_tasks()
        print(f"Potential Tasks:\n{potential_tasks}")

        # 5. Call Gemini to process and update calendar if this is not a test run
        if args.no_export:
            print(
                "Skipping exporting to google calendar, but here is the final prompt:"
            )
            print(
                gemini_manager.generate_full_prompt(
                    personal_scheduling_preferences, potential_tasks, recent_user_input
                )
            )
            continue

        print(f"Consulting Gemini and updating calendar for {user_id}...")
        try:
            result = gemini_manager.generate_and_execute(
                personal_scheduling_preferences, potential_tasks, recent_user_input
            )
            print(f"\n--- Gemini Response for {user_id} ---")
            print(result)
            print("-----------------------")
        except Exception as e:
            print(f"Error processing user {user_id}: {e}")

    print("\nAll users processed.")


if __name__ == "__main__":
    main()
