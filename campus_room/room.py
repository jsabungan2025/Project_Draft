class Room:
    def __init__(self, room_number: str, building: str, capacity: int, room_type: str):
        self._room_number = room_number
        self._building = building
        self._capacity = capacity
        self._room_type = room_type

    @property
    def room_number(self) -> str:
        return self._room_number

    @property
    def building(self) -> str:
        return self._building

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def room_type(self) -> str:
        return self._room_type

    def matches(self, building: str | None = None, room_type: str | None = None, min_capacity: int | None = None) -> bool:
        if building and self._building.lower() != building.lower():
            return False
        if room_type and self._room_type.lower() != room_type.lower():
            return False
        if min_capacity is not None and self._capacity < min_capacity:
            return False
        return True

    def __repr__(self) -> str:
        return (
            f"Room {self._room_number} ({self._building}, "
            f"{self._room_type}, cap {self._capacity})"
        )
