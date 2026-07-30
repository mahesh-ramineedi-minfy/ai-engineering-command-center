"""Generates the buildathon demo deck for AI Engineering Command Center."""

import os

from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn

# ---- palette -----------------------------------------------------------
INK = RGBColor(0x0B, 0x14, 0x22)       # near-black slate background
PANEL = RGBColor(0x13, 0x1F, 0x33)     # slightly lighter panel
ACCENT = RGBColor(0x39, 0xC0, 0xC5)    # teal accent
ACCENT_DIM = RGBColor(0x1F, 0x6E, 0x73)
WHITE = RGBColor(0xF4, 0xF7, 0xFB)
MUTED = RGBColor(0xA9, 0xB6, 0xC7)
WARN = RGBColor(0xF2, 0xA5, 0x3D)

FONT = "Segoe UI"

SLIDE_W = Inches(13.333)
SLIDE_H = Inches(7.5)


def new_deck():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    return prs


def blank_slide(prs):
    layout = prs.slide_layouts[6]  # blank
    slide = prs.slides.add_slide(layout)
    bg = slide.background
    bg.fill.solid()
    bg.fill.fore_color.rgb = INK
    return slide


def add_textbox(slide, left, top, width, height, text, size=18, color=WHITE,
                 bold=False, italic=False, align=PP_ALIGN.LEFT, font=FONT,
                 anchor=None, line_spacing=None):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    if anchor is not None:
        tf.vertical_anchor = anchor
    p = tf.paragraphs[0]
    p.alignment = align
    if line_spacing:
        p.line_spacing = line_spacing
    run = p.add_run()
    run.text = text
    run.font.size = Pt(size)
    run.font.color.rgb = color
    run.font.bold = bold
    run.font.italic = italic
    run.font.name = font
    return box


def add_bullets(slide, left, top, width, height, items, size=20, color=WHITE,
                 accent=ACCENT, gap=10, font=FONT):
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(gap)
        p.line_spacing = 1.15
        if isinstance(item, tuple):
            head, rest = item
        else:
            head, rest = None, item
        if head:
            r1 = p.add_run()
            r1.text = f"{head}  "
            r1.font.size = Pt(size)
            r1.font.bold = True
            r1.font.color.rgb = accent
            r1.font.name = font
            r2 = p.add_run()
            r2.text = rest
            r2.font.size = Pt(size)
            r2.font.color.rgb = color
            r2.font.name = font
        else:
            r = p.add_run()
            r.text = f"•  {rest}"
            r.font.size = Pt(size)
            r.font.color.rgb = color
            r.font.name = font
    return box


def add_kicker(slide, text):
    add_textbox(slide, Inches(0.7), Inches(0.4), Inches(8), Inches(0.4),
                text.upper(), size=14, color=ACCENT, bold=True)


def add_title(slide, text, top=Inches(0.75), size=32):
    add_textbox(slide, Inches(0.7), top, Inches(12), Inches(0.9), text,
                size=size, color=WHITE, bold=True)
    rule = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.72), top + Inches(0.85),
                                   Inches(1.1), Pt(4))
    rule.fill.solid()
    rule.fill.fore_color.rgb = ACCENT
    rule.line.fill.background()
    return rule


def box(slide, left, top, width, height, label, sublabel=None, fill=PANEL,
         line=ACCENT_DIM, text_color=WHITE, sub_color=MUTED, size=13, sub_size=10.5,
         shape_type=MSO_SHAPE.ROUNDED_RECTANGLE):
    shp = slide.shapes.add_shape(shape_type, left, top, width, height)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    shp.line.color.rgb = line
    shp.line.width = Pt(1.25)
    shp.shadow.inherit = False
    tf = shp.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.margin_left = Pt(6)
    tf.margin_right = Pt(6)
    tf.margin_top = Pt(4)
    tf.margin_bottom = Pt(4)
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = label
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = text_color
    r.font.name = FONT
    if sublabel:
        p2 = tf.add_paragraph()
        p2.alignment = PP_ALIGN.CENTER
        r2 = p2.add_run()
        r2.text = sublabel
        r2.font.size = Pt(sub_size)
        r2.font.color.rgb = sub_color
        r2.font.name = FONT
    return shp


def group_label(slide, left, top, text):
    add_textbox(slide, left, top, Inches(4), Inches(0.3), text.upper(), size=11,
                color=ACCENT, bold=True)


