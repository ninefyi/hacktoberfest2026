"""Score extraction on the fabricated demo sheet against its known answers."""
import sys
import time

import yaml

from billsplit.calc import charges_for, to_int
from billsplit.extract import Layout, extract

path = sys.argv[1] if len(sys.argv) > 1 else "demo/demo_sheet.jpg"
lay = Layout.load("layouts/apartment_a.yaml")
truth = yaml.safe_load(open("demo/demo_truth.yaml"))
t0 = time.time()
res = extract(path, lay); from billsplit.calc import reconcile; reconcile(res)
ch = charges_for(lay, res.electric, res.water)
ok = bad = silent = 0
for room in lay.rooms:
    t = truth[room]
    got = dict(e_prev=to_int(res.electric[room].prev), e_curr=to_int(res.electric[room].curr),
               w_prev=to_int(res.water[room].prev), w_curr=to_int(res.water[room].curr))
    wrong = [k for k in got if got[k] != t[k]]
    flagged = any(c.flags for c in ch[room])
    ok += 4 - len(wrong); bad += len(wrong)
    silent += bool(wrong) and not flagged
    if wrong:
        print(room, "WRONG", {k: (got[k], t[k]) for k in wrong}, "flagged" if flagged else "SILENT")
print(f"cells right {ok}/{ok + bad}; rows wrong but not flagged: {silent}; unmatched: {res.unmatched}; {time.time() - t0:.0f}s")
