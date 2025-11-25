from todoist_api_python.api import TodoistAPI
from datetime import datetime


class TodoistManager:
    def __init__(self, api_key):
        self.api = TodoistAPI(api_key)

    def get_potential_tasks(self):
        """
        Fetches overdue, due today, and inbox tasks with no due date.
        """
        try:
            tasks_pages = self.api.filter_tasks(query="overdue | today | (no date & #Inbox)")
            tasks = []
            for page in tasks_pages:
                tasks.extend(page)

            if not tasks:
                return "No overdue or due today tasks found."

            potential_tasks = ""
            for task in tasks:
                potential_tasks += f"- {task.content}"
                if task.description:
                    potential_tasks += f" ({task.description})"
                if task.due:
                    formatted_time = task.due.date.strftime("%I:%M %p")
                    if formatted_time != "12:00 AM":
                        potential_tasks += f" ({formatted_time})"
                potential_tasks += "\n"

            return potential_tasks

        except Exception as error:
            print(f"Error fetching tasks from Todoist: {error}")
            return f"Error fetching tasks from Todoist: {error}"
