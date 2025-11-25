import unittest
from unittest.mock import MagicMock
from src.todoist_manager import TodoistManager

class TestTodoistManager(unittest.TestCase):
    def setUp(self):
        self.api_key = "fake_api_key"
        self.manager = TodoistManager(self.api_key)
        self.manager.api = MagicMock()

    def test_get_potential_tasks_no_favorites(self):
        # Mock Projects (none favorite)
        mock_p1 = MagicMock()
        mock_p1.id = "1"
        mock_p1.name = "Inbox"
        mock_p1.is_favorite = False

        self.manager.api.get_projects.return_value = [mock_p1]

        # Mock Tasks
        mock_t1 = MagicMock()
        mock_t1.id = "t1"
        mock_t1.content = "Task 1"
        mock_t1.project_id = "1"
        mock_t1.description = "Desc"
        mock_t1.due = None

        self.manager.api.filter_tasks.return_value = [[mock_t1]]

        result = self.manager.get_potential_tasks()

        # Verify query
        self.manager.api.filter_tasks.assert_called_with(query="overdue | today | (no date & #Inbox)")

        # Verify output format
        self.assertIn("- Task 1 (Desc)", result)

    def test_get_potential_tasks_with_favorites(self):
        # Mock Projects
        mock_p1 = MagicMock()
        mock_p1.id = "1"
        mock_p1.name = "Inbox"
        mock_p1.is_favorite = False

        mock_p2 = MagicMock()
        mock_p2.id = "2"
        mock_p2.name = "Work Project"
        mock_p2.is_favorite = True

        mock_p3 = MagicMock()
        mock_p3.id = "3"
        mock_p3.name = "Shopping List" # Space in name
        mock_p3.is_favorite = True

        self.manager.api.get_projects.return_value = [mock_p1, mock_p2, mock_p3]

        # Mock Tasks
        mock_t1 = MagicMock()
        mock_t1.id = "t1"
        mock_t1.content = "Inbox Task"
        mock_t1.project_id = "1"
        mock_t1.description = ""
        mock_t1.due = None

        mock_t2 = MagicMock()
        mock_t2.id = "t2"
        mock_t2.content = "Work Task"
        mock_t2.project_id = "2"
        mock_t2.description = ""
        mock_t2.due = None

        mock_t3 = MagicMock()
        mock_t3.id = "t3"
        mock_t3.content = "Buy Milk"
        mock_t3.project_id = "3"
        mock_t3.description = ""
        mock_t3.due = None

        self.manager.api.filter_tasks.return_value = [[mock_t1, mock_t2, mock_t3]]

        result = self.manager.get_potential_tasks()

        # Verify query includes escaped favorites
        # Expected: overdue | today | (no date & #Inbox) | (assigned to: me & no date & (#Work\ Project | #Shopping\ List))
        # Note: escaping logic replace(" ", r"\ ")

        call_args = self.manager.api.filter_tasks.call_args
        self.assertIsNotNone(call_args)
        query_arg = call_args.kwargs.get('query')

        self.assertIn("overdue | today | (no date & #Inbox)", query_arg)
        self.assertIn("assigned to: me & no date", query_arg)
        # Check for escaped names
        self.assertIn(r"#Work\ Project", query_arg)
        self.assertIn(r"#Shopping\ List", query_arg)

        # Verify output format
        self.assertIn("- Inbox Task", result)
        self.assertIn("- Work Task", result)
        self.assertIn("- Buy Milk", result)

    def test_deduplication(self):
        mock_p1 = MagicMock()
        mock_p1.id = "1"
        mock_p1.name = "P1"
        mock_p1.is_favorite = True
        self.manager.api.get_projects.return_value = [mock_p1]

        mock_t1 = MagicMock()
        mock_t1.id = "t1"
        mock_t1.content = "Task 1"
        mock_t1.project_id = "1"
        mock_t1.description = ""
        mock_t1.due = None

        # Return same task twice
        self.manager.api.filter_tasks.return_value = [[mock_t1, mock_t1]]

        result = self.manager.get_potential_tasks()

        # Should only appear once
        count = result.count("- Task 1")
        self.assertEqual(count, 1)

if __name__ == '__main__':
    unittest.main()
