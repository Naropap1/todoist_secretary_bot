# AI Personal Assistant Script

This Python script transforms your daily planning by integrating **Todoist**, **Google Calendar**, **Gmail**, and **Google Gemini (AI)**. It acts as your intelligent secretary, fetching your overdue and due-today tasks, reading your latest email instructions, and orchestrating a perfect schedule for you.

## 🌟 Key Features

*   **🧠 Smart Daily Planning:** Automatically fetches overdue and due-today tasks from Todoist and schedules them into your Google Calendar.
*   **🗓️ Context-Aware Scheduling:** Checks your existing calendar events to ensure zero conflicts. It respects your time and works *around* your schedule.
*   **📧 Email Integration:** Reads your recent emails to gather critical "Recent User Input" that influences your daily plan. Prioritizes fresh context from your communications.
*   **⏰ Personalized Routines:** Takes your personal habits (wake-up time, meal times, work hours) into account to create a realistic and sustainable plan.
*   **👥 Multi-User Support:** Can manage schedules for multiple users in a single run, each with their own Todoist account, Calendar, email address, and preferences.
*   **🤖 Powered by Google Gemini:** Uses Google's advanced AI models to prioritize tasks, estimate durations, and make intelligent scheduling decisions.
*   **📝 Rich Event Descriptions:** Generates detailed calendar event descriptions that include:
    *   **Value Proposition:** Why this task is important.
    *   **Actionable Steps:** Breakdowns for larger tasks.
    *   **Relevant Links:** Quick access to resources.
    *   **Easter Eggs:** Fun emojis and jokes to keep you motivated!
*   **🛡️ Robust & Reliable:** Built-in error handling and rate-limiting protections ensure smooth operation even when API services are busy.
*   **🔒 Secure:** Your credentials are kept safe locally in the `tokens/` directory.

## Prerequisites

1.  **Python 3.9+** installed.
2.  **Google Cloud Project** with **Google Calendar API** and **Gmail API** enabled.
3.  **Todoist Account** (per user).
4.  **Google Gemini API Key**.
5.  **Gmail Account** (Admin) configured to receive and label user emails.

## Setup

### 1. Install Dependencies

Run the following command to install the required Python libraries:

```bash
pip install -r requirements.txt
```

### 2. Configure Credentials

You need to create a `credentials.json` file in the root directory. A template `credentials_template.json` is provided.

#### How to get the keys:

*   **Todoist API Key**:
    *   Go to [Todoist Integrations Settings](https://todoist.com/prefs/integrations).
    *   Scroll down to "API token" and copy it.

*   **Gemini API Key**:
    *   Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
    *   Create a new API key.

*   **Google Cloud Setup (Calendar & Gmail)**:
    *   Go to [Google Cloud Console](https://console.cloud.google.com/).
    *   Create a new project (or select an existing one).
    *   **Enable APIs:**
        *   Go to "APIs & Services" > "Library".
        *   Search for **Google Calendar API** and enable it.
        *   Search for **Gmail API** and enable it.
    *   **OAuth Consent Screen:**
        *   Go to "APIs & Services" > "OAuth consent screen".
        *   Configure it (User Type: External).
        *   Add your email (and any user emails) as **Test Users**.
    *   **Create Credentials:**
        *   Go to "APIs & Services" > "Credentials".
        *   Click "Create Credentials" > "OAuth client ID".
        *   Application type: **TVs and Limited Input devices**.
        *   Download the JSON file, rename it to `client_secret.json`, and place it in the root directory of this project.

### 3. Configure Gmail (Admin)

The "Admin" email address (specified in `credentials.json`) acts as the central receiver for instructions.

1.  **Create a Label:**
    *   Open Gmail for the Admin account.
    *   Create a new label named exactly `TODOBOT`.

2.  **Create a Filter:**
    *   Go to Gmail Settings > Filters and Blocked Addresses.
    *   Click "Create a new filter".
    *   **Has the words:** `[TODOBOT]` (or any unique tag you prefer users to use in the Subject).
    *   Click "Create filter".
    *   **Check these boxes:**
        *   Skip the Inbox (Archive it)
        *   Mark as read
        *   Apply the label: `TODOBOT`
    *   Click "Create filter".

**How it works:** Users send an email to the Admin address with `[TODOBOT]` in the subject. Gmail automatically labels it `TODOBOT` and archives it. The script reads these labeled emails.

### 4. First Run & Adding Users

Update `credentials.json` with the `admin_email` and user details (including `email`).

Run the script:

```bash
python main.py
```

**Authentication:**

1.  **Admin Auth:** The script will first ask you to authorize the **Admin** account (for Gmail access). Follow the link and enter the code.
2.  **User Auth:** Then, it will iterate through users and ask for authorization for their **Calendar** access.

## Usage

It is recommended to run this script once a day (e.g., in the evening) to plan for the next day.

*   **Linux/macOS**: You can set up a cron job.
*   **Windows**: You can use Task Scheduler.

## Customization

*   **Preferences**: Personal scheduling preferences are now defined in `credentials.json` for each user.
*   **Model**: The script is configured to use `gemini-2.5-pro`. You can change this in `src/gemini_manager.py` if needed.
