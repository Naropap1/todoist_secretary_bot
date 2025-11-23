import json
import os
import sys
from src.todoist_manager import TodoistManager
from src.calendar_manager import CalendarManager
from src.gemini_manager import GeminiManager

PERSONAL_SCHEDULING_PREFERENCES = """
Here are rules that you should follow when scheduling my days:
1. Everyday from 8am - 9:20am, I wake up, workout, eat breakfast, and do chores.
The chores I do in this timeslot are usually daily chores which I won't bother you with scheduling.
However, there are sometimes recurring chores that pop up potential chores.
Feel free to put some of those into this time slot for me.
2. If it is the weekend, please note that I like to eat lunch from 1pm-1:30pm.
3. If it is a workday, please note that I will be busy from 9-20am - 5pm doing work.
4. I would like to eat dinner from 6:30pm-7:30pm. Please block off this time.
6. From 10:00pm-8am I am resting. Do not scheduling during this time period.
"""


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

    todoist_api_key = config.get("todoist", {}).get("api_key")
    gemini_api_key = config.get("gemini", {}).get("api_key")
    calendar_config = config.get("google_calendar", {})

    if not todoist_api_key or not gemini_api_key:
        print("Error: Missing API keys in credentials.json")
        sys.exit(1)

    # 2. Initialize Managers
    print("Initializing services...")
    try:
        todoist_manager = TodoistManager(todoist_api_key)

        # Helper to get client secret file path
        client_secret = calendar_config.get("client_secret_file", "client_secret.json")
        calendar_manager = CalendarManager(client_secret_file=client_secret)

        gemini_manager = GeminiManager(gemini_api_key, calendar_manager)
    except Exception as e:
        print(f"Initialization failed: {e}")
        sys.exit(1)

    # 3. Get Tasks from Todoist
    print("Fetching tasks from Todoist...")
    potential_tasks = todoist_manager.get_potential_tasks()
    print(f"Potential Tasks:\n{potential_tasks}")

    # 5. Call Gemini to process and update calendar
    print("Consulting Gemini and updating calendar...")
    result = gemini_manager.generate_and_execute(
        PERSONAL_SCHEDULING_PREFERENCES, potential_tasks
    )

    print("\n--- Gemini Response ---")
    print(result)
    print("-----------------------")
    print("Done.")


if __name__ == "__main__":
    main()
