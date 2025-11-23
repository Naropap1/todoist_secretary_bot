import os.path
import datetime
import requests
import time
import json
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]


class CalendarManager:
    def __init__(
        self, client_secret_file="client_secret.json", token_file="token.json"
    ):
        self.creds = None
        self.client_secret_file = client_secret_file
        self.token_file = token_file
        self.service = None
        self.bot_calendar_id = None
        self.authenticate()

    def authenticate(self):
        """Authenticates the user and creates the service."""
        if os.path.exists(self.token_file):
            self.creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)

        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                if not os.path.exists(self.client_secret_file):
                    print(
                        f"Error: {self.client_secret_file} not found. Please download it from Google Cloud Console."
                    )
                    # Returning here might cause issues if we proceed to use the service.
                    # But since this is a local script, printing error is appropriate.
                    return

                print("\nInitiating authentication...")
                print("Trying Device Flow first (best for remote users)...")

                creds = self._authenticate_with_device_flow()

                if creds:
                    self.creds = creds
                else:
                    print("\nDevice Flow failed (likely due to client config). Falling back to Console Flow.")
                    print("Please copy the URL below and send it to the user.")
                    try:
                        flow = InstalledAppFlow.from_client_secrets_file(
                            self.client_secret_file, SCOPES
                        )
                        # run_console allows the user to copy-paste the code manually
                        self.creds = flow.run_console()
                    except Exception as e:
                        print(f"Console Flow failed: {e}")
                        return

            # Save the credentials for the next run
            with open(self.token_file, "w") as token:
                token.write(self.creds.to_json())

        try:
            self.service = build("calendar", "v3", credentials=self.creds)
            self.bot_calendar_id = self._get_or_create_secretary_calendar()
        except HttpError as error:
            print(f"An error occurred: {error}")
            self.service = None

    def _authenticate_with_device_flow(self):
        """
        Authenticates using the OAuth 2.0 Device Flow.
        Returns:
            google.oauth2.credentials.Credentials or None if failed.
        """
        try:
            with open(self.client_secret_file, "r") as f:
                client_config = json.load(f)

            # Handle both "installed" and "web" formats in client_secret.json
            config = client_config.get("installed") or client_config.get("web")
            if not config:
                print("Error: Invalid client_secret.json format.")
                return None

            client_id = config["client_id"]
            client_secret = config["client_secret"]

            # 1. Request a device code
            device_code_url = "https://oauth2.googleapis.com/device/code"
            response = requests.post(device_code_url, data={
                "client_id": client_id,
                "scope": " ".join(SCOPES)
            })

            if response.status_code != 200:
                print(f"Device Flow init failed: {response.text}")
                return None

            data = response.json()
            device_code = data["device_code"]
            user_code = data["user_code"]
            verification_url = data["verification_url"]
            interval = data.get("interval", 5)
            expires_in = data.get("expires_in", 1800)

            print(f"\n--- ACTION REQUIRED ---")
            print(f"1. Send this URL to the user: {verification_url}")
            print(f"2. Tell them to enter this code: {user_code}")
            print(f"Waiting for approval... (This script will poll until approved or expired)")

            # 2. Poll for the token
            token_url = "https://oauth2.googleapis.com/token"
            start_time = time.time()

            while True:
                time.sleep(interval)

                if time.time() - start_time > expires_in:
                    print("Device code expired.")
                    return None

                response = requests.post(token_url, data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "device_code": device_code,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code"
                })

                if response.status_code == 200:
                    token_data = response.json()
                    # Construct Credentials object
                    return Credentials(
                        token=token_data["access_token"],
                        refresh_token=token_data.get("refresh_token"),
                        token_uri=token_url,
                        client_id=client_id,
                        client_secret=client_secret,
                        scopes=SCOPES
                    )

                error = response.json().get("error")
                if error == "authorization_pending":
                    continue
                elif error == "slow_down":
                    interval += 5
                    continue
                else:
                    print(f"Error polling for token: {error}")
                    return None

        except Exception as e:
            print(f"An unexpected error occurred during Device Flow: {e}")
            return None

    def _get_or_create_secretary_calendar(self):
        """Finds the 'secretary_bot' calendar or creates it if it doesn't exist."""
        if not self.service:
            return None

        calendar_name = "secretary_bot"

        # List all calendars the user has access to
        page_token = None
        while True:
            calendar_list = (
                self.service.calendarList().list(pageToken=page_token).execute()
            )
            for calendar_list_entry in calendar_list["items"]:
                if calendar_list_entry["summary"] == calendar_name:
                    return calendar_list_entry["id"]
            page_token = calendar_list.get("nextPageToken")
            if not page_token:
                break

        # If not found, create it
        try:
            # Attempt to get primary calendar timezone
            primary_cal = self.service.calendars().get(calendarId="primary").execute()
            time_zone = primary_cal.get("timeZone", "UTC")
        except HttpError:
            time_zone = "UTC"

        new_calendar = {
            "summary": calendar_name,
            "timeZone": time_zone,
        }

        created_calendar = self.service.calendars().insert(body=new_calendar).execute()
        return created_calendar["id"]

    def add_event(
        self, summary: str, start_time: str, end_time: str, description: str = None
    ) -> str:
        """
        Adds an event to the calendar.

        Args:
            summary (str): The title of the event.
            start_time (str): The start time in ISO format (e.g., '2023-10-27T09:00:00').
            end_time (str): The end time in ISO format.
            description (str, optional): Description of the event.

        Returns:
            str: The link to the created event or error message.
        """
        if not self.service:
            return "Calendar service not initialized."

        calendar_id = self.bot_calendar_id or "primary"

        def ensure_timezone(time_str):
            try:
                dt = datetime.datetime.fromisoformat(time_str)
                if dt.tzinfo is None:
                    dt = dt.astimezone()
                return dt.isoformat()
            except ValueError:
                return time_str

        event = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": ensure_timezone(start_time),
            },
            "end": {
                "dateTime": ensure_timezone(end_time),
            },
        }

        try:
            event = (
                self.service.events()
                .insert(calendarId=calendar_id, body=event)
                .execute()
            )
            return f"Event created: {event.get('htmlLink')}"
        except HttpError as error:
            return f"An error occurred: {error}"

    def get_upcoming_events(self, max_results=10):
        """Gets the upcoming events."""
        if not self.service:
            return "Calendar service not initialized."

        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        all_events = []
        calendars_to_check = ["primary"]
        if self.bot_calendar_id and self.bot_calendar_id != "primary":
            calendars_to_check.append(self.bot_calendar_id)

        try:
            for cal_id in calendars_to_check:
                events_result = (
                    self.service.events()
                    .list(
                        calendarId=cal_id,
                        timeMin=now,
                        maxResults=max_results,
                        singleEvents=True,
                        orderBy="startTime",
                    )
                    .execute()
                )
                all_events.extend(events_result.get("items", []))

            if not all_events:
                return "No upcoming events found."

            # Sort combined events by start time
            all_events.sort(
                key=lambda x: x["start"].get("dateTime", x["start"].get("date"))
            )
            # Limit to max_results? Or maybe just show all gathered?
            # The original method was limiting results per request.
            # Here we might get max_results * 2. Let's slice it.
            all_events = all_events[:max_results]

            result_str = "Upcoming events:\n"
            for event in all_events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                result_str += f"{start} - {event['summary']}\n"
            return result_str

        except HttpError as error:
            return f"An error occurred: {error}"

    def get_events_for_day(self, date: datetime.date) -> str:
        """
        Gets events for a specific day.

        Args:
            date (datetime.date): The date to fetch events for.

        Returns:
            str: A string representation of the events.
        """
        if not self.service:
            return "Calendar service not initialized."

        # Create start and end time for the given date in the local system's timezone
        # astimezone() on a naive datetime assumes local time and adds the offset
        start_of_day = (
            datetime.datetime.combine(date, datetime.time.min).astimezone().isoformat()
        )
        end_of_day = (
            datetime.datetime.combine(date, datetime.time.max).astimezone().isoformat()
        )

        all_events = []
        calendars_to_check = ["primary"]
        if self.bot_calendar_id and self.bot_calendar_id != "primary":
            calendars_to_check.append(self.bot_calendar_id)

        try:
            for cal_id in calendars_to_check:
                events_result = (
                    self.service.events()
                    .list(
                        calendarId=cal_id,
                        timeMin=start_of_day,
                        timeMax=end_of_day,
                        singleEvents=True,
                        orderBy="startTime",
                    )
                    .execute()
                )
                all_events.extend(events_result.get("items", []))

            if not all_events:
                return f"No events found for {date}."

            # Sort combined events by start time
            all_events.sort(
                key=lambda x: x["start"].get("dateTime", x["start"].get("date"))
            )

            result_str = f"Events for {date}:\n"
            for event in all_events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                end = event["end"].get("dateTime", event["end"].get("date"))
                summary = event.get("summary", "No Title")
                description = event.get("description", "")
                location = event.get("location", "")

                result_str += f"- {summary}\n"
                result_str += f"  Start: {start}\n"
                result_str += f"  End: {end}\n"
                if location:
                    result_str += f"  Location: {location}\n"
                if description:
                    # Truncate description if it's too long to avoid cluttering the prompt
                    short_desc = (
                        (description[:100] + "...")
                        if len(description) > 100
                        else description
                    )
                    result_str += f"  Description: {short_desc}\n"
                result_str += "\n"
            return result_str

        except HttpError as error:
            return f"An error occurred while fetching events for {date}: {error}"
