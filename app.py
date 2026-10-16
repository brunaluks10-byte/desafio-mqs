import base64
import hashlib
import html
import json
import os
import random
import unicodedata
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import streamlit as st
from supabase import create_client


TZ = ZoneInfo("America/Sao_Paulo")
LETTERS = ("A", "B", "C", "D")
SECTORS = [
    "Comercial", "Pós-vendas", "Marketing", "Peças", "Serviços", "Operações",
    "Administrativo", "Financeiro", "RH", "Outro",
]
CATEGORIES = {
    "all": ("Desafio completo", "História, conhecimento técnico e cultura e valores."),
    "history": ("História MQS", "Origem, trajetória e evolução da Máquina Solo."),
    "technical": ("Conhecimento técnico", "Máquinas, aplicações e equipamentos do banco de perguntas."),
    "culture": ("Cultura e valores", "Princípios e valores que fazem parte do jeito MQS de trabalhar."),
}
QUESTION_COUNTS = {
    "5 perguntas — Aquecimento": 5,
    "10 perguntas — Desafio rápido": 10,
    "15 perguntas — Desafio completo": 15,
    "Todas as perguntas disponíveis": None,
}

st.set_page_config(page_title="Desafio MQS | Máquina Solo", page_icon="M", layout="wide")

st.markdown(
    """
<style>
:root {
  color-scheme: dark;
  --mqs-yellow: #FFC000;
  --mqs-bg: #101214;
  --mqs-panel: #1D2023;
  --mqs-surface: #25292D;
  --mqs-border: #373C41;
  --mqs-text: #F5F5F5;
  --mqs-muted: #A7ADB4;
}
.stApp, [data-testid="stAppViewContainer"] { background: var(--mqs-bg) !important; color: var(--mqs-text) !important; }
[data-testid="stHeader"] { background: rgba(16,18,20,.94) !important; height: 2.65rem !important; }
[data-testid="stToolbar"] { right: 1rem; }
.block-container { max-width: 1180px; padding-top: .55rem !important; padding-bottom: 2.5rem; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4 { color: var(--mqs-text) !important; letter-spacing: -.025em; }
.stApp p, .stApp li, .stApp label, .stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stWidgetLabel"], .stApp [data-testid="stWidgetLabel"] p,
.stApp [data-testid="stCaptionContainer"], .stApp [data-testid="stCaptionContainer"] p,
.stApp [data-testid="stMetricLabel"], .stApp [data-testid="stMetricValue"] { color: var(--mqs-text) !important; }
.stApp [data-testid="stCaptionContainer"] p { color: var(--mqs-muted) !important; }
.mqs-header { display:flex; align-items:center; justify-content:space-between; gap:1rem; padding:.8rem 0 .9rem; border-bottom:1px solid var(--mqs-border); margin-bottom:1rem; }
.mqs-brand { display:flex; flex-direction:column; gap:.12rem; }
.mqs-brand-label, .mqs-eyebrow { color:var(--mqs-yellow); font-size:.72rem; font-weight:750; letter-spacing:.13em; text-transform:uppercase; }
.mqs-brand h1 { margin:0; font-size:clamp(1.55rem,3vw,2.05rem); line-height:1.08; }
.mqs-header-note { color:var(--mqs-muted); font-size:.84rem; text-align:right; }
.mqs-hero { display:flex; align-items:center; justify-content:space-between; gap:1.5rem; padding:1.25rem 1.45rem; margin:.8rem 0 1.35rem; background:linear-gradient(110deg,#202428,#171A1D); border:1px solid var(--mqs-border); border-left:4px solid var(--mqs-yellow); border-radius:15px; }
.mqs-hero h2 { margin:.24rem 0 .35rem; font-size:clamp(1.35rem,2.6vw,1.9rem); }
.mqs-hero p { margin:0; max-width:700px; color:#D4D8DC !important; line-height:1.55; }
.mqs-hero-aside { flex:0 0 auto; padding:.7rem .85rem; border-radius:11px; border:1px solid #444A50; background:#191C1F; color:var(--mqs-muted); font-size:.78rem; line-height:1.5; }
.mqs-hero-aside strong { display:block; color:var(--mqs-yellow); font-size:.95rem; letter-spacing:.08em; }
.mqs-mascot { display:block; width:clamp(105px,17vw,185px); max-height:190px; object-fit:contain; flex:0 0 auto; }
.mqs-card-title { margin:.1rem 0 .3rem; font-size:1.06rem; font-weight:750; color:var(--mqs-text); }
.mqs-card-copy { min-height:2.55rem; color:var(--mqs-muted); font-size:.9rem; line-height:1.45; }
.mqs-question { padding:1.15rem 1.25rem; margin:.75rem 0 1rem; background:var(--mqs-panel); border:1px solid var(--mqs-border); border-radius:14px; font-size:clamp(1.15rem,2.2vw,1.65rem); line-height:1.4; font-weight:700; }
.mqs-kicker { color:var(--mqs-yellow); font-weight:750; font-size:.75rem; letter-spacing:.1em; text-transform:uppercase; }
.mqs-tip { padding:.85rem 1rem; border-left:3px solid var(--mqs-yellow); border-radius:0 10px 10px 0; background:#1B1E21; color:#D5D9DD; line-height:1.5; }
.mqs-status { display:inline-flex; align-items:center; gap:.5rem; padding:.38rem .7rem; border:1px solid #355441; border-radius:999px; background:#15221A; color:#B9E4C5; font-size:.82rem; font-weight:650; }
[data-testid="stMetric"] { background:var(--mqs-panel); border:1px solid var(--mqs-border); border-radius:12px; padding:.85rem 1rem; }
[data-testid="stMetricLabel"] { color:var(--mqs-muted) !important; }
[data-testid="stMetricValue"] { color:var(--mqs-text) !important; }
[data-testid="stVerticalBlockBorderWrapper"] { border-color:var(--mqs-border) !important; background:rgba(29,32,35,.8); border-radius:13px; }
.stApp div.stButton > button, .stApp [data-testid="stFormSubmitButton"] button, .stApp [data-testid="stDownloadButton"] button { min-height:2.65rem; border-radius:9px; font-weight:700; border:1px solid #4A5056; background:#282D31; color:var(--mqs-text); transition:background .16s ease,border-color .16s ease,transform .16s ease; }
.stApp div.stButton > button:hover, .stApp [data-testid="stFormSubmitButton"] button:hover { border-color:var(--mqs-yellow); transform:translateY(-1px); }
.stApp div.stButton > button[kind="primary"], .stApp [data-testid="stFormSubmitButton"] button[kind="primary"] { background:var(--mqs-yellow) !important; color:#151719 !important; border-color:var(--mqs-yellow) !important; font-weight:800; }
.stApp button:focus-visible, .stApp input:focus-visible, .stApp textarea:focus-visible, .stApp [role="radio"]:focus-visible { outline:3px solid #FFE08A !important; outline-offset:2px; }
.stApp input, .stApp textarea, .stApp [data-baseweb="select"] > div, .stApp [data-baseweb="input"] > div, .stApp [data-baseweb="textarea"] > div { background:#202428 !important; color:var(--mqs-text) !important; border-color:#4A5056 !important; }
.stApp input::placeholder, .stApp textarea::placeholder { color:#A7ADB4 !important; }
.stApp [data-baseweb="select"] *, .stApp [role="option"] { color:var(--mqs-text) !important; }
.stApp [data-testid="stTabs"] button, .stApp [data-testid="stRadio"] label { color:var(--mqs-text) !important; }
.stApp [data-testid="stAlert"] { border-radius:10px; }
.stApp [data-testid="stAlert"] p { color:inherit !important; }
.stApp [data-testid="stDataFrame"] { border:1px solid var(--mqs-border); border-radius:10px; overflow:hidden; }
@media (max-width: 700px) {
  .block-container { padding-left:1rem; padding-right:1rem; padding-top:.35rem !important; }
  .mqs-header { align-items:flex-start; }
  .mqs-header-note { max-width:8.5rem; }
  .mqs-hero { align-items:flex-start; padding:1rem; }
  .mqs-hero-aside { display:none; }
  .mqs-mascot { width:82px; max-height:115px; }
  .mqs-card-copy { min-height:0; }
  [data-testid="stMetric"] { padding:.7rem; }
}
</style>
""",
    unsafe_allow_html=True,
)


