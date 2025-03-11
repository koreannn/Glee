from dataclasses import dataclass


@dataclass
class ImageDto:
    name: str
    data: bytes
