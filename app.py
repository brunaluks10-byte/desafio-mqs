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
