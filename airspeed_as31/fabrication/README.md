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

The foam parts aren't included here. The plan's templates are laid out on 1000 × 500 mm Depron sheets, and the one-piece wing is about 710 mm across, which is wider than the P2's 600 × 308 mm bed.

Source plan © Laurent Berlivet / jivaro-models.org.
