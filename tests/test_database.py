import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from campus_room.database import CampusDatabase
from campus_room.exceptions import ConflictError
from campus_room.schedule import Schedule


class SqlitePersistenceTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.db = CampusDatabase(Path(self.folder.name) / "test.db")
        self.db.initialize()

    def tearDown(self):
        self.folder.cleanup()

    def test_seed_users_and_rooms(self):
        state = self.db.load()
        self.assertIn("s1", state.users)
        self.assertEqual(len(state.rooms.list_rooms()), 3)

    def test_booking_survives_reload(self):
        state = self.db.load()
        schedule = Schedule(datetime(2026, 10, 8, 9), datetime(2026, 10, 8, 11))
        booking = state.bookings.create_booking(
            state.users["s1"], state.rooms.get_room("101"), schedule, "review"
        )
        self.db.save_booking(booking)

        reloaded = self.db.load()
        found = reloaded.bookings.get_booking(booking.booking_id)
        self.assertTrue(found.active)
        self.assertEqual(found.room.room_number, "101")

        with self.assertRaises(ConflictError):
            reloaded.bookings.create_booking(
                reloaded.users["s2"],
                reloaded.rooms.get_room("101"),
                Schedule(datetime(2026, 10, 8, 10), datetime(2026, 10, 8, 12)),
                "lab",
            )


if __name__ == "__main__":
    unittest.main()
