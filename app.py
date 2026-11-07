"""
Survey Insight Assistant
Upload a survey CSV and get charts, AI-grouped themes from open-ended answers,
and a short summary with recommendations.

Built by Wong Jun Yi with Streamlit, pandas and Google Gemini.
"""

import html
import json
import os

import altair as alt
import pandas as pd
import streamlit as st

MAX_RESPONSES = 300          # cap sent to the AI per question, keeps it fast and free-tier friendly
MAX_RUNS_PER_SESSION = 5     # stops one visitor from using up the free Gemini quota on the live demo
DEFAULT_MODEL = "gemini-flash-latest"
FALLBACK_MODEL = "gemini-2.5-flash"

INK = "#0F1B3D"
SOFT = "#56618A"
LINE = "#D6DDF0"
ACCENT = "#2D5BFF"
ACCENT_SOFT = "#EAF0FF"

st.set_page_config(page_title="Survey Insight Assistant", page_icon="📊", layout="wide",
                   initial_sidebar_state="collapsed")


# ---------- look and feel ----------

def inject_css():
    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600&display=swap');
.stApp {{ font-family: "DM Sans", system-ui, sans-serif; }}
.stApp button, .stApp input, .stApp textarea, .stApp p, .stApp label, .stApp li {{ font-family: inherit; }}
[data-testid="stIconMaterial"], .material-symbols-rounded {{ font-family: "Material Symbols Rounded" !important; }}
h1, h2, h3, h4, .si-display {{ font-family: "Sora", system-ui, sans-serif !important; letter-spacing: -.02em; color: {INK}; }}
.block-container {{ max-width: 1100px; padding-top: 2.2rem; padding-bottom: 4rem; }}
[data-testid="stHeader"] {{ background: transparent; }}
.stApp {{ background: #F7F9FD; }}
[data-testid="stVerticalBlockBorderWrapper"] {{ background:#fff; }}

/* hero */
.si-hero {{ padding: 8px 0 18px; }}
.si-chip {{ display:inline-flex; align-items:center; gap:8px; padding:6px 12px; border-radius:999px; background:{ACCENT_SOFT}; border:1px solid #BFD0FF; font-weight:600; font-size:.9rem; color:{INK}; }}
.si-hero h1 {{ font-size: clamp(2.2rem, 5vw, 3.4rem); font-weight: 800; line-height: 1.05; margin: 14px 0 10px; padding: 0; }}
.si-hero p {{ font-size: 1.15rem; color: {SOFT}; max-width: 60ch; margin: 0; }}
.si-steps {{ display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:12px; margin-top:24px; }}
.si-step {{ border:1.5px solid {LINE}; border-radius:16px; padding:14px 16px; background:#fff; }}
.si-step b {{ display:block; font-family:"Sora",sans-serif; font-size:1rem; color:{INK}; }}
.si-step span {{ color:{SOFT}; font-size:.92rem; }}
.si-step i {{ font-style:normal; display:inline-flex; width:26px; height:26px; border-radius:50%; background:{ACCENT}; color:#fff; align-items:center; justify-content:center; font-size:.85rem; font-weight:700; margin-bottom:8px; }}

/* section headings */
.si-h {{ font-family:"Sora",sans-serif; font-weight:800; font-size:1.6rem; color:{INK}; margin:34px 0 4px; }}
.si-sub {{ color:{SOFT}; margin:0 0 14px; }}

/* metric cards */
.si-metrics {{ display:grid; grid-template-columns: repeat(3, minmax(0,1fr)); gap:12px; margin:8px 0 6px; }}
.si-metric {{ border:1.5px solid {LINE}; border-radius:16px; padding:16px 18px; background:#fff; }}
.si-metric .n {{ font-family:"Sora",sans-serif; font-weight:800; font-size:2rem; color:{INK}; line-height:1.1; }}
.si-metric .l {{ color:{SOFT}; font-size:.95rem; }}

/* bordered containers, uploader, buttons */
[data-testid="stVerticalBlockBorderWrapper"] {{ border-radius:18px !important; border:1.5px solid {LINE} !important; }}
[data-testid="stFileUploaderDropzone"] {{ border-radius:14px; border:2px dashed {LINE}; background:#F7F9FD; }}
.stButton > button, .stDownloadButton > button {{ border-radius:999px; border:1.5px solid {INK}; font-weight:600; padding:.5rem 1.2rem; color:{INK}; background:#fff; }}
.stButton > button:hover, .stDownloadButton > button:hover {{ background:{ACCENT_SOFT}; color:{INK}; border-color:{ACCENT}; }}
.stButton > button[kind="primary"] {{ background:{ACCENT}; border-color:{ACCENT}; color:#fff; }}
.stButton > button[kind="primary"]:hover {{ background:#1E46E0; border-color:#1E46E0; color:#fff; }}
.stMultiSelect [data-baseweb="tag"] {{ background:{ACCENT_SOFT}; border:1px solid #BFD0FF; color:{INK}; }}
.stMultiSelect [data-baseweb="tag"] span {{ color:{INK}; }}

/* empty state */
.si-empty {{ text-align:center; padding:28px 16px; color:{SOFT}; }}
.si-empty b {{ color:{INK}; font-family:"Sora",sans-serif; font-size:1.1rem; display:block; margin-bottom:4px; }}

/* results */
.si-q {{ font-family:"Sora",sans-serif; font-weight:800; font-size:1.35rem; color:{INK}; margin:28px 0 10px; }}
.si-summary {{ background:{ACCENT_SOFT}; border:1.5px solid #BFD0FF; border-radius:16px; padding:16px 18px; color:{INK}; font-size:1.05rem; margin-bottom:14px; }}
.si-summary small {{ display:block; font-weight:600; color:{SOFT}; margin-bottom:4px; font-size:.85rem; }}
.si-themes {{ display:grid; grid-template-columns: repeat(2, minmax(0,1fr)); gap:12px; }}
.si-theme {{ border:1.5px solid {LINE}; border-radius:16px; padding:16px 18px; background:#fff; }}
.si-theme-top {{ display:flex; justify-content:space-between; align-items:baseline; gap:12px; }}
.si-theme h4 {{ margin:0; padding:0; font-size:1.08rem; font-weight:700; }}
.si-count {{ flex:none; font-weight:700; color:{INK}; font-size:.92rem; }}
.si-bar {{ height:8px; border-radius:99px; background:#E6EBF7; margin:10px 0 10px; overflow:hidden; }}
.si-bar span {{ display:block; height:100%; background:{ACCENT}; border-radius:99px; }}
.si-theme p {{ margin:0 0 8px; color:{SOFT}; font-size:.95rem; }}
.si-quote {{ border-left:3px solid {ACCENT}; padding:4px 0 4px 12px; margin:8px 0 0; color:{INK}; font-size:.95rem; font-style:italic; }}
.si-recs {{ display:grid; gap:10px; margin-top:14px; }}
.si-rec {{ display:flex; gap:12px; align-items:flex-start; border:1.5px solid {LINE}; border-radius:14px; padding:12px 14px; background:#fff; color:{INK}; }}
.si-rec i {{ font-style:normal; flex:none; width:24px; height:24px; border-radius:50%; background:{ACCENT}; color:#fff; display:inline-flex; align-items:center; justify-content:center; font-size:.8rem; }}
.si-foot {{ margin-top:48px; padding-top:18px; border-top:1.5px solid {LINE}; color:{SOFT}; font-size:.9rem; }}
.si-foot a {{ color:{INK}; font-weight:600; }}

@media (max-width: 760px) {{
  .si-steps, .si-metrics, .si-themes {{ grid-template-columns: 1fr; }}
}}
</style>
""", unsafe_allow_html=True)


def esc(x) -> str:
    return html.escape(str(x if x is not None else ""))


# ---------- helpers ----------

def get_api_key() -> str:
    """Read the Gemini key from Streamlit secrets, an env variable, or the sidebar box."""
    try:
        key = st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        key = ""
    return key or os.environ.get("GEMINI_API_KEY", "")


def classify_columns(df: pd.DataFrame):
    """Split columns into multiple-choice, rating (numbers) and open-ended text."""
    choice, rating, text = [], [], []
    for col in df.columns:
        s = df[col].dropna()
        if s.empty:
            continue
        if pd.api.types.is_numeric_dtype(s):
            (rating if s.nunique() <= 11 else choice).append(col)
            continue
        avg_len = s.astype(str).str.len().mean()
        if avg_len > 30 or s.nunique() > max(12, len(s) * 0.5):
            text.append(col)
        else:
            choice.append(col)
    return choice, rating, text


def bar_chart(df: pd.DataFrame, col: str, is_rating: bool):
    counts = df[col].value_counts()
    if is_rating:
        counts = counts.sort_index()
    data = pd.DataFrame({"answer": counts.index.astype(str), "pct": (counts / counts.sum() * 100).round(0).values})
    order = list(data["answer"])
    base = alt.Chart(data)
    if is_rating:
        bars = base.mark_bar(color=ACCENT, cornerRadiusTopLeft=6, cornerRadiusTopRight=6).encode(
            x=alt.X("answer:N", sort=order, title=None, axis=alt.Axis(labelAngle=0)),
            y=alt.Y("pct:Q", title=None, axis=None))
        labels = base.mark_text(dy=-8, color=INK, fontWeight=600).encode(
            x=alt.X("answer:N", sort=order), y="pct:Q", text=alt.Text("pct:Q", format=".0f"))
        h = 200
    else:
        bars = base.mark_bar(color=ACCENT, cornerRadiusTopRight=6, cornerRadiusBottomRight=6, height=22).encode(
            y=alt.Y("answer:N", sort=order, title=None, axis=alt.Axis(labelLimit=220)),
            x=alt.X("pct:Q", title=None, axis=None, scale=alt.Scale(domain=[0, max(100, data.pct.max())])))
        labels = base.mark_text(align="left", dx=6, color=INK, fontWeight=600).encode(
            y=alt.Y("answer:N", sort=order), x="pct:Q", text=alt.Text("pct:Q", format=".0f"))
        h = max(90, 34 * len(data))
    chart = (bars + labels).properties(height=h).configure_view(strokeWidth=0) \
        .configure_axis(labelColor=SOFT, labelFontSize=13, grid=False, domain=False, ticks=False)
    return chart


def analyse_text(responses: list[str], question: str, api_key: str, model: str) -> dict:
    """Ask Gemini to group answers into themes. Returns a dict (see prompt for shape)."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    numbered = "\n".join(f"{i + 1}. {r}" for i, r in enumerate(responses))
    prompt = f"""You are a user researcher. Below are {len(responses)} survey answers to the question:
"{question}"

Group them into 3 to 6 clear themes. Count how many answers fit each theme (an answer can fit one theme only).
Pick 2 short quotes per theme copied exactly from the answers. Then write a 2-3 sentence summary and
3 practical recommendations.

Return JSON only, in this shape:
{{"themes":[{{"name":"","description":"","count":0,"quotes":["",""]}}],
  "summary":"", "recommendations":["","",""]}}

Answers:
{numbered}"""

    config = types.GenerateContentConfig(response_mime_type="application/json", temperature=0.2)
    try:
        resp = client.models.generate_content(model=model, contents=prompt, config=config)
    except Exception as e:
        # If the chosen model name isn't available, try a known one once.
        if model != FALLBACK_MODEL and ("not found" in str(e).lower() or "404" in str(e)):
            resp = client.models.generate_content(model=FALLBACK_MODEL, contents=prompt, config=config)
        else:
            raise
    return json.loads(resp.text)


def build_report(df, choice_cols, rating_cols, ai_results) -> str:
    """Make a Markdown report the user can download."""
    lines = ["# Survey insight report", "", f"Responses analysed: {len(df)}", ""]
    for col in choice_cols:
        lines.append(f"## {col}")
        pct = df[col].value_counts(normalize=True).mul(100).round(0)
        lines += [f"- {k}: {int(v)}%" for k, v in pct.items()] + [""]
    for col in rating_cols:
        lines += [f"## {col}", f"- Average: {df[col].mean():.1f}", ""]
    for col, res in ai_results.items():
        lines += [f"## {col}", "", res.get("summary", ""), "", "### Themes"]
        for t in res.get("themes", []):
            lines.append(f"- **{t.get('name', '')}** ({t.get('count', 0)}): {t.get('description', '')}")
            lines += [f'  - "{q}"' for q in t.get("quotes", [])]
        lines += ["", "### Recommendations"] + [f"- {r}" for r in res.get("recommendations", [])] + [""]
    return "\n".join(lines)


def render_results(col: str, res: dict, n_answers: int):
    st.markdown(f'<div class="si-q">{esc(col)}</div>', unsafe_allow_html=True)
    if res.get("summary"):
        st.markdown(f'<div class="si-summary"><small>Summary</small>{esc(res["summary"])}</div>',
                    unsafe_allow_html=True)
    themes = sorted(res.get("themes", []), key=lambda t: -int(t.get("count", 0) or 0))
    total = max(sum(int(t.get("count", 0) or 0) for t in themes), n_answers, 1)
    cards = []
    for t in themes:
        c = int(t.get("count", 0) or 0)
        pct = round(c / total * 100)
        quotes = "".join(f'<div class="si-quote">"{esc(q)}"</div>' for q in t.get("quotes", [])[:2])
        cards.append(f'''<div class="si-theme"><div class="si-theme-top"><h4>{esc(t.get("name", ""))}</h4>
<span class="si-count">{c} answers · {pct}%</span></div>
<div class="si-bar"><span style="width:{pct}%"></span></div>
<p>{esc(t.get("description", ""))}</p>{quotes}</div>''')
    if cards:
        st.markdown(f'<div class="si-themes">{"".join(cards)}</div>', unsafe_allow_html=True)
    recs = res.get("recommendations", [])
    if recs:
        items = "".join(f'<div class="si-rec"><i>✓</i><span>{esc(r)}</span></div>' for r in recs)
        st.markdown(f'<div class="si-h" style="font-size:1.1rem;margin-top:22px">Recommendations</div>'
                    f'<div class="si-recs">{items}</div>', unsafe_allow_html=True)


# ---------- page ----------

inject_css()

with st.sidebar:
    st.markdown("### Settings")
    api_key = get_api_key()
    if not api_key:
        api_key = st.text_input("Gemini API key", type="password",
                                help="Free from aistudio.google.com. It is only used for this session.")
    else:
        st.success("AI is ready to use")
    model = st.text_input("Model", value=DEFAULT_MODEL)
    runs_left = MAX_RUNS_PER_SESSION - st.session_state.get("runs", 0)
    st.caption(f"AI analyses left this visit: {max(runs_left, 0)} of {MAX_RUNS_PER_SESSION}")
    st.caption("Your data is sent to Google Gemini only when you click Analyse.")

st.markdown("""
<div class="si-hero">
  <span class="si-chip">✨ AI-powered survey analysis</span>
  <h1>Survey Insight Assistant</h1>
  <p>Turn hundreds of survey answers into clear themes, real quotes and recommendations in under a minute.</p>
  <div class="si-steps">
    <div class="si-step"><i>1</i><b>Upload your survey</b><span>Any CSV, like a Google Forms export</span></div>
    <div class="si-step"><i>2</i><b>See the numbers</b><span>Instant charts for every multiple-choice question</span></div>
    <div class="si-step"><i>3</i><b>Get AI insights</b><span>Themes, quotes and recommendations from written answers</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

with st.container(border=True):
    uploaded = st.file_uploader("Upload a CSV file", type="csv", label_visibility="collapsed")

if uploaded is not None and st.session_state.get("file_name") != uploaded.name:
    st.session_state["file_name"] = uploaded.name
    st.session_state.pop("ai_results", None)

if uploaded is None:
    st.markdown('<div class="si-empty"><b>Upload a survey to get started</b>'
                'Export your responses as a CSV file, for example from Google Forms or Microsoft Forms.</div>',
                unsafe_allow_html=True)
    st.stop()

try:
    df = pd.read_csv(uploaded)
except Exception:
    st.error("This file couldn't be read as a CSV. Export your survey as CSV and upload it again.")
    st.stop()
source = esc(uploaded.name)

choice_cols, rating_cols, text_cols = classify_columns(df)

st.markdown(f'<div class="si-h">Overview</div><p class="si-sub">{source}</p>', unsafe_allow_html=True)
st.markdown(f"""<div class="si-metrics">
<div class="si-metric"><div class="n">{len(df)}</div><div class="l">Responses</div></div>
<div class="si-metric"><div class="n">{len(df.columns)}</div><div class="l">Questions</div></div>
<div class="si-metric"><div class="n">{len(text_cols)}</div><div class="l">Open-ended questions for AI</div></div>
</div>""", unsafe_allow_html=True)
with st.expander("Preview the data"):
    st.dataframe(df, width="stretch", hide_index=True)

if choice_cols or rating_cols:
    st.markdown('<div class="si-h">The numbers</div><p class="si-sub">Percentage of responses for each answer.</p>',
                unsafe_allow_html=True)
    grid = st.columns(2, gap="medium")
    for i, col in enumerate(choice_cols + rating_cols):
        with grid[i % 2]:
            with st.container(border=True):
                st.markdown(f"**{esc(col)}**")
                if col in rating_cols:
                    st.caption(f"Average score: {df[col].mean():.1f}")
                st.altair_chart(bar_chart(df, col, col in rating_cols), width="stretch")

st.markdown('<div class="si-h">AI insights</div><p class="si-sub">Let AI read the written answers and find the '
            'patterns for you.</p>', unsafe_allow_html=True)
if not text_cols:
    st.info("This file has no open-ended questions to analyse.")
    st.stop()

with st.container(border=True):
    picked = st.multiselect("Questions to analyse", text_cols, default=text_cols)
    go = st.button("✨ Analyse with AI", type="primary", disabled=not picked)

if go:
    if not api_key:
        st.error("Add a Gemini API key in the sidebar first.")
        st.stop()
    runs = st.session_state.get("runs", 0)
    if runs >= MAX_RUNS_PER_SESSION:
        st.warning(f"You've used all {MAX_RUNS_PER_SESSION} AI analyses for this demo. "
                   "Refresh the page later to try again.")
        st.stop()
    st.session_state["runs"] = runs + 1
    results = {}
    for col in picked:
        answers = df[col].dropna().astype(str).str.strip()
        answers = answers[answers != ""].tolist()[:MAX_RESPONSES]
        with st.spinner(f"Reading {len(answers)} answers to \"{col}\"..."):
            try:
                results[col] = (analyse_text(answers, col, api_key, model), len(answers))
            except Exception as e:
                st.error(f"Couldn't analyse \"{col}\". Check the API key and model name, then try again. ({e})")
    st.session_state["ai_results"] = results

results = st.session_state.get("ai_results", {})
for col, (res, n) in results.items():
    render_results(col, res, n)

if results:
    report = build_report(df, choice_cols, rating_cols, {k: v[0] for k, v in results.items()})
    st.write("")
    st.download_button("Download full report", report, file_name="survey_insights.md")

st.markdown('<div class="si-foot">Built by <a href="https://wong-jun-yi.netlify.app" target="_blank">Wong Jun Yi</a> '
            'with Python, Streamlit and Google Gemini.</div>', unsafe_allow_html=True)
