"""Etapa 1: deteccion de regiones de figuras por pagina (generalizado por libro).

- PDFs con capa de texto: los elementos graficos (imagenes, dibujos vectoriales y lineas de texto que no son cuerpo:
  rotulos de ejes, etc.) se agrupan en clusters; cada caption "Figure X.Y" toma los clusters que le corresponden
  (a la derecha si el caption es lateral, encima si es un caption debajo de la figura, sin texto de cuerpo en el medio).
- PDFs escaneados (DUDAHART): OCR (tesseract TSV) -> lineas; caption por regex; region = tinta entre el texto de cuerpo
  previo y el caption.

Salida: 01_layout/pXXXX.json  {page, figures:[{label, bbox, caption_bbox}], eqnums:[...], header_bottom, printed}
        01_layout/figs/pXXXX_fN.png  (recorte a 200 dpi)    01_layout/ocr/pXXXX.tsv|txt (solo escaneados)
"""
import json
import re
import subprocess
import sys
import unicodedata

import numpy as np
import pymupdf

from config import SRC_PDF, D_LAYOUT, D_OCR, B, TESSERACT, parse_targets, page_offset

FIG_DIR = D_LAYOUT / "figs"
FIG_DIR.mkdir(parents=True, exist_ok=True)
CAP_RE = re.compile(B["cap_re"])
EQ_RE = re.compile(B["eq_re"]) if B.get("eq_re") else None


def norm(s):
    return unicodedata.normalize("NFKC", s)


# ----------------------------------------------------------------------------------------------- capa de texto
def lines_of(page):
    out = []
    for bi, b in enumerate(page.get_text("dict")["blocks"]):
        if b["type"] != 0:
            continue
        for l in b["lines"]:
            spans = [s for s in l["spans"] if s["text"].strip()]
            if not spans:
                continue
            out.append({
                "bbox": pymupdf.Rect(l["bbox"]),
                "block": pymupdf.Rect(b["bbox"]),
                "bi": bi,
                "text": norm("".join(s["text"] for s in l["spans"])).strip(),
                "size": max(s["size"] for s in spans),
                "font": spans[0]["font"].split("+")[-1],
                "color": spans[0]["color"],
            })
    return out


def printed_from_lines(ls, page_h):
    zone = [l for l in ls if l["bbox"].y1 < B["header_y"] or l["bbox"].y0 > B["footer_y"]]
    zone.sort(key=lambda l: (l["bbox"].y0 > B["header_y"], l["bbox"].y0))
    for l in zone:
        if re.fullmatch(r"\d{1,4}", l["text"]):
            return l["text"]
    for l in zone:
        t = re.sub(r"Chapter\s+\d+", " ", l["text"])
        t = re.sub(r"\d+\.\d+", " ", t)
        m = re.search(r"(?<![\w.])(\d{1,4})(?![\w.])", t)
        if m:
            return m.group(1)
    return "?"


def graphic_items(page, ls, cap_blocks):
    pr = page.rect
    H0, H1 = B["header_y"], B["footer_y"]
    items = []
    for im in page.get_image_info():
        r = pymupdf.Rect(im["bbox"]) & pr
        if r.width * r.height > 60 and r.y1 > H0 and r.y0 < H1 + 40:
            items.append(r)
    for d in page.get_drawings():
        r = pymupdf.Rect(d["rect"])
        if r.x1 <= 0 or r.y1 <= 0 or r.x0 >= pr.x1 or r.y0 >= pr.y1:
            continue  # marcas de corte fuera de pagina
        if r.height > 1.5 * pr.height or r.width > 1.5 * pr.width:
            continue  # rectangulos de recorte (clip) gigantes
        r = r & pr
        if r.y1 < H0 or r.y0 > H1 + 40:
            continue
        if r.height < 1.5 and r.width > 0.6 * pr.width:
            continue  # reglas horizontales de ancho completo (separadores)
        if r.width < 0.3 and r.height < 0.3:
            continue
        items.append(r)
    for l in ls:
        if l["bbox"].y1 < H0 or l["bbox"].y0 > H1:
            continue
        if l["size"] < B["body_min"] and not any(l["bbox"].intersects(cb) for cb in cap_blocks):
            items.append(pymupdf.Rect(l["bbox"]))
    # sacar lo que cae dentro de un bloque de caption (p. ej. la grilla "a b / c d" de Gonzalez)
    out = []
    for r in items:
        if any((r & cb).get_area() > 0.5 * max(r.get_area(), 1e-3) for cb in cap_blocks):
            continue
        out.append(r)
    return out


