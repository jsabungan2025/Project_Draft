import tempfile
import unittest
from pathlib import Path

from app import create_app


class WebsiteTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.app = create_app(Path(self.folder.name) / "web.db")
        self.client = self.app.test_client()

    def tearDown(self):
        self.folder.cleanup()

    def test_rooms_page(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"101", response.data)

    def test_book_then_conflict(self):
        first = self.client.post(
            "/book",
            data={
                "room_number": "101",
                "date": "2026-10-08",
                "start_hour": "9",
                "end_hour": "11",
                "purpose": "review",
            },
            follow_redirects=True,
        )
        self.assertIn(b"Booked B001", first.data)

        clash = self.client.post(
            "/switch-user",
            data={"user_id": "s2"},
            follow_redirects=True,
        )
        self.assertEqual(clash.status_code, 200)

        second = self.client.post(
            "/book",
            data={
                "room_number": "101",
                "date": "2026-10-08",
                "start_hour": "10",
                "end_hour": "12",
                "purpose": "lab",
            },
            follow_redirects=True,
        )
        self.assertIn(b"already booked", second.data)


if __name__ == "__main__":
    unittest.main()
