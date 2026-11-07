"""
Survey Insight Assistant
Upload a survey CSV and get charts, AI-grouped themes from open-ended answers,
and a short summary with recommendations.

Built by Wong Jun Yi with Streamlit, pandas and Google Gemini.
"""

import json
import os
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent
SAMPLE_FILE = APP_DIR / "sample_survey.csv"
MAX_RESPONSES = 300          # cap sent to the AI per question, keeps it fast and free-tier friendly
DEFAULT_MODEL = "gemini-flash-latest"
FALLBACK_MODEL = "gemini-2.5-flash"

st.set_page_config(page_title="Survey Insight Assistant", page_icon="📊", layout="wide")


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
            lines.append(f"- **{t['name']}** ({t.get('count', 0)}): {t.get('description', '')}")
            lines += [f'  - "{q}"' for q in t.get("quotes", [])]
        lines += ["", "### Recommendations"] + [f"- {r}" for r in res.get("recommendations", [])] + [""]
    return "\n".join(lines)


# ---------- sidebar ----------

with st.sidebar:
    st.header("Settings")
    api_key = get_api_key()
    if not api_key:
        api_key = st.text_input("Gemini API key", type="password",
                                help="Free from aistudio.google.com. It is only used for this session.")
    else:
        st.success("Gemini API key loaded")
    model = st.text_input("Model", value=DEFAULT_MODEL)
    st.caption("Your data is sent to Google Gemini only when you click Analyse.")

# ---------- main ----------

st.title("📊 Survey Insight Assistant")
st.write("Upload survey results to get instant charts, AI-grouped themes from open-ended answers, "
         "and a short summary you can drop into a report.")

c1, c2 = st.columns([3, 1])
uploaded = c1.file_uploader("Upload a CSV file", type="csv")
use_sample = c2.button("Try sample data", use_container_width=True)

if use_sample:
    st.session_state["use_sample"] = True
if uploaded is not None:
    st.session_state["use_sample"] = False

if uploaded is not None:
    df = pd.read_csv(uploaded)
elif st.session_state.get("use_sample") and SAMPLE_FILE.exists():
    df = pd.read_csv(SAMPLE_FILE)
    st.info("Using sample data: a made-up survey of young workers about their first jobs.")
else:
    st.stop()

choice_cols, rating_cols, text_cols = classify_columns(df)

m1, m2, m3 = st.columns(3)
m1.metric("Responses", len(df))
m2.metric("Questions", len(df.columns))
m3.metric("Open-ended questions", len(text_cols))

with st.expander("Preview data"):
    st.dataframe(df, use_container_width=True)

# Quick charts
if choice_cols or rating_cols:
    st.subheader("Quick charts")
    cols = st.columns(2)
    for i, col in enumerate(choice_cols + rating_cols):
        with cols[i % 2]:
            st.markdown(f"**{col}**")
            if col in rating_cols:
                st.caption(f"Average: {df[col].mean():.1f}")
                counts = df[col].value_counts().sort_index()
            else:
                counts = df[col].value_counts()
            st.bar_chart((counts / counts.sum() * 100).round(0).rename("% of responses"), horizontal=col not in rating_cols)

# AI themes
st.subheader("AI themes from open-ended answers")
if not text_cols:
    st.write("No open-ended questions found in this file.")
    st.stop()

picked = st.multiselect("Questions to analyse", text_cols, default=text_cols)
if st.button("Analyse with AI", type="primary", disabled=not picked):
    if not api_key:
        st.error("Add your Gemini API key in the sidebar first.")
        st.stop()
    results = {}
    for col in picked:
        answers = df[col].dropna().astype(str).str.strip()
        answers = answers[answers != ""].tolist()[:MAX_RESPONSES]
        with st.spinner(f"Reading {len(answers)} answers to \"{col}\"..."):
            try:
                results[col] = analyse_text(answers, col, api_key, model)
            except Exception as e:
                st.error(f"Couldn't analyse \"{col}\": {e}. Check your API key and model name, then try again.")
    st.session_state["ai_results"] = results

results = st.session_state.get("ai_results", {})
for col, res in results.items():
    st.markdown(f"### {col}")
    st.write(res.get("summary", ""))
    themes = res.get("themes", [])
    if themes:
        chart = pd.Series({t["name"]: t.get("count", 0) for t in themes}, name="Answers").sort_values()
        st.bar_chart(chart, horizontal=True)
        for t in themes:
            with st.expander(f"{t['name']} ({t.get('count', 0)})"):
                st.write(t.get("description", ""))
                for q in t.get("quotes", []):
                    st.markdown(f"> {q}")
    if res.get("recommendations"):
        st.markdown("**Recommendations**")
        for r in res["recommendations"]:
            st.markdown(f"- {r}")

if results:
    report = build_report(df, choice_cols, rating_cols, results)
    st.download_button("Download report (Markdown)", report, file_name="survey_insights.md")
