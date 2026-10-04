"""Read a handwritten meter sheet with a local Gemma model, one small crop at a time."""
import io
import json
import re
import sys
from dataclasses import dataclass, field

import ollama
import yaml
from PIL import Image, ImageOps

MODEL = "gemma3:12b"
BAND_ROWS = 5

SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "room": {"type": "string"},
            "prev": {"type": "string"},
            "curr": {"type": "string"},
            "written": {"type": "string"},
        },
        "required": ["room", "prev", "curr", "written"],
    },
}

PROMPT = """This is a crop of a handwritten Thai {kind} meter sheet with {n} rows.
Columns left to right: room number, {kind} meter previous month (prev), {kind} meter current month (curr),
and the {kind} cost the housekeeper wrote as 'units = baht' (written).
The crop may also show part of a neighbouring row above or below: ignore partial rows.
Return one object per fully visible row, top to bottom. In "room" put the room label printed
at the start of that row, read from the image (do not guess it). Copy every other value as a string exactly as written, keeping
leading zeros. Use "" for anything blank. Do not calculate anything."""


@dataclass
class Layout:
    name: str
    rooms: list[str]
    table_top: float
    table_bottom: float
    columns: list[float]  # room_l, e_prev_l, e_curr_l, e_cost_l, w_prev_l, w_curr_l, w_cost_l, right
    electric_rate: float = 7
    water_rate: float = 25

    @classmethod
    def load(cls, path: str) -> "Layout":
        return cls(**yaml.safe_load(open(path, encoding="utf-8")))


@dataclass
class Reading:
    room: str
    prev: str = ""
    curr: str = ""
    written: str = ""


@dataclass
class SheetReading:
    electric: dict[str, Reading] = field(default_factory=dict)
    water: dict[str, Reading] = field(default_factory=dict)
    alt_electric: dict[str, Reading] = field(default_factory=dict)  # second, independent read
    alt_water: dict[str, Reading] = field(default_factory=dict)
    unmatched: list[str] = field(default_factory=list)  # "electric 205" etc.: no row with that label was found


def load_image(path: str) -> Image.Image:
    return ImageOps.exif_transpose(Image.open(path)).convert("RGB")


