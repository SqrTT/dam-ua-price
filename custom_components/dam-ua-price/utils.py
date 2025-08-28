from dataclasses import dataclass

@dataclass(frozen=True)
class TimeRangePrice(float):
    start: float
    end: float
    value: float

    def contains(self, dt: float) -> bool:
        return self.start <= dt < self.end

    def duration(self) -> float:
        return self.end - self.start