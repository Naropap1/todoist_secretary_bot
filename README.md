# AI Personal Assistant Script

This Python script transforms your daily planning by integrating **Todoist**, **Google Calendar**, and **Google Gemini (AI)**. It acts as your intelligent secretary, fetching your overdue and due-today tasks and orchestrating a perfect schedule for you.

## 🌟 Key Features

*   **🧠 Smart Daily Planning:** Automatically fetches overdue and due-today tasks from Todoist and schedules them into your Google Calendar.
*   **🗓️ Context-Aware Scheduling:** Checks your existing calendar events to ensure zero conflicts. It respects your time and works *around* your schedule.
*   **⏰ Personalized Routines:** Takes your personal habits (wake-up time, meal times, work hours) into account to create a realistic and sustainable plan.
*   **👥 Multi-User Support:** Can manage schedules for multiple users in a single run, each with their own Todoist account, Calendar, and preferences.
*   **🤖 Powered by Google Gemini:** Uses Google's advanced AI models to prioritize tasks, estimate durations, and make intelligent scheduling decisions.
*   **📝 Rich Event Descriptions:** Generates detailed calendar event descriptions that include:
    *   **Value Proposition:** Why this task is important.
    *   **Actionable Steps:** Breakdowns for larger tasks.
    *   **Relevant Links:** Quick access to resources.
    *   **Easter Eggs:** Fun emojis and jokes to keep you motivated!
*   **🛡️ Robust & Reliable:** Built-in error handling and rate-limiting protections ensure smooth operation even when API services are busy.
*   **🔒 Secure:** Your credentials are kept safe locally.

## Prerequisites

1.  **Python 3.9+** installed.
2.  **Google Cloud Project** with **Google Calendar API** enabled.
3.  **Todoist Account** (per user).
4.  **Google Gemini API Key**.

## Setup

### 1. Install Dependencies

Run the following command to install the required Python libraries:

```bash
pip install -r requirements.txt
```

### 2. Configure Credentials

You need to create a `credentials.json` file in the root directory. A template `credentials_template.json` is provided.

**Structure:**

```json
{
    "gemini": {
        "api_key": "YOUR_GEMINI_API_KEY"
    },
    "google_calendar": {
        "client_secret_file": "client_secret.json",
        "scopes": ["https://www.googleapis.com/auth/calendar"]
    },
    "users": [
        {
            "user_id": "user1",
            "todoist_api_key": "USER1_TODOIST_API_KEY",
            "personal_scheduling_preferences": "Here are rules that you should follow when scheduling my days:\n1. Everyday from 8am - 9:20am, I wake up, workout, eat breakfast, and do chores.\nThe chores I do in this timeslot are usually daily chores which I won't bother you with scheduling.\nHowever, there are sometimes recurring chores that pop up in potential tasks.\nFeel free to put some of those into this time slot for me.\n2. If it is the weekend, please note that I like to eat lunch from 1pm-1:30pm.\n3. If it is a workday, please note that I will be busy from 9:20am - 5pm doing work.\n4. I would like to eat dinner from 6:30pm-7:30pm. Please block off this time.\n6. From 10:00pm-8am I am resting. Do not scheduling during this time period."
        },
        {
            "user_id": "user2",
            "todoist_api_key": "USER2_TODOIST_API_KEY",
            "personal_scheduling_preferences": "1. Wake up at 6am. 2. Gym 7-8. 3. Work 9-6."
        }
    ]
}
```

#### How to get the keys:

*   **Todoist API Key**:
    *   Go to [Todoist Integrations Settings](https://todoist.com/prefs/integrations).
    *   Scroll down to "API token" and copy it.

*   **Gemini API Key**:
    *   Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
    *   Create a new API key.

*   **Google Calendar Credentials**:
    *   Go to [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project (or select an existing one).
    *   Go to "APIs & Services" > "Library". Search for **Google Calendar API** and enable it.
    *   Go to "APIs & Services" > "OAuth consent screen". Configure it (User Type: External, then add your email as a test user).
    *   Go to "APIs & Services" > "Credentials".
    *   Click "Create Credentials" > "OAuth client ID".
    *   Application type: **Desktop app**.
    *   Download the JSON file, rename it to `client_secret.json`, and place it in the root directory of this project.
    *   Navigate to APIs & Services > OAuth consent screen > Audience.
    *   Add any users who will use the service with `+ Add Users`.

### 3. First Run & Adding Users

Run the script:

```bash
python main.py
```

**User Authentication (Console Flow):**

When adding a new user (or running for the first time), the script will use the **Console Flow**.

*   It will print a long URL.
*   Send this URL to the user.
*   They visit it, authorize, and get a code.
*   They send the code back to you, and you paste it into the terminal.

## Usage

It is recommended to run this script once a day (e.g., in the evening) to plan for the next day.

*   **Linux/macOS**: You can set up a cron job.
*   **Windows**: You can use Task Scheduler.

## Customization

*   **Preferences**: Personal scheduling preferences are now defined in `credentials.json` for each user.
*   **Model**: The script is configured to use `gemini-2.5-pro`. You can change this in `src/gemini_manager.py` if needed.