def clusters_of(items, gap=10):
    rects = [pymupdf.Rect(r) for r in items]
    changed = True
    while changed:
        changed = False
        out = []
        for r in rects:
            for i, o in enumerate(out):
                if (o + (-gap, -gap, gap, gap)).intersects(r):
                    out[i] = o | r
                    changed = True
                    break
            else:
                out.append(r)
        rects = out
    return [r for r in rects if r.width > 12 and r.height > 12]


def is_body(l):
    return l["size"] >= B["body_min"] and l["bbox"].width > 60 and len(l["text"].split()) >= 4


def analyze_text(doc, pno):
    page = doc[pno]
    ls = lines_of(page)
    W = page.rect.width
    caps = []
    for l in ls:
        m = CAP_RE.match(l["text"])
        if not m or B.get("cap_font", "") not in l["font"]:
            continue
        kind, label = m.group(1).lower(), m.group(2)
        if kind != "figure":
            continue
        # el bloque del caption: desde la linea del rotulo hasta el final del bloque. Solo lineas alineadas a la
        # izquierda con el rotulo y contiguas (el mismo bloque PDF a veces incluye rotulos de ejes de la figura)
        blk = pymupdf.Rect(l["bbox"])
        anchors = [l["bbox"].x0]
        if l["bbox"].width < 60:
            # rotulo solo ("Figure 4.1") con el texto del caption a su derecha en el mismo renglon (Bishop)
            row = [o for o in ls if o["bi"] == l["bi"] and o is not l
                   and abs((o["bbox"].y0 + o["bbox"].y1) - (l["bbox"].y0 + l["bbox"].y1)) < 8
                   and 0 <= o["bbox"].x0 - l["bbox"].x1 < 20]
            anchors += [o["bbox"].x0 for o in row]
            for o in row:
                blk |= o["bbox"]   # el renglon del rotulo es caption aunque sea de ancho completo
        for o in sorted((o for o in ls if o["bi"] == l["bi"] and o["bbox"].y0 >= l["bbox"].y0 - 4),
                        key=lambda o: o["bbox"].y0):
            if o is l:
                continue
            if min(abs(o["bbox"].x0 - a) for a in anchors) <= 25 and o["bbox"].y0 - blk.y1 < 8 \
                    and o["bbox"].x1 <= max(blk.x1, l["bbox"].x0 + 0.62 * W) + 5:
                blk |= o["bbox"]
        if blk.width < 40:
            blk = pymupdf.Rect(l["bbox"])
        # figura partida en dos paginas: "FIGURE 2.24 (Continued)" -> etiqueta propia 2.24c
        if re.search(r"(?i)\(continued\)", " ".join(o["text"] for o in ls if o["bi"] == l["bi"])[:80]):
            label += "c"
        caps.append((label, blk))
    cap_blocks = [c[1] for c in caps]
    body = [l for l in ls if is_body(l) and not any(l["bbox"].intersects(cb) for cb in cap_blocks)
            and B["header_y"] < l["bbox"].y0 < B["footer_y"]]
    cls = clusters_of(graphic_items(page, ls, cap_blocks))
    W = page.rect.width
    figs, used = [], set()

    def body_between(y_top, y_bot, x0, x1):
        return any(b["bbox"].y0 >= y_top - 2 and b["bbox"].y1 <= y_bot + 2 and b["bbox"].x1 > x0 and b["bbox"].x0 < x1
                   for b in body)

    for label, cb in sorted(caps, key=lambda c: c[1].y0):
        chosen, clip_bottom = [], None
        if B.get("side_captions") and cb.x0 < W * 0.3:
            # caption lateral: clusters a la derecha que se solapan verticalmente con el caption
            for i, k in enumerate(cls):
                if i not in used and (k.x0 + k.x1) / 2 > cb.x1 and k.x1 > cb.x1 + 30 \
                        and k.y0 < cb.y1 and k.y1 > cb.y0 - 6:
                    chosen.append(i)
            # extender a clusters encadenados verticalmente (grillas de subfiguras)
            grow = True
            while chosen and grow:
                grow = False
                R = pymupdf.Rect(cls[chosen[0]])
                for i in chosen[1:]:
                    R |= cls[i]
                for i, k in enumerate(cls):
                    if i in used or i in chosen:
                        continue
                    if (k.x0 + k.x1) / 2 > cb.x1 and (R + (0, -14, 0, 14)).intersects(k) \
                            and not body_between(min(R.y1, k.y1), max(R.y0, k.y0), k.x0, k.x1):
                        chosen.append(i)
                        grow = True
        if not chosen:
            # caption debajo de la figura: el cluster mas cercano encima (sin texto de cuerpo en el medio) y los
            # encadenados verticalmente hacia arriba
            cand = [i for i, k in enumerate(cls) if i not in used and k.y0 < cb.y0 - 5 and (k.y0 + k.y1) / 2 < cb.y0
                    and not body_between(k.y1, cb.y0, k.x0, k.x1)]
            cand.sort(key=lambda i: -cls[i].y1)
            if cand and cb.y0 - cls[cand[0]].y1 < 60:
                chosen = [cand[0]]
                R = pymupdf.Rect(cls[cand[0]])
                for i in cand[1:]:
                    k = cls[i]
                    if R.y0 - k.y1 < 40 and not body_between(k.y1, R.y0, k.x0, k.x1):
                        chosen.append(i)
                        R |= k
                clip_bottom = cb.y0 - 1
        if not chosen and B.get("side_captions") and cb.x0 < W * 0.3:
            # figura hecha solo de texto (p. ej. una matriz tipografica) a la derecha del caption lateral
            tl = [o["bbox"] for o in ls if o["bbox"].x0 > cb.x1 + 10 and o["bbox"].y0 < cb.y1 + 4
                  and o["bbox"].y1 > cb.y0 - 6 and not is_body(o)]
            if tl:
                r = pymupdf.Rect(tl[0])
                for t in tl[1:]:
                    r |= t
                r = pymupdf.Rect(r.x0 - 6, r.y0 - 6, r.x1 + 6, r.y1 + 6) & page.rect
                figs.append({"label": label, "bbox": [round(v, 2) for v in r], "caption_bbox": [round(v, 2) for v in cb]})
                continue
        if not chosen:
            figs.append({"label": label, "bbox": None, "caption_bbox": [round(v, 2) for v in cb], "warn": "sin_region"})
            continue
        r = pymupdf.Rect(cls[chosen[0]])
        for i in chosen[1:]:
            r |= cls[i]
        used.update(chosen)
        r = pymupdf.Rect(r.x0 - 3, r.y0 - 3, r.x1 + 3, r.y1 + 3) & page.rect
        if clip_bottom:
            r.y1 = min(r.y1, clip_bottom)
        r.y0 = max(r.y0, B["header_y"] - 2)
        if B.get("side_captions") and r.x0 < cb.x1 and cb.y0 < r.y1 and cb.y1 > r.y0:
            r.x0 = max(r.x0, cb.x1 + 2)   # no comerse el caption lateral
        figs.append({"label": label, "bbox": [round(v, 2) for v in r], "caption_bbox": [round(v, 2) for v in cb]})
    eqnums = []
    if EQ_RE:
        eqnums = sorted({m.group(1) for l in ls if l["bbox"].x0 > B["eq_x0"] for m in [EQ_RE.match(l["text"])] if m})
    return {"page": pno, "header_bottom": B["header_y"], "eqnums": eqnums, "figures": figs,
            "printed": printed_from_lines(ls, page.rect.height)}


