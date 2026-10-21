// ============================================================
//  STM ESC Enclosure
//  PCB: 55 x 45 mm  |  Corner radius: 2.5 mm
//  Generated for stmesc KiCad project
// ============================================================
//
//  PRINT SETTINGS (recommended):
//    Material : PETG or ABS (heat resistant)
//    Layer    : 0.20 mm
//    Infill   : 30-40%
//    Supports : Needed for lid screw bosses (lid only)
//    Perimeters: 3+
//
//  RENDER:
//    BASE : render_part = "base"
//    LID  : render_part = "lid"
//    BOTH : render_part = "both"
// ============================================================

render_part = "both";   // "base" | "lid" | "both"

// ── PCB dimensions ──────────────────────────────────────────
pcb_w   = 55.0;   // PCB width  (X)
pcb_d   = 45.0;   // PCB depth  (Y)
pcb_t   = 1.6;    // PCB thickness
pcb_r   = 2.5;    // PCB corner radius

// ── Clearance & wall ────────────────────────────────────────
xy_gap      = 0.5;   // gap around PCB on each side
z_bot_gap   = 2.0;   // space below PCB (airflow / standoff)
z_top_gap   = 15.0;  // space above PCB for tallest component (~12mm cap + margin)
wall        = 2.0;   // wall thickness
floor_t     = 1.5;   // base floor thickness
lid_t       = 2.0;   // lid thickness

// ── Derived inner cavity dimensions ─────────────────────────
in_w = pcb_w + 2 * xy_gap;
in_d = pcb_d + 2 * xy_gap;
in_h = z_bot_gap + pcb_t + z_top_gap;

// ── Outer dimensions ─────────────────────────────────────────
out_w = in_w + 2 * wall;
out_d = in_d + 2 * wall;
out_h = in_h + floor_t + lid_t;
out_r = pcb_r + wall;   // outer corner radius

// ── Standoff / boss ──────────────────────────────────────────
boss_r      = 2.5;   // screw boss outer radius
boss_h      = z_bot_gap + 0.5; // standoff height (lifts PCB)
screw_r     = 1.1;   // M2.5 clearance
boss_inset  = 3.0;   // corner inset from inner wall

// ── Lid snap/screw posts ─────────────────────────────────────
lid_post_r  = 2.5;
lid_post_h  = 5.0;
lid_screw_r = 1.1;

// ── Ventilation slots (top face of lid) ──────────────────────
vent_slots  = 6;
vent_w      = 1.5;
vent_l      = 20.0;
vent_gap    = 3.5;

// ── Connector cutouts (front face, -Y side) ──────────────────
// Power input connector (e.g. XT30/XT60 style, ~10×7 mm opening)
pwr_cut_w   = 11.0;
pwr_cut_h   = 8.0;
pwr_cut_x   = out_w / 2;          // centered left half
pwr_cut_z   = floor_t + z_bot_gap + pcb_t + 0.5; // just above PCB

// Motor phase output wires (3 × ~5 mm holes)
motor_hole_r = 3.0;
motor_hole_spacing = 10.0;

// Signal connector (JST 6-pin ~14 mm wide)
sig_cut_w   = 15.0;
sig_cut_h   = 6.0;
sig_cut_x   = out_w * 0.72;

// ── 3D primitive: rounded rectangle prism ────────────────────
module rrect(w, d, h, r, center=false) {
    dx = center ? -w/2 : 0;
    dy = center ? -d/2 : 0;
    translate([dx, dy, 0])
    hull() {
        for (xi = [r, w-r]) for (yi = [r, d-r])
            translate([xi, yi, 0]) cylinder(r=r, h=h, $fn=32);
    }
}

// ── Standoff post ────────────────────────────────────────────
module standoff(h, br, sr) {
    difference() {
        cylinder(r=br, h=h, $fn=24);
        cylinder(r=sr, h=h+1, $fn=20);
    }
}

