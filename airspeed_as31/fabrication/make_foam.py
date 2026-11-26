"""Laser-cut files for the Depron (foam) parts of the Airspeed A.S.31.

Reads ../airspeed_plan templates (airspeed_parts.pdf, three 1000 x 500 mm
sheets drawn 1:1) and writes:

  laser/foam_fullsize/  the original three sheets, cleaned up (cut, score
                        and label layers), for lasers with a bed of at least
                        1000 x 500 mm.
  laser/foam_p2/        the same parts re-nested onto 600 x 300 mm sheets for
                        the xTool P2 (600 x 308 mm bed). The wing and the
                        KFM step layer are wider than the bed, so they are
                        split with dovetail puzzle joints.

Colour layers in every SVG/DXF:
  red   (#FF0000, CUT)    cut through
  blue  (#0000FF, SCORE)  alignment axes for stacking fuselage layers:
                          light score or mark only
  black (#000000, LABEL)  part names: low-power engrave, or hide the layer

Run:  python3 make_foam.py   (needs pymupdf, shapely, numpy, scipy, pillow,
                              matplotlib, ezdxf)
"""
from pathlib import Path

import ezdxf
import numpy as np
import pymupdf
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
from PIL import Image, ImageDraw
from scipy.ndimage import binary_dilation
from scipy.signal import fftconvolve
from shapely import affinity
from shapely.geometry import (GeometryCollection, LineString, MultiLineString,
                              MultiPolygon, Point, Polygon, box)
from shapely.ops import polygonize, polylabel, unary_union

HERE = Path(__file__).parent
PDF = HERE.parent / "airspeed_parts.pdf"
OUT_FULL = HERE / "laser" / "foam_fullsize"
OUT_P2 = HERE / "laser" / "foam_p2"
PT = 25.4 / 72

# P2 sheet: 600 x 300 mm foam blank, 5 mm clear margin all round
SHEET_W, SHEET_H, MARGIN, GAP = 600, 300, 5, 3

# where to split the over-size parts (x in sheet-1 page coordinates, mm).
# Chosen to miss servo pockets and the battery opening, and staggered
# so the wing joints and the KFM-step joint don't line up.
SPLITS = {"WING": [270.0, 440.0], "KFM STEP": [520.0]}

# logo artwork on the template sheets (skipped)
LOGOS = [box(825, 395, 905, 470), box(655, 5, 730, 80), box(820, 35, 895, 110)]


# --------------------------------------------------------------------------
# PDF -> geometry
# --------------------------------------------------------------------------
def _bez(p0, p1, p2, p3, n=24):
    t = np.linspace(0, 1, n)[:, None]
    P = [np.array([p.x, p.y]) for p in (p0, p1, p2, p3)]
    return ((1 - t) ** 3 * P[0] + 3 * (1 - t) ** 2 * t * P[1]
            + 3 * (1 - t) * t ** 2 * P[2] + t ** 3 * P[3]) * PT


def _item_lines(it):
    k = it[0]
    if k == "l":
        return [np.array([[it[1].x, it[1].y], [it[2].x, it[2].y]]) * PT]
    if k == "c":
        return [_bez(*it[1:5])]
    if k == "re":
        r = it[1]
        return [np.array([[r.x0, r.y0], [r.x1, r.y0], [r.x1, r.y1],
                          [r.x0, r.y1], [r.x0, r.y0]]) * PT]
    if k == "qu":
        q = it[1]
        return [np.array([[p.x, p.y] for p in (q.ul, q.ur, q.lr, q.ll, q.ul)]) * PT]
    raise ValueError(k)


def read_page(page):
    cut, score = [], []
    for g in page.get_drawings():
        r = g["rect"]
        bb = box(r.x0 * PT, r.y0 * PT, r.x1 * PT, r.y1 * PT)
        if any(L.contains(bb) for L in LOGOS) or g["type"] not in ("s", "fs"):
            continue
        lines = [LineString(l) for it in g["items"] for l in _item_lines(it)]
        dashed = g.get("dashes") not in (None, "[] 0")
        thin = (g.get("width") or 1) < 0.75
        (score if dashed or thin else cut).extend(lines)
    words = [((w[0] + w[2]) / 2 * PT, (w[1] + w[3]) / 2 * PT, w[4])
             for w in page.get_text("words")]
    return cut, score, words


