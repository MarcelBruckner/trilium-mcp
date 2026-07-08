from datetime import date

import pytest

from tests.live._client import call, run_async

_TODAY = date.today()
_ISO_YEAR, _ISO_WEEK, _ = _TODAY.isocalendar()
_CASES = [
    ("getInboxNote", {"date": _TODAY.isoformat()}),
    ("getDayNote", {"date": _TODAY.isoformat()}),
    ("getWeekNote", {"week": f"{_ISO_YEAR:04d}-W{_ISO_WEEK:02d}"}),
    ("getMonthNote", {"month": _TODAY.strftime("%Y-%m")}),
    ("getYearNote", {"year": _TODAY.strftime("%Y")}),
]


@pytest.mark.parametrize("tool,args", _CASES, ids=[c[0] for c in _CASES])
def test_calendar_note_returns_note(tool, args):
    result = run_async(call(tool, args))
    assert isinstance(result.data, dict)
    assert result.data.get("noteId")
