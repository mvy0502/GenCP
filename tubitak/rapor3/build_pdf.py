"""Markdown -> PDF via reportlab with DejaVu (Turkish glyphs). Rebuilt: the Report 2 helper was purged."""
import re, sys, os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Image as RLImage, HRFlowable, KeepTogether)
F="/opt/homebrew/Caskroom/miniforge/base/pkgs/matplotlib-base-3.11.1-py311h3c3ad35_2/lib/python3.11/site-packages/matplotlib/mpl-data/fonts/ttf"
pdfmetrics.registerFont(TTFont("DJ", f"{F}/DejaVuSans.ttf"))
pdfmetrics.registerFont(TTFont("DJ-B", f"{F}/DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("DJ-I", f"{F}/DejaVuSans-Oblique.ttf"))
pdfmetrics.registerFontFamily("DJ", normal="DJ", bold="DJ-B", italic="DJ-I")
SRC, OUT, TITLE = sys.argv[1], sys.argv[2], sys.argv[3]
BASE=os.path.dirname(os.path.abspath(SRC))
INK=colors.HexColor("#1a1a1a"); ACC=colors.HexColor("#1f4e79"); MUT=colors.HexColor("#555555")
S=dict(
 h1=ParagraphStyle("h1",fontName="DJ-B",fontSize=15.5,leading=19,textColor=ACC,spaceAfter=1),
 h2=ParagraphStyle("h2",fontName="DJ",fontSize=10.6,leading=14,textColor=MUT,spaceAfter=7),
 h3=ParagraphStyle("h3",fontName="DJ-B",fontSize=11.6,leading=15,textColor=ACC,spaceBefore=11,spaceAfter=4),
 p=ParagraphStyle("p",fontName="DJ",fontSize=9.35,leading=13.4,textColor=INK,spaceAfter=5.5,alignment=4),
 cap=ParagraphStyle("cap",fontName="DJ-I",fontSize=8.2,leading=11,textColor=MUT,spaceBefore=2,spaceAfter=9,alignment=1),
 meta=ParagraphStyle("meta",fontName="DJ",fontSize=8.8,leading=12,textColor=MUT,spaceAfter=3),
)
def inl(t):
    t=t.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")
    t=re.sub(r"\*\*(.+?)\*\*", r'<font name="DJ-B">\1</font>', t)
    t=re.sub(r"(?<!\*)\*([^*]+?)\*(?!\*)", r'<font name="DJ-I">\1</font>', t)
    t=re.sub(r"`(.+?)`", r'<font name="DJ" color="#1f4e79">\1</font>', t)
    return t
story=[]; lines=open(SRC,encoding="utf-8").read().split("\n"); i=0
while i < len(lines):
    L=lines[i].rstrip(); i+=1
    if not L.strip(): continue
    if L.startswith("![]("):
        p=os.path.join(BASE, L[4:-1])
        from PIL import Image as PIm
        w,h=PIm.open(p).size
        maxw=170*mm; sc=min(maxw/w, 1.0)
        cap=None
        if i<len(lines) and lines[i].strip().startswith("*") and lines[i].strip().endswith("*"):
            cap=lines[i].strip().strip("*"); i+=1
        blk=[Spacer(1,3), RLImage(p,width=w*sc,height=h*sc)]
        if cap: blk.append(Paragraph(inl(cap), S["cap"]))
        else: blk.append(Spacer(1,7))
        story.append(KeepTogether(blk)); continue
    if L.startswith("---"): story.append(Spacer(1,4)); story.append(HRFlowable(width="100%",thickness=0.6,color=colors.HexColor("#cccccc"))); story.append(Spacer(1,5)); continue
    if L.startswith("## "): story.append(Paragraph(inl(L[3:]), S["h2"])); continue
    if L.startswith("# "): story.append(Paragraph(inl(L[2:]), S["h1"])); continue
    if L.startswith("**") and L.endswith("**") and len(L)<90 and L[2:-2].strip()[0].isdigit() and ". " in L[:8]:
        story.append(Paragraph(inl(L), S["h3"])); continue
    if re.match(r"^\*\*\d+\.", L): story.append(Paragraph(inl(L), S["h3"])); continue
    if L.startswith("**23 Ağustos") or L.startswith("Kod ve tüm"):
        story.append(Paragraph(inl(L), S["meta"])); continue
    story.append(Paragraph(inl(L), S["p"]))
def deco(c,d):
    c.saveState(); c.setFont("DJ",7.4); c.setFillColor(MUT)
    c.drawString(20*mm, 12*mm, "GenCP · Sonuç Raporu · 23 Ağustos 2026")
    c.drawRightString(190*mm, 12*mm, f"Sayfa {c.getPageNumber()}")
    c.setStrokeColor(colors.HexColor("#dddddd")); c.setLineWidth(0.5)
    c.line(20*mm, 15*mm, 190*mm, 15*mm); c.restoreState()
doc=BaseDocTemplate(OUT,pagesize=A4,leftMargin=20*mm,rightMargin=20*mm,topMargin=17*mm,bottomMargin=19*mm,title=TITLE,author="Vedat Yıldırım")
doc.addPageTemplates([PageTemplate(id="n",frames=[Frame(20*mm,19*mm,170*mm,259*mm,id="f")],onPage=deco)])
doc.build(story)
from pypdf import PdfReader
print(f"WROTE {OUT} — {len(PdfReader(OUT).pages)} pages")
