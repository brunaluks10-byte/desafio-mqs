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
        row["Nome"] = row.get("name", "")
        row["Setor"] = row.get("sector", "")
        row["Pontos"] = row.get("score", 0)
        row["Perguntas"] = row.get("total", 0)
        row["Aproveitamento"] = f'{float(row.get("percent") or 0):.1f}%'
    return rows

def campaign_is_open(settings):
    if not settings.get("campaign_open"):
        return False, "A campanha ainda não está aberta pela organização."
    today = date.today()
    start = settings.get("start_date")
    end = settings.get("end_date")
    if start and today < date.fromisoformat(str(start)[:10]):
        return False, f"A campanha começa em {date.fromisoformat(str(start)[:10]).strftime('%d/%m/%Y')}."
    if end and today > date.fromisoformat(str(end)[:10]):
        return False, "A campanha foi encerrada."
    return True, "Campanha aberta"

def seed_questions(client):
    existing = client.table("mqs_questions").select("id").limit(1).execute().data or []
    if existing:
        return False, "A base de perguntas já possui registros."
    path = os.path.join(os.path.dirname(__file__), "questions_initial.json")
    with open(path, "r", encoding="utf-8") as f:
        items = json.load(f)
    payload = [{
        "id": q["id"], "category": q["category"], "prompt": q["prompt"], "question_type": q["type"],
        "a": q["A"], "b": q["B"], "c": q["C"], "d": q["D"],
        "correct": q["correct"], "explanation": q["explanation"], "active": q["active"]
    } for q in items]
    client.table("mqs_questions").insert(payload).execute()
    return True, f"{len(payload)} perguntas iniciais importadas. Revise as perguntas inativas antes da campanha."

client = db()
if client is None:
    st.markdown('<div class="mqs-hero"><h1>DESAFIO MQS</h1><p>Máquina Solo · Conhecimento, colaboração e desafio</p></div>', unsafe_allow_html=True)
    st.error("A conexão com o banco ainda não foi configurada.")
    st.markdown("**Próxima configuração:** crie o projeto Supabase, execute o arquivo `supabase_schema.sql` e configure `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` e `MQS_ADMIN_PASSWORD` nos Secrets do Streamlit.")
    st.stop()

try:
    settings = fetch_settings(client)
except Exception as e:
    st.error("Não consegui acessar as tabelas do banco. Confira se executou o arquivo `supabase_schema.sql` no Supabase.")
    st.code(str(e))
    st.stop()

st.markdown(f'<div class="mqs-hero"><h1>{settings.get("title") or "DESAFIO MQS"}</h1><p>Máquina Solo · Conhecimento, colaboração e desafio</p></div>', unsafe_allow_html=True)
st.write("")
pages = ["Jogar", "Ranking", "Organização"]
page = st.radio("Menu", pages, horizontal=True, label_visibility="collapsed")

