import json
import os
import sys
from src.todoist_manager import TodoistManager
from src.calendar_manager import CalendarManager
from src.gemini_manager import GeminiManager

# Constant Preamble Prompt
PREAMBLE_PROMPT = """
You are an intelligent personal assistant. Your goal is to help me plan my day effectively.
I will provide you with a list of my overdue tasks and tasks due today from Todoist.
Based on these tasks, I want you to schedule time on my Google Calendar for tomorrow to work on them.

Instructions:
1. Analyze the tasks provided.
2. Prioritize them based on urgency (overdue first) and importance (if inferred).
3. Create calendar events for tomorrow to address these tasks.
4. Be realistic with time allocation (e.g., don't schedule 24 hours of work).
5. Leave some buffer time between tasks.
6. If there are too many tasks, prioritize the most critical ones and mention which ones were left out in your final response.
7. Use the `add_event` tool to schedule the tasks.
8. Finally, provide a summary of the plan you created.
"""

def load_config(config_path="credentials.json"):
    if not os.path.exists(config_path):
        print(f"Error: {config_path} not found.")
        print("Please create a 'credentials.json' file based on 'credentials_template.json'.")
        sys.exit(1)

    with open(config_path, 'r') as f:
        return json.load(f)

def main():
    print("Starting Personal Assistant Script...")

    # 1. Load Credentials
    config = load_config()

    todoist_api_key = config.get('todoist', {}).get('api_key')
    gemini_api_key = config.get('gemini', {}).get('api_key')
    calendar_config = config.get('google_calendar', {})

    if not todoist_api_key or not gemini_api_key:
        print("Error: Missing API keys in credentials.json")
        sys.exit(1)

    # 2. Initialize Managers
    print("Initializing services...")
    try:
        todoist_manager = TodoistManager(todoist_api_key)

        # Helper to get client secret file path
        client_secret = calendar_config.get('client_secret_file', 'client_secret.json')
        calendar_manager = CalendarManager(client_secret_file=client_secret)

        gemini_manager = GeminiManager(gemini_api_key, calendar_manager)
    except Exception as e:
        print(f"Initialization failed: {e}")
        sys.exit(1)

    # 3. Get Tasks from Todoist
    print("Fetching tasks from Todoist...")
    tasks_summary = todoist_manager.get_tasks_summary()
    print(f"Tasks retrieved:\n{tasks_summary}")

    # 4. Construct Prompt
    prompt = f"{PREAMBLE_PROMPT}\n\n{tasks_summary}"

    # 5. Call Gemini to process and update calendar
    print("Consulting Gemini and updating calendar...")
    result = gemini_manager.generate_and_execute(prompt)

    print("\n--- Gemini Response ---")
    print(result)
    print("-----------------------")
    print("Done.")

if __name__ == "__main__":
    main()
