from todoist_api_python.api import TodoistAPI
from datetime import datetime


class TodoistManager:
    def __init__(self, api_key):
        self.api = TodoistAPI(api_key)

    def _sanitize_project_name(self, name: str) -> str:
        """
        Escapes special characters in a project name for use in a Todoist filter query.
        """
        # Spaces must be escaped as "\ "
        safe_name = name.replace(" ", r"\ ")
        # Escape other special characters used in filters
        # Documented specials: & | ! ( )
        safe_name = safe_name.replace("(", r"\(").replace(")", r"\)").replace("&", r"\&").replace("|", r"\|").replace("!", r"\!")
        return safe_name

    def get_potential_tasks(self):
        """
        Fetches overdue, due today, and inbox tasks with no due date.
        Also includes tasks from favorited projects that are assigned to the user and have no due date.
        """
        try:
            # Fetch all projects to identify favorites and map IDs to names
            projects_data = self.api.get_projects()

            # Handle potential pagination (list of lists) or flat list
            projects = []
            if isinstance(projects_data, list):
                for item in projects_data:
                    if isinstance(item, list):
                        projects.extend(item)
                    else:
                        projects.append(item)
            else:
                projects = list(projects_data)

            project_map = {p.id: p.name for p in projects}
            fav_projects = [p for p in projects if p.is_favorite]

            # Base query
            query = "overdue | today | (no date & #Inbox)"

            # Add favorited projects to query
            if fav_projects:
                fav_query_parts = []
                for p in fav_projects:
                    # Escape special characters in project name for filter query
                    # Spaces must be escaped as "\ "
                    safe_name = p.name.replace(" ", r"\ ")
                    # Parentheses and other special chars might need escaping too,
                    # but spaces are the primary concern documented.
                    # Documented specials: & | ! ( )
                    safe_name = safe_name.replace("(", r"\(").replace(")", r"\)").replace("&", r"\&").replace("|", r"\|").replace("!", r"\!")
                    fav_query_parts.append(f"#{safe_name}")

                if fav_query_parts:
                    fav_query_string = " | ".join(fav_query_parts)
                    # Add to main query: OR (assigned to me & no date & (Fav1 | Fav2 ...))
                    query += f" | (assigned to: me & no date & ({fav_query_string}))"

            tasks_data = self.api.filter_tasks(query=query)

            # Handle potential pagination (list of lists) or flat list for tasks
            all_tasks = []
            if isinstance(tasks_data, list):
                for item in tasks_data:
                    if isinstance(item, list):
                        all_tasks.extend(item)
                    else:
                        all_tasks.append(item)
            else:
                all_tasks = list(tasks_data)

            tasks = []
            seen_task_ids = set()

            for task in all_tasks:
                if task.id not in seen_task_ids:
                    tasks.append(task)
                    seen_task_ids.add(task.id)

            if not tasks:
                return "No overdue or due today tasks found."

            potential_tasks = ""
            for task in tasks:
                # Prepend project name
                project_name = project_map.get(task.project_id, "Unknown Project")
                potential_tasks += f"- [{project_name}] {task.content}"

                if task.description:
                    potential_tasks += f" ({task.description})"
                if task.due:
                    formatted_time = task.due.date.strftime("%I:%M %p")
                    if formatted_time != "12:00 AM":
                        potential_tasks += f" ({formatted_time})"
                potential_tasks += "\n"

            return potential_tasks

        except Exception as error:
            import traceback
            traceback.print_exc()
            print(f"Error fetching tasks from Todoist: {error}")
            return f"Error fetching tasks from Todoist: {error}"
