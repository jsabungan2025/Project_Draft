from pathlib import Path

from flask import Flask, flash, redirect, render_template, request, session, url_for

from campus_room.database import CampusDatabase, parse_slot
from campus_room.exceptions import BookingLimitError, ConflictError
from campus_room.room import Room
from campus_room.user import Administrator


def create_app(db_path: str | Path | None = None) -> Flask:
    app = Flask(__name__)
    app.secret_key = "campusroom-dev-key"
    database = CampusDatabase(db_path or Path(app.root_path) / "instance" / "campusroom.db")
    database.initialize()

    def current_user():
        state = database.load()
        user_id = session.get("user_id", "s1")
        return state, state.users.get(user_id, state.users["s1"])

    @app.context_processor
    def inject_nav():
        state, user = current_user()
        return {
            "current_user": user,
            "all_users": state.users.values(),
            "is_admin": isinstance(user, Administrator),
        }

    @app.route("/", methods=["GET"])
    def rooms():
        state, _user = current_user()
        building = request.args.get("building") or None
        room_type = request.args.get("room_type") or None
        capacity_text = request.args.get("min_capacity") or ""
        min_capacity = int(capacity_text) if capacity_text.isdigit() else None
        found = state.rooms.search(building=building, room_type=room_type, min_capacity=min_capacity)
        return render_template("rooms.html", rooms=found)

    @app.route("/switch-user", methods=["POST"])
    def switch_user():
        session["user_id"] = request.form["user_id"]
        return redirect(request.referrer or url_for("rooms"))

    @app.route("/rooms/add", methods=["POST"])
    def add_room():
        state, user = current_user()
        if not isinstance(user, Administrator):
            flash("Only an administrator can add rooms.", "error")
            return redirect(url_for("rooms"))
        try:
            room = Room(
                request.form["room_number"].strip(),
                request.form["building"].strip(),
                int(request.form["capacity"]),
                request.form["room_type"].strip(),
            )
        except ValueError:
            flash("Could not add that room.", "error")
            return redirect(url_for("rooms"))
        try:
            state.rooms.get_room(room.room_number)
            flash(f"Room {room.room_number} already exists.", "error")
        except KeyError:
            database.save_room(room)
            flash(f"Added room {room.room_number}.", "ok")
        return redirect(url_for("rooms"))

    @app.route("/book", methods=["GET", "POST"])
    def book():
        state, user = current_user()
        if isinstance(user, Administrator):
            flash("Administrators manage rooms; switch to a student or faculty account to book.", "error")
            return redirect(url_for("rooms"))
        if request.method == "POST":
            try:
                booking = state.bookings.create_booking(
                    user,
                    state.rooms.get_room(request.form["room_number"]),
                    parse_slot(request.form["date"], request.form["start_hour"], request.form["end_hour"]),
                    request.form["purpose"].strip() or "class",
                )
                database.save_booking(booking)
                flash(f"Booked {booking.booking_id}.", "ok")
                return redirect(url_for("bookings"))
            except (ConflictError, BookingLimitError, ValueError, KeyError) as exc:
                flash(str(exc), "error")
        return render_template("book.html", rooms=state.rooms.list_rooms())

    @app.route("/bookings")
    def bookings():
        state, user = current_user()
        if isinstance(user, Administrator):
            items = state.bookings.list_bookings(active_only=False)
        else:
            items = [b for b in state.bookings.list_bookings(active_only=False) if b.user.user_id == user.user_id]
        return render_template("bookings.html", bookings=items)

    @app.route("/bookings/<booking_id>/cancel", methods=["POST"])
    def cancel(booking_id: str):
        state, user = current_user()
        try:
            cancelled = state.bookings.cancel_booking(booking_id, user)
            database.set_booking_active(cancelled.booking_id, False)
            flash(f"Cancelled {cancelled.booking_id}.", "ok")
        except (KeyError, PermissionError) as exc:
            flash(str(exc), "error")
        return redirect(url_for("bookings"))

    @app.route("/available", methods=["GET", "POST"])
    def available():
        state, _user = current_user()
        free = None
        schedule = None
        if request.method == "POST":
            try:
                schedule = parse_slot(
                    request.form["date"], request.form["start_hour"], request.form["end_hour"]
                )
                free = state.bookings.available_rooms(state.rooms.list_rooms(), schedule)
            except ValueError as exc:
                flash(str(exc), "error")
        return render_template("available.html", free_rooms=free, schedule=schedule)

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
