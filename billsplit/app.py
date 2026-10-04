"""apartment_a: photo of the housekeeper's reading sheet -> review table -> .csv."""
import os
import tempfile

import gradio as gr
import pandas as pd

from .calc import charge, reconcile
from .export import build
from .extract import Layout, Reading, extract

LAYOUT_PATH = "layouts/apartment_a.yaml"
LAYOUT = Layout.load(LAYOUT_PATH)
COLS = ["ห้อง", "ไฟ ก่อน", "ไฟ ปัจจุบัน (a)", "หน่วยไฟ (b)", "ค่าไฟ (c)",
        "น้ำ ก่อน", "น้ำ ปัจจุบัน (x)", "หน่วยน้ำ (y)", "ค่าน้ำ (z)", "⚠ ตรวจสอบ"]
EDITABLE = {1, 2, 5, 6}
STATIC = [i for i in range(len(COLS)) if i not in EDITABLE]
MONTHS = ["มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน", "กรกฎาคม",
          "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"]


def _s(v) -> str:
    return "" if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip()


def _fill(df: pd.DataFrame, meta: dict) -> pd.DataFrame:
    """Recompute usage, cost and check column from the (possibly edited) readings."""
    out = df.copy()
    for i, row in out.iterrows():
        room = _s(row[COLS[0]])
        w = meta["written"].get(room, ("", ""))
        e = charge(Reading(room, _s(row[COLS[1]]), _s(row[COLS[2]]), w[0]), "electric", LAYOUT.electric_rate)
        t = charge(Reading(room, _s(row[COLS[5]]), _s(row[COLS[6]]), w[1]), "water", LAYOUT.water_rate)
        out.loc[i, COLS[3]] = "" if e.units is None else str(e.units)
        out.loc[i, COLS[4]] = "" if e.baht is None else str(e.baht)
        out.loc[i, COLS[7]] = "" if t.units is None else str(t.units)
        out.loc[i, COLS[8]] = "" if t.baht is None else str(t.baht)
        notes = [f"{'ไฟ' if c.kind == 'electric' else 'น้ำ'}: {f}" for c in (e, t) for f in c.flags]
        for kind, c, prev, curr in (("electric", e, row[COLS[1]], row[COLS[2]]), ("water", t, row[COLS[5]], row[COLS[6]])):
            alt = meta["alts"].get((kind, room))  # shown only while the row is unedited
            if alt and (_s(prev), _s(curr)) == (alt[0], alt[1]):
                notes.append(f"{'ไฟ' if kind == 'electric' else 'น้ำ'}: two reads disagree (other read {alt[2]}→{alt[3]})")
        out.loc[i, COLS[9]] = "; ".join(notes)
    return out


def read_sheet(photo, progress=gr.Progress()):
    if not photo:
        raise gr.Error("Upload a photo of the reading sheet first.")
    res = extract(photo, LAYOUT, progress=lambda f, m: progress(f, desc=m))
    alts = reconcile(res)
    rows, written = [], {}
    for room in LAYOUT.rooms:
        e, w = res.electric[room], res.water[room]
        rows.append([room, e.prev, e.curr, "", "", w.prev, w.curr, "", "", ""])
        written[room] = (e.written, w.written)
    meta = {"written": written, "alts": alts}
    out = _fill(pd.DataFrame(rows, columns=COLS), meta)
    for u in res.unmatched:  # no row with that label was found: make the user type it
        kind, room = u.split(" ", 1)
        i = out.index[out[COLS[0]] == room][0]
        note = f"{'ไฟ' if kind == 'electric' else 'น้ำ'}: row not found, type it in"
        out.loc[i, COLS[9]] = (out.loc[i, COLS[9]] + "; " if out.loc[i, COLS[9]] else "") + note
    return out, meta


def recheck(df, meta):
    return _fill(pd.DataFrame(df, columns=COLS), meta)


def to_csv(df, month_idx, year):
    df = pd.DataFrame(df, columns=COLS)
    rows = [dict(room=_s(r[COLS[0]]), e_prev=_s(r[COLS[1]]), e_curr=_s(r[COLS[2]]),
                 w_prev=_s(r[COLS[5]]), w_curr=_s(r[COLS[6]]), check=_s(r[COLS[9]]))
            for _, r in df.iterrows()]
    year = int(year)
    path = os.path.join(tempfile.mkdtemp(), f"apartment_a-{year}-{int(month_idx) + 1:02d}.csv")
    return build(rows, LAYOUT.electric_rate, LAYOUT.water_rate, path)


with gr.Blocks(title="apartment_a: sheet to CSV") as demo:
    gr.Markdown("# apartment_a — รูปใบจดมิเตอร์ → CSV\n"
                "Gemma runs on this computer; nothing is uploaded. "
                "**Check every number against the photo before you download.**")
    photo = gr.Image(type="filepath", label="Photo of the reading sheet")
    read_btn = gr.Button("1. Read the sheet", variant="primary")
    meta = gr.State({"written": {}, "alts": {}})
    table = gr.Dataframe(headers=COLS, interactive=True, static_columns=STATIC, wrap=True,
                         label="2. Check and fix the readings (usage, cost and ⚠ update as you edit)")
    with gr.Row():
        month = gr.Dropdown(MONTHS, value=MONTHS[5], type="index", label="Month")
        year = gr.Number(value=2569, label="Year (พ.ศ.)", precision=0)
    dl_btn = gr.Button("3. Make the CSV file", variant="primary")
    csv_file = gr.File(label="Download .csv")

    read_btn.click(read_sheet, photo, [table, meta])
    table.input(recheck, [table, meta], table)
    dl_btn.click(to_csv, [table, month, year], csv_file)

if __name__ == "__main__":
    demo.launch()
