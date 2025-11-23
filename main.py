import json
import os
import sys
from src.todoist_manager import TodoistManager
from src.calendar_manager import CalendarManager
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
    print("Starting Personal Assistant Script...")

    # 1. Load Credentials
    config = load_config()

    gemini_api_key = config.get("gemini", {}).get("api_key")
    calendar_config = config.get("google_calendar", {})
    users = config.get("users", [])

    # Backward compatibility check: if no users list, but top level todoist exists
    if not users and config.get("todoist"):
        print(
            "Warning: Old configuration format detected. Please migrate to the new format."
        )
        # Create a dummy user from old config
        users = [
            {
                "user_id": "default_user",
                "todoist_api_key": config.get("todoist", {}).get("api_key"),
                # We can't easily recover the hardcoded preferences from the old main.py if they aren't in config.
                # But for now, let's assume the user updates the config as requested.
                "personal_scheduling_preferences": "Please update your config to include preferences.",
            }
        ]

    if not gemini_api_key:
        print("Error: Missing Gemini API key in credentials.json")
        sys.exit(1)

    if not users:
        print("Error: No users found in credentials.json")
        sys.exit(1)

    print(f"Found {len(users)} users to process.")

    for user in users:
        user_id = user.get("user_id", "unknown_user")
        # Sanitize user_id to ensure safe filename
        safe_user_id = "".join(
            c for c in user_id if c.isalnum() or c in ("-", "_")
        ).strip()
        if not safe_user_id:
            safe_user_id = "unknown_user"

        print(f"\n=== Processing User: {user_id} ===")

        todoist_api_key = user.get("todoist_api_key")
        personal_preferences = user.get("personal_scheduling_preferences")

        if not todoist_api_key:
            print(f"Skipping user {user_id}: Missing Todoist API key.")
            continue

        if not personal_preferences:
            print(f"Warning: User {user_id} has no personal scheduling preferences.")
            personal_preferences = ""

        # 2. Initialize Managers for this user
        print(f"Initializing services for {user_id}...")
        try:
            todoist_manager = TodoistManager(todoist_api_key)

            # Helper to get client secret file path
            client_secret = calendar_config.get(
                "client_secret_file", "client_secret.json"
            )
            # Unique token file for each user
            token_file = f"token_{safe_user_id}.json"
            calendar_manager = CalendarManager(
                client_secret_file=client_secret, token_file=token_file
            )

            gemini_manager = GeminiManager(gemini_api_key, calendar_manager)
        except Exception as e:
            print(f"Initialization failed for user {user_id}: {e}")
            continue

        # 3. Get Tasks from Todoist
        print(f"Fetching tasks from Todoist for {user_id}...")
        potential_tasks = todoist_manager.get_potential_tasks()
        print(f"Potential Tasks:\n{potential_tasks}")

        # 5. Call Gemini to process and update calendar
        print(f"Consulting Gemini and updating calendar for {user_id}...")
        try:
            result = gemini_manager.generate_and_execute(
                personal_preferences, potential_tasks
            )
            print(f"\n--- Gemini Response for {user_id} ---")
            print(result)
            print("-----------------------")
        except Exception as e:
            print(f"Error processing user {user_id}: {e}")

    print("\nAll users processed.")


if __name__ == "__main__":
    main()
