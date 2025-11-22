# AI Personal Assistant Script

This Python script integrates Todoist, Google Calendar, and Google Gemini (AI) to help you plan your day. It fetches your overdue and due-today tasks from Todoist and uses Gemini to intelligently schedule them on your Google Calendar for the following day.

## Prerequisites

1.  **Python 3.9+** installed.
2.  **Google Cloud Project** with **Google Calendar API** enabled.
3.  **Todoist Account**.
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
    "todoist": {
        "api_key": "YOUR_TODOIST_API_KEY"
    },
    "gemini": {
        "api_key": "YOUR_GEMINI_API_KEY"
    },
    "google_calendar": {
        "client_secret_file": "client_secret.json",
        "scopes": ["https://www.googleapis.com/auth/calendar"]
    }
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

### 3. First Run

Run the script:

```bash
python main.py
```

**Important:** The first time you run the script, a browser window will open asking you to log in to your Google account and authorize access to your calendar. This will generate a `token.json` file for future authentication.

## Usage

It is recommended to run this script once a day (e.g., in the evening) to plan for the next day.

*   **Linux/macOS**: You can set up a cron job.
*   **Windows**: You can use Task Scheduler.

## Customization

*   **Prompt**: You can modify the `PREAMBLE_PROMPT` in `main.py` to change how the AI prioritizes or schedules tasks.
*   **Model**: The script uses `gemini-1.5-flash`. You can change this in `src/gemini_manager.py`.