# ----------------------------------------------------------------------------------------------- escaneados
def ocr(doc, pno):
    """Devuelve (texto, lineas[{bbox(pt), text, conf, h}]) usando tesseract; cachea en 01_layout/ocr."""
    D_OCR.mkdir(parents=True, exist_ok=True)
    png = D_OCR / f"p{pno:04d}.png"
    tsv = D_OCR / f"p{pno:04d}.tsv"
    txt = D_OCR / f"p{pno:04d}.txt"
    dpi = B.get("dpi_scan", 150) * 2
    if not (tsv.exists() and txt.exists()):
        doc[pno].get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY).save(png)
        base = str(D_OCR / f"p{pno:04d}")
        subprocess.run([TESSERACT, str(png), base, "-l", "eng", "--psm", "3", "txt", "tsv"],
                       capture_output=True, check=True)
        png.unlink(missing_ok=True)
    s = 72.0 / dpi
    rows = [r.split("\t") for r in tsv.read_text(encoding="utf-8").splitlines()[1:]]
    lines = {}
    for r in rows:
        if len(r) < 12 or r[0] != "5" or not r[11].strip():
            continue
        key = (r[2], r[3], r[4])
        x, y, w, h, conf = int(r[6]), int(r[7]), int(r[8]), int(r[9]), float(r[10])
        L = lines.setdefault(key, {"words": [], "bbox": None, "confs": []})
        rect = pymupdf.Rect(x * s, y * s, (x + w) * s, (y + h) * s)
        L["bbox"] = rect if L["bbox"] is None else L["bbox"] | rect
        L["words"].append(r[11])
        L["confs"].append(conf)
    out = []
    for L in lines.values():
        out.append({"bbox": L["bbox"], "text": " ".join(L["words"]), "conf": sum(L["confs"]) / len(L["confs"]),
                    "n": len(L["words"])})
    out.sort(key=lambda l: (l["bbox"].y0, l["bbox"].x0))
    return txt.read_text(encoding="utf-8"), out