if page == "Jogar":
    is_open, status_msg = campaign_is_open(settings)
    if is_open:
        st.success("🟢 Campanha aberta — você pode participar!")
    else:
        st.info(status_msg)
    st.subheader("Participe do desafio")
    if not is_open:
        st.caption("A organização precisa abrir a campanha antes que as respostas sejam registradas.")
    with st.form("participant_form"):
        name = st.text_input("Seu nome", max_chars=100, disabled=not is_open)
        sectors = ["Comercial", "Pós-vendas", "Marketing", "Peças", "Serviços", "Operações", "Administrativo", "Financeiro", "RH", "Outro"]
        sector = st.selectbox("Seu setor", sectors, disabled=not is_open)
        if sector == "Outro":
            sector_other = st.text_input("Informe seu setor", disabled=not is_open)
        else:
            sector_other = ""
        start = st.form_submit_button("Começar desafio", type="primary", disabled=not is_open)
    if start:
        name = name.strip()
        sector = sector_other.strip() if sector == "Outro" else sector
        if len(name) < 2 or not sector:
            st.error("Informe seu nome e setor.")
        else:
            participant_key = hashlib.sha256((name.casefold().strip() + "|" + sector.casefold().strip()).encode()).hexdigest()
            exists = client.table("mqs_attempts").select("id").eq("participant_key", participant_key).limit(1).execute().data
            if exists:
                st.error("Já existe uma participação com esse nome e setor. Se houve algum erro, procure a organização.")
            else:
                qs = fetch_questions(client, active_only=True)
                if not qs:
                    st.error("Ainda não há perguntas ativas com gabarito. Avise a organização.")
                else:
                    n = max(1, min(int(settings.get("questions_per_game") or 10), len(qs)))
                    st.session_state.quiz = {
                        "name": name, "sector": sector, "participant_key": participant_key,
                        "questions": random.sample(qs, n), "index": 0, "answers": {}
                    }
                    st.rerun()
    quiz = st.session_state.get("quiz")
    if quiz:
        qs = quiz["questions"]
        idx = quiz["index"]
        if idx < len(qs):
            q = qs[idx]
            st.progress(idx / len(qs), text=f"Pergunta {idx + 1} de {len(qs)}")
            st.caption(f'{q.get("category", "Geral")} · Participante: {quiz["name"]}')
            st.markdown(f"### {q['prompt']}")
            choices = [("A", q.get("a","")), ("B", q.get("b","")), ("C", q.get("c","")), ("D", q.get("d",""))]
            choices = [(k, v) for k, v in choices if v]
            with st.form(f"answer_{idx}"):
                selected = st.radio("Escolha uma resposta", choices, format_func=lambda item: item[1], index=None)
                submitted = st.form_submit_button("Confirmar resposta" if idx < len(qs)-1 else "Finalizar desafio", type="primary")
            if submitted:
                if selected is None:
                    st.warning("Selecione uma alternativa antes de continuar.")
                else:
                    quiz["answers"][q["id"]] = selected[0]
                    quiz["index"] += 1
                    st.session_state.quiz = quiz
                    st.rerun()
        else:
            correct_count = sum(1 for q in qs if quiz["answers"].get(q["id"]) == q.get("correct"))
            score = correct_count
            total = len(qs)
            percent = round(score / total * 100, 1) if total else 0
            st.markdown("## Resultado da sua participação")
            c1, c2, c3 = st.columns(3)
            c1.metric("Pontos", f"{score}/{total}")
            c2.metric("Acertos", score)
            c3.metric("Aproveitamento", f"{percent:.1f}%")
            if not st.session_state.get("quiz_saved"):
                try:
                    payload = {
                        "name": quiz["name"], "sector": quiz["sector"],
                        "participant_key": quiz["participant_key"], "score": score,
                        "correct": score, "total": total, "percent": percent,
                        "answers": [{"question_id": q["id"], "selected": quiz["answers"].get(q["id"]), "correct": q.get("correct")} for q in qs],
                        "created_at": now_iso()
                    }
                    client.table("mqs_attempts").insert(payload).execute()
                    st.session_state.quiz_saved = True
                    st.success("Participação registrada no ranking!")
                except Exception as e:
                    st.error("Não consegui salvar sua participação. Tire uma foto desta mensagem e avise a organização.")
                    st.code(str(e))
            if st.button("Ver ranking", type="primary"):
                st.session_state.quiz = None
                st.session_state.quiz_saved = False
                st.rerun()
            with st.expander("Conferir respostas"):
                for q in qs:
                    sel = quiz["answers"].get(q["id"])
                    text_selected = q.get(sel.lower(), "") if sel else ""
                    text_correct = q.get(q.get("correct","").lower(), "")
                    st.markdown(f"**{q['prompt']}**")
                    st.write(f"Sua resposta: {text_selected or '—'}")
                    st.write(f"Resposta correta: {text_correct or 'A confirmar'}")
                    if q.get("explanation"):
                        st.caption(q["explanation"])

elif page == "Ranking":
    st.subheader("🏆 Ranking do Desafio MQS")
    try:
        board = fetch_leaderboard(client)
        if board:
            st.dataframe([{k: r[k] for k in ["Posição","Nome","Setor","Pontos","Perguntas","Aproveitamento"]} for r in board], use_container_width=True, hide_index=True)
        else:
            st.info("O ranking ainda não tem participações.")
        st.caption("O ranking é centralizado e pode ser consultado por todos os participantes.")
    except Exception as e:
        st.error("Não foi possível carregar o ranking.")
        st.code(str(e))

