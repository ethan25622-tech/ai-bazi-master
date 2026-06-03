"""Client for fetching Bazi results from https://zydx.top/paipan.php.

The site returns a normal HTML page after a POST.  This module keeps the
scraping small and dependency-free so it can be used in regression tests.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ENDPOINT = "https://zydx.top/paipan.php"
GANZHI_RE = re.compile(r"[\u7532\u4e59\u4e19\u4e01\u620a\u5df1\u5e9a\u8f9b\u58ec\u7678\u5b50\u4e11\u5bc5\u536f\u8fb0\u5df3\u5348\u672a\u7533\u9149\u620c\u4ea5]")


@dataclass(frozen=True)
class BirthInput:
    year: int
    month: int
    day: int
    hour: int
    minute: int = 0
    sex: int = 1
    name: str = "test"


@dataclass(frozen=True)
class Pillars:
    year: str
    month: str
    day: str
    hour: str


@dataclass(frozen=True)
class ZydxResult:
    input: BirthInput
    pillars: Pillars
    solar: str | None = None
    lunar: str | None = None
    jieqi: str | None = None


def fetch_zydx_html(birth: BirthInput, timeout: int = 20) -> str:
    body = {
        "act": "ok",
        "name": birth.name,
        "DateType": "0",
        "year": str(birth.year),
        "month": str(birth.month),
        "date": str(birth.day),
        "hour": str(birth.hour),
        "minute": str(birth.minute),
        "sex": str(birth.sex),
        "hsp": "1",
        "cgp": "1",
        "lnp": "1",
        "qyp": "1",
        "ssp": "1",
        "nyp": "1",
        "shenshap": "1",
        "mgp": "1",
        "csp": "1",
        "xyp": "1",
        "PPmode": "radiobutton",
        "save": "0",
    }
    data = urlencode(body).encode("utf-8")
    request = Request(
        ENDPOINT,
        data=data,
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "bazi-validator/1.0",
        },
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


def parse_zydx_html(page: str, birth: BirthInput) -> ZydxResult:
    stems = _extract_row_chars(page, "bm_tgline")
    branches = _extract_row_chars(page, "bm_dzline")
    if len(stems) != 4 or len(branches) != 4:
        raise ValueError(f"Could not parse four pillars from ZYDX result: stems={stems}, branches={branches}")

    pillars = Pillars(
        year=stems[0] + branches[0],
        month=stems[1] + branches[1],
        day=stems[2] + branches[2],
        hour=stems[3] + branches[3],
    )
    return ZydxResult(
        input=birth,
        pillars=pillars,
        solar=_extract_label(page, "公历"),
        lunar=_extract_label(page, "农历"),
        jieqi=_extract_label(page, "节气"),
    )


def fetch_zydx_result(birth: BirthInput, timeout: int = 20) -> ZydxResult:
    return parse_zydx_html(fetch_zydx_html(birth, timeout=timeout), birth)


def _extract_row_chars(page: str, row_id: str) -> list[str]:
    row_match = re.search(rf'<tr[^>]*id="{re.escape(row_id)}"[^>]*>(.*?)</tr>', page, flags=re.S)
    if not row_match:
        return []
    cells = re.findall(r"<td[^>]*>(.*?)</td>", row_match.group(1), flags=re.S)
    chars: list[str] = []
    for cell in cells[1:]:
        text = _strip_tags(cell)
        found = GANZHI_RE.findall(text)
        if found:
            chars.append(found[0])
    return chars


def _extract_label(page: str, label: str) -> str | None:
    match = re.search(rf"<b>{re.escape(label)}：</b>(.*?)(?:<br\s*/?>|<br>)", page, flags=re.S)
    if not match:
        return None
    return _strip_tags(match.group(1)).strip()


def _strip_tags(value: str) -> str:
    text = re.sub(r"<[^>]+>", "", value)
    return html.unescape(text).replace("\xa0", " ").strip()


def birth_from_mapping(data: dict[str, Any]) -> BirthInput:
    return BirthInput(
        year=int(data["year"]),
        month=int(data["month"]),
        day=int(data.get("day", data.get("date"))),
        hour=int(data["hour"]),
        minute=int(data.get("minute", 0)),
        sex=int(data.get("sex", 1)),
        name=str(data.get("name", "test")),
    )


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Fetch Bazi pillars from zydx.top.")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--month", type=int, required=True)
    parser.add_argument("--day", type=int, required=True)
    parser.add_argument("--hour", type=int, required=True)
    parser.add_argument("--minute", type=int, default=0)
    parser.add_argument("--sex", type=int, choices=[0, 1], default=1)
    parser.add_argument("--name", default="test")
    args = parser.parse_args()

    result = fetch_zydx_result(BirthInput(**vars(args)))
    print(json.dumps(asdict(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
