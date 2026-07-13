# English HO Layout — 12×12 ft Room

This folder contains the XTrackCAD layout file and the Python script that generated it.

## Files

| File | Purpose |
|------|---------|
| `english_ho_layout.xtc` | XTrackCAD layout file — open directly in XTrackCAD |
| `generate_layout.py` | Python script that computes all geometry and writes the `.xtc` file |

## How to open

1. Download and install **XTrackCAD** (free): https://xtrkcad-fork.sourceforge.net/
2. Open XTrackCAD → **File → Open** → select `english_ho_layout.xtc`

## Layout overview

| Feature | Value |
|---------|-------|
| Room size | 12 ft × 12 ft |
| Scale | HO (1:87, 16.5 mm gauge) |
| Era | BR Steam with some BR Blue Diesel |
| Benchwork | 24" around walls + 24" wide peninsula |
| Average aisle | ~33" |

### Mainline
- **Outer loop** — 30" radius corners
- **Inner loop** — 27" radius corners, 55 mm (2.165") spacing
- Front straight: **72"** — passenger station & 66" platform here
- Left straight: **72"** — express running

### Yard (front benchwork)
- 5 roads: 3 sidings, 1 carriage siding, 1 loco spur
- Siding length: **72"** (6 ft)
- Headshunt: **42"** (3.5 ft)
- Turnouts: **#6** throughout

### Branch line to coal mine
- Diverges from inner mainline at X = 96"
- **2% continuous grade** — rises **+2.5"** over ~125" plan length
- Minimum curve radius: **24"**

### Coal mine (peninsula end)
| Siding | Length | Capacity |
|--------|--------|----------|
| Loading siding 1 | 27" | 10 wagons |
| Loading siding 2 | 21.6" | 8 wagons |
| Loading siding 3 | 16.2" | 6 wagons |
| Maintenance spur | 12" | 1–2 locos |

### Peninsula
- Width: **24"**, Length: **60"** (5 ft)
- Centred at Y = 72" — aisles **36"** front and rear
- Attached to right-wall benchwork

### Back wall
- Scenic double-track mainline
- One staging provision turnout (future option)

## Recommended track

| Item | Suggestion |
|------|-----------|
| Flex track | Peco Streamline Code 100 HO |
| Turnouts | Peco SL-E395F (#6 Electrofrog) |
| Reason | Affordable, widely stocked in UK, works with all HO rolling stock |

## Control system note

The `.xtc` file is **wiring-neutral**. DCC is strongly recommended for this layout
(independent control of passenger trains, freight, and mine shunter simultaneously
without complex block wiring). A starter DCC set (e.g. Hornby Elite or Bachmann
EZ Command) is a good starting point.

## Regenerating the file

```bash
cd layout
python3 generate_layout.py
```

The script prints a full geometry summary and rewrites `english_ho_layout.xtc`.

## Future work / iterations

- [ ] Confirm room door/window positions and adjust benchwork notch
- [ ] Add lift-out gate at door opening if desired
- [ ] Add back-wall hidden staging (2–3 tracks off inner mainline)
- [ ] Refine branch S-curve alignment once XTrackCAD visual check is done
- [ ] Add structure/scenery annotation elements
