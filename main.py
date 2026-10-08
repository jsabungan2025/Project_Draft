from pathlib import Path

from campus_room.database import CampusDatabase, parse_slot
from campus_room.exceptions import BookingLimitError, ConflictError
from campus_room.user import Administrator

DB_PATH = Path(__file__).parent / "instance" / "campusroom.db"


def print_items(title: str, items) -> None:
    print(f"\n{title}")
    if not items:
        print("  (none)")
        return
    for item in items:
        print(f"  {item}")


def run_cli() -> None:
    db = CampusDatabase(DB_PATH)
    db.initialize()
    state = db.load()
    current = state.users["s1"]

    menu = """
CampusRoom
  1) Switch user
  2) List rooms
  3) Book a room
  4) List bookings
  5) Show rooms free at a time
  6) Cancel a booking
  0) Quit
"""
    while True:
        print(menu)
        print(f"Logged in as {current}")
        choice = input("Choice: ").strip()

        if choice == "0":
            break
        if choice == "1":
            print("Users:", ", ".join(f"{uid}={user.name}" for uid, user in state.users.items()))
            uid = input("User id: ").strip()
            current = state.users[uid]
        elif choice == "2":
            print_items("Rooms", state.rooms.list_rooms())
        elif choice == "3":
            room_number = input("Room number: ").strip()
            date_text = input("Date (YYYY-MM-DD): ").strip()
            start_hour = input("Start hour (0-23): ").strip()
            end_hour = input("End hour (0-23): ").strip()
            purpose = input("Purpose: ").strip()
            try:
                state = db.load()
                current = state.users[current.user_id]
                booking = state.bookings.create_booking(
                    current,
                    state.rooms.get_room(room_number),
                    parse_slot(date_text, start_hour, end_hour),
                    purpose,
                )
                db.save_booking(booking)
                print("Booked:", booking)
            except (ConflictError, BookingLimitError, ValueError, KeyError) as exc:
                print("Could not book:", exc)
        elif choice == "4":
            state = db.load()
            current = state.users[current.user_id]
            if isinstance(current, Administrator):
                print_items("All bookings", state.bookings.list_bookings(active_only=False))
            else:
                print_items("Your bookings", state.bookings.active_bookings_for(current))
        elif choice == "5":
            date_text = input("Date (YYYY-MM-DD): ").strip()
            start_hour = input("Start hour (0-23): ").strip()
            end_hour = input("End hour (0-23): ").strip()
            try:
                state = db.load()
                schedule = parse_slot(date_text, start_hour, end_hour)
                free = state.bookings.available_rooms(state.rooms.list_rooms(), schedule)
                print_items(f"Free rooms for {schedule}", free)
            except ValueError as exc:
                print("Invalid time:", exc)
        elif choice == "6":
            booking_id = input("Booking id: ").strip()
            try:
                state = db.load()
                current = state.users[current.user_id]
                cancelled = state.bookings.cancel_booking(booking_id, current)
                db.set_booking_active(cancelled.booking_id, False)
                print("Cancelled:", cancelled)
            except (KeyError, PermissionError) as exc:
                print("Could not cancel:", exc)
        else:
            print("Unknown choice.")


if __name__ == "__main__":
    run_cli()
