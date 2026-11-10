import numpy as np
import trimesh
from manifold3d import Manifold, Mesh

def make_box(x1, y1, z1, x2, y2, z2):
    dx = x2 - x1
    dy = y2 - y1
    dz = z2 - z1
    assert dx > 0 and dy > 0 and dz > 0, f"Box dimensions must be positive: dx={dx}, dy={dy}, dz={dz}"
    box = Manifold.cube([dx, dy, dz])
    return box.translate([x1, y1, z1])

def make_cylinder(cx, cy, r, z1, z2, segments=36):
    h = z2 - z1
    assert h > 0 and r > 0, f"Cylinder params must be positive: h={h}, r={r}"
    cyl = Manifold.cylinder(h, r, r, segments)
    return cyl.translate([cx, cy, z1])

def export_manifold_to_stl(m, filename):
    mesh = m.to_mesh()
    vert_properties = mesh.vert_properties
    verts = vert_properties[:, :3]
    tri_verts = mesh.tri_verts
    tri_mesh = trimesh.Trimesh(vertices=verts, faces=tri_verts)
    tri_mesh.export(filename)
    print(f"Exported: {filename} (Vertices: {len(verts)}, Faces: {len(tri_verts)}, Volume: {m.volume():.1f} mm³)")
    return tri_mesh