def connector(slide, x1, y1, x2, y2, color=ACCENT_DIM, dashed=False):
    conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x1, y1, x2, y2)
    conn.line.color.rgb = color
    conn.line.width = Pt(1.5)
    if dashed:
        ln = conn.line._get_or_add_ln()
        d = ln.makeelement(qn('a:prstDash'), {'val': 'dash'})
        ln.append(d)
    return conn


# =========================================================================
prs = new_deck()

# ---- Slide 1: Title -----------------------------------------------------
s = blank_slide(prs)
add_textbox(s, Inches(0.9), Inches(2.3), Inches(11.5), Inches(0.5),
            "BUILDATHON DEMO", size=16, color=ACCENT, bold=True)
add_textbox(s, Inches(0.9), Inches(2.75), Inches(11.5), Inches(1.6),
            "AI Engineering Command Center", size=44, color=WHITE, bold=True)
add_textbox(s, Inches(0.9), Inches(3.85), Inches(11), Inches(0.9),
            "One conversational interface for engineering operations — sprint, code, "
            "CI/CD, uptime, incidents, and logs, correlated by an agent.",
            size=18, color=MUTED)
rule = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.92), Inches(2.68), Inches(2.2), Pt(4))
rule.fill.solid(); rule.fill.fore_color.rgb = ACCENT; rule.line.fill.background()
add_textbox(s, Inches(0.9), Inches(6.7), Inches(8), Inches(0.4),
            "Presented by Mahesh Ramineedi, Technical Lead", size=13, color=MUTED)
s.notes_slide.notes_text_frame.text = (
    "Open by naming the pain, not the product: engineers lose time every day stitching "
    "together Jira, GitHub, CI/CD, monitoring, and logs by hand to answer simple questions "
    "like \"is this release healthy?\". This project is a conversational command center that "
    "does that correlation for you. Keep this slide under 20 seconds."
)

# ---- Slide 2: Problem ---------------------------------------------------
s = blank_slide(prs)
add_kicker(s, "The Problem")
add_title(s, "Engineering signal is scattered across six tools")
add_bullets(s, Inches(0.7), Inches(2.1), Inches(7.6), Inches(4.5), [
    ("Jira", "sprint progress and blocked issues"),
    ("GitHub", "commits, PRs, review status"),
    ("CI/CD", "build and deploy health"),
    ("Monitoring", "uptime and active incidents"),
    ("Logs", "the error that actually explains what broke"),
], size=19, gap=14)
add_textbox(s, Inches(0.7), Inches(6.15), Inches(11.5), Inches(1.0),
            "Answering “is this release healthy?” means opening 5+ tools and manually "
            "connecting the dots — every time.", size=17, color=WARN, italic=True)

# right-side visual: 5 disconnected chips
labels = ["Jira", "GitHub", "CI/CD", "Monitoring", "Logs"]
cy = Inches(2.3)
cx = Inches(9.3)
for i, lbl in enumerate(labels):
    box(s, cx, cy + Inches(0.95) * i, Inches(3.1), Inches(0.7), lbl,
        fill=PANEL, line=RGBColor(0x3A, 0x44, 0x55), size=15)
s.notes_slide.notes_text_frame.text = (
    "Land the pain concretely: to triage one incident, an engineer today has to open five "
    "separate tabs and manually connect the dots — a failed build here, an open incident "
    "there, a blocked ticket somewhere else — with nothing tying them together. That manual "
    "correlation is the actual bottleneck, not any one tool being bad on its own."
)

# ---- Slide 3: Solution ---------------------------------------------------
s = blank_slide(prs)
add_kicker(s, "The Solution")
add_title(s, "One orchestrator agent, six tools, one conversation")
add_bullets(s, Inches(0.7), Inches(2.15), Inches(11.7), Inches(3.6), [
    ("Investigates", "a single tool-use loop (NVIDIA NIM) calls tools across Jira, GitHub, "
        "CI/CD, monitoring, incidents, and a log-search RAG pipeline"),
    ("Correlates", "connects findings across systems — e.g. a failed build + an open "
        "incident + a blocked sprint issue becomes one risk story, not three alerts"),
    ("Reports", "returns an executive-ready summary with recommended actions: "
        "reprioritize, add resourcing, escalate"),
], size=19, gap=18)
add_textbox(s, Inches(0.7), Inches(6.2), Inches(11.7), Inches(0.8),
            "Ask it in plain language. It decides which signals matter and pulls them itself.",
            size=16, color=ACCENT, italic=True)