def ink_bbox(page, clip, dpi=72, thr=200):
    pix = page.get_pixmap(clip=clip, dpi=dpi, colorspace=pymupdf.csGRAY)
    a = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w)
    ink = a < thr
    # ignorar ruido: filas/columnas con muy poca tinta
    rows = np.where(ink.sum(axis=1) > 1)[0]
    cols = np.where(ink.sum(axis=0) > 1)[0]
    if len(rows) == 0 or len(cols) == 0:
        return None
    sx, sy = clip.width / pix.w, clip.height / pix.h
    return pymupdf.Rect(clip.x0 + cols[0] * sx, clip.y0 + rows[0] * sy,
                        clip.x0 + (cols[-1] + 1) * sx, clip.y0 + (rows[-1] + 1) * sy)


def analyze_scan(doc, pno):
    page = doc[pno]
    _, ls = ocr(doc, pno)
    pw = page.rect.width
    # caja de texto de la pagina (alterna entre paginas pares e impares): mediana de las lineas largas
    longs = [l for l in ls if l["n"] >= 8 and l["conf"] > 70]
    if longs:
        text_x0 = float(np.median([l["bbox"].x0 for l in longs]))
        text_x1 = float(np.percentile([l["bbox"].x1 for l in longs], 90))
    else:
        text_x0, text_x1 = 100, 460
    header_bottom = 0
    for l in ls:
        if l["bbox"].y1 < 100 and l["n"] <= 6:
            header_bottom = max(header_bottom, l["bbox"].y1 + 2)
    header_bottom = header_bottom or 85

    def body(l):
        # linea de texto corrido: ancha, con varias palabras y mayormente alfabetica (los rotulos de ejes
        # "9 10 11 12 13 14 15" no cuentan)
        words = l["text"].split()
        alpha = sum(1 for w in words if sum(c.isalpha() for c in w) >= 2)
        return (l["bbox"].width > 0.5 * (text_x1 - text_x0) and l["n"] >= 7 and l["conf"] > 60
                and l["bbox"].x0 < text_x1 and alpha >= 0.6 * len(words))

    caps = []
    for i, l in enumerate(ls):
        m = CAP_RE.match(l["text"])
        if m and abs(l["bbox"].x0 - text_x0) < 25:
            # bloque del caption: lineas siguientes con interlineado normal
            blk = pymupdf.Rect(l["bbox"])
            for o in ls[i + 1:]:
                if o["bbox"].y0 - blk.y1 > 8:
                    break
                blk |= o["bbox"]
            caps.append((m.group(1), blk))
    figs = []
    prev = header_bottom
    for label, cb in sorted(caps, key=lambda c: c[1].y0):
        top = prev
        for l in ls:
            if body(l) and l["bbox"].y0 >= top - 1 and l["bbox"].y1 <= cb.y0 - 1 and not CAP_RE.match(l["text"]):
                top = max(top, l["bbox"].y1)
        # ultima linea corta del parrafo (pegada a la anterior) tambien es texto, no figura
        for l in ls:
            if top - 1 <= l["bbox"].y0 <= top + 5 and l["bbox"].y1 <= cb.y0 - 1 and l["conf"] > 60 \
                    and abs(l["bbox"].x0 - text_x0) < 20 and not CAP_RE.match(l["text"]):
                top = max(top, l["bbox"].y1)
        region = pymupdf.Rect(text_x0 - 15, top + 2, text_x1 + 15, cb.y0 - 2)
        tight = ink_bbox(page, region) if region.height > 10 else None
        if tight is None or tight.height < 15:
            figs.append({"label": label, "bbox": None, "caption_bbox": [round(v, 2) for v in cb], "warn": "sin_region"})
        else:
            tight = pymupdf.Rect(tight.x0 - 4, tight.y0 - 4, tight.x1 + 4, tight.y1 + 4) & page.rect
            figs.append({"label": label, "bbox": [round(v, 2) for v in tight], "caption_bbox": [round(v, 2) for v in cb]})
        prev = cb.y1
    eqnums = sorted({m.group(1) for l in ls if l["bbox"].x0 > text_x1 - 60 for m in [EQ_RE.match(l["text"].strip())] if m}) if EQ_RE else []
    return {"page": pno, "header_bottom": header_bottom, "eqnums": eqnums, "figures": figs,
            "printed": str(pno + page_offset(pno))}