def get_secret(name, default=""):
    try:
        value = st.secrets.get(name)
    except Exception:
        value = None
    return value or os.getenv(name, default)


@st.cache_resource
def db():
    url = get_secret("SUPABASE_URL")
    key = get_secret("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        return None
    return create_client(url, key)


def now_iso():
    return datetime.now(TZ).isoformat()


def today_local():
    return datetime.now(TZ).date()


def admin_ok():
    return bool(st.session_state.get("admin_ok"))


def fetch_settings(client):
    result = client.table("mqs_settings").select("*").eq("id", 1).limit(1).execute()
    if result.data:
        return result.data[0]
    return {
        "id": 1, "title": "DESAFIO MQS", "campaign_open": False,
        "start_date": None, "end_date": None, "questions_per_game": 10,
    }


def fetch_questions(client, active_only=False):
    query = client.table("mqs_questions").select("*").order("category").order("id")
    if active_only:
        query = query.eq("active", True).neq("correct", "")
    return query.execute().data or []


def normalize(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    return "".join(char for char in text if not unicodedata.combining(char)).casefold().strip()


def category_matches(category, selected):
    if selected == "all":
        return True
    value = normalize(category)
    if selected == "history":
        return "hist" in value
    if selected == "technical":
        return "tecn" in value
    if selected == "culture":
        return "cultur" in value or "valor" in value
    return False


def question_is_eligible(question):
    correct = str(question.get("correct") or "").strip().upper()
    return bool(question.get("active")) and correct in LETTERS and bool(str(question.get(correct.lower()) or "").strip())


def eligible_questions(questions, selected_category):
    return [
        question for question in questions
        if question_is_eligible(question) and category_matches(question.get("category"), selected_category)
    ]


def select_questions(questions, count):
    """Select without replacement, distributing a combined round across categories."""
    groups = defaultdict(list)
    for question in questions:
        groups[str(question.get("category") or "Geral")].append(question)
    for rows in groups.values():
        random.shuffle(rows)

    selected = []
    used_by_group = defaultdict(int)
    while len(selected) < count:
        available = [name for name, rows in groups.items() if rows]
        if not available:
            break
        least_used = min(used_by_group[name] for name in available)
        balanced = [name for name in available if used_by_group[name] == least_used]
        chosen_group = random.choice(balanced)
        selected.append(groups[chosen_group].pop())
        used_by_group[chosen_group] += 1
    return selected


def fetch_leaderboard(client):
    rows = client.table("mqs_attempts").select(
        "id,name,sector,score,total,percent,created_at"
    ).execute().data or []
    rows.sort(key=lambda row: (
        -float(row.get("percent") or 0), -int(row.get("score") or 0),
        str(row.get("created_at") or ""), normalize(row.get("name")),
    ))
    rank = 0
    previous_result = None
    for index, row in enumerate(rows, 1):
        result_key = (float(row.get("percent") or 0), int(row.get("score") or 0))
        if result_key != previous_result:
            rank = index
            previous_result = result_key
        row["Posição"] = rank
        row["Nome"] = row.get("name", "")
        row["Setor"] = row.get("sector", "")
        row["Pontos"] = row.get("score", 0)
        row["Perguntas"] = row.get("total", 0)
        row["Aproveitamento"] = f'{float(row.get("percent") or 0):.1f}%'
    return rows


def campaign_is_open(settings):
    if not settings.get("campaign_open"):
        return False, "A campanha ainda não está aberta pela organização."
    today = today_local()
    start = settings.get("start_date")
    end = settings.get("end_date")
    if start and today < date.fromisoformat(str(start)[:10]):
        start_date = date.fromisoformat(str(start)[:10])
        return False, f"A campanha começa em {start_date.strftime('%d/%m/%Y')}."
    if end and today > date.fromisoformat(str(end)[:10]):
        return False, "A campanha foi encerrada."
    return True, "Campanha aberta"


def participant_key(name, sector):
    base = f"{normalize(name)}|{normalize(sector)}"
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def save_attempt_once(client, payload):
    """Use the existing unique participant key as an idempotency guard."""
    attempts = client.table("mqs_attempts")
    try:
        existing = attempts.select("id").eq("participant_key", payload["participant_key"]).limit(1).execute().data or []
        if existing:
            return True, "already_saved"
        attempts.insert(payload).execute()
        return True, "saved"
    except Exception:
        # A concurrent rerun can win the unique-key race after the first lookup.
        try:
            existing = attempts.select("id").eq("participant_key", payload["participant_key"]).limit(1).execute().data or []
            if existing:
                return True, "already_saved"
        except Exception:
            pass
        return False, "error"


def original_mascot_path():
    candidates = (
        Path(__file__).parent / "assets" / "tatu_original.png",
        Path(__file__).parent / "assets" / "tatu_original.webp",
        Path(__file__).parent / "tatu_original.png",
    )
    return next((path for path in candidates if path.is_file()), None)


def render_header(title):
    safe_title = html.escape(title or "DESAFIO MQS")
    st.markdown(
        f'<div class="mqs-header"><div class="mqs-brand">'
        f'<span class="mqs-brand-label">MÁQUINA SOLO · EDIÇÃO INTERNA</span>'
        f'<h1>{safe_title}</h1></div>'
        '<div class="mqs-header-note">PARTICIPAÇÃO · RANKING · CULTURA</div></div>',
        unsafe_allow_html=True,
    )


def render_hero():
    mascot_path = original_mascot_path()
    mascot = ""
    aside = (
        '<div class="mqs-hero-aside"><strong>Escolha seu ritmo</strong>'
        '5, 10, 15 ou todas as perguntas.</div>'
    )
    if mascot_path:
        mime = "image/webp" if mascot_path.suffix.lower() == ".webp" else "image/png"
        encoded = base64.b64encode(mascot_path.read_bytes()).decode("ascii")
        mascot = f'<img class="mqs-mascot" src="data:{mime};base64,{encoded}" alt="Tatu original da Máquina Solo">'
        aside = mascot
    st.markdown(
        '<div class="mqs-hero"><div><div class="mqs-eyebrow">Plataforma de aprendizado e colaboração</div>'
        '<h2>História, conhecimento técnico e valores que movem a Máquina Solo.</h2>'
        '<p>Teste seus conhecimentos, acumule pontos e descubra sua posição no ranking.</p></div>'
        f'{aside}</div>',
        unsafe_allow_html=True,
    )


def render_category_cards(selected_category, counts):
    entries = list(CATEGORIES.items())
    for start in range(0, len(entries), 2):
        columns = st.columns(2, gap="medium")
        for column, (category_id, (title, description)) in zip(columns, entries[start:start + 2]):
            with column:
                with st.container(border=True):
                    st.markdown(f'<div class="mqs-card-title">{html.escape(title)}</div>', unsafe_allow_html=True)
                    st.markdown(f'<div class="mqs-card-copy">{html.escape(description)}</div>', unsafe_allow_html=True)
                    st.caption(f"{counts.get(category_id, 0)} perguntas disponíveis")
                    selected = category_id == selected_category
                    if st.button(
                        "Selecionada" if selected else "Escolher categoria",
                        key=f"category_{category_id}",
                        type="primary" if selected else "secondary",
                        use_container_width=True,
                    ) and not selected:
                        st.session_state.selected_category = category_id
                        st.rerun()


def render_home(client, settings, is_open, status_message):
    render_hero()
    if is_open:
        st.markdown('<span class="mqs-status">● Campanha aberta</span>', unsafe_allow_html=True)
    else:
        st.info(status_message)
        st.caption("A organização precisa abrir a campanha antes que as respostas sejam registradas.")

    try:
        all_questions = fetch_questions(client, active_only=True)
    except Exception:
        st.error("Não foi possível carregar as perguntas agora. Tente novamente em instantes.")
        return

    counts = {
        category_id: len(eligible_questions(all_questions, category_id))
        for category_id in CATEGORIES
    }
    selected_category = st.session_state.get("selected_category", "all")
    if selected_category not in CATEGORIES:
        selected_category = "all"
        st.session_state.selected_category = selected_category

    st.subheader("Escolha sua trilha")
    render_category_cards(selected_category, counts)

    category_title = CATEGORIES[selected_category][0]
    selected_count = counts[selected_category]
    st.markdown(f"**Trilha selecionada:** {category_title} · {selected_count} perguntas elegíveis")
    st.subheader("Prepare sua participação")

    sector = st.selectbox("Seu setor", SECTORS, disabled=not is_open, key="participant_sector")
    sector_other = ""
    if sector == "Outro":
        sector_other = st.text_input("Informe seu setor", max_chars=80, disabled=not is_open, key="participant_sector_other")

    with st.form("participant_form"):
        name = st.text_input("Seu nome", max_chars=100, disabled=not is_open, key="participant_name")
        question_count_label = st.selectbox(
            "Quantidade de perguntas", list(QUESTION_COUNTS), index=1, disabled=not is_open,
        )
        st.caption("A quantidade escolhida será respeitada. A rodada não repetirá questões.")
        start = st.form_submit_button("COMEÇAR DESAFIO", type="primary", disabled=not is_open, use_container_width=True)

    if start:
        name = name.strip()
        final_sector = sector_other.strip() if sector == "Outro" else sector
        if len(name) < 2:
            st.error("Informe seu nome com pelo menos duas letras.")
            return
        if not final_sector:
            st.error("Informe seu setor para continuar.")
            return
        if selected_count < 1:
            st.error("Esta trilha ainda não tem perguntas ativas com gabarito. Avise a organização.")
            return

        requested = QUESTION_COUNTS[question_count_label]
        amount = selected_count if requested is None else requested
        if selected_count < amount:
            st.error(
                f"A trilha {category_title} tem {selected_count} perguntas elegíveis; "
                f"são necessárias {amount}. Escolha uma quantidade menor ou avise a organização."
            )
            return

        key = participant_key(name, final_sector)
        try:
            exists = client.table("mqs_attempts").select("id").eq("participant_key", key).limit(1).execute().data or []
        except Exception:
            st.error("Não foi possível confirmar sua participação com o ranking. Tente novamente em instantes.")
            return
        if exists:
            st.error("Já existe uma participação registrada com esse nome e setor. Se precisar de ajuda, procure a organização.")
            return

        chosen_questions = select_questions(eligible_questions(all_questions, selected_category), amount)
        if len(chosen_questions) != amount:
            st.error("Não foi possível montar uma rodada completa com as perguntas disponíveis. Avise a organização.")
            return

        st.session_state.quiz = {
            "run_id": hashlib.sha256(os.urandom(16)).hexdigest()[:12],
            "name": name,
            "sector": final_sector,
            "participant_key": key,
            "category": category_title,
            "questions": chosen_questions,
            "index": 0,
            "answers": {},
            "saved": False,
            "save_attempted": False,
        }
        st.rerun()

    st.markdown(
        '<div class="mqs-tip"><strong>Dica do Tatu</strong> · Preste atenção aos detalhes: '
        'algumas perguntas testam conhecimento técnico; outras exploram o jeito MQS de trabalhar.</div>',
        unsafe_allow_html=True,
    )


def current_score(quiz):
    return sum(
        1 for question in quiz["questions"]
        if quiz["answers"].get(question["id"]) == str(question.get("correct") or "").upper()
    )


def render_quiz(client, quiz):
    questions = quiz["questions"]
    index = quiz["index"]
    total = len(questions)
    score = current_score(quiz)

    st.markdown(f'<div class="mqs-kicker">{html.escape(quiz["category"])}</div>', unsafe_allow_html=True)
    st.subheader("Sua rodada")
    info = st.columns(4)
    info[0].metric("Participante", quiz["name"])
    info[1].metric("Setor", quiz["sector"])
    info[2].metric("Pontuação", f"{score}/{total}")
    info[3].metric("Pergunta", f"{min(index + 1, total)} de {total}")

    question = questions[index] if index < total else None
    answered = len(quiz["answers"])
    progress = answered / total if total else 0
    st.progress(progress, text=f"Progresso · {answered} de {total} respondidas · {progress:.0%}")

    if question is not None:
        st.markdown(
            f'<div class="mqs-kicker">Pergunta {index + 1} · {html.escape(str(question.get("category") or "Geral"))}</div>'
            f'<div class="mqs-question">{html.escape(str(question.get("prompt") or ""))}</div>',
            unsafe_allow_html=True,
        )
        question_id = question["id"]
        selected_answer = quiz["answers"].get(question_id)
        options = [letter for letter in LETTERS if str(question.get(letter.lower()) or "").strip()]

        if selected_answer is None:
            labels = {
                letter: f"{letter}. {question.get(letter.lower(), '')}"
                for letter in options
            }
            with st.form(f"answer_{quiz['run_id']}_{index}"):
                chosen = st.radio(
                    "Escolha uma alternativa",
                    options,
                    format_func=lambda letter: labels[letter],
                    index=None,
                )
                submitted = st.form_submit_button("Confirmar resposta", type="primary", use_container_width=True)
            if submitted:
                if chosen is None:
                    st.warning("Selecione uma alternativa antes de continuar.")
                else:
                    quiz["answers"][question_id] = chosen
                    st.session_state.quiz = quiz
                    st.rerun()
        else:
            correct = str(question.get("correct") or "").upper()
            answer_text = str(question.get(selected_answer.lower()) or "")
            correct_text = str(question.get(correct.lower()) or "")
            if selected_answer == correct:
                st.success(f"Resposta correta · {selected_answer}. {answer_text}")
            else:
                st.warning(f"Sua resposta: {selected_answer}. {answer_text} · Resposta correta: {correct}. {correct_text}")
            if question.get("explanation"):
                st.info(str(question["explanation"]))
            next_label = "Ver resultado" if index == total - 1 else "Próxima pergunta"
            if st.button(next_label, type="primary", key=f"next_{quiz['run_id']}_{index}", use_container_width=True):
                quiz["index"] += 1
                st.session_state.quiz = quiz
                st.rerun()

        st.markdown('<div class="mqs-tip">Pense com calma. Cada resposta é uma oportunidade de aprender.</div>', unsafe_allow_html=True)
        return

    percent = round(score / total * 100, 1) if total else 0
    st.subheader("Resultado da sua participação")
    result_columns = st.columns(3)
    result_columns[0].metric("Pontuação", f"{score}/{total}")
    result_columns[1].metric("Respondidas", total)
    result_columns[2].metric("Aproveitamento", f"{percent:.1f}%")

    if percent == 100:
        message = "Excelente resultado. Você conhece muito bem a Máquina Solo."
    elif percent >= 70:
        message = "Ótimo trabalho. Você mostrou um bom domínio do conteúdo."
    elif percent >= 40:
        message = "Boa participação. Continue explorando os conhecimentos MQS."
    else:
        message = "Obrigado por participar. Cada rodada é uma oportunidade de aprender."
    st.markdown(f'<div class="mqs-tip">{html.escape(message)}</div>', unsafe_allow_html=True)

    if not quiz.get("saved") and not quiz.get("save_attempted"):
        payload = {
            "name": quiz["name"],
            "sector": quiz["sector"],
            "participant_key": quiz["participant_key"],
            "score": score,
            "correct": score,
            "total": total,
            "percent": percent,
            "answers": [
                {
                    "question_id": question["id"],
                    "selected": quiz["answers"].get(question["id"]),
                    "correct": question.get("correct"),
                }
                for question in questions
            ],
            "created_at": now_iso(),
        }
        saved, save_status = save_attempt_once(client, payload)
        quiz["saved"] = saved
        quiz["save_attempted"] = True
        quiz["save_status"] = save_status
        st.session_state.quiz = quiz

    if quiz.get("saved"):
        if quiz.get("save_status") == "already_saved":
            st.success("Esta participação já estava registrada no ranking.")
        else:
            st.success("Participação registrada no ranking.")
    else:
        st.error("Não foi possível registrar sua participação agora. Seus dados continuam salvos nesta sessão.")
        if st.button("Tentar registrar novamente", key=f"retry_{quiz['run_id']}"):
            quiz["save_attempted"] = False
            st.session_state.quiz = quiz
            st.rerun()

    with st.expander("Conferir respostas"):
        for question in questions:
            selected = quiz["answers"].get(question["id"])
            correct = str(question.get("correct") or "").upper()
            st.markdown(f"**{question.get('prompt', '')}**")
            st.write(f"Sua resposta: {selected}. {question.get(selected.lower(), '') if selected else '—'}")
            st.write(f"Resposta correta: {correct}. {question.get(correct.lower(), '')}")
            if question.get("explanation"):
                st.caption(question["explanation"])

    if st.button("Consultar ranking", type="primary", key=f"ranking_{quiz['run_id']}"):
        st.session_state.quiz = None
        st.session_state.pending_page = "Ranking"
        st.rerun()


def render_leaderboard(client):
    st.subheader("Ranking do Desafio MQS")
    st.caption("Classificação por aproveitamento e, em seguida, pontuação. Quem empata nos dois critérios compartilha a posição.")
    if st.button("Atualizar ranking", key="refresh_ranking"):
        st.rerun()
    try:
        with st.spinner("Carregando a classificação..."):
            board = fetch_leaderboard(client)
    except Exception:
        st.error("Não foi possível carregar o ranking. Verifique a conexão e tente novamente.")
        return
    if not board:
        st.info("O ranking ainda não tem participações.")
        return

    top_rows = board[:3]
    podium = st.columns(len(top_rows))
    for column, row in zip(podium, top_rows):
        with column:
            with st.container(border=True):
                label = f"{row['Posição']}º lugar" if row["Posição"] > 0 else "Posição"
                st.caption(label)
                st.markdown(f"**{row['Nome']}**")
                st.caption(row["Setor"])
                st.metric("Pontuação", f"{row['Pontos']}/{row['Perguntas']}", f"{row['Aproveitamento']}")

    display_rows = [
        {key: row[key] for key in ("Posição", "Nome", "Setor", "Pontos", "Perguntas", "Aproveitamento")}
        for row in board
    ]
    st.dataframe(display_rows, use_container_width=True, hide_index=True)
    st.caption("Todos os dispositivos consultam a mesma classificação centralizada no Supabase.")


def render_admin_login():
    st.subheader("Área da organização")
    expected = get_secret("MQS_ADMIN_PASSWORD")
    if not expected:
        st.warning("A senha administrativa ainda não está configurada nos Secrets do Streamlit.")
        return
    with st.form("admin_login"):
        password = st.text_input("Senha administrativa", type="password")
        login = st.form_submit_button("Entrar", type="primary")
    if login:
        if password == expected:
            st.session_state.admin_ok = True
            st.rerun()
        st.error("Senha incorreta.")


def render_campaign_tab(client, settings):
    st.markdown("### Configuração da campanha")
    title = st.text_input("Título do desafio", value=settings.get("title") or "DESAFIO MQS")
    campaign_open = st.toggle("Campanha aberta", value=bool(settings.get("campaign_open")))
    start_date = st.date_input(
        "Data inicial",
        value=date.fromisoformat(str(settings["start_date"])[:10]) if settings.get("start_date") else today_local(),
    )
    end_date = st.date_input(
        "Data final",
        value=date.fromisoformat(str(settings["end_date"])[:10]) if settings.get("end_date") else today_local(),
    )
    per_game = st.number_input(
        "Quantidade padrão (configuração existente)", min_value=1, max_value=100,
        value=int(settings.get("questions_per_game") or 10),
    )
    st.caption("A pessoa participante também escolhe entre 5, 10, 15 ou todas as perguntas elegíveis da trilha.")
    if st.button("Salvar campanha", type="primary"):
        if end_date < start_date:
            st.error("A data final não pode ser anterior à data inicial.")
        elif not title.strip():
            st.error("Informe um título para a campanha.")
        else:
            try:
                client.table("mqs_settings").upsert({
                    "id": 1,
                    "title": title.strip(),
                    "campaign_open": campaign_open,
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "questions_per_game": int(per_game),
                }).execute()
                st.success("Configuração salva.")
                st.rerun()
            except Exception:
                st.error("Não foi possível salvar a configuração da campanha. Tente novamente.")


def render_questions_tab(client):
    st.markdown("### Banco de perguntas")
    try:
        questions = fetch_questions(client)
    except Exception:
        st.error("Não foi possível carregar as perguntas.")
        return

    if not questions:
        st.warning("Ainda não há perguntas cadastradas.")
        if st.button("Importar banco inicial de perguntas"):
            path = Path(__file__).with_name("questions_initial.json")
            try:
                with path.open("r", encoding="utf-8") as file:
                    items = json.load(file)
                existing = client.table("mqs_questions").select("id").limit(1).execute().data or []
                if existing:
                    st.warning("A base já possui registros; a importação foi interrompida sem alterar dados.")
                else:
                    payload = [{
                        "id": question["id"], "category": question["category"],
                        "prompt": question["prompt"], "question_type": question["type"],
                        "a": question["A"], "b": question["B"], "c": question["C"], "d": question["D"],
                        "correct": question["correct"], "explanation": question["explanation"],
                        "active": question["active"],
                    } for question in items]
                    client.table("mqs_questions").insert(payload).execute()
                    st.success(f"{len(payload)} perguntas importadas. Revise as questões pendentes antes de abrir a campanha.")
                    st.rerun()
            except Exception:
                st.error("Não foi possível importar o banco inicial. A tabela não foi limpa nem reinicializada.")

    if questions:
        st.caption(f"{len(questions)} perguntas cadastradas. As inativas ou sem gabarito ficam fora das rodadas.")
        options = [
            f"{question['id']} · {question.get('category', 'Geral')} · "
            f"{'Ativa' if question_is_eligible(question) else 'Inativa / revisar'}"
            for question in questions
        ]
        chosen_label = st.selectbox("Escolha uma pergunta para editar", options)
        selected_id = questions[options.index(chosen_label)]["id"]
        question = next(item for item in questions if item["id"] == selected_id)
        with st.form(f"edit_question_{selected_id}"):
            category = st.text_input("Categoria", value=question.get("category", ""))
            prompt = st.text_area("Enunciado", value=question.get("prompt", ""))
            a = st.text_input("Alternativa A", value=question.get("a", ""))
            b = st.text_input("Alternativa B", value=question.get("b", ""))
            c = st.text_input("Alternativa C", value=question.get("c", ""))
            d = st.text_input("Alternativa D", value=question.get("d", ""))
            existing_correct = str(question.get("correct") or "").upper()
            correct_options = ["", *LETTERS]
            correct_index = correct_options.index(existing_correct) if existing_correct in correct_options else 0
            correct = st.selectbox("Gabarito", correct_options, index=correct_index)
            explanation = st.text_area("Explicação / observação", value=question.get("explanation", ""))
            active = st.checkbox("Pergunta ativa", value=bool(question.get("active")))
            saved = st.form_submit_button("Salvar pergunta", type="primary")
        if saved:
            correct_text = {"A": a, "B": b, "C": c, "D": d}.get(correct, "")
            if active and (not correct or not correct_text.strip()):
                st.error("Uma pergunta só pode ficar ativa quando tiver gabarito e alternativa correspondente.")
            elif not category.strip() or not prompt.strip():
                st.error("Preencha a categoria e o enunciado.")
            else:
                try:
                    client.table("mqs_questions").update({
                        "category": category.strip(), "prompt": prompt.strip(),
                        "a": a, "b": b, "c": c, "d": d,
                        "correct": correct, "explanation": explanation, "active": active,
                    }).eq("id", selected_id).execute()
                    st.success("Pergunta atualizada.")
                    st.rerun()
                except Exception:
                    st.error("Não foi possível atualizar a pergunta.")

        with st.expander("Excluir pergunta"):
            st.warning(f"A exclusão remove a pergunta {selected_id} do banco e não pode ser desfeita por esta tela.")
            confirm_question_delete = st.checkbox(f"Confirmo a exclusão da pergunta {selected_id}", key=f"confirm_question_{selected_id}")
            if st.button("Excluir pergunta selecionada", disabled=not confirm_question_delete, key=f"delete_question_{selected_id}"):
                try:
                    client.table("mqs_questions").delete().eq("id", selected_id).execute()
                    st.success("Pergunta excluída.")
                    st.rerun()
                except Exception:
                    st.error("Não foi possível excluir a pergunta.")

    st.markdown("### Adicionar pergunta")
    with st.form("new_question"):
        new_id = st.text_input("ID (ex.: NOVA01)")
        new_category = st.text_input("Categoria da nova pergunta")
        new_prompt = st.text_area("Enunciado da nova pergunta")
        new_a = st.text_input("Alternativa A")
        new_b = st.text_input("Alternativa B")
        new_c = st.text_input("Alternativa C")
        new_d = st.text_input("Alternativa D")
        new_correct = st.selectbox("Gabarito da nova pergunta", ["", *LETTERS])
        new_explanation = st.text_area("Explicação / observação da nova pergunta")
        new_active = st.checkbox("Nova pergunta ativa")
        new_saved = st.form_submit_button("Adicionar pergunta")
    if new_saved:
        answer_text = {"A": new_a, "B": new_b, "C": new_c, "D": new_d}.get(new_correct, "")
        if not new_id.strip() or not new_category.strip() or not new_prompt.strip():
            st.error("Preencha o ID, a categoria e o enunciado.")
        elif new_active and (not new_correct or not answer_text.strip()):
            st.error("Uma pergunta só pode ficar ativa quando tiver gabarito e alternativa correspondente.")
        else:
            try:
                client.table("mqs_questions").insert({
                    "id": new_id.strip().upper(), "category": new_category.strip(),
                    "prompt": new_prompt.strip(), "question_type": "MCQ",
                    "a": new_a, "b": new_b, "c": new_c, "d": new_d,
                    "correct": new_correct, "explanation": new_explanation, "active": new_active,
                }).execute()
                st.success("Pergunta adicionada.")
                st.rerun()
            except Exception:
                st.error("Não foi possível adicionar a pergunta. Verifique se o ID já existe.")


def render_results_tab(client):
    st.markdown("### Resultados e participações")
    try:
        board = fetch_leaderboard(client)
    except Exception:
        st.error("Não foi possível carregar os resultados.")
        return
    st.metric("Participações registradas", len(board))
    if not board:
        st.info("Ainda não há resultados.")
        return
    st.dataframe(
        [{key: row[key] for key in ("Posição", "Nome", "Setor", "Pontos", "Perguntas", "Aproveitamento", "created_at")} for row in board],
        use_container_width=True, hide_index=True,
    )
    export_rows = [{key: row.get(key) for key in ("Posição", "Nome", "Setor", "Pontos", "Perguntas", "Aproveitamento", "created_at")} for row in board]
    data = json.dumps(export_rows, ensure_ascii=False, indent=2).encode("utf-8")
    st.download_button("Baixar resultados (JSON)", data=data, file_name="resultados_desafio_mqs.json", mime="application/json")

    labels = [f"{row['name']} · {row['sector']} · {row['score']}/{row['total']} pts · {row['id']}" for row in board]
    selected_label = st.selectbox("Participação para excluir", labels)
    selected_attempt = board[labels.index(selected_label)]
    with st.expander("Excluir participação"):
        st.warning(
            f"Esta ação remove do ranking a participação de {selected_attempt['name']} "
            f"({selected_attempt['sector']}) e os dados de respostas associados. Ela não pode ser desfeita por esta tela."
        )
        confirm_attempt_delete = st.checkbox(
            "Confirmo a exclusão desta participação", key=f"confirm_attempt_{selected_attempt['id']}"
        )
        if st.button("Excluir participação selecionada", disabled=not confirm_attempt_delete):
            try:
                client.table("mqs_attempts").delete().eq("id", selected_attempt["id"]).execute()
                st.success("Participação excluída.")
                st.rerun()
            except Exception:
                st.error("Não foi possível excluir a participação.")


def render_organization(client, settings):
    st.subheader("Área da organização")
    if not admin_ok():
        render_admin_login()
        return
    st.success("Acesso administrativo liberado.")
    if st.button("Sair da organização"):
        st.session_state.admin_ok = False
        st.rerun()
    tabs = st.tabs(["Campanha", "Perguntas", "Resultados"])
    with tabs[0]:
        render_campaign_tab(client, settings)
    with tabs[1]:
        render_questions_tab(client)
    with tabs[2]:
        render_results_tab(client)


client = db()
if client is None:
    render_header("DESAFIO MQS")
    st.error("A conexão com o banco ainda não está configurada.")
    st.markdown(
        "Configure `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` e `MQS_ADMIN_PASSWORD` "
        "nos Secrets do Streamlit. Execute `supabase_schema.sql` apenas se as tabelas ainda não existirem."
    )
    st.stop()

try:
    settings = fetch_settings(client)
except Exception:
    render_header("DESAFIO MQS")
    st.error("Não foi possível acessar a campanha no banco. Confira a conexão com o Supabase e tente novamente.")
    st.stop()

render_header(settings.get("title") or "DESAFIO MQS")
if st.session_state.get("pending_page"):
    st.session_state.nav_page = st.session_state.pop("pending_page")
page = st.radio(
    "Navegação", ["Jogar", "Ranking", "Organização"], horizontal=True,
    label_visibility="collapsed", key="nav_page",
)

if page == "Jogar":
    open_now, campaign_message = campaign_is_open(settings)
    quiz = st.session_state.get("quiz")
    if quiz:
        render_quiz(client, quiz)
    else:
        render_home(client, settings, open_now, campaign_message)
elif page == "Ranking":
    render_leaderboard(client)
else:
    render_organization(client, settings)
