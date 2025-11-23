from todoist_api_python.api import TodoistAPI
from datetime import datetime


class TodoistManager:
    def __init__(self, api_key):
        self.api = TodoistAPI(api_key)

    def get_potential_tasks(self):
        """
        Fetches overdue and due today tasks and returns a potential tasks string.
        """
        try:
            tasks_pages = self.api.filter_tasks(query="overdue | today")
            tasks = []
            for page in tasks_pages:
                tasks.extend(page)

            if not tasks:
                return "No overdue or due today tasks found."

            potential_tasks = ""
            for task in tasks:
                potential_tasks += f"- {task.content}"
                if task.due:
                    potential_tasks += f" ({task.due.date.strftime("%I:%M %p")})"
                potential_tasks += "\n"

            return potential_tasks

        except Exception as error:
            print(f"Error fetching tasks from Todoist: {error}")
            return f"Error fetching tasks from Todoist: {error}"
