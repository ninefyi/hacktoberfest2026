"""Turn confirmed readings into charges, and flag anything a human should double-check."""
import re
from dataclasses import dataclass, field

from .extract import Layout, Reading


def to_int(s: str) -> int | None:
    digits = re.sub(r"\D", "", s or "")
    return int(digits) if digits else None


def written_units(written: str) -> int | None:
    """'13=91' -> 13; '5398 : 98 = 784' -> 98 (the model sometimes prepends the current reading).
    Units are the second-to-last number when there are 3+, else the first of two."""
    nums = re.findall(r"\d+", written or "")
    if len(nums) >= 3:
        return int(nums[-2])
    if len(nums) == 2:
        return int(nums[0])
    return None


@dataclass
class Charge:
    room: str
    kind: str
    prev: int | None
    curr: int | None
    units: int | None
    rate: float
    baht: int | None
    flags: list[str] = field(default_factory=list)


def charge(r: Reading, kind: str, rate: float) -> Charge:
    prev, curr = to_int(r.prev), to_int(r.curr)
    flags: list[str] = []
    units = baht = None
    if prev is None or curr is None:
        flags.append("missing reading")
    else:
        units = curr - prev
        if units < 0:
            flags.append("reading went down")
        else:
            baht = round(units * rate)
        wu = written_units(r.written)
        if wu is not None and wu != units:
            flags.append(f"sheet says {wu} units, readings give {units}")
        if units > 0 and units > 300:
            flags.append("unusually high usage")
    return Charge(r.room, kind, prev, curr, units, rate, baht, flags)


def charges_for(lay: Layout, electric: dict[str, Reading], water: dict[str, Reading]):
    return {
        room: (
            charge(electric.get(room, Reading(room)), "electric", lay.electric_rate),
            charge(water.get(room, Reading(room)), "water", lay.water_rate),
        )
        for room in lay.rooms
    }


def reconcile(res) -> dict[tuple[str, str], tuple[str, str, str, str]]:
    """Compare the two reads of every row. Where they disagree, keep the one that agrees with the
    housekeeper's written units (or the one that doesn't go backwards), else the first.
    Returns {(kind, room): (kept_prev, kept_curr, other_prev, other_curr)} for disagreeing rows."""
    alts = {}
    for kind, main, alt in (("electric", res.electric, res.alt_electric), ("water", res.water, res.alt_water)):
        for room, a in list(main.items()):
            b = alt.get(room)
            if b is None or not (b.prev or b.curr):
                continue
            pa, ca, pb, cb = to_int(a.prev), to_int(a.curr), to_int(b.prev), to_int(b.curr)
            if (pa, ca) == (pb, cb):
                continue
            if not (a.prev or a.curr):  # first pass found nothing: take the second read
                main[room] = Reading(room, b.prev, b.curr, a.written or b.written)
                continue
            wu = written_units(a.written) or written_units(b.written)
            ua = ca - pa if pa is not None and ca is not None else None
            ub = cb - pb if pb is not None and cb is not None else None
            take_b = (wu is not None and ub == wu and ua != wu) or \
                     (ua is not None and ua < 0 and ub is not None and ub >= 0)
            keep, other = (b, a) if take_b else (a, b)
            main[room] = Reading(room, keep.prev, keep.curr, a.written or b.written)
            alts[(kind, room)] = (keep.prev, keep.curr, other.prev, other.curr)
    return alts