s.notes_slide.notes_text_frame.text = (
    "This is the core pitch: one orchestrator agent, not five separate dashboards or five "
    "separate bots. It decides which of the six tools to call based on the question, pulls "
    "the relevant data itself, and — critically — correlates across sources instead of just "
    "listing results. Emphasize the example: failed build + open incident + blocked sprint "
    "issue becomes ONE risk story with a recommended action, not three unrelated alerts."
)

# ---- Slide 4: Product screenshot ------------------------------------------
s = blank_slide(prs)
add_kicker(s, "The Product")
add_title(s, "What it looks like in practice", size=30)

img_path = os.path.join(os.path.dirname(__file__), "app_chat_ui.png")
img_w, img_h = Inches(8.7), Inches(8.7) * 1000 / 1600
img_left = (SLIDE_W - img_w) / 2
img_top = Inches(1.75)

frame = slide_shape = s.shapes.add_shape(
    MSO_SHAPE.RECTANGLE, img_left - Pt(4), img_top - Pt(4), img_w + Pt(8), img_h + Pt(8)
)
frame.fill.solid(); frame.fill.fore_color.rgb = PANEL
frame.line.color.rgb = ACCENT_DIM
frame.line.width = Pt(1.25)
frame.shadow.inherit = False

s.shapes.add_picture(img_path, img_left, img_top, width=img_w, height=img_h)

add_textbox(s, Inches(0.7), img_top + img_h + Inches(0.25), Inches(11.9), Inches(0.5),
            "A real question, answered by correlating Jira, GitHub, CI/CD, monitoring, and "
            "incidents — with the Sources panel showing which are live vs. mock.",
            size=13, color=MUTED, italic=True, align=PP_ALIGN.CENTER)
s.notes_slide.notes_text_frame.text = (
    "This is a real screenshot, not a mockup — captured live against the running app with "
    "USE_MOCK_DATA=false, real GitHub/Jira MCP connections, and the manager@example.com demo "
    "account. Point out three things: the tool chips under the reply (get_sprint_status, "
    "get_build_status, get_incident_history, get_uptime) show exactly which signals the agent "
    "pulled for this answer; the reply itself correlates all of them into one paragraph "
    "instead of listing four separate stats; and the Sources panel in the sidebar shows Jira/"
    "GitHub/CI-CD as live (green) vs. Monitoring/Incidents as mock (gray) — this is the "
    "StatusBar component that polls GET /api/integrations/status."
)

# ---- Slide 5: Architecture ------------------------------------------------
s = blank_slide(prs)
add_kicker(s, "How It Works")
add_title(s, "Architecture", size=30)

top0 = Inches(1.95)

# Frontend group
group_label(s, Inches(0.6), top0, "Frontend")
fe = box(s, Inches(0.6), top0 + Inches(0.3), Inches(2.3), Inches(0.85),
         "React Chat UI", "ChatWindow + StatusBar", size=13)

# Backend group container label
group_label(s, Inches(3.4), top0, "Backend (FastAPI)")
api = box(s, Inches(3.4), top0 + Inches(0.3), Inches(2.5), Inches(0.7),
          "POST /api/chat", "rate limit + validation", size=12.5)
orch = box(s, Inches(3.4), top0 + Inches(1.25), Inches(2.5), Inches(0.9),
           "Orchestrator", "tool-use loop, max 8 iters", size=13,
           fill=RGBColor(0x0F, 0x35, 0x38), line=ACCENT)

tools_top = top0 + Inches(2.45)
group_label(s, Inches(3.4), top0 + Inches(2.1), "6 Tools")
tool_names = ["Jira", "GitHub", "CI/CD", "Monitoring", "Incidents", "Log RAG"]
tw = Inches(0.98)
for i, name in enumerate(tool_names):
    box(s, Inches(3.4) + tw * i + Inches(0.05) * i, tools_top, tw, Inches(0.6),
        name, size=11.5, fill=PANEL, line=RGBColor(0x3A, 0x44, 0x55))

# External services group
group_label(s, Inches(9.9), top0, "External Services")
nim = box(s, Inches(9.9), top0 + Inches(0.3), Inches(2.9), Inches(0.7),
          "NVIDIA NIM", "chat completions + embeddings", size=12.5)
ghmcp = box(s, Inches(9.9), top0 + Inches(1.15), Inches(2.9), Inches(0.6),
            "GitHub remote MCP", size=12)
