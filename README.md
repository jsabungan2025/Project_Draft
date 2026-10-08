CampusRoom

Campus room booking with overlap conflict checking, SQLite storage, and a small Flask website.

Run the website

python -m pip install -r requirements.txt
python app.py

Open http://127.0.0.1:5000

Run the terminal menu

python main.py

The website and the CLI share instance/campusroom.db.

Tests

python -m unittest

Where things live







Piece



Path





HTML pages



templates/





CSS



static/style.css





SQLite file (created on first run)



instance/campusroom.db





Table setup and seed data



campus_room/database.py





Conflict checking



campus_room/schedule.py, campus_room/managers.py



OOP map







Concept



Where





Encapsulation



Private _ fields; change bookings through methods





Abstraction



Abstract User.get_booking_limit()





Inheritance



Student, Faculty, Administrator extend User





Polymorphism



Booking limits differ by role





Composition



A Booking has a Schedule and a Room





Association



A user is linked to their bookings through BookingManager

