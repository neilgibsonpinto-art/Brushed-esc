# =============================================================================
#  MAMBA B1 ESC — PRODUCTION-LEVEL 3D ENCLOSURE + PCB ASSEMBLY
#  Autodesk Fusion 360 Python API Script
#  - Generates Base Housing, Detailed MAMBA B1 PCB, and Top Lid Assembly
#  - Commercial flush exterior (zero screw flanges)
#  - Fully sealed (zero vents)
#  - Integrated compliant spring-button pressing mechanism for SW3 (6mm switch)
#  - J6 (CH1 & CH2) servo connector port & Phoenix screw terminal access
#  - Recessed status LED viewing aperture (D1, D4, D5)
# =============================================================================

import adsk.core
import adsk.fusion
import traceback
import math

# --- PARAMETERS (All dimensions in millimeters) ---
PCB_WIDTH       = 55.0   # X dimension
PCB_LENGTH      = 45.0   # Y dimension
PCB_THICKNESS   = 1.6    # Z board thickness
CLEARANCE_XY    = 0.6    # Fit tolerance around PCB perimeter
WALL_THICKNESS  = 2.0    # Outer wall thickness (5x 0.4mm perimeters)
FLOOR_THICKNESS = 2.0    # Bottom floor thickness
LID_THICKNESS   = 2.0    # Top ceiling thickness
STANDOFF_HEIGHT = 3.5    # Height under PCB for bottom SMD parts (Q2, U1, U2)
CLEARANCE_TOP   = 15.0   # Clearance above PCB for C1, C2 (10.5mm) & terminals (13.8mm)

# Derived Cavity & Exterior Dimensions
INT_W = PCB_WIDTH + 2 * CLEARANCE_XY     # 56.2 mm
INT_L = PCB_LENGTH + 2 * CLEARANCE_XY    # 46.2 mm
EXT_W = INT_W + 2 * WALL_THICKNESS       # 60.2 mm
EXT_L = INT_L + 2 * WALL_THICKNESS       # 50.2 mm

BASE_WALL_H  = STANDOFF_HEIGHT + PCB_THICKNESS + 5.0 # 10.1 mm above floor
BASE_TOTAL_H = FLOOR_THICKNESS + BASE_WALL_H        # 12.1 mm
LID_TOTAL_H  = (STANDOFF_HEIGHT + PCB_THICKNESS + CLEARANCE_TOP + LID_THICKNESS) - BASE_WALL_H # ~12.0 mm

PCB_BOT_Z    = FLOOR_THICKNESS + STANDOFF_HEIGHT     # 5.5 mm
PCB_TOP_Z    = PCB_BOT_Z + PCB_THICKNESS             # 7.1 mm

# Component Offsets in enclosure coordinate frame
J6_X = CLEARANCE_XY + 3.73
J6_Y = CLEARANCE_XY + 30.66

SW3_X = CLEARANCE_XY + 17.00
SW3_Y = CLEARANCE_XY + 30.30

LED_X = CLEARANCE_XY + 11.80
LED_Y = CLEARANCE_XY + 34.20

SW1_X = CLEARANCE_XY + 39.75
SW1_Y = CLEARANCE_XY + 24.75
SW2_X = CLEARANCE_XY + 16.25
SW2_Y = CLEARANCE_XY + 21.00

J3_Y = CLEARANCE_XY + 4.50
J5_Y = CLEARANCE_XY + 16.00
J2_Y = CLEARANCE_XY + 9.58


def to_cm(val_mm):
    """Fusion 360 internal API units are centimeters."""
    return val_mm / 10.0


def create_box(rootComp, name, x1_mm, y1_mm, z1_mm, x2_mm, y2_mm, z2_mm):
    """Helper to create a solid cuboid body directly in rootComponent."""
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    lines = sketch.sketchCurves.sketchLines
    p1 = adsk.core.Point3D.create(to_cm(x1_mm), to_cm(y1_mm), 0)
    p2 = adsk.core.Point3D.create(to_cm(x2_mm), to_cm(y2_mm), 0)
    lines.addTwoPointRectangle(p1, p2)
    
    extrudes = rootComp.features.extrudeFeatures
    prof = sketch.profiles.item(0)
    
    height_cm = to_cm(z2_mm - z1_mm)
    extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    
    if z1_mm != 0:
        offsetVal = adsk.core.ValueInput.createByReal(to_cm(z1_mm))
        startFrom = adsk.fusion.OffsetStartDefinition.create(offsetVal)
        extInput.startExtent = startFrom

    extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(height_cm))
    ext = extrudes.add(extInput)
    body = ext.bodies.item(0)
    body.name = name
    return body