jiramcp = box(s, Inches(9.9), top0 + Inches(1.9), Inches(2.9), Inches(0.6),
              "Atlassian remote MCP", size=12)
pg = box(s, Inches(9.9), top0 + Inches(2.65), Inches(2.9), Inches(0.75),
         "Postgres + pgvector", "conversations, log_chunks", size=12.5)

# connectors
connector(s, fe.left + fe.width, fe.top + fe.height // 2, api.left, api.top + api.height // 2)
connector(s, api.left + api.width // 2, api.top + api.height, orch.left + orch.width // 2, orch.top)
connector(s, orch.left + orch.width // 2, orch.top + orch.height,
          Inches(3.4) + tw * 3, tools_top)
connector(s, orch.left + orch.width, orch.top + orch.height // 2, nim.left, nim.top + nim.height // 2)
connector(s, Inches(3.4) + tw * 1 + Inches(0.05), tools_top, ghmcp.left, ghmcp.top + ghmcp.height // 2, dashed=True)
connector(s, Inches(3.4) + tw * 0, tools_top, jiramcp.left, jiramcp.top + jiramcp.height // 2, dashed=True)
connector(s, Inches(3.4) + tw * 5 + Inches(0.25), tools_top + Inches(0.6), pg.left, pg.top + pg.height // 2, dashed=True)

add_textbox(s, Inches(0.7), Inches(6.85), Inches(11.9), Inches(0.5),
            "Zero-param tools by design; GitHub/Jira reached via their official remote MCP servers, not raw REST.",
            size=12.5, color=MUTED, italic=True)
s.notes_slide.notes_text_frame.text = (
    "Walk left to right: React chat UI hits POST /api/chat, which runs the orchestrator's "
    "tool-use loop against NVIDIA NIM. The orchestrator dispatches to six tools, each backed "
    "by an integration client. GitHub and Jira go through their official remote MCP servers "
    "rather than raw REST calls — call this out, it's a deliberate and non-trivial choice. "
    "Log search is a RAG pipeline over Postgres/pgvector. If asked 'why not just call the "
    "REST APIs directly', explain MCP gives a stable, standardized tool surface instead of "
    "each client hand-rolling auth and endpoint quirks per vendor."
)

# ---- Slide 6: Differentiators --------------------------------------------
s = blank_slide(prs)
add_kicker(s, "What's Novel")
add_title(s, "Built on real integration constraints, not a toy demo")
add_bullets(s, Inches(0.7), Inches(2.1), Inches(11.9), Inches(4.6), [
    ("Real remote MCP", "GitHub and Jira data comes through their official remote MCP "
        "servers — not a REST wrapper"),
    ("RAG over logs", "pgvector-backed semantic search over CI/CD + application logs, "
        "as a 6th agent tool"),
    ("Single-tool-call design", "engineered around a real model constraint "
        "(kimi-k2.6 rejects batched tool calls) instead of switching models"),
    ("Zero-param tools", "each tool targets one configured repo/project/service — "
        "avoids the model hallucinating a plausible but wrong target"),
    ("Automatic model fallback", "falls back to a secondary NIM model mid-run if the "
        "primary is unavailable, no retry storm"),
    ("Zero-credential demoable", "every integration ships realistic mock data by default "
        "— the full app runs with no third-party keys"),
], size=16.5, gap=11)
s.notes_slide.notes_text_frame.text = (
    "This is the 'we actually built and debugged this against real systems' slide — each "
    "point came from a real constraint discovered during development, not a design doc. The "
    "single-tool-call point is a good story if asked: the default model (kimi-k2.6) hard-"
    "rejects batched tool calls with a 400 error, so the orchestrator forces one tool call "
    "per turn (parallel_tool_calls=False) rather than switching models. The zero-param tools "
    "point: an earlier version let the model pass a target repo/project per call, and a "
    "smaller model would hallucinate a plausible-but-wrong one — removing the parameter "
    "removed the failure mode entirely."
)

# ---- Slide 7: Tech stack --------------------------------------------------
s = blank_slide(prs)
add_kicker(s, "Under The Hood")
add_title(s, "Tech stack")
cols = [
    ("Backend", ["FastAPI", "SQLAlchemy (async)", "PostgreSQL + pgvector"]),
    ("Frontend", ["React (Vite)", "Single-page chat UI"]),
    ("AI / Agent", ["NVIDIA NIM (OpenAI-compatible)", "moonshotai/kimi-k2.6 (default)",
                    "meta/llama-3.1-70b-instruct (fallback)", "nvidia/nv-embedqa-e5-v5"]),
    ("Integrations", ["GitHub remote MCP", "Atlassian (Jira) remote MCP", "Mock monitoring/incidents"]),
]
colw = Inches(2.95)
for i, (head, items) in enumerate(cols):
    left = Inches(0.7) + colw * i + Inches(0.15) * i
    card = box(s, left, Inches(2.1), colw, Inches(4.3), head, size=16,
               fill=PANEL, line=ACCENT, text_color=ACCENT,
               shape_type=MSO_SHAPE.ROUNDED_RECTANGLE)
    card.text_frame.vertical_anchor = MSO_ANCHOR.TOP
    card.text_frame.paragraphs[0].space_after = Pt(10)
    for it in items:
        p = card.text_frame.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.space_after = Pt(8)
        r = p.add_run()
        r.text = f"• {it}"
        r.font.size = Pt(13)
        r.font.color.rgb = WHITE
        r.font.bold = False
        r.font.name = FONT
    card.text_frame.margin_left = Pt(12)
    card.text_frame.margin_top = Pt(12)
s.notes_slide.notes_text_frame.text = (
    "Quick reference slide, don't over-narrate — move fast. Worth flagging if asked: the "
    "primary model needs per-account approval on NVIDIA NIM even when catalog-listed, which "
    "is why there's an automatic fallback model wired in (meta/llama-3.1-70b-instruct) rather "
    "than the app just failing on a fresh account. Also nv-embedqa-e5-v5 was chosen over a "
    "catalog-listed alternative that looked fine but 500'd on every real embeddings call."
)

# ---- Slide 8: Live demo cue ------------------------------------------------
s = blank_slide(prs)
add_kicker(s, "Live Demo")
add_title(s, '"Why did the checkout deploy fail?"')
steps = [
    "User asks the question in the chat UI",
    "Orchestrator calls search_error_logs(query=…)",
    "Query is embedded (NVIDIA NIM) and matched against pgvector log_chunks",
    "Top matching log line comes back (e.g. a 500 error spike → rollback)",
    "Agent replies citing the specific log line — not a generic guess",
]
top = Inches(2.15)
for i, step in enumerate(steps):
    y = top + Inches(0.78) * i
    dot = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(0.75), y, Inches(0.45), Inches(0.45))
    dot.fill.solid(); dot.fill.fore_color.rgb = ACCENT; dot.line.fill.background()
    dtf = dot.text_frame
    dtf.vertical_anchor = MSO_ANCHOR.MIDDLE
    dp = dtf.paragraphs[0]; dp.alignment = PP_ALIGN.CENTER
    dr = dp.add_run(); dr.text = str(i + 1)
    dr.font.size = Pt(14); dr.font.bold = True; dr.font.color.rgb = INK; dr.font.name = FONT
    add_textbox(s, Inches(1.4), y + Inches(0.03), Inches(11), Inches(0.6), step,
                size=17, color=WHITE)
add_textbox(s, Inches(0.7), Inches(6.6), Inches(11.7), Inches(0.6),
            "→ switching to the live app now", size=15, color=ACCENT, italic=True, bold=True)
s.notes_slide.notes_text_frame.text = (
    "Cue to alt-tab into the running app. Ask this exact question (or something close to it) "
    "live so the audience sees the tool call happen in real time, not just a canned answer. "
    "If the demo environment is offline or credentials aren't handy, narrate the five steps "
    "on this slide as a fallback and mention USE_MOCK_DATA lets the whole flow run end-to-end "
    "with zero external credentials — that's worth saying even if the live demo works, since "
    "it explains why the demo is low-risk to run in front of judges."
)

# ---- Slide 9: Roadmap ------------------------------------------------------
s = blank_slide(prs)
add_kicker(s, "What's Next")
add_title(s, "Roadmap")
add_bullets(s, Inches(0.7), Inches(2.15), Inches(11.7), Inches(4.5), [
    ("Real monitoring provider", "wire in Datadog / Grafana / PagerDuty in place of the "
        "always-mock monitoring client"),
    ("More signal sources", "the integration pattern is a 2-step add — a client with "
        "fetch_summary() plus one tool registration, no orchestrator changes"),
    ("Production-grade rate limiting", "swap the in-memory per-IP limiter for a shared "
        "store before running multiple workers"),
    ("Multi-tenant / auth", "scope conversations and configured targets per team"),
], size=18.5, gap=16)
s.notes_slide.notes_text_frame.text = (
    "Show this is a foundation, not a finished product, without undercutting what's already "
    "working. Monitoring is the one source that's always mock (no universal vendor API "
    "exists) — that's the most obvious next real-data integration. The 'more signal sources' "
    "point is a good chance to reinforce the extensibility story: adding a new source is a "
    "2-step add (client + tool registration), no orchestrator changes needed.\n"
    "\n"
    "Q&A PREP — likely questions and grounded answers, by topic:\n"
    "\n"
    "PRODUCT: Different from just checking dashboards? Dashboards show per-system numbers; "
    "this agent correlates across them (failed build + open incident + blocked sprint issue "
    "= one risk story with a recommended action).\n"
    "\n"
    "ARCHITECTURE: Why one orchestrator, not multiple agents? Simpler failure modes, one "
    "place to reason about tool choice, no inter-agent coordination needed for a single-user "
    "chat loop. Why one tool call per turn? Default model (kimi-k2.6) hard-rejects batched "
    "tool_calls with a 400; parallel_tool_calls=False forces one per turn; "
    "MAX_TOOL_ITERATIONS=8 covers 5 tools + 1 synthesis turn with margin. Why zero-param "
    "tools? An earlier version let the model pick a target repo/project per call and a "
    "smaller model hallucinated plausible-but-wrong values — removing the parameter removed "
    "the failure mode. Why GitHub/Jira via remote MCP not REST? Standardized tool surface "
    "instead of hand-rolling auth/parsing per vendor. What if NIM is down/rate-limited? "
    "timeout=20s, max_retries=1, no pooling, clean 502/503/504 instead of a hang; automatic "
    "fallback to meta/llama-3.1-70b-instruct mid-run if the primary model fails. Why "
    "pgvector? Reuses the same Postgres instance already used for app data, no extra infra.\n"
    "\n"
    "SECURITY: Prompt injection via tool output (e.g. malicious commit message)? System "
    "prompt treats tool output as data, never instructions, verified live against a "
    "jailbreak-style prompt. Chat guardrails? 422 on empty/>4000-char messages, per-IP rate "
    "limit (20/min default, 429 + Retry-After, in-memory — abuse mitigation not a security "
    "boundary). Auth? JWT access token + httponly refresh cookie; refresh-token reuse "
    "revokes all sessions for that user (theft-detection pattern). Zero-credential demo? "
    "Yes — USE_MOCK_DATA=true by default, every integration falls back to realistic mock "
    "data; monitoring/incidents always mock, log search always the mock corpus by design.\n"
    "\n"
    "NOT PRODUCTION-READY YET (be upfront if asked): in-memory rate limiter (single-process "
    "only), monitoring/incidents mock-only, no multi-tenant scoping, no migration tooling "
    "(create_all, no Alembic).\n"
    "\n"
    "DEMO FALLBACK: if live demo breaks, slide 4's screenshot is real (not a mockup), and "
    "slide 8 narrates the traced 'why did the checkout deploy fail?' example step by step "
    "without needing the live app."
)

# ---- Slide 10: Thank you ----------------------------------------------------
s = blank_slide(prs)
add_textbox(s, Inches(0.9), Inches(2.9), Inches(11), Inches(1.2),
            "Thank you", size=44, color=WHITE, bold=True)
add_textbox(s, Inches(0.9), Inches(3.8), Inches(11), Inches(0.6),
            "Questions?", size=20, color=MUTED)
rule = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.92), Inches(2.83), Inches(1.4), Pt(4))
rule.fill.solid(); rule.fill.fore_color.rgb = ACCENT; rule.line.fill.background()
add_textbox(s, Inches(0.9), Inches(6.7), Inches(11), Inches(0.4),
            "github.com/mahesh-ramineedi-minfy/ai-engineering-command-center", size=13, color=MUTED)
s.notes_slide.notes_text_frame.text = (
    "Invite questions. Likely ones to be ready for: why a single orchestrator instead of "
    "multiple specialized agents (simpler failure modes, one place to reason about tool "
    "choice); how credentials/security are handled (env-var driven, mock-by-default, no "
    "secrets in the repo); what happens if NVIDIA NIM is down (bounded timeout + retry, "
    "automatic fallback model, then a clean 502/503/504 instead of a hang)."
)

out_path = os.path.join(os.path.dirname(__file__), "AI_Engineering_Command_Center_Demo.pptx")
prs.save(out_path)
print(f"Saved {out_path} with {len(prs.slides)} slides")
