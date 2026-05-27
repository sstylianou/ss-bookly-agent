#!/usr/bin/env python3
"""
generate_deck.py — Bookly / Decagon pitch deck (PowerPoint)
5 slides, dark exec theme, Decagon branding.
"""
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR

# ── Palette ────────────────────────────────────────────────────────────────
BG      = RGBColor(0x0B, 0x0F, 0x1A)   # near-black navy
CARD    = RGBColor(0x13, 0x1B, 0x2E)   # elevated card surface
ACCENT  = RGBColor(0x6C, 0x63, 0xFF)   # Decagon purple
ACC2    = RGBColor(0xA5, 0x9F, 0xFF)   # soft purple
WHITE   = RGBColor(0xFF, 0xFF, 0xFF)
GREY    = RGBColor(0x8B, 0x9A, 0xB8)   # body text
GREY2   = RGBColor(0x3B, 0x45, 0x5E)   # dividers / muted
AMBER   = RGBColor(0xF5, 0x9E, 0x0B)   # trade-off label
GREEN   = RGBColor(0x22, 0xD3, 0x6E)   # "worth it" label

# ── Slide dimensions: 13.33" × 7.5" widescreen ────────────────────────────
W = Inches(13.33)
H = Inches(7.5)

prs = Presentation()
prs.slide_width  = W
prs.slide_height = H
BLANK = prs.slide_layouts[6]


# ── Helpers ─────────────────────────────────────────────────────────────────

def bg(slide):
    fill = slide.background.fill
    fill.solid()
    fill.fore_color.rgb = BG


def box(slide, text, l, t, w, h,
        size=16, bold=False, italic=False,
        colour=WHITE, align=PP_ALIGN.LEFT,
        anchor=MSO_ANCHOR.TOP, wrap=True):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = wrap
    tf.anchor    = anchor
    p   = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text           = text
    run.font.size      = Pt(size)
    run.font.bold      = bold
    run.font.italic    = italic
    run.font.color.rgb = colour
    return tb


def rect(slide, l, t, w, h, fill, line=None, lw=0.75):
    s = slide.shapes.add_shape(1, l, t, w, h)
    s.fill.solid()
    s.fill.fore_color.rgb = fill
    if line:
        s.line.color.rgb = line
        s.line.width     = Pt(lw)
    else:
        s.line.fill.background()
    return s


def footer(slide, page):
    rect(slide, Inches(0), H - Inches(0.45), W, Inches(0.45), CARD)
    box(slide, "Confidential  ·  Prepared by Decagon  ·  May 2026",
        Inches(0.4), H - Inches(0.45), Inches(10), Inches(0.45),
        size=10, colour=GREY2)
    box(slide, f"{page} / 5",
        Inches(12.0), H - Inches(0.45), Inches(1.1), Inches(0.45),
        size=10, colour=GREY2, align=PP_ALIGN.RIGHT)


def header(slide, label):
    """Left accent bar + DECAGON wordmark + section label + divider."""
    rect(slide, Inches(0), Inches(0), Inches(0.07), H, ACCENT)
    box(slide, "DECAGON",
        Inches(0.25), Inches(0.22), Inches(3), Inches(0.38),
        size=12, bold=True, colour=ACCENT)
    box(slide, label,
        Inches(0.25), Inches(0.65), Inches(10), Inches(0.35),
        size=12, colour=GREY)
    rect(slide, Inches(0.25), Inches(1.05), Inches(12.83), Inches(0.01), GREY2)


# ══════════════════════════════════════════════════════════════════════════
# SLIDE 1 — Title
# ══════════════════════════════════════════════════════════════════════════
s1 = prs.slides.add_slide(BLANK)
bg(s1)

rect(s1, Inches(0), Inches(0), Inches(0.07), H, ACCENT)   # left bar

box(s1, "DECAGON",
    Inches(0.3), Inches(0.3), Inches(4), Inches(0.45),
    size=14, bold=True, colour=ACCENT)

