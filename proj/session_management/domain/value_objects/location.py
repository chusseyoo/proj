from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Location:
    latitude: float
    longitude: float
    description: Optional[str] = None
    radius_meters: int = 30

    def __post_init__(self):
        if not (-90 <= self.latitude <= 90):
            raise ValueError("latitude out of range")
        if not (-180 <= self.longitude <= 180):
            raise ValueError("longitude out of range")
        if self.radius_meters < 0:
            raise ValueError("radius_meters must be non-negative")

    def within_radius(self, other_lat: float, other_lon: float) -> bool:
        raise NotImplementedError("Use a geo util to compute distance")
