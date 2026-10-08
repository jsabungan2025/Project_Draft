from abc import ABC, abstractmethod


class User(ABC):
    """Abstract campus user. Subclasses decide how many active bookings are allowed."""

    def __init__(self, user_id: str, name: str):
        self._user_id = user_id
        self._name = name

    @property
    def user_id(self) -> str:
        return self._user_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def role(self) -> str:
        return self.__class__.__name__

    @abstractmethod
    def get_booking_limit(self) -> int:
        pass

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self._user_id}, {self._name})"


class Student(User):
    def get_booking_limit(self) -> int:
        return 2


class Faculty(User):
    def get_booking_limit(self) -> int:
        return 5


class Administrator(User):
    def get_booking_limit(self) -> int:
        # Admins manage rooms and view bookings; they do not reserve rooms here.
        return 0
