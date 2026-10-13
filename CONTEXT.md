# Hacktoberfest Weekend Challenge: Build for a Friend

A one-weekend build for a DEV challenge: an open-source-AI project that solves a real problem for a specific person the author knows.

## Language

**Challenge**:
The DEV "Hacktoberfest Weekend Challenge: Build for a Friend". Submissions close Oct 4, 11:59 PM PDT (Oct 5, 14:59 author-local, UTC+8).

**Friend**:
The person the project is built for: someone close to the author who turns the Reading sheet into what each Room owes. Consents to being described publicly.

**Housekeeper**:
The person who reads the meters and writes the figures by hand on the Reading sheet.

**Reading sheet**:
The housekeeper's handwritten monthly table for apartment_a: one row per Room, with electric and water meter figures. Delivered to the Friend as a photo.

**Room**:
One rental unit at apartment_a, numbered 101-108 and 201-208.

**Meter reading**:
The number a meter shows. Each Room has an electric and a water meter, each with a previous-month and a current-month reading.

**Usage**:
Current Meter reading minus previous Meter reading, for one meter of one Room.

**Charge**:
Usage multiplied by the unit rate: 7 baht per electric unit, 28 baht per water unit.

**Written figures**:
The Usage and Charge the housekeeper wrote on the Reading sheet. They are a cross-check only; the computed Usage and Charge are authoritative.

**Review table**:
The on-screen table of one row per Room, shown after the photo is read and before download, where the Friend can correct any Meter reading.

**CSV file**:
The .csv file downloaded from the Review table: one row per Room with Meter readings, Usage, Charge, a check note, and a totals row. Opens in Excel.

**Submission**:
The single DEV post, using the challenge template, that presents the project. Judged mainly on writing quality.

**Open model**:
An open-weights AI model run on the author's own machine (Gemma via a local runner), as opposed to a hosted closed service.

## Flagged ambiguities
- "Paperwork explainer" and "Payment form" (earlier ideas) are superseded: the product is now Reading sheet photo -> Review table -> CSV file. No payments, no QR, no other buildings.

---

# Hacktoberfest Open-Source AI Challenge: Week 1 "Touch Grass"

A second, separate project context. The sections above describe the earlier Weekend Challenge (meter sheets); this one describes the Week 1 build.

## Language

**Week 1 Challenge**:
The DEV "Hacktoberfest Open-Source AI Challenge: Week 1", theme "Touch Grass". Submissions close Oct 11, 11:59 PM PDT (Oct 12, 14:59 author-local, UTC+8). One entry per author, and it must be a new project.

**Walker**:
The person who goes outside and wears the Ring. The author, plus one other regular walker if they consent to being described.

**Ring**:
The Pebble Index 01: a button-and-microphone ring worn on a finger. Records only while the button is held.

**Walk**:
One outing between putting the Ring on and getting home. The unit the Journal is written for.

**Note**:
One spoken recording made with the Ring during a Walk, with its transcript. The Walker's own words are never overwritten.

**Mailbox**:
The public service on Render (a web backend plus a Postgres database) that accepts each Note forwarded by the Pebble phone app and holds it until the Walker collects it. It never runs the model.

**Pull**:
The command the Walker runs by hand on their own computer to collect new Notes from the Mailbox before reading them with the local model.

**Receiver**:
The small program on the author's computer that accepts Notes straight from the phone over home Wi-Fi. Kept as the fallback if the Mailbox does not work out.

**Observation**:
A structured fact the model pulls out of a Note (what was seen or thought, roughly where, when). Always shown beside the Note it came from.

**Journal**:
The Markdown write-up of one Walk: a short paragraph by the model, the Observations, and the Walker's own Notes kept visible. The Walker confirms it before it counts.

**Field test**:
A real Walk of 45+ minutes with the Ring, documented honestly (what worked, what the Ring or model got wrong).

**Submission**:
The single DEV post, using the challenge template, tagged `devchallenge` and `hf26challenge`. Judged mostly on writing.

## Flagged ambiguities
- "Open-source AI at the core" means the local model (Gemma via Ollama) plus the open Pebble transcription. Notes pass through the Mailbox, but no hosted model ever reads them.

---

# Hacktoberfest Open-Source AI Challenge: Week 2 "Side Hustle"

A third, separate project context. The sections above describe the Weekend and Week 1 builds; this one describes the Week 2 build.

## Language

**Week 2 Challenge**:
The DEV "Hacktoberfest Open-Source AI Challenge: Week 2", theme "Side Hustle": build something with open-source AI that someone would actually pay for. Submissions close Oct 18, 11:59 PM PDT (Oct 19, 14:59 author-local, UTC+8). One entry per author, and it must be a new project.

**Traveller**:
The person who takes a Trip photo and wants something to post about it on their own social account. Uses the tool for free.

**Trip photo**:
One photo of a place the Traveller visited.

**Place**:
The place name on a Post kit. Always the Traveller's own text: either typed in the Place field or accepted from a Place guess. Never written into the Post kit without the Traveller's confirmation.

**Note**:
The optional short text the Traveller types with a Trip photo about what it shows or how it felt.

**Place guess**:
The local model's suggestion of what place a Trip photo shows, offered when the Place field is empty. Labelled as a guess, shown beside the Place field for the Traveller to accept, edit or ignore. Not used in the title, caption or hashtags until confirmed.

**Post kit**:
What the tool returns for one Trip photo: an image title, the Place (empty with a warning if the Traveller gave none), a one-sentence caption, and at least 3 hashtags. Thai by default, with a Thai/English switch.

**Post-as-is rate**:
The share of Post kits the First user accepts without editing.

**Accuracy bar**:
The pre-set threshold for "accurate enough to stop being free": Post-as-is rate of at least 70% on the Eval set, with 0 invented place names (a Place on a Post kit that the Traveller did not type or confirm). Fixed before testing. The Place guess hit rate is reported alongside, with no threshold.

**Eval set**:
The author's own 20 Trip photos, each with a known Place and a Note (about 15 are recognisable places, 5 are unnamed or ordinary views). Published examples have GPS and identifiable faces removed.

**First user**:
The one person the author knows who tries the tool on their phone over home Wi-Fi and judges the Post kits.

**Future payer**:
A hypothetical customer who might pay later (for example a page admin or homestay owner who posts places for income). A hypothesis only; no price is asked and no demand is claimed.

**Submission**:
The single DEV post, using the challenge template, tagged `devchallenge` and `hf26challenge`. Judged mostly on writing.

## Flagged ambiguities
- "Free" vs "Side Hustle": the tool is free now and willingness to pay is unproven; the post says so.
- The model may guess a place from the image (Place guess), but a guess is not a Place until the Traveller confirms it. "Invented place name" means a Place on a Post kit the Traveller did not type or confirm.
- An earlier rule had the place name copied only from a single caption ("Place hint"); the spike showed the model copied the whole caption into the place field, so it was replaced by separate Place and Note fields.
