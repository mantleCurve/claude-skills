#!/usr/bin/env python3
"""Build the specimen page: inline glyphs.json and the PRD into <root>/specimen/index.html. Stdlib only.

    python3 build_specimen.py --root <project>      (default root: the current directory)

Run glyphs.py first. If <root>/specimen/index.html does not exist it is created from
specimen_template.html next to this script ({{FAMILY}} filled in); afterwards only the marked
regions are regenerated, so the rest of the page can be hand-edited in the project:

    <!--HERO-START-->      ... <!--HERO-END-->        masthead, hero word, summary, key facts
    <!--MANDATED-START-->  ... <!--MANDATED-END-->    one card per entry of the PRD's mandated-glyph section
    <!--PRD-START-->       ... <!--PRD-END-->         the whole PRD as HTML
    /*GLYPHS-START*/       ... /*GLYPHS-END*/         glyphs.json (inside the <script>)
    /*SETTINGS-START*/     ... /*SETTINGS-END*/       sample strings from the PRD's sample-strings appendix

PRD conventions this relies on (see references/prd-template.md):
    - H1 "<Family> — Product Requirements Document" and a header table with Owner / Version / Classification
    - a heading containing "Mandated glyphs" followed by blocks of  **<glyph> (<subtitle>)**  + bullets
    - a heading containing "Sample strings" (Appendix A) with bullet items in backticks
"""
import html
import json
import os
import re
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from project import load_project, root_parser  # noqa: E402

TEMPLATE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "specimen_template.html")


# ---------------------------------------------------------------- markdown -> html
def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return text


def slug(text):
    return "prd-" + re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def md_to_html(md):
    lines = md.splitlines()
    out, i = [], 0
    toc = []

    def flush_para(buf):
        if buf:
            out.append("<p>%s</p>" % inline(" ".join(buf)))
            buf.clear()

    para = []
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            flush_para(para)
            i += 1
            continue
        if stripped == "---":
            flush_para(para)
            out.append("<hr>")
            i += 1
            continue
        m = re.match(r"^(#{1,3})\s+(.*)$", stripped)
        if m:
            flush_para(para)
            level = len(m.group(1))
            title = m.group(2)
            if level == 1:
                out.append('<h2 class="prd-title">%s</h2>' % inline(title))
            else:
                sid = slug(title)
                tag = "h3" if level == 2 else "h4"
                if level == 2:
                    toc.append((sid, title))
                out.append('<%s id="%s">%s</%s>' % (tag, sid, inline(title), tag))
            i += 1
            continue
        if stripped.startswith("|"):
            flush_para(para)
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                rows.append(cells)
                i += 1
            header, body = rows[0], [r for r in rows[1:] if not all(re.match(r"^:?-{2,}:?$", c) for c in r)]
            t = ['<div class="table-wrap"><table>', "<thead><tr>"]
            t += ["<th>%s</th>" % inline(c) for c in header]
            t.append("</tr></thead><tbody>")
            for r in body:
                r = r + [""] * (len(header) - len(r))
                t.append("<tr>" + "".join("<td>%s</td>" % inline(c) for c in r) + "</tr>")
            t.append("</tbody></table></div>")
            out.append("".join(t))
            continue
        if re.match(r"^[-*]\s+", stripped):
            flush_para(para)
            out.append("<ul>")
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                out.append("<li>%s</li>" % inline(re.sub(r"^\s*[-*]\s+", "", lines[i])))
                i += 1
            out.append("</ul>")
            continue
        if re.match(r"^\d+\.\s+", stripped):
            flush_para(para)
            out.append("<ol>")
            while i < len(lines) and re.match(r"^\s*\d+\.\s+", lines[i]):
                out.append("<li>%s</li>" % inline(re.sub(r"^\s*\d+\.\s+", "", lines[i])))
                i += 1
            out.append("</ol>")
            continue
        para.append(stripped)
        i += 1
    flush_para(para)
    nav = ['<nav class="prd-toc" aria-label="PRD sections"><ol>']
    nav += ['<li><a href="#%s">%s</a></li>' % (sid, inline(t)) for sid, t in toc]
    nav.append("</ol></nav>")
    return "".join(nav) + "\n" + "\n".join(out)


# ---------------------------------------------------------------- PRD extraction
def section(md, title_pattern):
    """Body of the first heading (any level) whose text matches title_pattern, up to the next
    heading of the same or higher level."""
    m = re.search(r"^(#{1,4})\s+.*%s.*$" % title_pattern, md, re.M | re.I)
    if not m:
        return ""
    level = len(m.group(1))
    rest = md[m.end():]
    n = re.search(r"^#{1,%d}\s+" % level, rest, re.M)
    return rest[: n.start()] if n else rest


def first_paragraph(md):
    for block in re.split(r"\n\s*\n", md.strip()):
        b = block.strip()
        if b and not b.startswith(("#", "|", "-", "*", ">")) and not re.match(r"^\d+\.\s", b):
            return " ".join(b.splitlines())
    return ""


def mandated_cards(md, charmap, known):
    """Blocks of  **t (straight)**  followed by bullets -> card html."""
    body = section(md, r"Mandated glyphs")
    cards, cur = [], None
    for line in body.splitlines():
        s = line.strip()
        m = re.match(r"^\*\*(.+?)\*\*\s*$", s)
        if m:
            head = m.group(1)
            mm = re.match(r"^(\S+)\s*(?:\((.*)\))?$", head)
            name, sub = (mm.group(1), mm.group(2) or "") if mm else (head, "")
            gname = charmap.get(name, name)
            cur = {"name": name, "glyph": gname, "sub": sub, "items": []}
            cards.append(cur)
        elif cur is not None and re.match(r"^[-*]\s+", s):
            cur["items"].append(re.sub(r"^[-*]\s+", "", s))
    out = []
    for c in cards:
        missing = "" if c["glyph"] in known else ' <small style="color:var(--accent)">not drawn yet</small>'
        out.append(
            '<article class="m-card">'
            '<div class="m-fig" data-glyph="%s" data-mode="grid"></div>'
            '<h3>%s <small>%s</small>%s</h3><ul>%s</ul></article>'
            % (html.escape(c["glyph"], quote=True), inline(c["name"]), inline(c["sub"]), missing,
               "".join("<li>%s</li>" % inline(i) for i in c["items"])))
    if not out:
        out.append('<p class="note">The PRD has no "Mandated glyphs" section with **glyph** blocks; nothing to show.</p>')
    return "\n".join(out)