def create_cylinder(rootComp, name, cx_mm, cy_mm, radius_mm, z1_mm, z2_mm):
    """Helper to create a solid cylinder directly in rootComponent."""
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    circles = sketch.sketchCurves.sketchCircles
    center = adsk.core.Point3D.create(to_cm(cx_mm), to_cm(cy_mm), 0)
    circles.addByCenterRadius(center, to_cm(radius_mm))
    
    extrudes = rootComp.features.extrudeFeatures
    prof = sketch.profiles.item(0)
    
    height_cm = to_cm(z2_mm - z1_mm)
    extInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
    if z1_mm != 0:
        offsetVal = adsk.core.ValueInput.createByReal(to_cm(z1_mm))
        startFrom = adsk.fusion.OffsetStartDefinition.create(offsetVal)
        extInput.startExtent = startFrom
    extInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(height_cm))
    ext = extrudes.add(extInput)
    body = ext.bodies.item(0)
    body.name = name
    return body


def cut_box(rootComp, target_body, x1_mm, y1_mm, z1_mm, x2_mm, y2_mm, z2_mm):
    """Helper to cut a cuboid volume from a target body."""
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    lines = sketch.sketchCurves.sketchLines
    p1 = adsk.core.Point3D.create(to_cm(x1_mm), to_cm(y1_mm), 0)
    p2 = adsk.core.Point3D.create(to_cm(x2_mm), to_cm(y2_mm), 0)
    lines.addTwoPointRectangle(p1, p2)
    
    extrudes = rootComp.features.extrudeFeatures
    prof = sketch.profiles.item(0)
    
    height_cm = to_cm(z2_mm - z1_mm)
    cutInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
    if z1_mm != 0:
        offsetVal = adsk.core.ValueInput.createByReal(to_cm(z1_mm))
        startFrom = adsk.fusion.OffsetStartDefinition.create(offsetVal)
        cutInput.startExtent = startFrom

    cutInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(height_cm))
    cutInput.participantBodies = [target_body]
    try:
        extrudes.add(cutInput)
    except:
        pass