# ----------------------------------------------------------------------------------------------- comun
def analyze(doc, pno):
    info = analyze_scan(doc, pno) if B.get("scanned") else analyze_text(doc, pno)
    # bbox corregido a mano para figuras con rotulo detectadas mal: books.py "fig_bbox" = {pno: {label: [x0,y0,x1,y1]}}
    for f in info["figures"]:
        fix = B.get("fig_bbox", {}).get(pno, {}).get(f["label"])
        if fix:
            f["bbox"] = [float(v) for v in fix]
            f["manual_bbox"] = True
    # figuras sin rotulo "Figure N" (graficos de ejemplos, diagramas de problemas, columnas graficas de tablas):
    # definidas a mano en books.py "extra_figs" = {pno: [(label, [x0,y0,x1,y1], hint), ...]}
    for lab, bbox, hint in B.get("extra_figs", {}).get(pno, []):
        info["figures"].append({"label": lab, "bbox": [float(v) for v in bbox], "caption_bbox": [0, 0, 0, 0],
                                "manual": True, "hint": hint})
    return info


def crop_figures(doc, info, dpi=200):
    page = doc[info["page"]]
    for i, f in enumerate(info["figures"]):
        if not f.get("bbox"):
            continue
        out = FIG_DIR / f"p{info['page']:04d}_f{i}.png"
        f["png"] = out.name
        pix = page.get_pixmap(clip=pymupdf.Rect(f["bbox"]), dpi=dpi)
        mask = B.get("fig_mask", {}).get(info["page"], {}).get(f["label"])
        if not mask:
            pix.save(out)
            continue
        # retoque manual (books.py "fig_mask"): blanquear zonas ajenas a la figura (p. ej. el encabezado de
        # pagina que la atraviesa) y redibujar los trazos que cruzaban esa zona. Coordenadas en pt de pagina.
        from PIL import Image, ImageDraw
        im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        dr = ImageDraw.Draw(im)
        bx, by, k = f["bbox"][0], f["bbox"][1], dpi / 72
        for x0, y0, x1, y1 in mask.get("white", []):
            dr.rectangle([(x0 - bx) * k, (y0 - by) * k, (x1 - bx) * k, (y1 - by) * k], fill="white")
        for x0, y0, x1, y1, w in mask.get("lines", []):
            dr.line([(x0 - bx) * k, (y0 - by) * k, (x1 - bx) * k, (y1 - by) * k], fill="black", width=max(1, round(w * k)))
        for poly in mask.get("polys", []):
            dr.polygon([((x - bx) * k, (y - by) * k) for x, y in poly], fill="black")
        # rotulos tapados por el blanqueo: [x, y_arriba, texto, tamano_pt, fuente_ttf]
        for x, y, txt, size, font in mask.get("texts", []):
            from PIL import ImageFont
            fnt = ImageFont.truetype(font, round(size * k))
            dr.text(((x - bx) * k, (y - by) * k), txt, fill="black", font=fnt)
        im.save(out)
        f["masked"] = True


