import os.path
import datetime
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

                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file, SCOPES
                )
                self.creds = flow.run_local_server(port=0)

            # Save the credentials for the next run
            with open(self.token_file, "w") as token:
                token.write(self.creds.to_json())

        try:
            self.service = build("calendar", "v3", credentials=self.creds)
            self.bot_calendar_id = self._get_or_create_secretary_calendar()
        except HttpError as error:
            print(f"An error occurred: {error}")
            self.service = None

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
