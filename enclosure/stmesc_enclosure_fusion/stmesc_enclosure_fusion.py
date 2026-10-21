"""
STM ESC — Professional Product Enclosure
Fusion 360 API Script  v4  (Professional Edition)
==================================================
Product features implemented:
  FRONT face  : 1× Power IN connector  (XT30, 12×9 mm)
  REAR  face  : 2× Motor OUT connectors (XT30, 12×9 mm each)
  LEFT / RIGHT: Ventilation fin array  (5 slots per side)
  LID top     : 3× LED indicator windows  (Ø3.5 mm)
                1× Mode button  (Ø8 mm hole, Ø12 mm recess)
                "STM ESC" embossed label
                Vent slot array
  BOTTOM      : 4× PCB standoff bosses  (M2.5)
  SIDES       : 2× Mounting tabs with M3 holes

HOW TO RUN:
  1. Fusion 360  →  File → New Design
  2. Shift+S  →  Scripts and Add-Ins  →  "+"  →  browse here  →  Open
  3. Select "stmesc_enclosure_fusion"  →  Run
  4. File → Save  (saves as .f3d)
"""

import adsk.core, adsk.fusion, traceback, math

# ═══════════════════════════════════════════════
#  PARAMETERS  (all mm)
# ═══════════════════════════════════════════════

# ── PCB
PCB_W, PCB_D, PCB_T = 55.0, 45.0, 1.6
PCB_R = 2.5

# ── Clearances & walls
XY_GAP    = 0.5
Z_BOT_GAP = 2.0
Z_TOP_GAP = 15.0
WALL      = 2.0
FLOOR_T   = 1.5
LID_T     = 2.0
LIP_H     = 3.0

# ── Derived
IN_W  = PCB_W + 2*XY_GAP         # 56
IN_D  = PCB_D + 2*XY_GAP         # 46
IN_H  = Z_BOT_GAP + PCB_T + Z_TOP_GAP   # 19.1
OUT_W = IN_W + 2*WALL              # 60
OUT_D = IN_D + 2*WALL              # 50
OUT_R = PCB_R + WALL               # 4.5
BASE_H= IN_H + FLOOR_T             # 20.6

# ── PCB standoff bosses
BOSS_R, BOSS_H, SCREW_R, BOSS_INSET = 2.5, Z_BOT_GAP+0.5, 1.25, 3.0
BOSS_PTS = [
    (WALL+BOSS_INSET,       WALL+BOSS_INSET),
    (WALL+IN_W-BOSS_INSET,  WALL+BOSS_INSET),
    (WALL+IN_W-BOSS_INSET,  WALL+IN_D-BOSS_INSET),
    (WALL+BOSS_INSET,       WALL+IN_D-BOSS_INSET),
]

# ── Lid corner screw posts
POST_R, POST_H, POST_SCR_R = 2.5, 5.0, 1.25
POST_Z = FLOOR_T + IN_H - POST_H
POST_PTS = [
    (WALL*0.5,        WALL*0.5),
    (OUT_W-WALL*0.5,  WALL*0.5),
    (OUT_W-WALL*0.5,  OUT_D-WALL*0.5),
    (WALL*0.5,        OUT_D-WALL*0.5),
]

# ── FRONT face (Y=0): Power IN connector  XT30
PWR_W, PWR_H = 12.0, 9.0
PWR_X = (OUT_W - PWR_W) / 2   # centered = 24 mm from left
PWR_Z = FLOOR_T + Z_BOT_GAP   # = 3.5 mm from base bottom

# ── REAR face (Y=OUT_D): 2× Motor OUT connectors
MOT_W, MOT_H = 12.0, 9.0
MOT_GAP = 8.0                  # gap between the two connectors
_tot = 2*MOT_W + MOT_GAP       # = 32
MOT_X1 = (OUT_W - _tot) / 2   # = 14 mm from left
MOT_X2 = MOT_X1 + MOT_W + MOT_GAP   # = 34 mm from left
MOT_Z  = FLOOR_T + Z_BOT_GAP  # same height as power connector

# ── Side ventilation fins (X=0 and X=OUT_W faces)
VENT_N    = 5
VENT_W_SZ = 1.5    # slot width  (Z direction)
VENT_L_SZ = 15.0   # slot length (Y direction)
VENT_GAP  = 3.5    # gap between slots
VENT_Z0   = FLOOR_T + 4.0   # first slot starts here

# ── Mounting tabs (on left X=0 and right X=OUT_W faces)
TAB_W_SZ  = 9.0    # extent along Y
TAB_OUT   = 5.0    # protrusion beyond wall
TAB_H_SZ  = 2.5    # tab thickness (height)
TAB_SCR_R = 1.6    # M3 clearance

