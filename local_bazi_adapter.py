"""Adapter for validating the bundled or configured bazi_engine.py."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ENGINE_DIR = Path(os.environ.get("BAZI_ENGINE_DIR", Path(__file__).resolve().parent / "bazi_legacy"))
sys.path.insert(0, str(ENGINE_DIR))

from bazi_master.calendar_terms import apply_to_module  # noqa: E402
import bazi_engine  # noqa: E402
from bazi_engine import BaziChart  # noqa: E402

apply_to_module(bazi_engine)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    data = json.loads(sys.stdin.read())
    gender = "女" if int(data.get("sex", 1)) == 0 else "男"
    longitude = float(data.get("longitude", 120))
    chart = BaziChart(
        int(data["year"]),
        int(data["month"]),
        int(data.get("day", data.get("date"))),
        int(data["hour"]),
        int(data.get("minute", 0)),
        longitude=longitude,
        gender=gender,
    )
    print(json.dumps({
        "pillars": {
            "year": chart.nian_zhu,
            "month": chart.yue_zhu,
            "day": chart.ri_zhu,
            "hour": chart.shi_zhu,
        }
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
