import re

from core.utils.time_utils import utc_now_iso


def test_utc_now_iso_format() -> None:
    timestamp = utc_now_iso()
    pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z$"
    assert re.match(pattern, timestamp)
    