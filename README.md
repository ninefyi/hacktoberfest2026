# apartment_a: reading sheet to CSV

Take a photo of the housekeeper's handwritten monthly meter sheet, check the numbers in a table, and download a CSV with every room's electric and water usage and cost. A local open model (Gemma 3) reads the handwriting; **nothing leaves your machine**.

Built for the [Hacktoberfest Weekend Challenge: Build for a Friend](https://dev.to/devteam/join-the-hacktoberfest-weekend-challenge-build-for-a-friend-2450-in-prizes-across-17-winners-1aj5), for someone close to me who has to turn this sheet into what each room owes every month.

## What you get

| ห้อง | ไฟ ก่อน | ไฟ ปัจจุบัน (a) | หน่วยไฟ (b) | ค่าไฟ (c) | น้ำ ก่อน | น้ำ ปัจจุบัน (x) | หน่วยน้ำ (y) | ค่าน้ำ (z) | ตรวจสอบ |
|---|---|---|---|---|---|---|---|---|---|

- (b) = (a) − previous reading, (c) = (b) × 7 baht
- (y) = (x) − previous reading, (z) = (y) × 28 baht
- a totals row at the bottom, and a note in the last column for rows that need a second look

## How it works

```
photo ─► crop 5 rows at a time ─► Gemma 3 12B (Ollama, local) ─► readings
      ─► you check / fix them in a table ─► usage × rate ─► .csv
```

- **Small crops, not the whole page.** Gemma mixes up columns on a full page. A crop of five rows (room column stitched onto the electric *or* the water block) reads far better.
- **Rows are matched by the printed room label**, never by position, so a tilted photo can't put one room's numbers on another's row.
- **The sheet checks itself.** The housekeeper also writes `units = baht` next to each reading. The app recomputes it from the readings and flags a row when they disagree, a reading goes down, or usage looks too high.
- **You confirm everything** in an editable table before you download.

## Run it

```bash
brew install ollama && ollama serve &     # or install from ollama.com
ollama pull gemma3:12b                    # ~8 GB; needs ~16 GB RAM
uv sync
uv run python -m billsplit.app
```

Open http://localhost:7860, drop in a photo, and follow steps 1 to 3. Try it with `demo/demo_sheet.jpg`, a fabricated sheet in the same template.

## Honest limits

- Handwriting is hard. On the real apartment_a sheet, most rows come out right, but expect a few wrong digits per sheet. That is why the check table exists. A wrong digit that also leaves the usage looking plausible and the housekeeper's written figure empty can slip past the flags, so read the table against the photo.
- The layout is calibrated for this one printed template (`layouts/apartment_a.yaml`). A very tilted photo can still shift rows.
- Reading a sheet takes about three to four minutes on a laptop.
- The CSV holds values, not formulas, so fix a wrong reading in the app's table before downloading.

## Privacy

Real sheets are in `.gitignore`. The repository contains only a fabricated demo sheet.

## License

MIT, see [LICENSE](LICENSE).
