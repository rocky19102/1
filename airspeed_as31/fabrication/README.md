# Airspeed A.S.31: laser and 3D-print files

These files cover the non-foam parts of the Jivaro Models Airspeed A.S.31 (71 cm span). The only hard part drawn on the plan is the **motor firewall** ("Cloison moteur : contre-plaqué 3 mm"). Everything else that isn't foam is bought stock:

| Stock part | Size |
|---|---|
| Tail booms | carbon rectangular tube or bar, 4 × 6 mm |
| Wing spars | carbon flat strip, 6 × 1 mm |
| Elevator joiner | samba (hardwood) stick, 6 × 6 mm |
| Elevator pushrod | Ø2 mm outer tube + Ø0.8 mm music wire |

## Firewall dimensions (measured from the 1:1 plan PDF)

- Outer diameter: 35.0 mm. Thickness: 3 mm.
- Centre hole: Ø11.5 mm, for the shaft and bearing boss.
- 3 × Ø3.6 mm M3 screw holes and 3 × Ø6.9 mm cooling holes. They alternate every 60° on a 23 mm bolt circle.

The motor screws to the back of the firewall. The motor can spins inside the cut-out in foam layers F1–F4, and the shaft passes forward through the centre hole.

## xTool P2 (laser): `laser/`

- `firewall_3mm_plywood_x4.svg` / `.dxf`: four firewalls, which gives you spares. Scale is 1:1 in mm. All lines are cut lines (red, 0.1 mm stroke).
- Material: 3 mm birch or basswood plywood. Use the xTool Creative Space material preset for 3 mm plywood and do a test cut first.
- Turn on "inner contours first", or cut the holes before the outlines, so the disc doesn't drop or shift before its holes are cut.
- Check the outer diameter with calipers. Laser kerf makes discs about 0.1–0.2 mm undersize, which doesn't matter for this part.

## Bambu X1C (3D print): `print/`

| File | What it is |
|---|---|
| `motor_mount_plan_pattern.stl` | A printed copy of the plywood firewall, with the plan's 23 mm 3-hole pattern. |
| `motor_mount_universal_slots.stl` | The same disc with 4 radial M3 slots that cover bolt circles of about 16–28 mm (X-mounts, 16 × 19 patterns, and so on). Use it if your motor's holes don't match the plan. |
| `kfm_sanding_block.stl` | A sanding block with two half-round grooves: R3.5 for the 6 mm sheet edges (stab, ailerons) and R6.5 for the 12 mm KFM step leading edge. Line the grooves with sandpaper on double-sided tape. |
| `airspeed_as31_all_parts.3mf` | All three parts on one plate, ready for Bambu Studio. |

Suggested print settings:
- **Motor mounts:** PETG, ASA or PETG-CF. Print them flat, at 0.16–0.2 mm layers with 100% infill. Use M3 screws, or melt in M3 heat-set inserts from the front. PLA can soften from motor heat, so avoid it.
- **Sanding block:** PLA is fine. Use 3 walls and 15% infill, and print it standing on one of its long flat faces so neither groove needs support.

## Check your motor before you cut

I couldn't confirm the T-Motor AS2308 bolt pattern online. Measure your motor's mounting holes, or check T-Motor's drawing. If they don't match the 23 mm 3-hole circle, use the universal slotted mount, or change `SCREW_ANG`, `BOLT_R` and the other values at the top of `make_parts.py` and run it again:

```
pip install ezdxf manifold3d trimesh numpy
python3 make_parts.py
```

The foam parts are covered further down this README.

---

# Foam (Depron) parts: `laser/foam_p2/` and `laser/foam_fullsize/`

These files come from `make_foam.py`, which reads the plan's cutting templates (`airspeed_parts.pdf`). That PDF has three 1000 × 500 mm sheets drawn 1:1.

## Files for the xTool P2: `laser/foam_p2/`

The parts are re-packed onto 600 × 300 mm foam blanks. The P2's bed is 600 × 308 mm. Parts sit at least 5 mm in from the blank's edges.

| File | Foam | Parts |
|---|---|---|
| `p2_depron_6mm_sheet01` | 6 mm | KFM STEP 1/2, WING 2/3, STAB, REAR POINT, F10, F16 |
| `p2_depron_6mm_sheet02` | 6 mm | WING 1/3, WING 3/3, F5, F6, F11, F12, E6, ELEVATOR 2 |
| `p2_depron_6mm_sheet03` | 6 mm | F1–F4, KFM STEP 2/2, E1, E2, AILERON 1 and 2, ELEVATOR 1 |
| `p2_depron_6mm_sheet04` | 6 mm | F7, F8, F13–F15, E3, E4, E5, E7, BOOM COVER 2, STAB CENTRE |
| `p2_depron_6mm_sheet05` | 6 mm | F9, BOOM COVER 1, 3 and 4, BOOM SIDE 1–8 |
| `p2_depron_3mm_sheet01` | 3 mm | CABIN SKIN 1 and 2 |

Each sheet comes as both `.svg` and `.dxf`. `preview_6mm.png` and `preview_3mm.png` show every sheet at a glance.

**The wing and the KFM step are split.** On the plan, both are one piece about 710 mm across, which is too big for the bed. The files cut them into pieces that lock together with dovetail tabs:
- The wing is in 3 pieces, cut at 270 mm and 440 mm from the left edge of the plan sheet.
- The KFM step is in 2 pieces, cut at 520 mm.

The cut positions miss the servo pockets and the battery opening, and the wing and step joints are staggered so they don't line up. I checked that the pieces add back up to exactly the original shapes.
- Lay the wing pieces flat on the plan and glue the dovetails with foam-safe CA or UHU Por. The carbon spars, the KFM step layer and the stacked fuselage layers all glue over the joints, which makes the wing strong again.

### Colour layers

| Colour | Layer | What to do with it |
|---|---|---|
| Red `#FF0000` | CUT | Cut all the way through. Holes come before outlines in the file, so pieces don't drop early. |
| Blue `#0000FF` | SCORE | The centre axes from the plan. The fuselage layers F1–F16 line up on these when you stack them. Use a very light score or mark, not a cut. |
| Black `#000000` | LABEL | Part names. Use a very low-power engrave or hide the layer. |

### Laser settings for Depron (XPS foam)

- **Start low and test.** XPS foam needs very little power on a 55 W CO2 laser. Cut a small test square first, starting at about **15% power and 150 mm/s** for 6 mm. Raise the power or lower the speed until it drops out cleanly. Use roughly half that power for 3 mm.
- **Air assist on.** It keeps the edges from melting and beading.
- **Ventilation is required.** Cutting polystyrene gives off styrene fumes, so keep the P2's exhaust connected and vented outdoors.
- **Kerf:** the cut lines are on the drawn line, so expect about 0.3 mm kerf. That leaves cross-lap slots such as E2/E6 slightly loose, which is fine with glue.
- Only cut Depron or another plain polystyrene foam. Never cut PVC foam board (Foamex/Sintra), because it gives off chlorine gas.

## Full-size sheets: `laser/foam_fullsize/`

These are the plan's original three sheets at 1000 × 500 mm, cleaned up with the same three layers. They're for a laser with a bigger bed, or for printing as paper templates.

## Changing the sheet size

If your foam comes in a different size, edit `SHEET_W`, `SHEET_H` or `MARGIN` at the top of `make_foam.py` and run it again. You can also change `SPLITS` to move the wing joints.

```
pip install pymupdf shapely numpy scipy pillow matplotlib ezdxf
python3 make_foam.py
```

Source plan © Laurent Berlivet / jivaro-models.org.
