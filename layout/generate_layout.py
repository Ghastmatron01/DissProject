#!/usr/bin/env python3
"""
English HO Layout Generator
Generates an XTrackCAD (.xtc) file for a 12x12ft room layout.

Layout features:
  - Double-track mainline around all four walls
  - Town scene on front wall with 66" passenger platform
  - 5-road yard off inner mainline
  - Branch line climbing 2% to coal mine on right-wall peninsula
  - Coal mine scene with run-around loop and 3 loading sidings
  - Provision for back-wall staging (future option)

Coordinate system:
  Origin (0,0) = front-left corner of room
  X increases toward the RIGHT wall
  Y increases toward the BACK wall
  Units: inches

Track angles (XTrackCAD convention):
  0.0   = heading EAST  (+X, toward right wall)
  90.0  = heading NORTH (+Y, toward back wall)
  180.0 = heading WEST  (-X, toward left wall)
  270.0 = heading SOUTH (-Y, toward front wall)
"""

import math
import os

# ---------------------------------------------------------------------------
# Room & benchwork
# ---------------------------------------------------------------------------
ROOM_W   = 144.0   # 12 ft wide
ROOM_H   = 144.0   # 12 ft deep
BW_DEPTH =  24.0   # around-the-wall benchwork depth (inches)

# Benchwork inner edges (aisle side)
BW_FRONT = BW_DEPTH            # Y = 24
BW_BACK  = ROOM_H - BW_DEPTH  # Y = 120
BW_LEFT  = BW_DEPTH            # X = 24
BW_RIGHT = ROOM_W - BW_DEPTH  # X = 120

# Door: centred on front wall, ~18" wide
DOOR_CX = ROOM_W / 2.0         # X = 72
DOOR_W  = 18.0

# ---------------------------------------------------------------------------
# Peninsula  (right-wall, 5 ft long x 24 in wide)
# Centred in the room (Y = 60-84), root at right-wall benchwork
# Aisles either side: Y=24..60 (36") and Y=84..120 (36")
# ---------------------------------------------------------------------------
PEN_X_ROOT = BW_RIGHT          # 120  — where peninsula meets right benchwork
PEN_X_END  =  60.0             # far (left) end of peninsula
PEN_Y_LOW  =  60.0             # south edge
PEN_Y_HIGH =  84.0             # north edge
PEN_Y_CEN  = (PEN_Y_LOW + PEN_Y_HIGH) / 2.0   # 72.0

# ---------------------------------------------------------------------------
# Mainline track positions
# ---------------------------------------------------------------------------
OUTER_WALL_OFFSET = 6.0
TRACK_SPACING_MM  = 55.0
TRACK_SPACING_IN  = TRACK_SPACING_MM / 25.4       # ~2.165"

# Outer loop track (close to wall)
OT_FRONT_Y = OUTER_WALL_OFFSET                    # 6.0
OT_RIGHT_X = ROOM_W - OUTER_WALL_OFFSET           # 138.0
OT_BACK_Y  = ROOM_H - OUTER_WALL_OFFSET           # 138.0
OT_LEFT_X  = OUTER_WALL_OFFSET                    # 6.0

# Inner loop track (55 mm toward room centre)
IT_FRONT_Y = OT_FRONT_Y + TRACK_SPACING_IN        # ~8.165
IT_RIGHT_X = OT_RIGHT_X - TRACK_SPACING_IN        # ~135.835
IT_BACK_Y  = OT_BACK_Y  - TRACK_SPACING_IN        # ~135.835
IT_LEFT_X  = OT_LEFT_X  + TRACK_SPACING_IN        # ~8.165

# Curve radii
R_OUTER  = 30.0   # outer mainline corners
R_INNER  = 27.0   # inner mainline corners
R_BRANCH = 24.0   # branch line (minimum)