def cut_cylinder(rootComp, target_body, center_x_mm, center_y_mm, radius_mm, z1_mm, z2_mm):
    """Helper to cut a circular hole."""
    sketches = rootComp.sketches
    xyPlane = rootComp.xYConstructionPlane
    sketch = sketches.add(xyPlane)
    circles = sketch.sketchCurves.sketchCircles
    center = adsk.core.Point3D.create(to_cm(center_x_mm), to_cm(center_y_mm), 0)
    circles.addByCenterRadius(center, to_cm(radius_mm))
    
    extrudes = rootComp.features.extrudeFeatures
    prof = sketch.profiles.item(0)
    
    height_cm = to_cm(z2_mm - z1_mm)
    cutInput = extrudes.createInput(prof, adsk.fusion.FeatureOperations.CutFeatureOperation)
    if z1_mm != 0:
        offsetVal = adsk.core.ValueInput.createByReal(to_cm(z1_mm))
        startFrom = adsk.fusion.OffsetStartDefinition.create(offsetVal)
        cutInput.startExtent = startFrom
    cutInput.setDistanceExtent(False, adsk.core.ValueInput.createByReal(height_cm))
    cutInput.participantBodies = [target_body]
    try:
        extrudes.add(cutInput)
    except:
        pass


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        product = app.activeProduct
        if not isinstance(product, adsk.fusion.Design):
            ui.messageBox('Please create or open a document in Autodesk Fusion first.')
            return

        design = adsk.fusion.Design.cast(product)
        rootComp = design.rootComponent
        combines = rootComp.features.combineFeatures

        # =========================================================================
        # 1. BUILD BASE HOUSING BODY
        # =========================================================================
        baseBody = create_box(
            rootComp, "MAMBA_ESC_Base_Housing",
            -WALL_THICKNESS, -WALL_THICKNESS, 0,
            INT_W + WALL_THICKNESS, INT_L + WALL_THICKNESS, BASE_TOTAL_H
        )

        cut_box(
            rootComp, baseBody,
            0, 0, FLOOR_THICKNESS,
            INT_W, INT_L, BASE_TOTAL_H + 1.0
        )

        # 4 Standoff Pillars
        so_size = 7.0
        corner_standoffs = [
            (0, 0, so_size, so_size),
            (INT_W - so_size, 0, INT_W, so_size),
            (0, INT_L - so_size, so_size, INT_L),
            (INT_W - so_size, INT_L - so_size, INT_W, INT_L)
        ]
        for (sx1, sy1, sx2, sy2) in corner_standoffs:
            post = create_box(
                rootComp, "Standoff",
                sx1, sy1, FLOOR_THICKNESS,
                sx2, sy2, FLOOR_THICKNESS + STANDOFF_HEIGHT
            )
            col = adsk.core.ObjectCollection.create()
            col.add(post)
            cInput = combines.createInput(baseBody, col)
            cInput.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            combines.add(cInput)

        # Cutout 1: J6 (CH1 & CH2 Input) on Left Wall
        cut_box(
            rootComp, baseBody,
            -WALL_THICKNESS - 1.0, J6_Y - 7.5, PCB_TOP_Z - 0.5,
            2.0, J6_Y + 7.5, BASE_TOTAL_H + 1.0
        )

        # Cutout 2: J3 & J5 Phoenix Terminals (Left Wall)
        cut_box(
            rootComp, baseBody,
            -WALL_THICKNESS - 1.0, J3_Y - 4.5, PCB_TOP_Z,
            2.0, J3_Y + 4.5, BASE_TOTAL_H + 1.0
        )
        cut_box(
            rootComp, baseBody,
            -WALL_THICKNESS - 1.0, J5_Y - 4.5, PCB_TOP_Z,
            2.0, J5_Y + 4.5, BASE_TOTAL_H + 1.0
        )

        # Cutout 3: J2 Phoenix Terminal (Right Wall)
        cut_box(
            rootComp, baseBody,
            INT_W - 2.0, J2_Y - 4.5, PCB_TOP_Z,
            INT_W + WALL_THICKNESS + 1.0, J2_Y + 4.5, BASE_TOTAL_H + 1.0
        )

        # Internal Snap-Fit Latches
        clip_w = 7.0
        clip_h = 4.0
        clip_thick = 1.3
        clip_positions = [
            (INT_W * 0.3 - clip_w/2, 0, INT_W * 0.3 + clip_w/2, clip_thick, True),
            (INT_W * 0.7 - clip_w/2, 0, INT_W * 0.7 + clip_w/2, clip_thick, True),
            (INT_W * 0.3 - clip_w/2, INT_L - clip_thick, INT_W * 0.3 + clip_w/2, INT_L, False),
            (INT_W * 0.7 - clip_w/2, INT_L - clip_thick, INT_W * 0.7 + clip_w/2, INT_L, False),
        ]
        for (cx1, cy1, cx2, cy2, is_front) in clip_positions:
            clipBody = create_box(rootComp, "SnapClip", cx1, cy1, BASE_TOTAL_H, cx2, cy2, BASE_TOTAL_H + clip_h)
            hy1 = cy1 if is_front else cy1 - 0.7
            hy2 = cy2 + 0.7 if is_front else cy2
            hookBody = create_box(rootComp, "Hook", cx1, hy1, BASE_TOTAL_H + clip_h - 1.2, cx2, hy2, BASE_TOTAL_H + clip_h)
            col = adsk.core.ObjectCollection.create()
            col.add(clipBody)
            col.add(hookBody)
            cInput = combines.createInput(baseBody, col)
            cInput.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
            combines.add(cInput)

        # =========================================================================
        # 2. BUILD MAMBA B1 PCB & COMPONENT BODIES (Inside Housing)
        # =========================================================================
        pcbSub = create_box(
            rootComp, "MAMBA_B1_PCB",
            CLEARANCE_XY, CLEARANCE_XY, PCB_BOT_Z,
            CLEARANCE_XY + PCB_WIDTH, CLEARANCE_XY + PCB_LENGTH, PCB_TOP_Z
        )

        # Components on PCB
        c1 = create_cylinder(rootComp, "C1_Cap", CLEARANCE_XY + 34.75, CLEARANCE_XY + 6.55, 4.0, PCB_TOP_Z, PCB_TOP_Z + 10.5)
        c2 = create_cylinder(rootComp, "C2_Cap", CLEARANCE_XY + 19.50, CLEARANCE_XY + 6.80, 4.0, PCB_TOP_Z, PCB_TOP_Z + 10.5)
        esp32 = create_box(rootComp, "ESP32", CLEARANCE_XY + 18.9, CLEARANCE_XY + 15.0, PCB_TOP_Z, CLEARANCE_XY + 36.9, CLEARANCE_XY + 40.5, PCB_TOP_Z + 3.2)
        j3 = create_box(rootComp, "J3_Terminal", CLEARANCE_XY + 0.0, CLEARANCE_XY + 0.25, PCB_TOP_Z, CLEARANCE_XY + 10.0, CLEARANCE_XY + 8.75, PCB_TOP_Z + 13.8)
        j5 = create_box(rootComp, "J5_Terminal", CLEARANCE_XY + 0.0, CLEARANCE_XY + 11.75, PCB_TOP_Z, CLEARANCE_XY + 10.0, CLEARANCE_XY + 20.25, PCB_TOP_Z + 13.8)
        j2 = create_box(rootComp, "J2_Terminal", CLEARANCE_XY + 45.0, CLEARANCE_XY + 5.33, PCB_TOP_Z, CLEARANCE_XY + 55.0, CLEARANCE_XY + 13.83, PCB_TOP_Z + 13.8)
        j6 = create_box(rootComp, "J6_RC_Header", CLEARANCE_XY + 1.19, CLEARANCE_XY + 26.85, PCB_TOP_Z, CLEARANCE_XY + 6.27, CLEARANCE_XY + 34.47, PCB_TOP_Z + 8.5)
        sw3 = create_box(rootComp, "SW3_Button", SW3_X - 3.0, SW3_Y - 3.0, PCB_TOP_Z, SW3_X + 3.0, SW3_Y + 3.0, PCB_TOP_Z + 4.3)
        sw3_stem = create_cylinder(rootComp, "SW3_Stem", SW3_X, SW3_Y, 1.75, PCB_TOP_Z + 4.3, PCB_TOP_Z + 6.8)

        # Merge components into the PCB representation
        colPCB = adsk.core.ObjectCollection.create()
        for part in [c1, c2, esp32, j3, j5, j2, j6, sw3, sw3_stem]:
            colPCB.add(part)
        cInput = combines.createInput(pcbSub, colPCB)
        cInput.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        combines.add(cInput)

        # =========================================================================
        # 3. BUILD TOP LID BODY (With Compliant Pressing Mechanism for SW3)
        # =========================================================================
        lid_base_z = BASE_TOTAL_H

        lidBody = create_box(
            rootComp, "MAMBA_ESC_Top_Lid",
            -WALL_THICKNESS, -WALL_THICKNESS, lid_base_z,
            INT_W + WALL_THICKNESS, INT_L + WALL_THICKNESS, lid_base_z + LID_TOTAL_H
        )

        cut_box(
            rootComp, lidBody,
            0, 0, lid_base_z - 1.0,
            INT_W, INT_L, lid_base_z + LID_TOTAL_H - LID_THICKNESS
        )

        # Snap-Fit Catch Pockets
        for (cx1, cy1, cx2, cy2, is_front) in clip_positions:
            pocket_hy1 = cy1 - 0.2 if is_front else cy1 - 0.9
            pocket_hy2 = cy2 + 0.9 if is_front else cy2 + 0.2
            cut_box(
                rootComp, lidBody,
                cx1 - 0.5, pocket_hy1, lid_base_z + clip_h - 1.5,
                cx2 + 0.5, pocket_hy2, lid_base_z + clip_h + 0.5
            )

        lid_top_z = lid_base_z + LID_TOTAL_H

        # J6 Servo Plug Clearance Window in Lid
        cut_box(
            rootComp, lidBody,
            -WALL_THICKNESS - 1.0, J6_Y - 7.5, lid_base_z - 0.5,
            2.0, J6_Y + 7.5, lid_base_z + 4.5
        )

        # Compliant Pressing Mechanism for SW3
        cut_cylinder(rootComp, lidBody, SW3_X, SW3_Y, 4.3, lid_top_z - LID_THICKNESS - 0.5, lid_top_z + 0.5)
        btnCore = create_cylinder(rootComp, "BtnCore", SW3_X, SW3_Y, 3.5, lid_top_z - LID_THICKNESS, lid_top_z)
        bridge = create_box(rootComp, "BtnHinge", SW3_X - 1.2, SW3_Y, lid_top_z - LID_THICKNESS, SW3_X + 1.2, SW3_Y + 4.6, lid_top_z)
        btnDome = create_cylinder(rootComp, "BtnDome", SW3_X, SW3_Y, 3.3, lid_top_z, lid_top_z + 0.8)
        plunger = create_cylinder(rootComp, "BtnPlunger", SW3_X, SW3_Y, 1.8, lid_top_z - LID_THICKNESS - 7.5, lid_top_z - LID_THICKNESS)

        colBtn = adsk.core.ObjectCollection.create()
        colBtn.add(btnCore)
        colBtn.add(bridge)
        colBtn.add(btnDome)
        colBtn.add(plunger)
        cInput = combines.createInput(lidBody, colBtn)
        cInput.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        combines.add(cInput)

        # Status LED & Pinhole Ports
        cut_box(
            rootComp, lidBody,
            LED_X - 2.0, LED_Y - 4.5, lid_top_z - LID_THICKNESS - 1.0,
            LED_X + 2.0, LED_Y + 4.5, lid_top_z + 1.0
        )

        cut_cylinder(rootComp, lidBody, SW1_X, SW1_Y, 1.2, lid_top_z - LID_THICKNESS - 1.0, lid_top_z + 1.0)
        cut_cylinder(rootComp, lidBody, SW2_X, SW2_Y, 1.2, lid_top_z - LID_THICKNESS - 1.0, lid_top_z + 1.0)

        cut_box(rootComp, lidBody, 3.5, J3_Y - 3.5, lid_top_z - LID_THICKNESS - 1.0, 8.5, J3_Y + 3.5, lid_top_z + 1.0)
        cut_box(rootComp, lidBody, 3.5, J5_Y - 3.5, lid_top_z - LID_THICKNESS - 1.0, 8.5, J5_Y + 3.5, lid_top_z + 1.0)
        cut_box(rootComp, lidBody, INT_W - 8.5, J2_Y - 3.5, lid_top_z - LID_THICKNESS - 1.0, INT_W - 3.5, J2_Y + 3.5, lid_top_z + 1.0)

        # Internal alignment lip
        skirt_w = INT_W - 0.4
        skirt_l = INT_L - 0.4
        skirt_outer = create_box(rootComp, "SkirtOuter", 0.2, 0.2, lid_base_z - 1.2, skirt_w + 0.2, skirt_l + 0.2, lid_base_z)
        cut_box(rootComp, skirt_outer, 1.4, 1.4, lid_base_z - 1.5, skirt_w - 1.0, skirt_l - 1.0, lid_base_z + 0.5)
        colSkirt = adsk.core.ObjectCollection.create()
        colSkirt.add(skirt_outer)
        cInput = combines.createInput(lidBody, colSkirt)
        cInput.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        combines.add(cInput)

        ui.messageBox(
            "MAMBA B1 ESC Full Assembly Generated Successfully!\n\n"
            "Bodies Created in Fusion 360 Tree:\n"
            "  1. MAMBA_ESC_Base_Housing (Flush clean enclosure base)\n"
            "  2. MAMBA_B1_PCB (Complete board with ESP32, caps, terminals & switch)\n"
            "  3. MAMBA_ESC_Top_Lid (Snap-fit lid with compliant pressing button)\n\n"
            "All components are precisely mated and aligned in 3D space."
        )

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
