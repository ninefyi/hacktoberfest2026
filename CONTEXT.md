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