def parts_from_page(page, thickness):
    cut, score, words = read_page(page)
    faces = list(polygonize(unary_union(cut)))
    # the sheet border rectangles enclose all the waste foam
    frames = [f for f in faces if f.envelope.area > 50000
              and abs(Polygon(f.exterior).area - f.envelope.area) < 1]
    cand = [f for f in faces if all(f is not fr for fr in frames)]
    # a face lying inside another candidate face is a hole of that part
    parts = [f for f in cand
             if not any(o is not f and Polygon(o.exterior).contains(f.representative_point())
                        and o.area > f.area for o in cand)]
    score_u = unary_union(score)
    out = []
    for f in parts:
        name = None
        for x, y, w in words:
            if w[:1] in "EF" and w[1:].isdigit() and f.buffer(-0.5).contains(Point(x, y)):
                name = w
        out.append({"poly": f, "score": f.buffer(-0.3).intersection(score_u),
                    "name": name, "t": thickness})
    return out


def name_parts(parts, sheet):
    """Give names to parts the plan leaves unlabelled."""
    for p in parts:
        if p["name"]:
            continue
        f = p["poly"]
        x0, y0, x1, y1 = f.bounds
        w, h = x1 - x0, y1 - y0
        if sheet == 3:
            p["name"] = "CABIN SKIN"
        elif f.area > 40000:
            p["name"] = "WING" if len(f.interiors) == 4 else "KFM STEP"
        elif min(w, h) < 20:
            p["name"] = "BOOM COVER" if min(w, h) > 12 else "BOOM SIDE"
        elif y0 < 1:
            p["name"] = "AILERON"
        elif f.area > 20000:
            p["name"] = "STAB"
        elif abs(f.area - 3802) < 50:
            p["name"] = "ELEVATOR"
        elif abs(f.area - 3050) < 50:
            p["name"] = "STAB CENTRE"
        else:
            p["name"] = "REAR POINT"


# --------------------------------------------------------------------------
# splitting with dovetails
# --------------------------------------------------------------------------
def dovetail(x, y, d, neck=8.0, head=13.0, depth=9.0):
    return Polygon([(x, y - neck / 2), (x + d * depth, y - head / 2),
                    (x + d * depth, y + head / 2), (x, y + neck / 2)])


