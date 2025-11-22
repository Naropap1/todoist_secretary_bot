import google.generativeai as genai
from src.calendar_manager import CalendarManager
import datetime

class GeminiManager:
    def __init__(self, api_key, calendar_manager: CalendarManager):
        genai.configure(api_key=api_key)
        self.calendar_manager = calendar_manager

        # Define the tools that Gemini can use
        self.tools = [
            self.calendar_manager.add_event
        ]

        # Initialize the model with tools
        self.model = genai.GenerativeModel(
            model_name='gemini-1.5-flash-001', # Using 1.5 Flash as it's efficient and supports tools
            tools=self.tools
        )

    def generate_and_execute(self, prompt_content):
        """
        Sends the prompt to Gemini and handles tool calls.
        """

        # Get tomorrow's date for context, as the user wants to update calendar for the next day
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)

        full_prompt = f"""
        Current Date: {datetime.date.today()}
        Target Date for Planning: {tomorrow}

        {prompt_content}
        """

        # Start a chat session (often better for tool use preservation)
        chat = self.model.start_chat(enable_automatic_function_calling=True)

        try:
            response = chat.send_message(full_prompt)
            return response.text
        except Exception as e:
            return f"Error interacting with Gemini: {e}"
