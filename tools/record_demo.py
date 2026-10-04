"""Record the demo video: drives the real app (http://localhost:7860) in Chrome with the fabricated demo sheet.
The model takes ~3.5 minutes to read the sheet; that stretch is sped up in the final video."""
import glob
import os
import shutil
import subprocess
import time

import imageio_ffmpeg
import yaml
from playwright.sync_api import sync_playwright

URL = "http://localhost:7860"
SPEEDUP = 12
truth = yaml.safe_load(open("demo/demo_truth.yaml"))
FIRST_CELL = f"{truth['101']['e_prev']:04d}".lstrip("0")  # 101's electric previous reading

CAPTION_JS = """t => { let d = document.getElementById('cap');
  if (!d) { d = document.createElement('div'); d.id = 'cap';
    d.style.cssText = 'position:fixed;top:0;left:0;right:0;z-index:99999;padding:14px 20px;background:#111;color:#fff;font:600 20px system-ui;text-align:center';
    document.body.appendChild(d); }
  d.textContent = t; d.style.display = t ? 'block' : 'none'; }"""

os.makedirs("demo/_raw", exist_ok=True)
for f in glob.glob("demo/_raw/*"):
    os.remove(f)
marks = {}
with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", headless=True)
    t0 = time.time()
    ctx = b.new_context(viewport={"width": 1280, "height": 800}, record_video_dir="demo/_raw",
                        record_video_size={"width": 1280, "height": 800})
    pg = ctx.new_page()
    cap = lambda t: pg.evaluate(CAPTION_JS, t)
    pg.goto(URL); pg.wait_for_timeout(2000)
    cap("1. Drop in the photo of the housekeeper's sheet (demo data)"); pg.wait_for_timeout(1500)
    pg.set_input_files("input[type=file]", "demo/demo_sheet.jpg"); pg.wait_for_timeout(3500)
    cap("2. Gemma 3 reads it on this laptop. Nothing is uploaded.")
    pg.get_by_role("button", name="1. Read the sheet").click()
    marks["read_start"] = time.time() - t0
    pg.get_by_role("gridcell").filter(has_text=FIRST_CELL).first.wait_for(timeout=900_000)
    marks["read_end"] = time.time() - t0
    cap("3. Check the numbers against the photo"); pg.wait_for_timeout(1500)
    cell = pg.get_by_role("gridcell").filter(has_text=FIRST_CELL).first
    cell.scroll_into_view_if_needed(); pg.wait_for_timeout(3500)
    cur = pg.get_by_role("row").nth(1).get_by_role("gridcell").nth(2)
    right = cur.inner_text().strip()
    cap("A wrong digit? Fix it in the table. Usage, cost and the warning update.")
    cur.dblclick(); pg.wait_for_timeout(500); pg.keyboard.press("Meta+a")
    pg.keyboard.type(str(int(right) + 26).zfill(4), delay=120); pg.keyboard.press("Enter"); pg.wait_for_timeout(3500)
    cap("Put the right number back and the warning goes away.")
    cur = pg.get_by_role("row").nth(1).get_by_role("gridcell").nth(2)
    cur.dblclick(); pg.wait_for_timeout(500); pg.keyboard.press("Meta+a")
    pg.keyboard.type(right, delay=120); pg.keyboard.press("Enter"); pg.wait_for_timeout(3500)
    cap("4. Download the CSV")
    pg.get_by_role("button", name="3. Make the CSV file").click()
    pg.wait_for_timeout(3000)  # the file appears under "Download .csv"
    pg.evaluate("window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})")
    pg.wait_for_timeout(4500)
    ctx.close(); b.close()

raw = glob.glob("demo/_raw/*.webm")[0]
a, bnd = marks["read_start"] + 0.5, marks["read_end"] - 0.5
ff = imageio_ffmpeg.get_ffmpeg_exe()
fc = (f"[0:v]trim=0:{a},setpts=PTS-STARTPTS[v0];"
      f"[0:v]trim={a}:{bnd},setpts=(PTS-STARTPTS)/{SPEEDUP}[v1];"
      f"[0:v]trim={bnd},setpts=PTS-STARTPTS[v2];[v0][v1][v2]concat=n=3:v=1:a=0[v]")
subprocess.run([ff, "-y", "-i", raw, "-filter_complex", fc, "-map", "[v]", "-c:v", "libx264",
                "-pix_fmt", "yuv420p", "-crf", "24", "demo/demo.mp4"], check=True, capture_output=True)
shutil.rmtree("demo/_raw")
print("saved demo/demo.mp4", {k: round(v) for k, v in marks.items()})