def split_part(part, X, spacing=55.0, end_clear=14.0):
    f = part["poly"]
    x0, y0, x1, y1 = f.bounds
    seg = f.intersection(LineString([(X, y0 - 1), (X, y1 + 1)]))
    segs = getattr(seg, "geoms", [seg])
    to_right, to_left = [], []          # tabs owned by left / right piece
    k = 0
    for s in segs:
        ya, yb = sorted(c[1] for c in s.coords)
        L = yb - ya - 2 * end_clear
        if L <= 0:
            continue
        n = max(1, int(L // spacing) + 1)
        ys = [ya + end_clear + (L * (i + 0.5) / n) for i in range(n)]
        for y in ys:
            d = 1 if k % 2 == 0 else -1
            t = dovetail(X, y, d)
            if t.buffer(2).within(f):
                (to_right if d > 0 else to_left).append(t)
                k += 1
    tr = unary_union(to_right) if to_right else Polygon()
    tl = unary_union(to_left) if to_left else Polygon()
    left = f.intersection(box(x0 - 1, y0 - 1, X, y1 + 1)).union(tr).difference(tl)
    right = f.intersection(box(X, y0 - 1, x1 + 1, y1 + 1)).union(tl).difference(tr)
    res = []
    for g in (left, right):
        g = g.intersection(f).buffer(0)
        if isinstance(g, MultiPolygon):
            g = max(g.geoms, key=lambda q: q.area)
        res.append({**part, "poly": g, "score": g.buffer(-0.3).intersection(part["score"])})
    return res


def apply_splits(parts):
    out = []
    for p in parts:
        xs = SPLITS.get(p["name"])
        if not xs:
            out.append(p)
            continue
        pieces = [p]
        for X in xs:
            nxt = []
            for q in pieces:
                if q["poly"].bounds[0] < X < q["poly"].bounds[2]:
                    nxt += split_part(q, X)
                else:
                    nxt.append(q)
            pieces = nxt
        pieces.sort(key=lambda q: q["poly"].bounds[0])
        for i, q in enumerate(pieces, 1):
            q["name"] = f"{p['name']} {i}/{len(pieces)}"
        out += pieces
    return out


# --------------------------------------------------------------------------
# labels
# --------------------------------------------------------------------------
FONT = FontProperties(family="DejaVu Sans", weight="bold")


def text_poly(s, size):
    tp = TextPath((0, 0), s, size=size, prop=FONT)
    polys = [Polygon(p) for p in tp.to_polygons() if len(p) >= 3]
    # even-odd: letters with counters (O, A, 8...)
    g = Polygon()
    for q in sorted(polys, key=lambda q: -q.area):
        g = g.symmetric_difference(q)
    return affinity.scale(g, 1, -1, origin=(0, 0))   # SVG y is down


def make_label(part):
    f = part["poly"]
    x0, y0, x1, y1 = f.bounds
    rot = (x1 - x0) < (y1 - y0) * 0.6
    c = polylabel(f, tolerance=0.5)
    r = f.exterior.distance(c)
    for hole in f.interiors:
        r = min(r, hole.distance(c))
    text = part["name"] + ("" if part["t"] == 6 else " 3mm")
    for size in (8, 6, 5, 4, 3, 2.5):
        t = text_poly(text, size)
        if rot:
            t = affinity.rotate(t, -90, origin=(0, 0))
        tc = t.envelope.centroid
        t = affinity.translate(t, c.x - tc.x, c.y - tc.y)
        if t.buffer(1).within(f) and not any(
                Polygon(h).intersects(t.buffer(1)) for h in f.interiors):
            return t
    return Polygon()


# --------------------------------------------------------------------------
# transforms & output
# --------------------------------------------------------------------------
def xform(part, fn):
    return {**part, "poly": fn(part["poly"]), "score": fn(part["score"]),
            "label": fn(part["label"])}


def _rings(g):
    if g.is_empty:
        return []
    if isinstance(g, Polygon):
        return [g.exterior] + list(g.interiors)
    if hasattr(g, "geoms"):
        return [r for q in g.geoms for r in _rings(q)]
    return []


def _lines(g):
    if g.is_empty:
        return []
    if isinstance(g, LineString):
        return [g]
    if hasattr(g, "geoms"):
        return [l for q in g.geoms for l in _lines(q)]
    return []


def _d(coords, close):
    pts = " L".join(f"{x:.3f},{y:.3f}" for x, y in coords)
    return f"M{pts}{' Z' if close else ''}"


def write_sheet(parts, W, H, stem, title):
    cut = [p["poly"] for p in parts]
    holes_first = []
    for p in cut:  # inner contours first so pieces don't drop early
        holes_first += [_d(r.coords, True) for r in p.interiors]
    outer = [_d(p.exterior.coords, True) for p in cut]
    score = [_d(l.coords, False) for p in parts for l in _lines(p["score"])]
    def _polys(g):
        if g.is_empty:
            return []
        return [g] if isinstance(g, Polygon) else [q for q in g.geoms if isinstance(q, Polygon)]
    # one path per letter so even-odd fill keeps the counters (O, A, R) open
    label = [" ".join(_d(r.coords, True) for r in _rings(q))
             for p in parts for q in _polys(p["label"])]
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" '
           f'viewBox="0 0 {W} {H}">', f"<title>{title}</title>",
           '<g id="LABEL" fill="#000000" fill-rule="evenodd" stroke="none">',
           *[f'<path d="{d}"/>' for d in label], "</g>",
           '<g id="SCORE" fill="none" stroke="#0000FF" stroke-width="0.1">',
           *[f'<path d="{d}"/>' for d in score], "</g>",
           '<g id="CUT" fill="none" stroke="#FF0000" stroke-width="0.1">',
           *[f'<path d="{d}"/>' for d in holes_first + outer], "</g>", "</svg>"]
    (stem.with_suffix(".svg")).write_text("\n".join(svg))

    doc = ezdxf.new("R2010", setup=False)
    doc.units = ezdxf.units.MM
    for n, c in (("CUT", 1), ("SCORE", 5), ("LABEL", 7)):
        doc.layers.add(n, color=c)
    msp = doc.modelspace()
    flip = lambda cs: [(x, H - y) for x, y in cs]
    for p in cut:
        for r in list(p.interiors) + [p.exterior]:
            msp.add_lwpolyline(flip(r.coords), close=True, dxfattribs={"layer": "CUT"})
    for p in parts:
        for l in _lines(p["score"]):
            msp.add_lwpolyline(flip(l.coords), dxfattribs={"layer": "SCORE"})
        for r in _rings(p["label"]):
            msp.add_lwpolyline(flip(r.coords), close=True, dxfattribs={"layer": "LABEL"})
    doc.saveas(stem.with_suffix(".dxf"))


def preview(sheets, path, W, H, s=1.0):
    pad = 12
    im = Image.new("RGB", (int(W * s) + 2 * pad, (int(H * s) + pad) * len(sheets) + pad), "white")
    dr = ImageDraw.Draw(im)
    for i, parts in enumerate(sheets):
        oy = pad + i * (int(H * s) + pad)
        dr.rectangle([pad, oy, pad + W * s, oy + H * s], outline=(170, 170, 170))
        T = lambda cs: [(pad + x * s, oy + y * s) for x, y in cs]
        for p in parts:
            dr.polygon(T(p["poly"].exterior.coords), fill=(255, 236, 200), outline=(220, 0, 0))
            for r in p["poly"].interiors:
                dr.polygon(T(r.coords), fill="white", outline=(220, 0, 0))
            for l in _lines(p["score"]):
                dr.line(T(l.coords), fill=(0, 0, 255))
            for r in _rings(p["label"]):
                dr.line(T(r.coords), fill=(0, 0, 0))
    im.save(path)


# --------------------------------------------------------------------------
# nesting (raster, bottom-left fill, 1 mm grid)
# --------------------------------------------------------------------------
def orient(part):
    """Rotate so the minimum-area bounding rectangle is axis aligned."""
    mrr = part["poly"].minimum_rotated_rectangle
    c = list(mrr.exterior.coords)
    e = max([(c[i], c[i + 1]) for i in range(4)],
            key=lambda ab: np.hypot(ab[1][0] - ab[0][0], ab[1][1] - ab[0][1]))
    ang = np.degrees(np.arctan2(e[1][1] - e[0][1], e[1][0] - e[0][0]))
    o = part["poly"].centroid
    return xform(part, lambda g: affinity.rotate(g, -ang, origin=o))


def mask(poly, pad):
    x0, y0, x1, y1 = poly.bounds
    w, h = int(np.ceil(x1 - x0)) + 1, int(np.ceil(y1 - y0)) + 1
    im = Image.new("1", (w, h), 0)
    ImageDraw.Draw(im).polygon([(x - x0, y - y0) for x, y in poly.exterior.coords], fill=1)
    m = np.array(im, dtype=bool)
    m = np.pad(m, pad)
    return binary_dilation(m, iterations=pad)


def nest(parts, W, H):
    UW, UH = W - 2 * MARGIN, H - 2 * MARGIN
    pad = int(np.ceil(GAP / 2)) + 1
    parts = sorted((orient(p) for p in parts), key=lambda p: -p["poly"].envelope.area)
    sheets = []   # [occupancy, placed]
    for p in parts:
        options = []
        for rot in (0, 90, 180, 270):
            q = xform(p, lambda g: affinity.rotate(g, rot, origin=p["poly"].centroid))
            x0, y0, x1, y1 = q["poly"].bounds
            if x1 - x0 > UW or y1 - y0 > UH:
                continue
            options.append((q, mask(q["poly"], pad)))
        if not options:
            raise SystemExit(f"{p['name']} does not fit on a {W}x{H} sheet")
        placed = False
        for sh in sheets + [None]:
            if sh is None:
                sh = [np.zeros((UH + 2 * pad, UW + 2 * pad), bool), []]
                sheets.append(sh)
            occ = sh[0]
            best = None
            for q, m in options:
                mh, mw = m.shape
                if mh > occ.shape[0] or mw > occ.shape[1]:
                    continue
                conv = fftconvolve(occ.astype(float), m[::-1, ::-1].astype(float), mode="valid")
                free = np.argwhere(conv < 0.5)        # (row=y, col=x)
                if len(free) == 0:
                    continue
                k = np.lexsort((free[:, 0], free[:, 1]))[0]   # min x, then min y
                yy, xx = free[k]
                if best is None or (xx, yy) < best[0]:
                    best = ((xx, yy), q, m)
            if best is None:
                continue
            (xx, yy), q, m = best
            occ[yy:yy + m.shape[0], xx:xx + m.shape[1]] |= m
            x0, y0, _, _ = q["poly"].bounds
            dx, dy = MARGIN + xx - x0, MARGIN + yy - y0  # occ index r maps to MARGIN + r - pad
            sh[1].append(xform(q, lambda g: affinity.translate(g, dx, dy)))
            placed = True
            break
        assert placed
    return [s[1] for s in sheets]


# --------------------------------------------------------------------------
def main():
    OUT_FULL.mkdir(parents=True, exist_ok=True)
    OUT_P2.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(PDF)

    p1 = parts_from_page(doc[0], 6)
    name_parts(p1, 1)
    p2all = parts_from_page(doc[1], 6)
    left = [p for p in p2all if p["poly"].bounds[2] < 740]   # sheet 2 (6 mm)
    right = [p for p in p2all if p["poly"].bounds[0] > 740]  # sheet 3 (3 mm)
    for p in right:
        p["t"] = 3
    name_parts(left, 2)
    name_parts(right, 3)

    # number duplicate names: AILERON 1, AILERON 2...
    every = p1 + left + right
    for nm in {p["name"] for p in every}:
        same = [p for p in every if p["name"] == nm]
        if len(same) > 1:
            same.sort(key=lambda p: (p["poly"].bounds[0], p["poly"].bounds[1]))
            for i, p in enumerate(same, 1):
                p["name"] = f"{nm} {i}"
    for p in every:
        p["label"] = make_label(p)   # full-size sheets: label in place

    # full-size cleaned sheets
    write_sheet(p1, 1000, 500, OUT_FULL / "sheet1_depron_6mm", "Airspeed AS31 sheet 1, Depron 6 mm")
    write_sheet(left, 1000, 500, OUT_FULL / "sheet2_depron_6mm", "Airspeed AS31 sheet 2, Depron 6 mm")
    sh3 = [xform(p, lambda g: affinity.translate(g, -749.2, 0)) for p in right]
    write_sheet(sh3, 251, 500, OUT_FULL / "sheet3_depron_3mm", "Airspeed AS31 sheet 3, Depron 3 mm")

    # P2 sheets
    six = apply_splits(p1) + left
    for t, group in ((6, six), (3, right)):
        sheets = nest(group, SHEET_W, SHEET_H)
        for parts in sheets:  # sanity: inside the sheet margin, no overlaps
            for i, a in enumerate(parts):
                x0, y0, x1, y1 = a["poly"].bounds
                assert x0 >= MARGIN - 0.5 and y0 >= MARGIN - 0.5
                assert x1 <= SHEET_W - MARGIN + 0.5 and y1 <= SHEET_H - MARGIN + 0.5, (a["name"], a["poly"].bounds)
                for b in parts[i + 1:]:
                    assert a["poly"].distance(b["poly"]) >= 1.0, (a["name"], b["name"])
        # label after nesting so text is always upright on the sheet
        sheets = [[{**p, "label": make_label(p)} for p in parts] for parts in sheets]
        for i, parts in enumerate(sheets, 1):
            stem = OUT_P2 / f"p2_depron_{t}mm_sheet{i:02d}"
            write_sheet(parts, SHEET_W, SHEET_H, stem,
                        f"Airspeed AS31 P2 {t} mm sheet {i}/{len(sheets)}")
        preview(sheets, OUT_P2 / f"preview_{t}mm.png", SHEET_W, SHEET_H)
        print(f"{t} mm: {len(group)} parts on {len(sheets)} sheets of {SHEET_W}x{SHEET_H}")
        for i, parts in enumerate(sheets, 1):
            print(f"  sheet {i}: " + ", ".join(p["name"] for p in parts))


if __name__ == "__main__":
    main()