# ---------------------------------------------------------------------------
# Outer loop corner centres
# ---------------------------------------------------------------------------
OC_FL = (OT_LEFT_X  + R_OUTER, OT_FRONT_Y + R_OUTER)  # (36,   36  )
OC_FR = (OT_RIGHT_X - R_OUTER, OT_FRONT_Y + R_OUTER)  # (108,  36  )
OC_BR = (OT_RIGHT_X - R_OUTER, OT_BACK_Y  - R_OUTER)  # (108,  108 )
OC_BL = (OT_LEFT_X  + R_OUTER, OT_BACK_Y  - R_OUTER)  # (36,   108 )

# Inner loop corner centres
IC_FL = (IT_LEFT_X  + R_INNER, IT_FRONT_Y + R_INNER)
IC_FR = (IT_RIGHT_X - R_INNER, IT_FRONT_Y + R_INNER)
IC_BR = (IT_RIGHT_X - R_INNER, IT_BACK_Y  - R_INNER)
IC_BL = (IT_LEFT_X  + R_INNER, IT_BACK_Y  - R_INNER)

# ---------------------------------------------------------------------------
# Platform  (outer mainline, front wall, 66" centred)
# ---------------------------------------------------------------------------
PLATFORM_LEN     = 66.0
PLATFORM_X_START = (ROOM_W / 2.0) - (PLATFORM_LEN / 2.0)   # 39.0
PLATFORM_X_END   = PLATFORM_X_START + PLATFORM_LEN           # 105.0
PLATFORM_Y       = OT_FRONT_Y                                 # 6.0

# ---------------------------------------------------------------------------
# Yard   (off inner mainline, front benchwork, right of centre)
# 5 roads: 3 sidings, 1 carriage siding, 1 loco spur
# Peco #6 equivalent: frog angle ~9.47°, approx length 9.5"
# ---------------------------------------------------------------------------
TURNOUT_FROG = 6
FROG_ANGLE   = math.degrees(math.atan(1.0 / TURNOUT_FROG))   # ~9.47°
TURNOUT_LEN  = 9.5

YD_START_X         = 82.0
YD_START_Y         = IT_FRONT_Y
YD_SIDING_SPACING  = TRACK_SPACING_IN * 2.5    # ~5.4"

YARD_ROADS    = 5
YARD_ROAD_LEN = 72.0
HEADSHUNT_LEN = 42.0

def yard_road_y(n):
    return YD_START_Y + (n + 1) * YD_SIDING_SPACING

def yard_start_x(n):
    return YD_START_X + (n + 1) * TURNOUT_LEN

# ---------------------------------------------------------------------------
# Branch line   (inner mainline → right-wall shelf → peninsula)
# Grade: 2% continuous, total rise 2.5"
# ---------------------------------------------------------------------------
BRANCH_START_X  = 96.0
BRANCH_START_Y  = IT_FRONT_Y
BRANCH_GRADE    = 0.02
BRANCH_RISE     = 2.5
BRANCH_PLAN_LEN = BRANCH_RISE / BRANCH_GRADE    # 125"

# S-curve arc lengths (quarter-circle each)
SEG1_LEN = math.pi * R_BRANCH / 2.0    # ~37.7"
SEG2_LEN = math.pi * R_BRANCH / 2.0    # ~37.7"

# Right-wall shelf straight (north, heading toward peninsula)
BR_SHELF_X  = ROOM_W - OUTER_WALL_OFFSET - TRACK_SPACING_IN * 4   # ~129.3"
BR_JOIN_Y   = 40.0

# Adjust shelf length so total plan length >= 125"
SEG4_LEN       = PEN_Y_CEN - PEN_Y_LOW          # ~12"
SEG3_LEN_ADJ   = max(BRANCH_PLAN_LEN - SEG1_LEN - SEG2_LEN - SEG4_LEN,
                     PEN_Y_LOW - BR_JOIN_Y)

def branch_elev(d):
    return min(BRANCH_GRADE * d, BRANCH_RISE)