def sample_settings(md, charmap, known):
    """Appendix A bullets (`...`) -> SETTINGS entries; strings mostly outside the set become notes."""
    body = section(md, r"Sample strings") or section(md, r"Appendix A")
    strings = []
    for line in body.splitlines():
        if re.match(r"^\s*[-*]\s+", line):
            codes = re.findall(r"`([^`]+)`", line)
            strings += codes or [re.sub(r"^\s*[-*]\s+", "", line).strip()]
    out = []
    for text in strings:
        chars = [ch for ch in text if ch != " "]
        missing = sorted({ch for ch in chars if charmap.get(ch, ch) not in known})
        covered = len(chars) - sum(1 for ch in chars if ch in missing)
        label = text.split(" ")[0][:16] or "Sample"
        size = 72 if len(text) <= 16 else 64 if len(text) <= 28 else 52
        if chars and covered / float(len(chars)) < 0.6:
            out.append({"label": label, "text": None, "size": size,
                        "note": "%s: outside the sample set (%s), not rendered." % (text, " ".join(missing))})
        else:
            e = {"label": label, "text": text, "size": size}
            if missing:
                e["note"] = "Omitted, not in the sample set: %s" % " ".join(missing)
            out.append(e)
    return out


def hero_html(proj, md):
    weights = proj["weights"]
    facts = []
    if proj["classification"]:
        facts.append(("Classification", proj["classification"]))
    facts.append(("Default", "%s, wght %d, stem %d" % (proj["default"], proj["css_weights"][proj["default"]],
                                                      weights[proj["default"]])))
    facts.append(("Weights", " · ".join("%s %d" % kv for kv in weights.items())))
    dl = "".join("<dt>%s</dt><dd>%s</dd>" % (html.escape(k), html.escape(v)) for k, v in facts)
    summary = first_paragraph(section(md, r"Summary"))
    left = " · ".join(x for x in (proj["owner"], "Type specimen") if x)
    return (
        '\n    <div class="masthead">'
        '<span class="label">%s</span><span class="label">%s</span></div>\n'
        '    <div class="hero" id="hero" data-text="%s" aria-label="%s set in its own sample glyphs"></div>\n'
        '    <div class="hero-meta"><p>%s</p><dl>%s</dl></div>\n'
        % (html.escape(left), html.escape(proj["version"]), html.escape(proj["family"], quote=True),
           html.escape(proj["family"], quote=True), inline(summary), dl))


# ---------------------------------------------------------------- assembly
def replace_between(src, start, end, body):
    if start not in src or end not in src:
        sys.exit("specimen/index.html is missing the %s ... %s markers; restore them from the template" % (start, end))
    a = src.index(start) + len(start)
    b = src.index(end)
    return src[:a] + body + src[b:]


def main():
    args = root_parser(__doc__).parse_args()
    proj = load_project(args.root)
    if not os.path.exists(proj["glyphs_json"]):
        sys.exit("no %s: run glyphs.py --root %s first" % (proj["glyphs_json"], proj["root"]))
    if not os.path.exists(proj["prd"]):
        sys.exit("no %s: write the PRD first (references/prd-template.md)" % proj["prd"])
    if not os.path.exists(proj["specimen"]):
        os.makedirs(os.path.dirname(proj["specimen"]), exist_ok=True)
        shutil.copy(TEMPLATE, proj["specimen"])
        print("created %s from the template" % proj["specimen"])

    data_text = open(proj["glyphs_json"], encoding="utf-8").read()
    data = json.loads(data_text)
    charmap = data.get("charmap", {})
    known = set(data["weights"][next(iter(data["weights"]))]["glyphs"])
    md = open(proj["prd"], encoding="utf-8").read()

    src = open(proj["specimen"], encoding="utf-8").read()
    src = src.replace("{{FAMILY}}", html.escape(proj["family"]))
    src = re.sub(r"<title>.*?</title>", "<title>%s Specimen</title>" % html.escape(proj["family"]), src, count=1)
    src = replace_between(src, "<!--HERO-START-->", "<!--HERO-END-->", hero_html(proj, md))
    src = replace_between(src, "<!--MANDATED-START-->", "<!--MANDATED-END-->", "\n" + mandated_cards(md, charmap, known) + "\n")
    src = replace_between(src, "<!--PRD-START-->", "<!--PRD-END-->", "\n" + md_to_html(md) + "\n")
    src = replace_between(src, "/*GLYPHS-START*/", "/*GLYPHS-END*/", data_text.replace("</", "<\\/"))
    settings = json.dumps(sample_settings(md, charmap, known), ensure_ascii=False).replace("</", "<\\/")
    src = replace_between(src, "/*SETTINGS-START*/", "/*SETTINGS-END*/", settings)
    open(proj["specimen"], "w", encoding="utf-8").write(src)
    print("built %s (%d bytes, %d glyphs, %d weights)" % (proj["specimen"], os.path.getsize(proj["specimen"]),
                                                          len(known), len(data["weights"])))


if __name__ == "__main__":
    main()