# Large title
box(s1, "Bex",
    Inches(0.3), Inches(1.6), W - Inches(0.6), Inches(1.7),
    size=96, bold=True, colour=WHITE, align=PP_ALIGN.CENTER)

box(s1, "AI Customer Support Agent for Bookly",
    Inches(0.3), Inches(3.15), W - Inches(0.6), Inches(0.75),
    size=28, colour=ACC2, align=PP_ALIGN.CENTER)

# Rule
rect(s1, Inches(4.2), Inches(4.1), Inches(4.9), Inches(0.012), ACCENT)

box(s1, "A trust-first architecture for enterprise customer experience",
    Inches(0.3), Inches(4.25), W - Inches(0.6), Inches(0.55),
    size=15, italic=True, colour=GREY, align=PP_ALIGN.CENTER)

footer(s1, 1)


# ══════════════════════════════════════════════════════════════════════════
# SLIDE 2 — The Thesis
# ══════════════════════════════════════════════════════════════════════════
s2 = prs.slides.add_slide(BLANK)
bg(s2)
header(s2, "01  —  THE THESIS")

# Quote card
rect(s2, Inches(0.25), Inches(1.25), Inches(12.83), Inches(1.6), CARD)
rect(s2, Inches(0.25), Inches(1.25), Inches(0.06),  Inches(1.6), ACCENT)

box(s2, "“Great CX agents earn trust before they earn efficiency.”",
    Inches(0.5), Inches(1.35), Inches(12.5), Inches(1.4),
    size=32, bold=True, colour=WHITE, align=PP_ALIGN.LEFT,
    anchor=MSO_ANCHOR.MIDDLE)

# Three supporting points
points = [
    ("Most support bots fail by hallucinating policies, inventing order details, and giving wrong answers with confidence. "
     "This erodes trust faster than any wait time.",
     GREY),
    ("Bex is built around one principle: never fabricate, always know your limits, hand off gracefully when you reach them.",
     WHITE),
    ("Every decision — narrow tool schemas, hard identity guardrails, structured escalation paths — flows directly from this belief. "
     "Resolution and trust are not in tension. One enables the other.",
     GREY),
]

y = Inches(3.1)
for body, colour in points:
    rect(s2, Inches(0.25), y + Inches(0.12), Inches(0.035), Inches(0.38), ACCENT)
    box(s2, body, Inches(0.45), y, Inches(12.63), Inches(0.65),
        size=16, colour=colour)
    y += Inches(0.88)

footer(s2, 2)


# ══════════════════════════════════════════════════════════════════════════
# SLIDE 3 — Architecture
# ══════════════════════════════════════════════════════════════════════════
s3 = prs.slides.add_slide(BLANK)
bg(s3)
header(s3, "02  —  ARCHITECTURE")

# ── Request flow ─────────────────────────────────────────────────────────
FW  = Inches(2.17)   # box width
FH  = Inches(0.72)   # box height
FY  = Inches(1.2)
AW  = Inches(0.3)    # arrow width

# 5 boxes, 4 arrows: total = 5*2.17 + 4*0.30 = 10.85 + 1.20 = 12.05"  starts at 0.64"
FX  = [Inches(0.64 + i * (2.17 + 0.30)) for i in range(5)]
labels = ["Customer", "Multi-turn\nCollection", "Claude  +\nTools", "Tool\nExecution", "Response"]
accented = {0, 4}

