"""Pydantic Schemas for waypoints.json"""

from pydantic.v1 import BaseModel # type: ignore
import typing as t

class Coordinate(str):
    @classmethod
    def __get_validators__(cls) -> t.Generator[t.Callable[..., "Coordinate"], None, None]:
        yield cls.validate

    @classmethod
    def validate(cls, v: t.Any) -> "Coordinate":
        if not isinstance(v, str):
            raise TypeError("Coordinate must be a string")
        if not v.count(" ") >= 4:
            raise ValueError("Coordinate must have at least 5 values separated by spaces")
        return Coordinate(v)

    def __repr__(self) -> str:
        return f"Coordinate({super().__repr__()})"

    @property
    def vec(self) -> list[float]:
        return [float(x) for x in self.split(" ")]

    def __add__(self, other: "str | Coordinate") -> "Coordinate":
        if not isinstance(other, Coordinate):
            other = Coordinate(other)
        return Coordinate(" ".join([str(a + b) for a, b in zip(self.vec, other.vec)]))

    def distance_to(self, other: "str | Coordinate") -> float:
        if not isinstance(other, Coordinate):
            other = Coordinate(other)
        distance: float = sum([(a - b) ** 2 for a, b in zip(self.vec, other.vec)]) ** 0.5
        return distance

    def __sub__(self, other: "str | Coordinate") -> "Coordinate":
        if not isinstance(other, Coordinate):
            other = Coordinate(other)
        return Coordinate(" ".join([str(a - b) for a, b in zip(self.vec, other.vec)]))


class Location(BaseModel):
    loc: Coordinate
    loc_type: t.Literal["j", "c"]


class Nest(BaseModel):
    loc: Location
    safe_loc: str
    orientation: t.Literal["portrait", "landscape"]
    place_plate_wiggle: t.Optional[list[Coordinate]] = None


class MotionProfile(BaseModel):
    id: int  # motion profile id
    speed: float  # peak motion speed as percentage
    speed2: float  # secondary peak motion speed as percentage for cartesian moves
    acceleration: float  # peak motion acceleration as percentage
    deceleration: float  # peak motion deceleration as percentage
    accelramp: float  # acceleration ramp time in seconds
    decelramp: float  # deceleration ramp time in seconds
    inrange: float  # Distance from target to consider motion complete
    straight: int  # Boolean determining if the motion is curved/0 or straight/-1

    def __str__(self) -> str:
        return f"{self.id} {self.speed} {self.speed2} {self.acceleration} {self.deceleration} {self.accelramp} {self.decelramp} {self.inrange} {self.straight}"

class Grip(BaseModel):
    width: int
    speed: int 
    force: int 


class Waypoints(BaseModel):
    graph_edges: list[tuple[str, str]]
    locations: dict[str, Location]
    nests: dict[str, Nest]
    motion_profiles: list[MotionProfile]
    grip_params: dict[str, Grip]
