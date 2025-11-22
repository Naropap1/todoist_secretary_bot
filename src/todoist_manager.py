from todoist_api_python.api import TodoistAPI

class TodoistManager:
    def __init__(self, api_key):
        self.api = TodoistAPI(api_key)

    def get_tasks_summary(self):
        """
        Fetches overdue and due today tasks and returns a summary string.
        """
        try:
            # Fetch tasks with filter 'overdue | today'
            # Note: The python wrapper get_tasks(filter=...) allows filtering.
            tasks = self.api.get_tasks(filter='overdue | today')

            if not tasks:
                return "No overdue or due today tasks found."

            summary = "Here are the overdue and due today tasks:\n"
            for task in tasks:
                due_date = task.due.date if task.due else "No due date"
                summary += f"- {task.content} (Due: {due_date})\n"

            return summary

        except Exception as error:
            print(f"Error fetching tasks from Todoist: {error}")
            return f"Error fetching tasks from Todoist: {error}"
