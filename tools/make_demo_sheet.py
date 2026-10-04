"""Draw a fabricated reading sheet in the apartment_a template (invented numbers) for the public demo."""
import random

import yaml
from PIL import Image, ImageDraw, ImageFont

random.seed(11)
lay = yaml.safe_load(open("layouts/apartment_a.yaml", encoding="utf-8"))
W, H = 1108, 1477
ROOMS = lay["rooms"]
XS = [round(c * W) for c in lay["columns"]]
TOP, BOT = round(lay["table_top"] * H), round(lay["table_bottom"] * H)
ROW_H = (BOT - TOP) / len(ROOMS)
printed = ImageFont.truetype("/System/Library/Fonts/Supplemental/Tahoma.ttf", 22)
hand = ImageFont.truetype("/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf", 34)

img = Image.new("RGB", (W, H), "#f6f6f2")
d = ImageDraw.Draw(img)
d.text((W // 2, 250), "หอพักตัวอย่าง (ข้อมูลสมมติ)", font=printed, fill="black", anchor="ma")
d.text((W // 2, 300), "วันที่จด 25  เดือน มิ.ย.  พ.ศ. 69", font=printed, fill="black", anchor="ma")
heads = ["ห้อง", "มิเตอร์ไฟ\nเดือนก่อน", "มิเตอร์ไฟ\nปัจจุบัน", "ค่าไฟ", "มิเตอร์น้ำ\nเดือนก่อน", "มิเตอร์น้ำ\nปัจจุบัน", "ค่าน้ำ"]
hy = TOP - 70
for i, t in enumerate(heads):
    d.multiline_text(((XS[i] + XS[i + 1]) // 2, hy + 8), t, font=printed, fill="black", anchor="ma", align="center")
for i in range(len(ROOMS) + 1):
    y = round(TOP + i * ROW_H)
    d.line([(XS[0], y), (XS[-1], y)], fill="black", width=2)
d.line([(XS[0], TOP - 75), (XS[-1], TOP - 75)], fill="black", width=2)
for x in XS:
    d.line([(x, TOP - 75), (x, BOT)], fill="black", width=2)

truth, ink = {}, "#1a237e"
for r, room in enumerate(ROOMS):
    ep, wp = random.randint(100, 9000), random.randint(50, 900)
    eu, wu = random.randint(8, 70), random.randint(1, 12)
    truth[room] = dict(e_prev=ep, e_curr=ep + eu, e_units=eu, w_prev=wp, w_curr=wp + wu, w_units=wu)
    cells = [room, f"{ep:04d}", f"{ep + eu:04d}=", f"{eu}={eu * lay['electric_rate']}",
             f"{wp:04d}", f"{wp + wu:04d}=", f"{wu}={wu * lay['water_rate']}"]
    y = round(TOP + (r + 0.5) * ROW_H)
    for i, t in enumerate(cells):
        cx = (XS[i] + XS[i + 1]) // 2 + random.randint(-5, 5)
        d.text((cx, y + random.randint(-3, 3)), t, font=printed if i == 0 else hand,
               fill="black" if i == 0 else ink, anchor="mm")
img = img.rotate(-0.8, fillcolor="#f6f6f2", resample=Image.BICUBIC)
img.save("demo/demo_sheet.jpg", quality=90)
yaml.safe_dump(truth, open("demo/demo_truth.yaml", "w"))
print("wrote demo/demo_sheet.jpg and demo/demo_truth.yaml")