ELEV_S1      = branch_elev(SEG1_LEN)
ELEV_S2      = branch_elev(SEG1_LEN + SEG2_LEN)
ELEV_SHELF   = branch_elev(SEG1_LEN + SEG2_LEN + SEG3_LEN_ADJ)
ELEV_MINE    = branch_elev(SEG1_LEN + SEG2_LEN + SEG3_LEN_ADJ + SEG4_LEN)

# ---------------------------------------------------------------------------
# Coal mine (peninsula far end)
# ---------------------------------------------------------------------------
MINE_X           = 66.0
MINE_Y_CEN       = PEN_Y_CEN    # 72.0
MINE_LOOP_OFFSET = TRACK_SPACING_IN * 3.0   # ~6.5" between loop legs
MINE_SIDING_LEN  = [27.0, 21.6, 16.2]      # 10 / 8 / 6 wagons @ 2.7" per wagon
MINE_SID_SPACING = TRACK_SPACING_IN * 3.0
MAINT_SPUR_LEN   = 12.0

# ---------------------------------------------------------------------------
# XTrackCAD file writer
# ---------------------------------------------------------------------------

class TrackWriter:
    def __init__(self, title="English HO Layout"):
        self.title  = title
        self.tracks = []
        self._id    = 1

    def _nid(self):
        tid = self._id
        self._id += 1
        return tid

    def straight(self, x, y, angle, length, elev=0.0, label=""):
        self.tracks.append(dict(type="STRAIGHT", id=self._nid(),
                                x=x, y=y, angle=angle, length=length,
                                elev=elev, label=label))

    def curve(self, cx, cy, a0, a1, radius, elev=0.0, label=""):
        """
        cx,cy  : arc centre
        a0,a1  : start/end angles from centre (degrees, 0=east, CCW positive)
        Clockwise arc: a0 > a1  (e.g. 270→0 wraps through 360)
        """
        self.tracks.append(dict(type="CURVE", id=self._nid(),
                                cx=cx, cy=cy, a0=a0, a1=a1, radius=radius,
                                elev=elev, label=label))

    def turnout(self, x, y, angle, hand="RH", label=""):
        self.tracks.append(dict(type="TURNOUT", id=self._nid(),
                                x=x, y=y, angle=angle, hand=hand, label=label))

    # -- formatters ----------------------------------------------------------

    def _fmt_straight(self, t):
        return (f"STRAIGHT {t['id']} 0 "
                f"{t['x']:.4f} {t['y']:.4f} "
                f"{t['angle']:.4f} {t['length']:.4f} "
                f"{t['elev']:.4f}")

    def _fmt_curve(self, t):
        return (f"CURVE {t['id']} 0 "
                f"{t['cx']:.4f} {t['cy']:.4f} "
                f"{t['a0']:.4f} {t['a1']:.4f} "
                f"{t['radius']:.4f} "
                f"{t['elev']:.4f}")

    def _fmt_turnout(self, t):
        div_sign   = -1 if t["hand"] == "RH" else 1
        div_angle  = t["angle"] + div_sign * FROG_ANGLE
        return (f"TURNOUT {t['id']} 0 "
                f"{t['x']:.4f} {t['y']:.4f} {t['angle']:.4f} "
                f"{t['hand']} {TURNOUT_FROG} {TURNOUT_LEN:.4f} "
                f"{div_angle:.4f}")

    # -- output --------------------------------------------------------------

    def write(self, path):
        with open(path, "w") as f:
            # Header
            f.write("XTrackCAD 2.0.0 Layout File\n")
            f.write(f"TITLE {self.title}\n")
            f.write("SCALE HO\n")
            f.write("DIMSCALE 1\n")
            f.write(f"ROOMSIZECOORDS 0.0000 0.0000 {ROOM_W:.4f} {ROOM_H:.4f}\n")
            f.write("SNAPGRID 1.0000 1.0000\n\n")

            current_label = None
            for t in self.tracks:
                lbl = t.get("label", "")
                if lbl and lbl != current_label:
                    current_label = lbl
                    f.write(f"\n# --- {lbl} ---\n")
                if t["type"] == "STRAIGHT":
                    f.write(self._fmt_straight(t) + "\n")
                elif t["type"] == "CURVE":
                    f.write(self._fmt_curve(t) + "\n")
                elif t["type"] == "TURNOUT":
                    f.write(self._fmt_turnout(t) + "\n")

            f.write("\n# END OF LAYOUT FILE\n")
            f.write(f"# Total elements: {self._id - 1}\n")


