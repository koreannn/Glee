from dataclasses import dataclass


@dataclass(kw_only=True)
class Suggestion:
    title: str
    content: str