def overlay(doc, info, out):
    d = pymupdf.open()
    d.insert_pdf(doc, from_page=info["page"], to_page=info["page"])
    p = d[0]
    for f in info["figures"]:
        if f.get("bbox"):
            p.draw_rect(pymupdf.Rect(f["bbox"]), color=(1, 0, 0), width=1.5, overlay=True)
        if not f.get("manual"):
            p.draw_rect(pymupdf.Rect(f["caption_bbox"]), color=(0, 0, 1), width=1, overlay=True)
    p.get_pixmap(dpi=60).save(out)
    d.close()


def run(pages, force=False, debug=False):
    doc = pymupdf.open(SRC_PDF)
    for pno in pages:
        out = D_LAYOUT / f"p{pno:04d}.json"
        if out.exists() and not force:
            continue
        info = analyze(doc, pno)
        crop_figures(doc, info)
        out.write_text(json.dumps(info, indent=1), encoding="utf-8")
        if debug:
            (D_LAYOUT / "debug").mkdir(exist_ok=True)
            overlay(doc, info, D_LAYOUT / "debug" / f"p{pno:04d}.png")


def load(pno):
    return json.loads((D_LAYOUT / f"p{pno:04d}.json").read_text(encoding="utf-8"))


if __name__ == "__main__":
    args = sys.argv[1:]
    force = "--force" in args
    debug = "--debug" in args
    args = [a for a in args if a not in ("--force", "--debug")]
    pages = parse_targets(args or ["all"])
    run(pages, force, debug)
    for p in pages:
        info = load(p)
        if info["figures"]:
            print(p, info["printed"], [(f["label"], f.get("bbox") and [round(v) for v in f["bbox"]], f.get("warn", ""))
                                       for f in info["figures"]])
        else:
            print(p, info["printed"])
