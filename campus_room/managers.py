from campus_room.booking import Booking
from campus_room.exceptions import BookingLimitError, ConflictError
from campus_room.room import Room
from campus_room.schedule import Schedule
from campus_room.user import Administrator, User


class RoomManager:
    def __init__(self):
        self._rooms: dict[str, Room] = {}

    def add_room(self, room: Room) -> None:
        self._rooms[room.room_number] = room

    def get_room(self, room_number: str) -> Room:
        try:
            return self._rooms[room_number]
        except KeyError as exc:
            raise KeyError(f"Unknown room: {room_number}") from exc

    def list_rooms(self) -> list[Room]:
        return list(self._rooms.values())

    def search(
        self,
        building: str | None = None,
        room_type: str | None = None,
        min_capacity: int | None = None,
    ) -> list[Room]:
        return [
            room
            for room in self._rooms.values()
            if room.matches(building=building, room_type=room_type, min_capacity=min_capacity)
        ]


class BookingManager:
    def __init__(self):
        self._bookings: list[Booking] = []
        self._next_id = 1

    def _new_id(self) -> str:
        booking_id = f"B{self._next_id:03d}"
        self._next_id += 1
        return booking_id

    def restore(self, booking: Booking) -> None:
        """Reload a booking that already exists in SQLite."""
        self._bookings.append(booking)
        digits = "".join(ch for ch in booking.booking_id if ch.isdigit())
        if digits:
            self._next_id = max(self._next_id, int(digits) + 1)

    def find_conflicts(self, room: Room, schedule: Schedule) -> list[Booking]:
        return [booking for booking in self._bookings if booking.conflicts_with(room, schedule)]

    def active_bookings_for(self, user: User) -> list[Booking]:
        return [booking for booking in self._bookings if booking.active and booking.user.user_id == user.user_id]

    def create_booking(self, user: User, room: Room, schedule: Schedule, purpose: str) -> Booking:
        limit = user.get_booking_limit()
        if len(self.active_bookings_for(user)) >= limit:
            raise BookingLimitError(
                f"{user.name} already has {limit} active booking(s) (role limit)."
            )

        conflicts = self.find_conflicts(room, schedule)
        if conflicts:
            details = "; ".join(str(item) for item in conflicts)
            raise ConflictError(
                f"Room {room.room_number} is already booked during that time: {details}"
            )

        booking = Booking(self._new_id(), user, room, schedule, purpose)
        self._bookings.append(booking)
        return booking

    def cancel_booking(self, booking_id: str, requester: User) -> Booking:
        booking = self.get_booking(booking_id)
        is_owner = booking.user.user_id == requester.user_id
        is_admin = isinstance(requester, Administrator)
        if not is_owner and not is_admin:
            raise PermissionError("You can only cancel your own bookings.")
        booking.cancel()
        return booking

    def get_booking(self, booking_id: str) -> Booking:
        for booking in self._bookings:
            if booking.booking_id == booking_id:
                return booking
        raise KeyError(f"Unknown booking: {booking_id}")

    def list_bookings(self, active_only: bool = True) -> list[Booking]:
        if active_only:
            return [booking for booking in self._bookings if booking.active]
        return list(self._bookings)

    def available_rooms(self, rooms: list[Room], schedule: Schedule) -> list[Room]:
        return [room for room in rooms if not self.find_conflicts(room, schedule)]