# ---------------------------------------------------------------------------
# Layout construction
# ---------------------------------------------------------------------------

def build_layout():
    w = TrackWriter("English HO Layout 12x12ft - BR Steam Era")

    # ------------------------------------------------------------------ #
    # OUTER MAINLINE  (clockwise, R=30")                                  #
    # ------------------------------------------------------------------ #
    LBL = "OUTER MAINLINE"

    # Front straight  E (X=36 → X=108, Y=6)
    w.straight(OC_FL[0], OT_FRONT_Y, 0.0,
               OC_FR[0] - OC_FL[0], label=LBL)

    # Front-right corner  (centre 108,36 — arc 270°→0°)
    w.curve(OC_FR[0], OC_FR[1], 270.0, 360.0, R_OUTER, label=LBL)

    # Right straight  N (X=138, Y=36 → Y=108)
    w.straight(OT_RIGHT_X, OC_FR[1], 90.0,
               OC_BR[1] - OC_FR[1], label=LBL)

    # Back-right corner  (centre 108,108 — arc 0°→90°)
    w.curve(OC_BR[0], OC_BR[1], 0.0, 90.0, R_OUTER, label=LBL)

    # Back straight  W (Y=138, X=108 → X=36)
    w.straight(OC_BR[0], OT_BACK_Y, 180.0,
               OC_BR[0] - OC_BL[0], label=LBL)

    # Back-left corner  (centre 36,108 — arc 90°→180°)
    w.curve(OC_BL[0], OC_BL[1], 90.0, 180.0, R_OUTER, label=LBL)

    # Left straight  S (X=6, Y=108 → Y=36)
    w.straight(OT_LEFT_X, OC_BL[1], 270.0,
               OC_BL[1] - OC_FL[1], label=LBL)

    # Front-left corner  (centre 36,36 — arc 180°→270°)
    w.curve(OC_FL[0], OC_FL[1], 180.0, 270.0, R_OUTER, label=LBL)

    # ------------------------------------------------------------------ #
    # INNER MAINLINE  (clockwise, R=27")                                  #
    # ------------------------------------------------------------------ #
    LBL = "INNER MAINLINE"

    w.straight(IC_FL[0], IT_FRONT_Y, 0.0,
               IC_FR[0] - IC_FL[0], label=LBL)

    w.curve(IC_FR[0], IC_FR[1], 270.0, 360.0, R_INNER, label=LBL)

    w.straight(IT_RIGHT_X, IC_FR[1], 90.0,
               IC_BR[1] - IC_FR[1], label=LBL)

    w.curve(IC_BR[0], IC_BR[1], 0.0, 90.0, R_INNER, label=LBL)

    w.straight(IC_BR[0], IT_BACK_Y, 180.0,
               IC_BR[0] - IC_BL[0], label=LBL)

    w.curve(IC_BL[0], IC_BL[1], 90.0, 180.0, R_INNER, label=LBL)

    w.straight(IT_LEFT_X, IC_BL[1], 270.0,
               IC_BL[1] - IC_FL[1], label=LBL)

    w.curve(IC_FL[0], IC_FL[1], 180.0, 270.0, R_INNER, label=LBL)

    # ------------------------------------------------------------------ #
    # PLATFORM  (66" on outer front straight)                             #
    # ------------------------------------------------------------------ #
    w.straight(PLATFORM_X_START, PLATFORM_Y + 4.0, 0.0,
               PLATFORM_LEN,
               label="PLATFORM 66inch Passenger Station")

    # ------------------------------------------------------------------ #
    # YARD  (5-road, off inner mainline, front benchwork)                 #
    # ------------------------------------------------------------------ #
    YARD_LABELS = [
        "YARD SIDING 1",
        "YARD SIDING 2",
        "YARD SIDING 3",
        "YARD CARRIAGE SIDING",
        "YARD LOCO SPUR",
    ]

    # Yard entrance turnout on inner mainline
    w.turnout(YD_START_X, YD_START_Y, 0.0, "RH", label="YARD THROAT TURNOUT 1")

    for n in range(YARD_ROADS):
        ty = yard_road_y(n)
        tx = yard_start_x(n)

        if n < YARD_ROADS - 1:
            # cascading turnout for next road
            w.turnout(tx, ty, 0.0, "RH",
                      label=f"YARD THROAT TURNOUT {n + 2}")

        # Siding straight
        lbl_s = YARD_LABELS[n] if n < len(YARD_LABELS) else f"YARD SIDING {n+1}"
        w.straight(tx, ty, 0.0, YARD_ROAD_LEN, label=lbl_s)

    # Headshunt (runs back along the right end of yard, heading east)
    w.straight(YD_START_X + YARD_ROAD_LEN,
               YD_START_Y,
               90.0, HEADSHUNT_LEN,
               label="YARD HEADSHUNT")

    # ------------------------------------------------------------------ #
    # BRANCH LINE  (inner mainline → right wall → peninsula, 2% grade)   #
    # ------------------------------------------------------------------ #

    # Diverging turnout off inner mainline
    w.turnout(BRANCH_START_X, BRANCH_START_Y, 0.0, "RH",
              label="BRANCH JUNCTION TURNOUT")

    # Arc 1: curve from heading east to heading north
    # Centre is R_BRANCH north of branch start (after turnout)
    a1_cx = BRANCH_START_X + TURNOUT_LEN
    a1_cy = BRANCH_START_Y + R_BRANCH
    w.curve(a1_cx, a1_cy, 270.0, 360.0, R_BRANCH,
            elev=ELEV_S1 / 2,
            label="BRANCH S-CURVE PART 1")

    # Arc 2: reverse curve from heading north to heading east (to aim at right wall)
    a2_cx = a1_cx + R_BRANCH
    a2_cy = a1_cy + R_BRANCH
    w.curve(a2_cx, a2_cy, 180.0, 270.0, R_BRANCH,
            elev=ELEV_S2,
            label="BRANCH S-CURVE PART 2")

    # Right-wall shelf straight heading north
    w.straight(BR_SHELF_X, BR_JOIN_Y, 90.0,
               SEG3_LEN_ADJ,
               elev=ELEV_SHELF,
               label="BRANCH RIGHT-WALL SHELF CLIMBING 2pct")

    # Curve onto peninsula (north→west, R=24")
    # Centre: at root of peninsula, R above PEN_Y_LOW
    pen_cx = PEN_X_ROOT - R_BRANCH
    pen_cy = PEN_Y_LOW  + R_BRANCH
    w.curve(pen_cx, pen_cy, 0.0, 90.0, R_BRANCH,
            elev=ELEV_SHELF,
            label="BRANCH CURVE ONTO PENINSULA")

    # Peninsula approach straight (heading west, toward mine)
    pen_app_len = pen_cx - MINE_X - TURNOUT_LEN
    w.straight(pen_cx, pen_cy, 180.0, pen_app_len,
               elev=ELEV_MINE,
               label="BRANCH PENINSULA APPROACH")

    # ------------------------------------------------------------------ #
    # COAL MINE SCENE  (peninsula far end)                                #
    # ------------------------------------------------------------------ #

    mine_base_elev = BRANCH_RISE

    # Run-around throat (LH turnout — loop goes to north/left side)
    w.turnout(MINE_X + TURNOUT_LEN, MINE_Y_CEN, 180.0, "LH",
              label="MINE RUN-AROUND THROAT TURNOUT")

    # Run-around south leg (trains enter going west, loop back east)
    w.straight(MINE_X + TURNOUT_LEN, MINE_Y_CEN - MINE_LOOP_OFFSET / 2,
               180.0, 24.0,
               elev=mine_base_elev,
               label="MINE RUN-AROUND SOUTH LEG")

    # Run-around north leg (heading east)
    w.straight(MINE_X, MINE_Y_CEN + MINE_LOOP_OFFSET / 2,
               0.0, 24.0,
               elev=mine_base_elev,
               label="MINE RUN-AROUND NORTH LEG")

    # West connecting curve (closes the loop)
    loop_r = MINE_LOOP_OFFSET / 2.0
    loop_cx = MINE_X - loop_r
    loop_cy = MINE_Y_CEN
    w.curve(loop_cx, loop_cy, 270.0, 90.0, loop_r,
            elev=mine_base_elev,
            label="MINE RUN-AROUND WEST CURVE")

    # Three loading sidings (off south leg, heading west)
    for i, slen in enumerate(MINE_SIDING_LEN):
        sid_y = MINE_Y_CEN - MINE_LOOP_OFFSET / 2 - (i + 1) * MINE_SID_SPACING
        tx = MINE_X + TURNOUT_LEN - i * TURNOUT_LEN
        w.turnout(tx, sid_y + MINE_SID_SPACING, 180.0, "LH",
                  label=f"MINE LOADING SIDING {i+1} TURNOUT")
        w.straight(tx - TURNOUT_LEN, sid_y, 180.0, slen,
                   elev=mine_base_elev,
                   label=f"MINE LOADING SIDING {i+1} ({int(slen/2.7)} wagons)")

    # Maintenance spur (off north leg, heading east into spur)
    maint_y = MINE_Y_CEN + MINE_LOOP_OFFSET / 2 + MINE_SID_SPACING
    w.turnout(MINE_X + 4, MINE_Y_CEN + MINE_LOOP_OFFSET / 2, 0.0, "RH",
              label="MINE MAINTENANCE SPUR TURNOUT")
    w.straight(MINE_X + 4 + TURNOUT_LEN, maint_y, 0.0, MAINT_SPUR_LEN,
               elev=mine_base_elev,
               label="MINE MAINTENANCE SPUR")

    # ------------------------------------------------------------------ #
    # BACK WALL  (double-track scenic, staging provision noted)           #
    # ------------------------------------------------------------------ #
    LBL = "BACK WALL SCENIC DOUBLE TRACK"
    back_outer_len = OC_BR[0] - OC_BL[0]
    back_inner_len = IC_BR[0] - IC_BL[0]
    w.straight(OC_BL[0], OT_BACK_Y, 180.0, back_outer_len, label=LBL)
    w.straight(IC_BL[0], IT_BACK_Y, 180.0, back_inner_len, label=LBL)

    # Staging provision turnout on inner mainline (future option)
    w.turnout(IC_BL[0] + 12, IT_BACK_Y, 180.0, "LH",
              label="STAGING PROVISION TURNOUT (FUTURE)")

    return w


