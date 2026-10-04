"""Write the confirmed readings to a .csv (UTF-8 with BOM so Excel shows Thai correctly)."""
import csv

from .calc import charge
from .extract import Reading

HEADERS = ["ห้อง", "ไฟ เดือนก่อน", "ไฟ ปัจจุบัน (a)", "หน่วยไฟ (b)", "ค่าไฟ (c)",
           "น้ำ เดือนก่อน", "น้ำ ปัจจุบัน (x)", "หน่วยน้ำ (y)", "ค่าน้ำ (z)", "ตรวจสอบ"]


def build(rows: list[dict], electric_rate: float, water_rate: float, path: str) -> str:
    """rows: dicts with room, e_prev, e_curr, w_prev, w_curr (strings) and check (str).
    Usage and cost are recomputed here from the readings, so they always match them."""
    sums = [0, 0, 0, 0]
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(HEADERS)
        for r in rows:
            e = charge(Reading(r["room"], r["e_prev"], r["e_curr"]), "electric", electric_rate)
            t = charge(Reading(r["room"], r["w_prev"], r["w_curr"]), "water", water_rate)
            for i, v in enumerate((e.units, e.baht, t.units, t.baht)):
                sums[i] += v or 0
            w.writerow([r["room"], r["e_prev"], r["e_curr"], _n(e.units), _n(e.baht),
                        r["w_prev"], r["w_curr"], _n(t.units), _n(t.baht), r.get("check", "")])
        w.writerow(["รวม", "", "", sums[0], sums[1], "", "", sums[2], sums[3], ""])
    return path


def _n(v) -> str | int:
    return "" if v is None else v
