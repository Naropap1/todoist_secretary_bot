from google import genai
from google.genai import types
from src.calendar_manager import CalendarManager
import datetime
import time
import logging
import re

SECRETARY_PROMPT = """
Current Date: {today}

You are a productivity guru and an expert personal assistant. You are tasked with planning my day today.
In order to accomplish this task you will be given three key pieces data.

Personal Scheduling Preferences: This is a detailed list of general rules I tend to follow day to day. I am a person with established daily routines.
For the most part these won't be changed and are going to heavily dictate what windows you have to work with when scheduling!
That being said, please note that the "My Scheduling Preferences" are strongly suggested guidelines.
Use all information at your disposal to come up with the perfect schedule! I trust your prioritization skills as you are the expert.

Pre-Existing Events: This can provide you valuable context such as where I will be and when.
Such context may be crucial when making your scheduling decisions.
You must also use this information to make sure you don't accidentally generate any conflicts!
This is a golden rule that cannot be broken: you must work around "Pre-Existing Events" in my calendar.
You cannot make events that conflict with "Pre-Existing Events", and you can not change pre-existing events!

Potential Tasks: This is a list of potential tasks that I'd like to get done someday.
Is today the day? That is for you to figure out. Here are some rule of thumb things to consider.
It is optimal to do the highest priority tasks first that will yield the most benefit to me.
That being said, it is also optimal to fit tasks into convenient time slots where they complement my day.
Keep your eye out for tasks that group together really well into a single timeslot. Sometimes tasks come with a time.
This time is the preferred time of day I like doing this task, but it is also just a suggestion.
Some tasks may have descriptions enclosed in parenthesis, and these descriptions provide important context for scheduling decisions.
Trust your prioritizaiton and scheduling skills.

With all this information you will have enough context to start making decisions. Here are some extra instructions you should try to follow.
You will need to calculate how long you think tasks take in order to effectively make this schedule.
Remember to be realistic with time allocation (e.g., don't schedule 24 hours of work).
Know that there are only so many truly difficult tasks a person can do in a day, make sure to find the perfect balance.
It is important to have fun in life to keep things fresh.
Hide fun easter eggs in the task descriptions for me, add fun emojis where you can, and crack jokes when possible.
If I keep coming back because my calender is entertaining, it would make sure I keep interacting with my productive scheudle.

Final pieces of crucial instructions for you to follow.
You will be updating my calendar directly by using the `add_event` tool to schedule the tasks.
You will notice that this function has a description parameter. This is where your skills as a productivity guru will shine!
Add the following information to the description:
1. What value this event will provide me in life.
2. If the tasks in the event are large and or daunting, please breakdown the task into actionable steps.
3. Provide relevant links to the task and or steps when necessary.

Okay you are now ready for the key pieces of data.

Pre-Exisiting Events:
{existing_events}

Personal Scheduling Preferences:
{personal_scheduling_preferences}

Potential Tasks:
{potential_tasks}
"""


class GeminiManager:
    def __init__(self, api_key, calendar_manager: CalendarManager):
        self.client = genai.Client(api_key=api_key)
        self.calendar_manager = calendar_manager

        # Define the tools that Gemini can use
        self.tools = [self.calendar_manager.add_event]

    def generate_full_prompt(self, personal_scheduling_preferences, potential_tasks):
        today = datetime.date.today()
        existing_events = self.calendar_manager.get_events_for_day(today)
        return SECRETARY_PROMPT.format(
            today=today,
            existing_events=existing_events,
            personal_scheduling_preferences=personal_scheduling_preferences,
            potential_tasks=potential_tasks,
        )

    def generate_and_execute(self, personal_scheduling_preferences, potential_tasks):
        """
        Sends the prompt to Gemini and handles tool calls.
        """
        full_prompt = self.generate_full_prompt(
            personal_scheduling_preferences, potential_tasks
        )

        max_retries = 5
        base_delay = 90  # Increased to 90 seconds (1.5 minutes) to avoid rate limits

        for attempt in range(max_retries):
            try:
                chat = self.client.chats.create(
                    model="gemini-2.5-pro",
                    config=types.GenerateContentConfig(tools=self.tools),
                )
                response = chat.send_message(full_prompt)
                return response.text
            except Exception as e:
                error_msg = str(e)
                # Check for 503 UNAVAILABLE or overloaded message
                if "503" in error_msg or "overloaded" in error_msg.lower():
                    if attempt < max_retries - 1:
                        sleep_time = base_delay * (2**attempt)
                        logging.warning(
                            f"Gemini is overloaded. Retrying in {sleep_time} seconds... (Attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(sleep_time)
                        continue

                # Check for 429 RESOURCE_EXHAUSTED
                if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                    if attempt < max_retries - 1:
                        # Try to find the retry delay in the error message
                        # Look for 'retryDelay': '17s' or similar
                        delay_match = re.search(
                            r"retryDelay':\s*'([\d\.]+)s'", error_msg
                        )
                        if not delay_match:
                            # Try looking for "Please retry in 17.501247704s."
                            delay_match = re.search(r"retry in ([\d\.]+)s", error_msg)

                        if delay_match:
                            try:
                                retry_delay = float(delay_match.group(1))
                                # Add a small buffer just in case
                                sleep_time = retry_delay + 1.0
                            except ValueError:
                                sleep_time = base_delay * (2**attempt)
                        else:
                            sleep_time = base_delay * (2**attempt)

                        # Ensure we wait at least the base delay (1.5 minutes) to be safe against quota limits
                        if sleep_time < base_delay:
                            sleep_time = base_delay

                        logging.warning(
                            f"Gemini quota exceeded. Retrying in {sleep_time:.2f} seconds... (Attempt {attempt + 1}/{max_retries})"
                        )
                        time.sleep(sleep_time)
                        continue

                # If it's not a retryable error or we've exhausted retries
                return f"Error interacting with Gemini: {e}"
