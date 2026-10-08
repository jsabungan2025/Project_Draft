import unittest
from datetime import datetime

from campus_room import (
    BookingLimitError,
    BookingManager,
    ConflictError,
    Faculty,
    Room,
    Schedule,
    Student,
)


def slot(hour: int, end_hour: int) -> Schedule:
    day = datetime(2026, 10, 8)
    return Schedule(day.replace(hour=hour), day.replace(hour=end_hour))


class ConflictCheckingTests(unittest.TestCase):
    def setUp(self):
        self.room = Room("101", "Science", 30, "classroom")
        self.other = Room("102", "Science", 20, "laboratory")
        self.ana = Student("s1", "Ana")
        self.ben = Student("s2", "Ben")
        self.bookings = BookingManager()

    def test_overlap_is_rejected(self):
        self.bookings.create_booking(self.ana, self.room, slot(9, 11), "review")
        with self.assertRaises(ConflictError):
            self.bookings.create_booking(self.ben, self.room, slot(10, 12), "lab")

    def test_back_to_back_is_allowed(self):
        first = self.bookings.create_booking(self.ana, self.room, slot(9, 11), "review")
        second = self.bookings.create_booking(self.ben, self.room, slot(11, 13), "lab")
        self.assertTrue(first.active)
        self.assertTrue(second.active)

    def test_same_time_different_room_is_allowed(self):
        self.bookings.create_booking(self.ana, self.room, slot(9, 11), "review")
        other = self.bookings.create_booking(self.ben, self.other, slot(9, 11), "meeting")
        self.assertEqual(other.room.room_number, "102")

    def test_cancelled_slot_can_be_reused(self):
        booking = self.bookings.create_booking(self.ana, self.room, slot(9, 11), "review")
        self.bookings.cancel_booking(booking.booking_id, self.ana)
        reused = self.bookings.create_booking(self.ben, self.room, slot(9, 11), "lab")
        self.assertTrue(reused.active)

    def test_student_booking_limit(self):
        self.bookings.create_booking(self.ana, self.room, slot(8, 9), "one")
        self.bookings.create_booking(self.ana, self.other, slot(9, 10), "two")
        with self.assertRaises(BookingLimitError):
            self.bookings.create_booking(self.ana, self.room, slot(14, 15), "three")

    def test_faculty_has_higher_limit(self):
        faculty = Faculty("f1", "Prof. Cruz")
        for hour in range(8, 13):
            self.bookings.create_booking(faculty, self.room, slot(hour, hour + 1), f"class {hour}")
        self.assertEqual(len(self.bookings.active_bookings_for(faculty)), 5)


if __name__ == "__main__":
    unittest.main()
