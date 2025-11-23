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
        except HttpError as error:
            print(f"An error occurred: {error}")
            self.service = None

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

        event = {
            "summary": summary,
            "description": description,
            "start": {
                "dateTime": start_time,
                "timeZone": "UTC",  # Adjust if needed, or let Gemini specify offset
            },
            "end": {
                "dateTime": end_time,
                "timeZone": "UTC",
            },
        }

        try:
            event = (
                self.service.events().insert(calendarId="primary", body=event).execute()
            )
            return f"Event created: {event.get('htmlLink')}"
        except HttpError as error:
            return f"An error occurred: {error}"

    def get_upcoming_events(self, max_results=10):
        """Gets the upcoming events."""
        if not self.service:
            return "Calendar service not initialized."

        now = datetime.datetime.utcnow().isoformat() + "Z"  # 'Z' indicates UTC time
        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=now,
                    maxResults=max_results,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            if not events:
                return "No upcoming events found."

            result_str = "Upcoming events:\n"
            for event in events:
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

        try:
            events_result = (
                self.service.events()
                .list(
                    calendarId="primary",
                    timeMin=start_of_day,
                    timeMax=end_of_day,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )
            events = events_result.get("items", [])

            if not events:
                return f"No events found for {date}."

            result_str = f"Events for {date}:\n"
            for event in events:
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
