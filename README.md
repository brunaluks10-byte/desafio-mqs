# Desafio MQS — Python + Streamlit + Supabase

Este pacote é uma nova versão do Desafio MQS, pensada para abrir por link em celulares e computadores. O ranking e as participações ficam em um banco de dados Supabase. O pacote leva a base inicial de perguntas do projeto anterior (48 perguntas); as perguntas marcadas como inativas precisam ser revisadas antes de abrir a campanha.

## Arquivos
- `app.py`: aplicativo Streamlit (jogo, ranking e área administrativa).
- `requirements.txt`: bibliotecas necessárias para publicar.
- `supabase_schema.sql`: cria as tabelas do banco.
- `questions_initial.json`: banco inicial de perguntas.
- `.streamlit/secrets.toml.example`: exemplo das configurações secretas.

## O que você precisa configurar
1. Criar uma conta/projeto no Supabase.
2. No Supabase, abrir **SQL Editor → New query**, colar o conteúdo de `supabase_schema.sql` e clicar em **Run**.
3. Copiar a URL do projeto e a chave `service_role`/`secret` do backend. Guarde a chave; não a envie em mensagens e não a publique no GitHub.
4. Criar um repositório no GitHub e carregar os arquivos deste pacote (não carregar um arquivo real `secrets.toml`).
5. Em `share.streamlit.io`, conectar ao GitHub e publicar `app.py`.
6. Em **App settings → Secrets** no Streamlit, cadastrar:
   - `SUPABASE_URL = "https://SEU-PROJETO.supabase.co"`
   - `SUPABASE_SERVICE_ROLE_KEY = "SUA_CHAVE_PRIVADA_DO_SERVIDOR"`
   - `MQS_ADMIN_PASSWORD = "CRIE_UMA_SENHA_FORTE"`
7. Abrir o app, entrar em **Organização**, importar as perguntas iniciais, revisar os gabaritos e definir o período da campanha. Só depois marque **Campanha aberta**.

## Importante
- A chave de servidor do Supabase deve ficar somente nos Secrets do Streamlit. Nunca coloque essa chave no código público, no navegador ou em mensagens.
- Antes de usar com a equipe, faça uma participação de teste e remova-a pelo painel de resultados.
- Esta versão precisa ser publicada e testada antes de compartilhar o link com os colaboradores.
- O ranking não é um sistema de autenticação corporativa: a regra atual limita uma participação por combinação de nome e setor. Para campanha com prêmio, recomendamos acrescentar autenticação individual.
