from campus_room.room import Room
from campus_room.schedule import Schedule
from campus_room.user import User


class Booking:
    def __init__(
        self,
        booking_id: str,
        user: User,
        room: Room,
        schedule: Schedule,
        purpose: str,
        active: bool = True,
    ):
        self._booking_id = booking_id
        self._user = user
        self._room = room
        self._schedule = schedule
        self._purpose = purpose
        self._active = active

    @property
    def booking_id(self) -> str:
        return self._booking_id

    @property
    def user(self) -> User:
        return self._user

    @property
    def room(self) -> Room:
        return self._room

    @property
    def schedule(self) -> Schedule:
        return self._schedule

    @property
    def purpose(self) -> str:
        return self._purpose

    @property
    def active(self) -> bool:
        return self._active

    def cancel(self) -> None:
        self._active = False

    def conflicts_with(self, room: Room, schedule: Schedule) -> bool:
        if not self._active:
            return False
        if self._room.room_number != room.room_number:
            return False
        return self._schedule.overlaps(schedule)

    def __repr__(self) -> str:
        status = "active" if self._active else "cancelled"
        return (
            f"[{self._booking_id}] {self._room.room_number} "
            f"{self._schedule} — {self._user.name} ({self._purpose}) [{status}]"
        )