else:
    st.subheader("🔐 Área da organização")
    if not admin_ok():
        with st.form("admin_login"):
            password = st.text_input("Senha administrativa", type="password")
            login = st.form_submit_button("Entrar", type="primary")
        if login:
            expected = get_secret("MQS_ADMIN_PASSWORD")
            if expected and password == expected:
                st.session_state.admin_ok = True
                st.rerun()
            else:
                st.error("Senha incorreta ou senha administrativa não configurada nos Secrets.")
    else:
        st.success("Acesso administrativo liberado.")
        if st.button("Sair da organização"):
            st.session_state.admin_ok = False
            st.rerun()
        tabs = st.tabs(["Campanha", "Perguntas", "Resultados"])
        with tabs[0]:
            st.markdown("### Configuração da campanha")
            title = st.text_input("Título do desafio", value=settings.get("title") or "DESAFIO MQS")
            is_campaign_open = st.toggle("Campanha aberta", value=bool(settings.get("campaign_open")))
            start_date = st.date_input("Data inicial", value=date.fromisoformat(settings["start_date"]) if settings.get("start_date") else date.today())
            end_date = st.date_input("Data final", value=date.fromisoformat(settings["end_date"]) if settings.get("end_date") else date.today())
            per_game = st.number_input("Perguntas por participação", min_value=1, max_value=100, value=int(settings.get("questions_per_game") or 10))
            if st.button("Salvar campanha", type="primary"):
                if end_date < start_date:
                    st.error("A data final não pode ser anterior à data inicial.")
                else:
                    client.table("mqs_settings").upsert({
                        "id": 1, "title": title, "campaign_open": is_campaign_open,
                        "start_date": start_date.isoformat(), "end_date": end_date.isoformat(),
                        "questions_per_game": int(per_game)
                    }).execute()
                    st.success("Configuração salva.")
                    st.rerun()
        with tabs[1]:
            st.markdown("### Banco de perguntas")
            qs = fetch_questions(client)
            if not qs:
                st.warning("Ainda não há perguntas cadastradas.")
                if st.button("Importar banco inicial de perguntas"):
                    ok, msg = seed_questions(client)
                    (st.success if ok else st.warning)(msg)
                    st.rerun()
            else:
                st.caption(f"{len(qs)} perguntas cadastradas.")
                selected_id = st.selectbox("Escolha uma pergunta para editar", [q["id"] for q in qs])
                q = next(q for q in qs if q["id"] == selected_id)
                with st.form("edit_question"):
                    category = st.text_input("Categoria", value=q.get("category",""))
                    prompt = st.text_area("Enunciado", value=q.get("prompt",""))
                    a = st.text_input("Alternativa A", value=q.get("a",""))
                    b = st.text_input("Alternativa B", value=q.get("b",""))
                    c = st.text_input("Alternativa C", value=q.get("c",""))
                    d = st.text_input("Alternativa D", value=q.get("d",""))
                    correct = st.selectbox("Gabarito", ["", "A", "B", "C", "D"], index=(["", "A", "B", "C", "D"].index(q.get("correct","")) if q.get("correct","") in ["", "A", "B", "C", "D"] else 0))
                    explanation = st.text_area("Explicação / observação", value=q.get("explanation",""))
                    active = st.checkbox("Pergunta ativa", value=bool(q.get("active")))
                    saved = st.form_submit_button("Salvar pergunta", type="primary")
                if saved:
                    client.table("mqs_questions").update({
                        "category": category, "prompt": prompt, "a": a, "b": b, "c": c, "d": d,
                        "correct": correct, "explanation": explanation, "active": active
                    }).eq("id", selected_id).execute()
                    st.success("Pergunta atualizada.")
                    st.rerun()
                st.markdown("### Adicionar pergunta")
                with st.form("new_question"):
                    new_id = st.text_input("ID (ex.: NOVA01)")
                    new_category = st.text_input("Categoria da nova pergunta")
                    new_prompt = st.text_area("Enunciado da nova pergunta")
                    na = st.text_input("Alternativa A")
                    nb = st.text_input("Alternativa B")
                    nc = st.text_input("Alternativa C")
                    nd = st.text_input("Alternativa D")
                    ncorrect = st.selectbox("Gabarito da nova pergunta", ["", "A", "B", "C", "D"])
                    nexp = st.text_area("Explicação / observação da nova pergunta")
                    nactive = st.checkbox("Nova pergunta ativa")
                    new_saved = st.form_submit_button("Adicionar pergunta")
                if new_saved:
                    if not new_id.strip() or not new_prompt.strip():
                        st.error("Preencha ao menos o ID e o enunciado.")
                    else:
                        client.table("mqs_questions").insert({
                            "id": new_id.strip().upper(), "category": new_category, "prompt": new_prompt,
                            "question_type": "MCQ", "a": na, "b": nb, "c": nc, "d": nd,
                            "correct": ncorrect, "explanation": nexp, "active": nactive
                        }).execute()
                        st.success("Pergunta adicionada.")
                        st.rerun()
        with tabs[2]:
            st.markdown("### Resultados e participação")
            board = fetch_leaderboard(client)
            st.metric("Participações registradas", len(board))
            if board:
                st.dataframe([{k: r[k] for k in ["Posição","Nome","Setor","Pontos","Perguntas","Aproveitamento","created_at"]} for r in board], use_container_width=True, hide_index=True)
                csv = json.dumps(board, ensure_ascii=False, indent=2).encode("utf-8")
                st.download_button("Baixar resultados (JSON)", data=csv, file_name="resultados_desafio_mqs.json", mime="application/json")
                delete_id = st.selectbox("ID da participação para excluir", [r["id"] for r in board])
                if st.button("Excluir participação selecionada"):
                    client.table("mqs_attempts").delete().eq("id", delete_id).execute()
                    st.success("Participação excluída.")
                    st.rerun()
            else:
                st.info("Ainda não há resultados.")