// ── Base ─────────────────────────────────────────────────────
module base() {
    difference() {
        // Outer shell
        rrect(out_w, out_d, in_h + floor_t, out_r);

        // Inner cavity (open top)
        translate([wall, wall, floor_t])
            rrect(in_w, in_d, in_h + 1, pcb_r);

        // ── Connector cutouts on FRONT face (Y=0) ──
        // Power input
        translate([wall + xy_gap + (in_w - pwr_cut_w) / 4, -1, floor_t + z_bot_gap + pcb_t])
            cube([pwr_cut_w, wall + 2, pwr_cut_h]);

        // Signal connector
        translate([wall + xy_gap + in_w * 0.50, -1, floor_t + z_bot_gap + pcb_t])
            cube([sig_cut_w, wall + 2, sig_cut_h]);

        // ── Motor wire holes on BACK face (Y=out_d) ──
        for (i = [-1, 0, 1])
            translate([out_w/2 + i * motor_hole_spacing, out_d + 1,
                       floor_t + z_bot_gap + pcb_t + 2])
                rotate([90, 0, 0])
                    cylinder(r=motor_hole_r, h=wall + 3, $fn=24);

        // ── Ventilation slots on left/right sides ──
        for (side = [0, 1]) {
            mirror_x = side == 0 ? 0 : out_w;
            sign_x   = side == 0 ? -1 : 1;
            for (i = [0:vent_slots-1]) {
                tz = floor_t + 3 + i * (vent_w + vent_gap);
                translate([mirror_x - sign_x*(wall+1),
                           (out_d - vent_l)/2,
                           tz])
                    cube([wall + 2, vent_l, vent_w]);
            }
        }
    }

    // ── PCB standoff bosses (4 corners) ──────────────────────
    for (xi = [wall + boss_inset, wall + in_w - boss_inset])
    for (yi = [wall + boss_inset, wall + in_d - boss_inset])
        translate([xi, yi, floor_t])
            standoff(boss_h, boss_r, screw_r);

    // ── Lid screw posts (inside corners of base rim) ──────────
    for (xi = [wall/2, out_w - wall/2])
    for (yi = [wall/2, out_d - wall/2])
        translate([xi, yi, floor_t + in_h - lid_post_h])
            standoff(lid_post_h, lid_post_r, lid_screw_r);
}

// ── Lid ──────────────────────────────────────────────────────
module lid() {
    difference() {
        union() {
            // Flat panel
            rrect(out_w, out_d, lid_t, out_r);

            // Lip that drops into the box (1 mm deep inside)
            translate([wall - 0.4, wall - 0.4, -3])
                rrect(in_w + 0.8, in_d + 0.8, 3.1, pcb_r - 0.3);
        }

        // Screw holes for lid posts
        for (xi = [wall/2, out_w - wall/2])
        for (yi = [wall/2, out_d - wall/2])
            translate([xi, yi, -4])
                cylinder(r=lid_screw_r, h=lid_t + 5, $fn=20);

        // Ventilation slots on top
        for (i = [0:vent_slots-1]) {
            tx = (out_w - vent_slots * vent_w - (vent_slots-1) * vent_gap) / 2
                 + i * (vent_w + vent_gap);
            translate([tx, (out_d - vent_l)/2, -1])
                cube([vent_w, vent_l, lid_t + 2]);
        }

        // Label recess (shallow 0.4 mm for etching)
        translate([out_w/2, out_d * 0.75, lid_t - 0.4])
            linear_extrude(0.5)
                text("STM ESC", size=5, halign="center", valign="center",
                     font="Liberation Sans:style=Bold");
    }
}

// ── Assembly / Export ─────────────────────────────────────────
if (render_part == "base") {
    base();
} else if (render_part == "lid") {
    translate([0, 0, 0]) lid();
} else {
    // Show both side-by-side
    base();
    translate([out_w + 5, 0, lid_t])
        rotate([180, 0, 0])
            lid();
}
