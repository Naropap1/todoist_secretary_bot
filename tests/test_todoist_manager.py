import unittest
from unittest.mock import MagicMock
from src.todoist_manager import TodoistManager

class TestTodoistManager(unittest.TestCase):
    def setUp(self):
        self.api_key = "fake_api_key"
        self.manager = TodoistManager(self.api_key)
        self.manager.api = MagicMock()

    def test_sanitize_project_name(self):
        # Test helper directly
        self.assertEqual(self.manager._sanitize_project_name("Simple"), "Simple")
        self.assertEqual(self.manager._sanitize_project_name("With Space"), r"With\ Space")
        self.assertEqual(self.manager._sanitize_project_name("Foo & Bar"), r"Foo\ \&\ Bar")
        self.assertEqual(self.manager._sanitize_project_name("(Parentheses)"), r"\(Parentheses\)")

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

        # Mock generic paginator return (iterator of lists)
        self.manager.api.filter_tasks.return_value = [[mock_t1]]

        result = self.manager.get_potential_tasks()

        # Verify query
        self.manager.api.filter_tasks.assert_called_with(query="overdue | today | (no date & #Inbox)")

        # Verify output format
        self.assertIn("- [Inbox] Task 1 (Desc)", result)

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
        mock_p3.name = "Shopping List"
        mock_p3.is_favorite = True

        self.manager.api.get_projects.return_value = [mock_p1, mock_p2, mock_p3]

        # Mock Tasks
        mock_t1 = MagicMock()
        mock_t1.id = "t1"
        mock_t1.content = "Inbox Task"
        mock_t1.project_id = "1"

        mock_t2 = MagicMock()
        mock_t2.id = "t2"
        mock_t2.content = "Work Task"
        mock_t2.project_id = "2"

        mock_t3 = MagicMock()
        mock_t3.id = "t3"
        mock_t3.content = "Buy Milk"
        mock_t3.project_id = "3"

        self.manager.api.filter_tasks.return_value = [[mock_t1, mock_t2, mock_t3]]

        result = self.manager.get_potential_tasks()

        call_args = self.manager.api.filter_tasks.call_args
        query_arg = call_args.kwargs.get('query')

        self.assertIn(r"#Work\ Project", query_arg)
        self.assertIn(r"#Shopping\ List", query_arg)

        self.assertIn("- [Inbox] Inbox Task", result)
        self.assertIn("- [Work Project] Work Task", result)
        self.assertIn("- [Shopping List] Buy Milk", result)

    def test_deduplication(self):
        mock_p1 = MagicMock()
        mock_p1.id = "1"
        mock_p1.name = "P1"
        self.manager.api.get_projects.return_value = [mock_p1]

        mock_t1 = MagicMock()
        mock_t1.id = "t1"
        mock_t1.content = "Task 1"
        mock_t1.project_id = "1"

        self.manager.api.filter_tasks.return_value = [[mock_t1, mock_t1]]

        result = self.manager.get_potential_tasks()
        self.assertEqual(result.count("- [P1] Task 1"), 1)

    def test_flat_list_return_behavior(self):
        """
        Test the case where filter_tasks might return a flat list of tasks (or iterator yielding tasks directly)
        instead of pages, which was hypothesized as the cause of the bug.
        """
        mock_p1 = MagicMock()
        mock_p1.id = "1"
        mock_p1.name = "P1"
        self.manager.api.get_projects.return_value = [mock_p1]

        mock_t1 = MagicMock()
        mock_t1.id = "t1"
        mock_t1.content = "Task 1"
        mock_t1.project_id = "1"
        mock_t1.description = ""
        mock_t1.due = None

        # Simulate filter_tasks yielding Tasks directly, NOT lists of tasks
        self.manager.api.filter_tasks.return_value = [mock_t1]

        result = self.manager.get_potential_tasks()

        # Verify it handled it correctly
        self.assertIn("- [P1] Task 1", result)
        self.assertNotIn("Error", result)

if __name__ == '__main__':
    unittest.main()
