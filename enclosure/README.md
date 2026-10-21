# STM ESC Enclosure

Parametric 3D-printable enclosure for the `stmesc` KiCad PCB.

## Board Dimensions (from `stmesc.kicad_pcb`)

| Property | Value |
|---|---|
| PCB Width | 55.0 mm |
| PCB Depth | 45.0 mm |
| PCB Thickness | 1.6 mm |
| Corner radius | 2.5 mm |

## Enclosure Dimensions

| Property | Value |
|---|---|
| Outer Width | 60.0 mm |
| Outer Depth | 50.0 mm |
| Outer Height (base + lid) | ~24 mm |
| Wall thickness | 2.0 mm |
| Clearance around PCB | 0.5 mm each side |

## Files

| File | Description |
|---|---|
| `stmesc_enclosure.scad` | Main OpenSCAD parametric source |

## Features

### Base
- **Floor** with 1.5 mm thickness
- **4× PCB standoff bosses** at board corners — M2.5 screws, 2.0 mm height
- **Front face cutouts:**
  - Power input connector slot (11 × 8 mm) — for XT30/XT60 power lead
  - Signal connector slot (15 × 6 mm) — for JST 6-pin servo/CAN connector
- **Rear face cutouts:**
  - 3× motor phase wire holes (Ø6 mm) — for 3-phase motor outputs
- **Side ventilation slots** — 6 slots per side, 1.5 mm wide
- **4× lid screw posts** at box corners (M2.5)

### Lid
- **Snap lip** that drops 3 mm into the base opening
- **4× screw holes** aligning with base posts
- **Top ventilation slots** (6 slots)
- **Label recess** embossed with "STM ESC"

## Rendering & Export

### In OpenSCAD
1. Open `stmesc_enclosure.scad`
2. Set `render_part = "base"`, press **F6** → **File → Export → Export as STL**
3. Set `render_part = "lid"`, repeat

### Recommended Print Settings
| Setting | Value |
|---|---|
| Material | PETG or ABS (heat resistant) |
| Layer height | 0.20 mm |
| Infill | 30–40% |
| Perimeters | 3+ |
| Supports | Lid screw bosses only |

## Customization

All key dimensions are parametric at the top of the `.scad` file:

```openscad
xy_gap      = 0.5;   // gap around PCB on each side
z_bot_gap   = 2.0;   // space below PCB (airflow / standoff)
z_top_gap   = 15.0;  // space above PCB (tallest component)
wall        = 2.0;   // wall thickness
```

Adjust `z_top_gap` if your tallest component exceeds 12 mm.