# ── LID: 3 LED indicator windows  (top face)
LED_R     = 1.75         # radius → 3.5 mm diameter hole
LED_Y_POS = 8.0          # from front edge of lid
LED_XS    = [14.0, 21.5, 29.0]   # x positions relative to lid left edge

# LED surround recess (shallow trough around LED row)
LTROUGH_W = (LED_XS[-1] - LED_XS[0]) + 2*LED_R + 6.0   # ≈ 22.5 mm
LTROUGH_H = 7.0
LTROUGH_D = 0.6   # recess depth

# ── LID: Mode button
BTN_X_POS  = 47.0    # from lid left edge
BTN_Y_POS  = 8.0     # same row as LEDs
BTN_R      = 4.0     # through hole radius  (8 mm button)
BTN_RCS_R  = 6.5     # surrounding recess radius
BTN_RCS_D  = 0.8     # recess depth

# ── LID: top vent slots (centered, rear half of lid)
LVNT_N   = 6
LVNT_W   = 1.5
LVNT_L   = 18.0
LVNT_GAP = 3.0


# ═══════════════════════════════════════════════
#  HELPERS
# ═══════════════════════════════════════════════

NewBody = adsk.fusion.FeatureOperations.NewBodyFeatureOperation
Join    = adsk.fusion.FeatureOperations.JoinFeatureOperation
Cut     = adsk.fusion.FeatureOperations.CutFeatureOperation


def c(mm):   return mm / 10.0
def v(mm):   return adsk.core.ValueInput.createByReal(c(mm))
def pt(x, y, z=0): return adsk.core.Point3D.create(c(x), c(y), c(z))


def zplane(comp, z_mm):
    inp = comp.constructionPlanes.createInput()
    inp.setByOffset(comp.xYConstructionPlane, v(z_mm))
    return comp.constructionPlanes.add(inp)


def rect_prof(comp, z_mm, x, y, w, d):
    """Sketch a rectangle and return its profile."""
    sk = comp.sketches.add(zplane(comp, z_mm))
    sk.sketchCurves.sketchLines.addTwoPointRectangle(
        pt(x, y), pt(x+w, y+d))
    return sk.profiles.item(0)


def ext(comp, prof, h, op, bods=None):
    """Extrude profile."""
    inp = comp.features.extrudeFeatures.createInput(prof, op)
    inp.setDistanceExtent(False, v(h))
    if bods:
        inp.participantBodies = bods
    return comp.features.extrudeFeatures.add(inp)


def cut_rect(comp, body, x, y, z, w, d, h):
    prof = rect_prof(comp, z, x, y, w, d)
    ext(comp, prof, h, Cut, [body])


def cyl(comp, body, cx, cy, z, r, h, join=True):
    sk = comp.sketches.add(zplane(comp, z))
    sk.sketchCurves.sketchCircles.addByCenterRadius(pt(cx, cy), c(r))
    ext(comp, sk.profiles.item(0), h, Join if join else Cut, [body])


def fillet_vert(comp, body, r):
    """Fillet all Z-parallel edges (vertical corners)."""
    col = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        try:
            g = edge.geometry
            if g.curveType == adsk.core.Curve3DTypes.Line3DCurveType:
                s, e = g.startPoint, g.endPoint
                if math.hypot(e.x-s.x, e.y-s.y) < 1e-4:
                    col.add(edge)
        except Exception:
            pass
    if col.count:
        fi = comp.features.filletFeatures.createInput()
        fi.addConstantRadiusEdgeSet(col, v(r), True)
        comp.features.filletFeatures.add(fi)


def fillet_z(comp, body, z_mm, r):
    """Fillet all edges at a given Z height (top or bottom perimeter)."""
    z = c(z_mm)
    col = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        try:
            bb = edge.boundingBox
            if abs(bb.minPoint.z - z) < 0.003 and abs(bb.maxPoint.z - z) < 0.003:
                col.add(edge)
        except Exception:
            pass
    if col.count:
        try:
            fi = comp.features.filletFeatures.createInput()
            fi.addConstantRadiusEdgeSet(col, v(r), True)
            comp.features.filletFeatures.add(fi)
        except Exception:
            pass   # top fillet is cosmetic — skip if it fails