# ---------------------------------------------------------------------------
# Summary printer
# ---------------------------------------------------------------------------

def print_summary():
    sep = "=" * 65
    print(sep)
    print("  ENGLISH HO LAYOUT — 12x12 ft — GEOMETRY SUMMARY")
    print(sep)
    print(f"  Room:                  {ROOM_W:.0f}\" x {ROOM_H:.0f}\"  "
          f"({ROOM_W/12:.0f} ft x {ROOM_H/12:.0f} ft)")
    print(f"  Benchwork depth:       {BW_DEPTH:.0f}\"")
    print(f"  Average aisle width:   ~33\"")
    print()
    print("  MAINLINE LOOPS")
    print(f"    Outer radius:        {R_OUTER:.0f}\"")
    print(f"    Inner radius:        {R_INNER:.0f}\"")
    print(f"    Track spacing:       {TRACK_SPACING_MM:.0f} mm  ({TRACK_SPACING_IN:.3f}\")")
    print(f"    Front straight:      {OC_FR[0]-OC_FL[0]:.1f}\"  outer loop")
    print(f"    Left straight:       {OC_BL[1]-OC_FL[1]:.1f}\"  for express running")
    print()
    print("  PASSENGER STATION  (front wall)")
    print(f"    Platform length:     {PLATFORM_LEN:.0f}\"  ({PLATFORM_LEN/12:.1f} ft)")
    print(f"    Platform X:          {PLATFORM_X_START:.1f}\" – {PLATFORM_X_END:.1f}\"")
    print()
    print("  YARD  (front benchwork)")
    print(f"    Roads:               {YARD_ROADS}")
    print(f"    Siding length:       {YARD_ROAD_LEN:.0f}\"  ({YARD_ROAD_LEN/12:.1f} ft)")
    print(f"    Headshunt:           {HEADSHUNT_LEN:.0f}\"  ({HEADSHUNT_LEN/12:.1f} ft)")
    print(f"    Turnout type:        #{TURNOUT_FROG} ({FROG_ANGLE:.1f}°)")
    print()
    print("  PENINSULA")
    print(f"    Width:               {PEN_Y_HIGH - PEN_Y_LOW:.0f}\"")
    print(f"    Length:              {PEN_X_ROOT - PEN_X_END:.0f}\"  "
          f"({(PEN_X_ROOT-PEN_X_END)/12:.1f} ft)")
    print(f"    Y centreline:        {PEN_Y_CEN:.0f}\"  "
          f"(aisle front {PEN_Y_LOW-BW_FRONT:.0f}\"  /  rear {BW_BACK-PEN_Y_HIGH:.0f}\")")
    print()
    print("  BRANCH LINE")
    print(f"    Start:               X={BRANCH_START_X:.1f}\", Y={BRANCH_START_Y:.3f}\"")
    print(f"    Minimum radius:      {R_BRANCH:.0f}\"")
    print(f"    Grade:               {BRANCH_GRADE*100:.0f}%  continuous")
    print(f"    Total rise:          {BRANCH_RISE:.2f}\"  at mine top")
    print(f"    Plan length needed:  {BRANCH_PLAN_LEN:.1f}\"  ({BRANCH_PLAN_LEN/12:.1f} ft)")
    print(f"    Shelf elevation:     +{ELEV_SHELF:.3f}\"")
    print(f"    Mine elevation:      +{ELEV_MINE:.3f}\"")
    print()
    print("  COAL MINE  (peninsula)")
    wagons = [10, 8, 6]
    for i, (slen, wag) in enumerate(zip(MINE_SIDING_LEN, wagons)):
        print(f"    Loading siding {i+1}:    {slen:.1f}\"  ({wag} wagons)")
    print(f"    Maintenance spur:    {MAINT_SPUR_LEN:.0f}\"")
    print(f"    Base elevation:      +{BRANCH_RISE:.2f}\"  above mainline")
    print()
    print("  TRACK RECOMMENDATION")
    print("    Peco Streamline HO Code 100 (affordable, robust, widely stocked)")
    print("    Turnouts: Peco SL-E395F (#6 Electrofrog) for clean running")
    print()
    print("  CONTROL")
    print("    File is wiring-neutral.  DCC recommended for multi-loco operation.")
    print(sep)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    out_dir  = os.path.dirname(os.path.abspath(__file__))
    out_file = os.path.join(out_dir, "english_ho_layout.xtc")

    print_summary()
    print()

    layout = build_layout()
    layout.write(out_file)

    n = layout._id - 1
    print(f"  Written {n} track elements to:")
    print(f"  {out_file}")
    print()
    print("  Open in XTrackCAD v4.3 or later via  File → Open.")
    print()
