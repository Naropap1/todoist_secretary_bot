from google import genai
from google.genai import types
from src.calendar_manager import CalendarManager
import datetime

class GeminiManager:
    def __init__(self, api_key, calendar_manager: CalendarManager):
        self.client = genai.Client(api_key=api_key)
        self.calendar_manager = calendar_manager

        # Define the tools that Gemini can use
        self.tools = [
            self.calendar_manager.add_event
        ]

    def generate_and_execute(self, prompt_content):
        """
        Sends the prompt to Gemini and handles tool calls.
        """

        # Get tomorrow's date for context, as the user wants to update calendar for the next day
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)

        # Fetch existing events for tomorrow
        existing_events = self.calendar_manager.get_events_for_day(tomorrow)

        full_prompt = f"""
        Current Date: {datetime.date.today()}
        Target Date for Planning: {tomorrow}

        Existing Calendar Events for {tomorrow}:
        {existing_events}

        {prompt_content}
        """

        try:
            chat = self.client.chats.create(
                model='gemini-1.5-flash-001',
                config=types.GenerateContentConfig(
                    tools=self.tools
                )
            )
            response = chat.send_message(full_prompt)
            return response.text
        except Exception as e:
            return f"Error interacting with Gemini: {e}"