def _crop_block(img: Image.Image, lay: Layout, kind: str, y0: float, y1: float, scale: float = 2) -> bytes:
    w, h = img.size
    c = lay.columns
    lo, hi = (c[1], c[4]) if kind == "electric" else (c[4], c[7])
    box = lambda a, b: img.crop((int(a * w), int(y0 * h), int(b * w), int(y1 * h)))
    room, block = box(c[0], c[1]), box(lo, min(hi + 0.012, 1.0))
    out = Image.new("RGB", (room.width + block.width, room.height), "white")
    out.paste(room, (0, 0))
    out.paste(block, (room.width, 0))
    out = out.resize((int(out.width * scale), int(out.height * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    out.save(buf, "JPEG", quality=92)
    return buf.getvalue()


def _ink(img: Image.Image, lay: Layout, kind: str, y0: float, y1: float) -> float:
    """Fraction of handwriting-like dark pixels in a block's cells: low means nothing is written."""
    import numpy as np
    w, h = img.size
    c = lay.columns
    lo, hi = (c[1], c[4]) if kind == "electric" else (c[4], c[7])
    a = np.asarray(img.convert("L").crop((int(lo * w), int(y0 * h), int(hi * w), int(y1 * h)))).astype(float)
    my, mx = max(int(a.shape[0] * 0.06), 1), max(int(a.shape[1] * 0.06), 1)
    a = a[my:-my, mx:-mx]  # trim the grid lines at the crop edge
    d = a < np.percentile(a, 70) - 55
    # keep only pixels with dark neighbours on both axes, which drops thin ruled lines
    k = d[1:-1, 1:-1] & (d[:-2, 1:-1] | d[2:, 1:-1]) & (d[1:-1, :-2] | d[1:-1, 2:])
    return float(k.mean())


# Calibrated on three sheets: written blocks score 0.09-0.18, empty ones 0.02-0.04.
INK_MIN = 0.033


def _key(label: str) -> str:
    """Match room labels loosely: '201' -> '201', 'W3' / 'พ3' -> '3'."""
    digits = "".join(c for c in label if c.isdigit())
    return digits if digits else label.strip().lower()


def _ask(img, lay, kind, y0, y1, rooms, model, scale=2):
    resp = ollama.chat(
        model=model,
        messages=[{
            "role": "user",
            "content": PROMPT.format(kind=kind, n=len(rooms) + 2),
            "images": [_crop_block(img, lay, kind, y0, y1, scale)],
        }],
        format=SCHEMA,
        options={"temperature": 0},
    )
    return {_key(r.get("room", "")): r for r in json.loads(resp.message.content)}


def read_band(img: Image.Image, lay: Layout, kind: str, i0: int, i1: int,
              model: str = MODEL, scale: float = 2) -> tuple[list[Reading], list[str]]:
    """Read rows i0..i1. Values are matched to rooms by the label the model reads in each row,
    never by position, so a drifting crop can't put one room's numbers on another's form.
    Returns (readings, rooms that could not be matched)."""
    pitch = (lay.table_bottom - lay.table_top) / len(lay.rooms)
    rooms = lay.rooms[i0:i1]
    wanted = {_key(r): r for r in rooms}
    found: dict[str, Reading] = {}
    y_in0, y_in1 = lay.table_top + i0 * pitch, lay.table_top + i1 * pitch
    if _ink(img, lay, kind, y_in0, y_in1) < INK_MIN:
        return [Reading(r) for r in rooms], []  # nothing written in this block: skip the model
    # first try the expected crop padded by a row either side; if rooms are missing,
    # try the same band nudged up and down (perspective drift).
    for shift in (0.0, -0.6, 0.6):
        y0 = lay.table_top + (i0 - 1 + shift) * pitch
        y1 = lay.table_top + (i1 + 1 + shift) * pitch
        got = _ask(img, lay, kind, max(y0, 0.0), min(y1, 1.0), rooms, model, scale)
        for k, room in wanted.items():
            if room not in found and k in got:
                row = got[k]
                found[room] = Reading(room, row.get("prev", ""), row.get("curr", ""), row.get("written", ""))
        if len(found) == len(rooms):
            break
    missing = [r for r in rooms if r not in found]
    return [found.get(r, Reading(r)) for r in rooms], missing


def _has_data(r: Reading) -> bool:
    return bool(r.prev or r.curr)


def make_bands(n: int, first: int = BAND_ROWS) -> list[tuple[int, int]]:
    """Split n rows into bands of BAND_ROWS, the first band being `first` rows long."""
    edges = [0, min(first, n)]
    while edges[-1] < n:
        edges.append(min(edges[-1] + BAND_ROWS, n))
    bands = list(zip(edges, edges[1:]))
    if len(bands) > 1 and bands[-1][1] - bands[-1][0] < 3:
        # A 1-2 row tail is too small to locate, and one long band misaligns. Use a normal
        # band that overlaps the previous one; rooms already read are kept.
        bands[-1] = (n - BAND_ROWS, n)
    return bands


# Two independent passes: different band boundaries and zoom, so errors are unlikely to repeat.
PASSES = [(BAND_ROWS, 2), (3, 3)]


def extract(path: str, lay: Layout, model: str = MODEL, progress=None, second_pass: bool = False) -> SheetReading:
    img = load_image(path)
    n = len(lay.rooms)
    result = SheetReading()
    passes = PASSES if second_pass else PASSES[:1]
    plan = [(k, p, bnd) for p, (first, scale) in enumerate(passes)
            for k in ("electric", "water") for bnd in make_bands(n, first)]
    for done, (kind, p, (i0, i1)) in enumerate(plan, 1):
        scale = passes[p][1]
        if p == 0:
            store = result.electric if kind == "electric" else result.water
        else:
            store = result.alt_electric if kind == "electric" else result.alt_water
        rows, missing = read_band(img, lay, kind, i0, i1, model, scale)
        for r in rows:
            if r.room not in store or not _has_data(store[r.room]):
                store[r.room] = r
        if p == 0:
            result.unmatched += [f"{kind} {m}" for m in missing]
        if progress:
            progress(done / len(plan), f"{'double-check ' if p else ''}{kind} rows {lay.rooms[i0]}-{lay.rooms[i1 - 1]}")
    # a room that appeared in an overlapping band after being reported missing is no longer missing
    result.unmatched = [u for u in result.unmatched
                        if not _has_data((result.electric if u.startswith("electric") else result.water)[u.split(" ", 1)[1]])]
    return result


if __name__ == "__main__":
    lay = Layout.load(sys.argv[1])
    if len(sys.argv) > 3:  # e.g. 207:302 - read only part of the sheet
        a, b = sys.argv[3].split(":")
        i, j = lay.rooms.index(a), lay.rooms.index(b) + 1
        lay = Layout(**{**lay.__dict__, "rooms": lay.rooms[i:j],
                        "table_top": lay.table_top + i * (lay.table_bottom - lay.table_top) / len(lay.rooms),
                        "table_bottom": lay.table_top + j * (lay.table_bottom - lay.table_top) / len(lay.rooms)})
    res = extract(sys.argv[2], lay, progress=lambda f, m: print(f"{f:.0%} {m}", file=sys.stderr))
    if res.unmatched:
        print("UNMATCHED:", ", ".join(res.unmatched))
    from .calc import charges_for
    ch = charges_for(lay, res.electric, res.water)
    for room in lay.rooms:
        e, w = res.electric[room], res.water[room]
        flags = "; ".join(f"{c.kind}: {f}" for c in ch[room] for f in c.flags)
        print(f"{room:>4} | E {e.prev:>6} {e.curr:>6} {e.written:>10} | W {w.prev:>6} {w.curr:>6} {w.written:>10} | {flags}")
