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

    def _collect_all_items(self, api_response):
        """
        Helper to robustly collect all items from a potential iterator or list of lists.
        Handles:
        - List of items
        - List of lists (pagination)
        - Iterator of items
        - Iterator of lists (pagination)
        """
        all_items = []

        # Convert iterator to list first if necessary
        # This handles the case where api_response is a generator/iterator
        try:
            # We don't use isinstance(api_response, Iterator) because some custom iterators might not satisfy it easily
            # or if it is just a list, iter(list) works too.
            # But the safest way given the error is to check if it's a list first.
            if not isinstance(api_response, list):
                 # This captures the "Iterator" case which was falling into the 'else' block before
                 initial_collection = list(api_response)
            else:
                 initial_collection = api_response
        except TypeError:
             # Not iterable? Should not happen with valid API response
             print(f"Warning: api_response of type {type(api_response)} is not iterable.")
             return []

        # At this point, initial_collection is a list.
        # It could be [item1, item2] OR [[item1, item2], [item3]]

        for item in initial_collection:
            if isinstance(item, list):
                all_items.extend(item)
            else:
                all_items.append(item)

        return all_items

    def get_potential_tasks(self):
        """
        Fetches overdue, due today, and inbox tasks with no due date.
        Also includes tasks from favorited projects that are assigned to the user and have no due date.
        """
        try:
            # Fetch all projects to identify favorites and map IDs to names
            projects_data = self.api.get_projects()
            projects = self._collect_all_items(projects_data)

            # Defensive: ensure items have 'id'
            valid_projects = []
            for p in projects:
                if hasattr(p, 'id') and hasattr(p, 'name'):
                    valid_projects.append(p)
                else:
                    # Log warning only if it looks like we failed to flatten
                    if isinstance(p, list):
                         print(f"Warning: Nested list found in projects after flattening: {p}")
                    else:
                         pass # Might be unexpected object, but ignore safely

            fav_projects = [p for p in valid_projects if getattr(p, 'is_favorite', False)]

            # Base query
            query = "overdue | today | (no date & #Inbox)"

            # Add favorited projects to query
            if fav_projects:
                fav_query_parts = []
                for p in fav_projects:
                    safe_name = self._sanitize_project_name(p.name)
                    fav_query_parts.append(f"#{safe_name}")

                if fav_query_parts:
                    fav_query_string = " | ".join(fav_query_parts)
                    # Add to main query: OR (assigned to me & no date & (Fav1 | Fav2 ...))
                    query += f" | (assigned to: me & no date & ({fav_query_string}))"

            tasks_data = self.api.filter_tasks(query=query)
            all_tasks = self._collect_all_items(tasks_data)

            tasks = []
            seen_task_ids = set()

            for task in all_tasks:
                if not hasattr(task, 'id'):
                     continue
                if task.id not in seen_task_ids:
                    tasks.append(task)
                    seen_task_ids.add(task.id)

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
            import traceback
            traceback.print_exc()
            print(f"Error fetching tasks from Todoist: {error}")
            return f"Error fetching tasks from Todoist: {error}"
