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
    name: str
    tool_id: int
    id: int
    coordinates: Coordinate
    location_type: t.Literal["j", "c"]
    orientation: t.Literal["portrait", "landscape"]

class MotionProfile(BaseModel):
    id: int  # motion profile id
    name: str # motion profile name
    speed: float  # peak motion speed as percentage
    speed2: float  # secondary peak motion speed as percentage for cartesian moves
    acceleration: float  # peak motion acceleration as percentage
    deceleration: float  # peak motion deceleration as percentage
    accel_ramp: float  # acceleration ramp time in seconds
    decel_ramp: float  # deceleration ramp time in seconds
    inrange: float  # Distance from target to consider motion complete
    straight: int  # Boolean determining if the motion is curved/0 or straight/-1

    def __str__(self) -> str:
        return f"{self.id} {self.speed} {self.speed2} {self.acceleration} {self.deceleration} {self.accel_ramp} {self.decel_ramp} {self.inrange} {self.straight}"

class MotionProfiles(BaseModel):
    profiles: list[MotionProfile]

class Labware(BaseModel):
    id: int
    name: str
    description: str
    number_of_rows: int
    number_of_columns: int
    z_offset: float
    width : float
    height: float 
    plate_lid_offset: float #offset when the lid is on the plate
    lid_offset: float #offset when lid is on nest
    stack_height: float
    has_lid: bool

    image_url: t.Optional[str] = ""  # Allow image_url to be null or omitted

    class Config:
        # Allow extra fields like "created_at", "updated_at"
        extra = "allow"

class Labwares(BaseModel):
    labwares: list[Labware]

class Grip(BaseModel):
    id: int
    width: int
    speed: int 
    force: int 
    name: str
    tool_id: int

class Grips(BaseModel):
    grip_params: list[Grip]
    
class Waypoints(BaseModel):
    locations: list[Location]

class SequenceCommand(BaseModel):
    command: str
    params: t.Optional[dict[str, t.Any]]

class ArmSequence(BaseModel):
    name: str
    description: str
    commands: list[SequenceCommand]

class ArmSequences(BaseModel):
    sequences: list[ArmSequence]
