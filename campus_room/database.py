from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from campus_room.booking import Booking
from campus_room.managers import BookingManager, RoomManager
from campus_room.room import Room
from campus_room.schedule import Schedule
from campus_room.user import Administrator, Faculty, Student, User

ROLE_TYPES = {
    "Student": Student,
    "Faculty": Faculty,
    "Administrator": Administrator,
}


@dataclass
class CampusState:
    users: dict[str, User]
    rooms: RoomManager
    bookings: BookingManager


class CampusDatabase:
    """SQLite storage for users, rooms, and bookings."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    @contextmanager
    def session(self):
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        with self.session() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    role TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS rooms (
                    room_number TEXT PRIMARY KEY,
                    building TEXT NOT NULL,
                    capacity INTEGER NOT NULL,
                    room_type TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS bookings (
                    booking_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    room_number TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    end_time TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    active INTEGER NOT NULL DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (room_number) REFERENCES rooms(room_number)
                );
                """
            )
            existing = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
            if existing == 0:
                self._seed(conn)

    def _seed(self, conn: sqlite3.Connection) -> None:
        conn.executemany(
            "INSERT INTO users (user_id, name, role) VALUES (?, ?, ?)",
            [
                ("s1", "Ana", "Student"),
                ("s2", "Ben", "Student"),
                ("f1", "Prof. Cruz", "Faculty"),
                ("admin", "Registrar", "Administrator"),
            ],
        )
        conn.executemany(
            "INSERT INTO rooms (room_number, building, capacity, room_type) VALUES (?, ?, ?, ?)",
            [
                ("101", "Science", 30, "classroom"),
                ("102", "Science", 20, "laboratory"),
                ("A3", "Library", 8, "meeting"),
            ],
        )

    def load(self) -> CampusState:
        users = self.load_users()
        rooms = self.load_rooms()
        bookings = self.load_bookings(users, rooms)
        return CampusState(users=users, rooms=rooms, bookings=bookings)

    def load_users(self) -> dict[str, User]:
        with self.session() as conn:
            rows = conn.execute("SELECT user_id, name, role FROM users").fetchall()
        users: dict[str, User] = {}
        for row in rows:
            cls = ROLE_TYPES[row["role"]]
            users[row["user_id"]] = cls(row["user_id"], row["name"])
        return users

    def load_rooms(self) -> RoomManager:
        manager = RoomManager()
        with self.session() as conn:
            rows = conn.execute(
                "SELECT room_number, building, capacity, room_type FROM rooms"
            ).fetchall()
        for row in rows:
            manager.add_room(
                Room(row["room_number"], row["building"], row["capacity"], row["room_type"])
            )
        return manager

    def load_bookings(self, users: dict[str, User], rooms: RoomManager) -> BookingManager:
        manager = BookingManager()
        with self.session() as conn:
            rows = conn.execute(
                """
                SELECT booking_id, user_id, room_number, start_time, end_time, purpose, active
                FROM bookings
                """
            ).fetchall()
        for row in rows:
            schedule = Schedule(
                datetime.fromisoformat(row["start_time"]),
                datetime.fromisoformat(row["end_time"]),
            )
            manager.restore(
                Booking(
                    row["booking_id"],
                    users[row["user_id"]],
                    rooms.get_room(row["room_number"]),
                    schedule,
                    row["purpose"],
                    active=bool(row["active"]),
                )
            )
        return manager

    def save_booking(self, booking: Booking) -> None:
        with self.session() as conn:
            conn.execute(
                """
                INSERT INTO bookings (
                    booking_id, user_id, room_number, start_time, end_time, purpose, active
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    booking.booking_id,
                    booking.user.user_id,
                    booking.room.room_number,
                    booking.schedule.start.isoformat(timespec="minutes"),
                    booking.schedule.end.isoformat(timespec="minutes"),
                    booking.purpose,
                    int(booking.active),
                ),
            )

    def set_booking_active(self, booking_id: str, active: bool) -> None:
        with self.session() as conn:
            conn.execute(
                "UPDATE bookings SET active = ? WHERE booking_id = ?",
                (int(active), booking_id),
            )

    def save_room(self, room: Room) -> None:
        with self.session() as conn:
            conn.execute(
                """
                INSERT INTO rooms (room_number, building, capacity, room_type)
                VALUES (?, ?, ?, ?)
                """,
                (room.room_number, room.building, room.capacity, room.room_type),
            )


def parse_slot(date_text: str, start_hour: str, end_hour: str) -> Schedule:
    day = datetime.strptime(date_text, "%Y-%m-%d")
    start = day.replace(hour=int(start_hour), minute=0)
    end = day.replace(hour=int(end_hour), minute=0)
    return Schedule(start, end)
