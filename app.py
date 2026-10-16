import os
import json
import random
import hashlib
from datetime import date, datetime
from zoneinfo import ZoneInfo

import streamlit as st
from supabase import create_client

TZ = ZoneInfo("America/Sao_Paulo")
st.set_page_config(page_title="Desafio MQS | Máquina Solo", page_icon="🦔", layout="wide")

st.markdown("""
<style>
:root { --mqs-yellow: #FFC000; --mqs-gray: #7F7F7F; --mqs-ink: #202326; }
.stApp, [data-testid="stAppViewContainer"] { background: #f5f6f8 !important; color: #202326 !important; }
.block-container { max-width: 1120px; padding-top: 1.5rem; padding-bottom: 3rem; }
.mqs-hero { background: #202326; color: #ffffff; padding: 2rem; border-radius: 22px; border-left: 10px solid #FFC000; margin-bottom: 1.2rem; }
.mqs-hero h1 { color: #FFC000 !important; margin: 0; font-size: clamp(2rem, 5vw, 3.4rem); }
.mqs-hero p { color: #f3f4f6 !important; margin-bottom: 0; }
/* Legibilidade geral: títulos, rótulos, textos e abas */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p,
.stApp label, .stApp [data-testid="stWidgetLabel"],
.stApp [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stCaptionContainer"],
.stApp [data-testid="stCaptionContainer"] p,
.stApp [data-testid="stRadio"] label,
.stApp [data-testid="stCheckbox"] label,
.stApp [data-testid="stTabs"] button,
.stApp [data-testid="stMetricLabel"], .stApp [data-testid="stMetricValue"] {
  color: #202326 !important;
}
/* Campos de preenchimento claros com texto escuro */
.stApp input, .stApp textarea,
.stApp [data-baseweb="select"] > div,
.stApp [data-baseweb="input"] > div,
.stApp [data-baseweb="textarea"] > div {
  background-color: #ffffff !important;
  color: #202326 !important;
  border-color: #cbd0d6 !important;
}
.stApp input::placeholder, .stApp textarea::placeholder { color: #6b7280 !important; }
.stApp [data-baseweb="select"] *, .stApp [role="option"] { color: #202326 !important; }
.stApp [data-testid="stMetric"] { background: #ffffff; color: #202326; padding: 1rem; border-radius: 12px; border: 1px solid #e4e6e9; }
.stApp div.stButton > button { border-radius: 9px; font-weight: 650; }
.stApp div.stButton > button[kind="primary"] { background: #FFC000 !important; color: #202326 !important; border: 0 !important; font-weight: 800; }
.stApp div.stButton > button:not([kind="primary"]) { background: #202326; color: #ffffff; border: 1px solid #202326; }
.stApp [data-testid="stAlert"] p { color: inherit !important; }
@media (max-width: 640px) {
  .block-container { padding-left: 1rem; padding-right: 1rem; padding-top: 1rem; }
  .mqs-hero { padding: 1.3rem; border-radius: 15px; }
}
</style>
""", unsafe_allow_html=True)

def get_secret(name, default=""):
    try:
        return st.secrets.get(name, default)
    except Exception:
        return os.getenv(name, default)

@st.cache_resource
def db():
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)

def now_iso():
    return datetime.now(TZ).isoformat()

def admin_ok():
    return bool(st.session_state.get("admin_ok"))

def fetch_settings(client):
    result = client.table("mqs_settings").select("*").eq("id", 1).limit(1).execute()
    if result.data:
        return result.data[0]
    default = {"id": 1, "title": "DESAFIO MQS", "campaign_open": False, "start_date": None, "end_date": None, "questions_per_game": 10}
    client.table("mqs_settings").upsert(default).execute()
    return default

def fetch_questions(client, active_only=False):
    query = client.table("mqs_questions").select("*").order("category").order("id")
    if active_only:
        query = query.eq("active", True).neq("correct", "")
    return query.execute().data or []

def fetch_leaderboard(client):
    rows = client.table("mqs_attempts").select("id,name,sector,score,total,percent,created_at").execute().data or []
    rows.sort(key=lambda r: (-float(r.get("percent") or 0), -int(r.get("score") or 0), r.get("created_at") or ""))
    for i, row in enumerate(rows, 1):
        row["Posição"] = i