def label_emboss(comp, body, x_off):
    """Emboss 'STM ESC' text on top of lid (cosmetic, optional)."""
    try:
        pl  = zplane(comp, LID_T)
        sk  = comp.sketches.add(pl)
        ti  = sk.sketchTexts.createInput2("STM ESC", c(5))
        ti.setAsMultiLine(
            pt(x_off + OUT_W*0.28, OUT_D*0.68),
            pt(x_off + OUT_W*0.72, OUT_D*0.68),
            adsk.fusion.HorizontalAlignments.CenterHorizontalAlignment,
            adsk.fusion.VerticalAlignments.MiddleVerticalAlignment, 0)
        sk.sketchTexts.add(ti)
        if sk.profiles.count:
            col = adsk.core.ObjectCollection.create()
            for i in range(sk.profiles.count):
                col.add(sk.profiles.item(i))
            inp2 = comp.features.extrudeFeatures.createInput(col, Cut)
            inp2.setDistanceExtent(False, v(-0.5))
            inp2.participantBodies = [body]
            comp.features.extrudeFeatures.add(inp2)
    except Exception:
        pass


# ═══════════════════════════════════════════════
#  BUILD BASE
# ═══════════════════════════════════════════════

def build_base(comp):
    # 1 ── Outer solid box
    feat = ext(comp, rect_prof(comp, 0, 0, 0, OUT_W, OUT_D), BASE_H, NewBody)
    body = feat.bodies.item(0)
    body.name = "ESC_Base"

    # 2 ── Round the four vertical corner edges
    fillet_vert(comp, body, OUT_R)

    # 3 ── Soft fillet on top rim (premium product finish)
    fillet_z(comp, body, BASE_H, 1.0)

    # 4 ── Hollow out the interior
    cut_rect(comp, body, WALL, WALL, FLOOR_T, IN_W, IN_D, IN_H + 1)

    # 5 ── PCB standoff bosses  (4 corners)
    for bx, by in BOSS_PTS:
        cyl(comp, body, bx, by, FLOOR_T,  BOSS_R,  BOSS_H,         join=True)
        cyl(comp, body, bx, by, 0,         SCREW_R, BOSS_H+FLOOR_T+0.1, join=False)

    # 6 ── Lid screw posts  (4 inner corners)
    for px, py in POST_PTS:
        cyl(comp, body, px, py, POST_Z, POST_R,    POST_H,    join=True)
        cyl(comp, body, px, py, POST_Z, POST_SCR_R, POST_H+0.1, join=False)

    # 7 ── FRONT face (Y=0): Power IN  XT30
    cut_rect(comp, body,
             PWR_X,  -0.1,  PWR_Z,
             PWR_W,  WALL+0.2,  PWR_H)

    # 8 ── REAR face (Y=OUT_D): Motor 1 + Motor 2
    cut_rect(comp, body,
             MOT_X1,  OUT_D-WALL-0.1,  MOT_Z,
             MOT_W,   WALL+0.2,         MOT_H)
    cut_rect(comp, body,
             MOT_X2,  OUT_D-WALL-0.1,  MOT_Z,
             MOT_W,   WALL+0.2,         MOT_H)

    # 9 ── Side ventilation slots  (left X=0 and right X=OUT_W faces)
    vy0 = (OUT_D - VENT_L_SZ) / 2
    for side in (0, 1):
        x0 = -0.1 if side == 0 else OUT_W - WALL - 0.1
        for i in range(VENT_N):
            vz = VENT_Z0 + i * (VENT_W_SZ + VENT_GAP)
            cut_rect(comp, body, x0, vy0, vz, WALL+0.2, VENT_L_SZ, VENT_W_SZ)

    # 10 ── Mounting tabs  (left and right faces, at base level)
    for side in (0, 1):
        tx  = -TAB_OUT  if side == 0 else OUT_W
        ty  = (OUT_D - TAB_W_SZ) / 2
        tcx = -TAB_OUT/2 if side == 0 else OUT_W + TAB_OUT/2
        prof_tab = rect_prof(comp, 0, tx, ty, TAB_OUT, TAB_W_SZ)
        ext(comp, prof_tab, TAB_H_SZ, Join, [body])
        cyl(comp, body, tcx, OUT_D/2, -0.1, TAB_SCR_R, TAB_H_SZ+0.2, join=False)

    return body


# ═══════════════════════════════════════════════
#  BUILD LID
# ═══════════════════════════════════════════════