def build_models():
    # Board Specs
    PCB_W = 55.0
    PCB_L = 45.0
    PCB_T = 1.6
    CLR = 0.6
    WALL = 2.0
    FLOOR = 2.0
    LID_T = 2.0
    STANDOFF_H = 3.5
    CLEARANCE_TOP = 15.0

    INT_W = PCB_W + 2 * CLR    # 56.2 mm
    INT_L = PCB_L + 2 * CLR    # 46.2 mm
    EXT_W = INT_W + 2 * WALL   # 60.2 mm
    EXT_L = INT_L + 2 * WALL   # 50.2 mm

    BASE_WALL_H = STANDOFF_H + PCB_T + 5.0 # 10.1 mm
    BASE_TOTAL_H = FLOOR + BASE_WALL_H     # 12.1 mm
    LID_TOTAL_H = (STANDOFF_H + PCB_T + CLEARANCE_TOP + LID_T) - BASE_WALL_H # 12.0 mm

    PCB_BOT_Z = FLOOR + STANDOFF_H        # 5.5 mm
    PCB_TOP_Z = PCB_BOT_Z + PCB_T         # 7.1 mm

    # Component Offsets in enclosure coordinate frame
    J6_X = CLR + 3.73
    J6_Y = CLR + 30.66
    SW3_X = CLR + 17.00
    SW3_Y = CLR + 30.30
    LED_X = CLR + 11.80
    LED_Y = CLR + 34.20
    SW1_X = CLR + 39.75
    SW1_Y = CLR + 24.75
    SW2_X = CLR + 16.25
    SW2_Y = CLR + 21.00
    J3_Y = CLR + 4.50
    J5_Y = CLR + 16.00
    J2_Y = CLR + 9.58

    # =========================================================================
    # 1. BASE HOUSING (Clean, Professional, Flush Body)
    # =========================================================================
    base_outer = make_box(-WALL, -WALL, 0, INT_W + WALL, INT_L + WALL, BASE_TOTAL_H)
    base_cavity = make_box(0, 0, FLOOR, INT_W, INT_L, BASE_TOTAL_H + 1.0)
    base = base_outer - base_cavity

    # 4 PCB Corner Standoffs (H=3.5mm)
    so_size = 7.0
    for (sx1, sy1, sx2, sy2) in [
        (0, 0, so_size, so_size),
        (INT_W - so_size, 0, INT_W, so_size),
        (0, INT_L - so_size, so_size, INT_L),
        (INT_W - so_size, INT_L - so_size, INT_W, INT_L)
    ]:
        so = make_box(sx1, sy1, FLOOR, sx2, sy2, FLOOR + STANDOFF_H)
        base = base + so

    # Cutout 1: J6 (CH1 & CH2 Input 2x03 header) on Left Wall
    j6_cutout = make_box(-WALL - 1.0, J6_Y - 7.5, PCB_TOP_Z - 0.5, 2.0, J6_Y + 7.5, BASE_TOTAL_H + 1.0)
    base = base - j6_cutout

    # Cutout 2: J3 & J5 Phoenix Terminals (Left Wall)
    j3_cutout = make_box(-WALL - 1.0, J3_Y - 4.5, PCB_TOP_Z, 2.0, J3_Y + 4.5, BASE_TOTAL_H + 1.0)
    j5_cutout = make_box(-WALL - 1.0, J5_Y - 4.5, PCB_TOP_Z, 2.0, J5_Y + 4.5, BASE_TOTAL_H + 1.0)
    base = base - j3_cutout - j5_cutout

    # Cutout 3: J2 Phoenix Terminal (Right Wall)
    j2_cutout = make_box(INT_W - 2.0, J2_Y - 4.5, PCB_TOP_Z, INT_W + WALL + 1.0, J2_Y + 4.5, BASE_TOTAL_H + 1.0)
    base = base - j2_cutout

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
        clip_arm = make_box(cx1, cy1, BASE_TOTAL_H, cx2, cy2, BASE_TOTAL_H + clip_h)
        hy1 = cy1 if is_front else cy1 - 0.7
        hy2 = cy2 + 0.7 if is_front else cy2
        clip_hook = make_box(cx1, hy1, BASE_TOTAL_H + clip_h - 1.2, cx2, hy2, BASE_TOTAL_H + clip_h)
        base = base + clip_arm + clip_hook

    # =========================================================================
    # 2. TOP LID (With Compliant Pressing Mechanism)
    # =========================================================================
    LID_BASE_Z = BASE_TOTAL_H
    LID_TOP_Z = LID_BASE_Z + LID_TOTAL_H

    lid_outer = make_box(-WALL, -WALL, LID_BASE_Z, INT_W + WALL, INT_L + WALL, LID_TOP_Z)
    lid_cavity = make_box(0, 0, LID_BASE_Z - 1.0, INT_W, INT_L, LID_TOP_Z - LID_T)
    lid = lid_outer - lid_cavity

    # Internal Snap-Fit Catch Pockets in Lid
    for (cx1, cy1, cx2, cy2, is_front) in clip_positions:
        pocket_hy1 = cy1 - 0.2 if is_front else cy1 - 0.9
        pocket_hy2 = cy2 + 0.9 if is_front else cy2 + 0.2
        pocket = make_box(cx1 - 0.5, pocket_hy1, LID_BASE_Z + clip_h - 1.5, cx2 + 0.5, pocket_hy2, LID_BASE_Z + clip_h + 0.5)
        lid = lid - pocket

    # J6 CH1/CH2 Servo Plug Clearance Window in Lid
    j6_lid_cut = make_box(-WALL - 1.0, J6_Y - 7.5, LID_BASE_Z - 0.5, 2.0, J6_Y + 7.5, LID_BASE_Z + 4.5)
    lid = lid - j6_lid_cut

    # Compliant Pressing Mechanism for SW3
    annulus = make_cylinder(SW3_X, SW3_Y, 4.3, LID_TOP_Z - LID_T - 0.5, LID_TOP_Z + 0.5, 48) - \
              make_cylinder(SW3_X, SW3_Y, 3.5, LID_TOP_Z - LID_T - 1.0, LID_TOP_Z + 1.0, 48)
    bridge_w = 2.4
    bridge_keep = make_box(SW3_X - bridge_w/2, SW3_Y, LID_TOP_Z - LID_T - 1.0, SW3_X + bridge_w/2, SW3_Y + 6.0, LID_TOP_Z + 1.0)
    flex_slit = annulus - bridge_keep
    lid = lid - flex_slit

    button_cap = make_cylinder(SW3_X, SW3_Y, 3.3, LID_TOP_Z, LID_TOP_Z + 0.8, 36)
    lid = lid + button_cap

    actuator_plunger = make_cylinder(SW3_X, SW3_Y, 1.8, LID_TOP_Z - LID_T - 7.5, LID_TOP_Z - LID_T, 32)
    lid = lid + actuator_plunger

    # LED & Pinhole Ports
    led_window = make_box(LED_X - 2.0, LED_Y - 4.5, LID_TOP_Z - LID_T - 1.0, LED_X + 2.0, LED_Y + 4.5, LID_TOP_Z + 1.0)
    lid = lid - led_window

    sw1_hole = make_cylinder(SW1_X, SW1_Y, 1.2, LID_TOP_Z - LID_T - 1.0, LID_TOP_Z + 1.0)
    sw2_hole = make_cylinder(SW2_X, SW2_Y, 1.2, LID_TOP_Z - LID_T - 1.0, LID_TOP_Z + 1.0)
    lid = lid - sw1_hole - sw2_hole

    sd_j3 = make_box(3.5, J3_Y - 3.5, LID_TOP_Z - LID_T - 1.0, 8.5, J3_Y + 3.5, LID_TOP_Z + 1.0)
    sd_j5 = make_box(3.5, J5_Y - 3.5, LID_TOP_Z - LID_T - 1.0, 8.5, J5_Y + 3.5, LID_TOP_Z + 1.0)
    sd_j2 = make_box(INT_W - 8.5, J2_Y - 3.5, LID_TOP_Z - LID_T - 1.0, INT_W - 3.5, J2_Y + 3.5, LID_TOP_Z + 1.0)
    lid = lid - sd_j3 - sd_j5 - sd_j2

    # Internal alignment lip
    skirt_w = INT_W - 0.4
    skirt_l = INT_L - 0.4
    skirt_outer = make_box(0.2, 0.2, LID_BASE_Z - 1.2, skirt_w + 0.2, skirt_l + 0.2, LID_BASE_Z)
    skirt_cavity = make_box(1.4, 1.4, LID_BASE_Z - 1.5, skirt_w - 1.0, skirt_l - 1.0, LID_BASE_Z + 0.5)
    skirt = skirt_outer - skirt_cavity
    lid = lid + skirt

    # =========================================================================
    # 3. DETAILED MAMBA B1 PCB MODEL (Substrate + All Key Components)
    # =========================================================================
    pcb_sub = make_box(CLR, CLR, PCB_BOT_Z, CLR + PCB_W, CLR + PCB_L, PCB_TOP_Z)

    # Electrolytic Capacitors C1, C2 (Height: 10.5mm, Diam: 8.0mm)
    c1 = make_cylinder(CLR + 34.75, CLR + 6.55, 4.0, PCB_TOP_Z, PCB_TOP_Z + 10.5)
    c2 = make_cylinder(CLR + 19.50, CLR + 6.80, 4.0, PCB_TOP_Z, PCB_TOP_Z + 10.5)

    # ESP32-WROOM Module U3 (18mm x 25.5mm x 3.2mm)
    esp32 = make_box(CLR + 27.90 - 9.0, CLR + 27.75 - 12.75, PCB_TOP_Z, CLR + 27.90 + 9.0, CLR + 27.75 + 12.75, PCB_TOP_Z + 3.2)

    # Phoenix Terminals J3, J5, J2 (10mm x 8.5mm x 13.8mm)
    j3_blk = make_box(CLR + 5.0 - 5.0, CLR + 4.50 - 4.25, PCB_TOP_Z, CLR + 5.0 + 5.0, CLR + 4.50 + 4.25, PCB_TOP_Z + 13.8)
    j5_blk = make_box(CLR + 5.0 - 5.0, CLR + 16.00 - 4.25, PCB_TOP_Z, CLR + 5.0 + 5.0, CLR + 16.00 + 4.25, PCB_TOP_Z + 13.8)
    j2_blk = make_box(CLR + 50.0 - 5.0, CLR + 9.58 - 4.25, PCB_TOP_Z, CLR + 50.0 + 5.0, CLR + 9.58 + 4.25, PCB_TOP_Z + 13.8)

    # J6 (CH1 & CH2 Input 2x03 header: 5.08mm x 7.62mm x 8.5mm)
    j6_blk = make_box(CLR + 3.73 - 2.54, CLR + 30.66 - 3.81, PCB_TOP_Z, CLR + 3.73 + 2.54, CLR + 30.66 + 3.81, PCB_TOP_Z + 8.5)

    # SW3 6mm Push Button (Body: 6x6x4.3mm, Stem: Ø3.5mm up to 6.8mm)
    sw3_base = make_box(SW3_X - 3.0, SW3_Y - 3.0, PCB_TOP_Z, SW3_X + 3.0, SW3_Y + 3.0, PCB_TOP_Z + 4.3)
    sw3_stem = make_cylinder(SW3_X, SW3_Y, 1.75, PCB_TOP_Z + 4.3, PCB_TOP_Z + 6.8)
    sw3_full = sw3_base + sw3_stem

    # LEDs D1, D4, D5 (0805 chips)
    led1 = make_box(CLR + 11.8 - 0.6, CLR + 32.25 - 1.0, PCB_TOP_Z, CLR + 11.8 + 0.6, CLR + 32.25 + 1.0, PCB_TOP_Z + 0.8)
    led4 = make_box(CLR + 11.8 - 0.6, CLR + 34.15 - 1.0, PCB_TOP_Z, CLR + 11.8 + 0.6, CLR + 34.15 + 1.0, PCB_TOP_Z + 0.8)
    led5 = make_box(CLR + 11.8 - 0.6, CLR + 36.20 - 1.0, PCB_TOP_Z, CLR + 11.8 + 0.6, CLR + 36.20 + 1.0, PCB_TOP_Z + 0.8)

    # Bottom MOSFET Q2 (TO-252 package) hanging under PCB
    q2_fet = make_box(CLR + 13.0 - 3.3, CLR + 20.0 - 5.0, PCB_BOT_Z - 2.3, CLR + 13.0 + 3.3, CLR + 20.0 + 5.0, PCB_BOT_Z)

    pcb_full = pcb_sub + c1 + c2 + esp32 + j3_blk + j5_blk + j2_blk + j6_blk + sw3_full + led1 + led4 + led5 + q2_fet

    # =========================================================================
    # EXPORT INDIVIDUAL & ASSEMBLED MODELS
    # =========================================================================
    print("Exporting production STLs...")
    export_manifold_to_stl(base, "MAMBA_B1_ESC_Enclosure_Base.stl")
    export_manifold_to_stl(lid, "MAMBA_B1_ESC_Enclosure_Lid.stl")
    export_manifold_to_stl(pcb_full, "MAMBA_B1_PCB_Detailed.stl")

    # Complete Assembly (Base + PCB seated + Lid closed)
    full_assembly = base + pcb_full + lid
    export_manifold_to_stl(full_assembly, "MAMBA_B1_ESC_Assembly_With_PCB.stl")

    # Exploded Assembly (Base at bottom, PCB lifted by +15mm, Lid lifted by +35mm)
    pcb_exploded = pcb_full.translate([0, 0, 15.0])
    lid_exploded = lid.translate([0, 0, 35.0])
    exploded_assembly = base + pcb_exploded + lid_exploded
    export_manifold_to_stl(exploded_assembly, "MAMBA_B1_ESC_Exploded_Assembly.stl")

    print("All assembly models generated successfully!")

if __name__ == "__main__":
    build_models()