for i, (label, x) in enumerate(zip(labels, FX)):
    fc = ACCENT if i in accented else CARD
    lc = None    if i in accented else ACCENT
    r  = rect(s3, x, FY, FW, FH, fc, line=lc, lw=1.2)
    box(s3, label, x, FY, FW, FH,
        size=12, bold=(i in accented), colour=WHITE,
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if i < 4:
        box(s3, "→", x + FW, FY, AW, FH,
            size=16, colour=ACCENT,
            align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

# ── Four component cards ──────────────────────────────────────────────────
CY = Inches(2.18)
CH = Inches(3.65)
CW = Inches(2.97)
CG = Inches(0.20)
CX = [Inches(0.25 + i * (2.97 + 0.20)) for i in range(4)]

cols = [
    ("ORCHESTRATION", ["Single agent loop", "Direct Anthropic API", "No frameworks", "One class, one loop"]),
    ("TOOLS",         ["get_order_status", "initiate_return", "escalate_to_human", "All mocked"]),
    ("MEMORY",        ["Full conversation", "history on every", "call — no retrieval", "errors possible"]),
    ("PROMPTS",       ["Identity (system)", "Static policies", "3 guardrails", "Few-shot examples"]),
]

for (title, items), x in zip(cols, CX):
    rect(s3, x, CY,              CW, CH, CARD, line=GREY2, lw=0.75)
    rect(s3, x, CY,              CW, Inches(0.42), ACCENT)
    box(s3, title, x, CY, CW, Inches(0.42),
        size=11, bold=True, colour=WHITE,
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    iy = CY + Inches(0.52)
    for item in items:
        box(s3, "·  " + item, x + Inches(0.15), iy, CW - Inches(0.2), Inches(0.5),
            size=13, colour=GREY)
        iy += Inches(0.52)

# ── Guardrails strip ──────────────────────────────────────────────────────
GY = Inches(6.05)
rect(s3, Inches(0.25), GY, Inches(12.83), Inches(0.55), CARD)
rect(s3, Inches(0.25), GY, Inches(0.06),  Inches(0.55), ACCENT)
box(s3, "GUARDRAILS:    1. Bookly scope only    ·    2. Grounded responses — no fabrication    ·    3. No unauthorised data access",
    Inches(0.45), GY, Inches(12.5), Inches(0.55),
    size=12, colour=GREY, anchor=MSO_ANCHOR.MIDDLE)

footer(s3, 3)


# ══════════════════════════════════════════════════════════════════════════
# SLIDE 4 — Key Decisions
# ══════════════════════════════════════════════════════════════════════════
s4 = prs.slides.add_slide(BLANK)
bg(s4)
header(s4, "03  —  KEY DECISIONS")

decisions = [
    {
        "title":    "Narrow Tool Schemas",
        "chose":    "Required fields on every tool. Claude cannot call get_order_status without both order ID and email — the Anthropic API enforces it at the schema level.",
        "tradeoff": "More schemas to define and maintain as the tool surface grows.",
        "why":      "Eliminates ambiguous calls. Forces data collection before action. Makes every tool invocation predictable and auditable.",
    },
    {
        "title":    "Full History, Not RAG",
        "chose":    "Every Claude call receives the complete conversation history. No vector store, no retrieval step, no embedding pipeline.",
        "tradeoff": "Token cost grows linearly with conversation length.",
        "why":      "Support conversations run <20 turns. Zero retrieval errors. Claude has full context for nuanced follow-ups. RAG makes sense at scale — not here.",
    },
    {
        "title":    "Prompt-Driven Clarification",
        "chose":    "Claude decides when to ask for more information, guided by guardrails and few-shot examples — not a hardcoded intent classifier or decision tree.",
        "tradeoff": "Slightly less deterministic than rule-based routing.",
        "why":      "Handles ambiguous phrasing naturally. Behaviour updated by editing the prompt, not redeploying code. Scales to new use cases without new routing logic.",
    },
]

KW = Inches(3.95)
KH = Inches(5.55)
KY = Inches(1.25)
KX = [Inches(0.25 + i * (3.95 + 0.22)) for i in range(3)]

LABEL_SIZES = {"WHAT WE CHOSE": ACCENT, "THE TRADE-OFF": AMBER, "WHY IT’S WORTH IT": GREEN}

for dec, x in zip(decisions, KX):
    rect(s4, x, KY, KW, KH, CARD, line=GREY2, lw=0.75)
    # Title bar
    rect(s4, x, KY, KW, Inches(0.48), ACCENT)
    box(s4, dec["title"], x, KY, KW, Inches(0.48),
        size=14, bold=True, colour=WHITE,
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    lx = x + Inches(0.22)
    bw = KW - Inches(0.44)
    y  = KY + Inches(0.62)

    for section_label, content, text_h in [
        ("WHAT WE CHOSE",       dec["chose"],    Inches(1.35)),
        ("THE TRADE-OFF",       dec["tradeoff"], Inches(0.75)),
        ("WHY IT’S WORTH IT", dec["why"],   Inches(1.25)),
    ]:
        lcolour = LABEL_SIZES[section_label]
        box(s4, section_label, lx, y, bw, Inches(0.28),
            size=9, bold=True, colour=lcolour)
        y += Inches(0.28)
        box(s4, content, lx, y, bw, text_h,
            size=13, colour=WHITE if section_label == "WHAT WE CHOSE" else GREY,
            wrap=True)
        y += text_h + Inches(0.18)

footer(s4, 4)


# ══════════════════════════════════════════════════════════════════════════
# SLIDE 5 — What We'd Do Differently
# ══════════════════════════════════════════════════════════════════════════
s5 = prs.slides.add_slide(BLANK)
bg(s5)
header(s5, "04  —  WHAT WE’D DO DIFFERENTLY IN PRODUCTION")

items = [
    ("01", "Auth Before the Conversation Starts",
     "Replace mid-chat email checks with session tokens or OTP at login. Identity confirmed once — not per request."),
    ("02", "RAG for Policy Knowledge Base",
     "Replace the static context string with vector search over a full policy library. Scales to hundreds of pages without bloating every prompt."),
    ("03", "Streaming Responses",
     "Use the Anthropic streaming API so responses appear progressively. Critical for perceived latency on longer, tool-chained answers."),
    ("04", "Evaluation Harness",
     "Systematic test cases for every guardrail, flow, and edge case — run automatically on every prompt change before production deployment."),
    ("05", "Real Helpdesk Integration",
     "escalate_to_human() posts to Zendesk / Intercom with full conversation context and the customer record — not a mock ticket ID."),
    ("06", "Structured Logging & Audit Trail",
     "Every tool call, result, and model response logged for GDPR compliance, CSAT analysis, and prompt regression debugging."),
]

IH  = Inches(0.92)   # row height
IW  = Inches(5.90)   # column width
IY0 = Inches(1.3)    # top of grid
BADGE_W = Inches(0.48)

for i, (num, title, body) in enumerate(items):
    col = i % 2
    row = i // 2
    x   = Inches(0.25) + col * (IW + Inches(0.28))
    y   = IY0 + row * (IH + Inches(0.22))

    # Number badge
    rect(s5, x, y, BADGE_W, IH, ACCENT)
    box(s5, num, x, y, BADGE_W, IH,
        size=13, bold=True, colour=WHITE,
        align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)

    # Content card
    cw = IW - BADGE_W
    rect(s5, x + BADGE_W, y, cw, IH, CARD, line=GREY2, lw=0.5)
    box(s5, title,
        x + BADGE_W + Inches(0.15), y + Inches(0.07),
        cw - Inches(0.2), Inches(0.32),
        size=13, bold=True, colour=WHITE)
    box(s5, body,
        x + BADGE_W + Inches(0.15), y + Inches(0.40),
        cw - Inches(0.2), Inches(0.52),
        size=11, colour=GREY, wrap=True)

footer(s5, 5)


# ── Save ──────────────────────────────────────────────────────────────────
OUT = "bookly-bex-deck.pptx"
prs.save(OUT)
print(f"✅  Saved: {OUT}")
