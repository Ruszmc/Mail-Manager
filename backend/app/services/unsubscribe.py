import re
from typing import NamedTuple


class UnsubscribeLinks(NamedTuple):
    mailto: list[str]
    urls: list[str]


def parse_list_unsubscribe(header: str | None) -> UnsubscribeLinks:
    if not header:
        return UnsubscribeLinks([], [])
    parts = re.split(r",\s*", header.strip())
    mailto = []
    urls = []
    for part in parts:
        cleaned = part.strip().strip("<>")
        if cleaned.startswith("mailto:"):
            mailto.append(cleaned)
        elif cleaned.startswith("http"):
            urls.append(cleaned)
    return UnsubscribeLinks(mailto, urls)