def build_lid(comp, x_off=0):
    # 1 ── Panel
    feat = ext(comp, rect_prof(comp, 0, x_off, 0, OUT_W, OUT_D), LID_T, NewBody)
    body = feat.bodies.item(0)
    body.name = "ESC_Lid"

    # 2 ── Round vertical corners
    fillet_vert(comp, body, OUT_R)

    # 3 ── Soft fillet on top face perimeter
    fillet_z(comp, body, LID_T, 1.0)

    # 4 ── Snap lip (hangs down from panel bottom face)
    lx = x_off + WALL - 0.3
    ly = WALL - 0.3
    prof_lip = rect_prof(comp, 0, lx, ly, IN_W+0.6, IN_D+0.6)
    inp_lip = comp.features.extrudeFeatures.createInput(prof_lip, Join)
    inp_lip.setDistanceExtent(False, v(-LIP_H))
    inp_lip.participantBodies = [body]
    comp.features.extrudeFeatures.add(inp_lip)

    # 5 ── Lid screw through-holes  (align with base posts)
    for px, py in POST_PTS:
        cyl(comp, body, x_off+px, py, -LIP_H-0.1,
            POST_SCR_R, LID_T+LIP_H+0.2, join=False)

    # ── ── ── ── ── ── ── ── ──
    #  FRONT STRIP  (y near 0)
    #  LED trough recess + 3 LED holes + mode button recess + button hole
    # ── ── ── ── ── ── ── ── ──

    # 6 ── LED surround trough  (shallow rectangular recess on top face)
    ltr_cx = (LED_XS[0] + LED_XS[-1]) / 2        # 21.5 (center of 3 LEDs)
    ltr_x  = x_off + ltr_cx - LTROUGH_W / 2       # left edge of trough
    ltr_y  = LED_Y_POS - LTROUGH_H / 2            # = 4.5
    cut_rect(comp, body,
             ltr_x, ltr_y, LID_T - LTROUGH_D,
             LTROUGH_W, LTROUGH_H, LTROUGH_D + 0.1)

    # 7 ── LED through-holes  (3 × Ø3.5 mm)
    for lx_rel in LED_XS:
        cyl(comp, body, x_off+lx_rel, LED_Y_POS,
            -0.1, LED_R, LID_T+0.2, join=False)

    # 8 ── Mode button recess  (circular, 0.8 mm deep)
    cyl(comp, body, x_off+BTN_X_POS, BTN_Y_POS,
        LID_T - BTN_RCS_D, BTN_RCS_R, BTN_RCS_D+0.1, join=False)

    # 9 ── Mode button through-hole  (Ø8 mm)
    cyl(comp, body, x_off+BTN_X_POS, BTN_Y_POS,
        -0.1, BTN_R, LID_T+0.2, join=False)

    # ── ── ── ── ── ── ── ── ──
    #  REAR HALF  – vent slots
    # ── ── ── ── ── ── ── ── ──

    # 10 ── Top vent slots  (centered on rear portion of lid)
    total_vw = LVNT_N * LVNT_W + (LVNT_N-1) * LVNT_GAP   # = 24 mm
    vx0  = x_off + (OUT_W - total_vw) / 2                  # centered X
    vy0  = OUT_D * 0.50                                      # starts at Y=25
    for i in range(LVNT_N):
        vx = vx0 + i * (LVNT_W + LVNT_GAP)
        cut_rect(comp, body, vx, vy0, -0.1, LVNT_W, LVNT_L, LID_T+0.2)

    # 11 ── "STM ESC" emboss label  (optional)
    label_emboss(comp, body, x_off)

    return body


# ═══════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════

def run(context):
    ui = None
    try:
        app    = adsk.core.Application.get()
        ui     = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)

        if not design:
            ui.messageBox(
                "Please open a Fusion 360 Design first.\n(File → New Design)",
                "STM ESC Enclosure")
            return

        design.designType = adsk.fusion.DesignTypes.ParametricDesignType
        root = design.rootComponent

        msg = (
            "STM ESC Enclosure  —  Professional Edition\n"
            "─────────────────────────────────────────\n"
            "  FRONT : Power IN  (XT30,  12×9 mm)\n"
            "  REAR  : Motor 1 + Motor 2  (XT30 each)\n"
            "  SIDES : 5× ventilation slots\n"
            "  TOP   : 3× LED windows  +  Mode button\n"
            "          'STM ESC' label  +  vent array\n"
            "  TABS  : M3 mounting holes (left & right)\n"
            "─────────────────────────────────────────\n"
            "Click OK to build  (~30 seconds)"
        )
        ui.messageBox(msg, "STM ESC Enclosure v4")

        build_base(root)
        build_lid(root, x_off=OUT_W + 10)   # lid placed to the right for export

        design.timeline.moveToEnd()

        ui.messageBox(
            "Done!  Two bodies created:\n\n"
            "  ESC_Base  —  60 × 50 × 20.6 mm\n"
            "  ESC_Lid   —  60 × 50 ×  2.0 mm  (+3 mm lip)\n\n"
            "Next steps:\n"
            "  • File → Save → .f3d\n"
            "  • Make → 3D Print → export STL per body\n"
            "  • Apply 'Appearance' for colour/material preview",
            "Complete!")

    except Exception:
        if ui:
            ui.messageBox("Script error:\n\n" + traceback.format_exc())
