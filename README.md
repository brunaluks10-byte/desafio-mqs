# Desafio MQS

Aplicativo corporativo de treinamento e engajamento construído com Streamlit e Supabase. O ranking e as participações permanecem centralizados no Supabase; a interface é responsiva e usa a identidade grafite, preta, branca e amarela da Máquina Solo.

## Arquivos

- `app.py`: participação, quiz, ranking e área da organização.
- `requirements.txt`: dependências do Streamlit e do cliente Supabase.
- `supabase_schema.sql`: esquema existente de campanha, perguntas e participações.
- `questions_initial.json`: banco inicial de 48 perguntas, incluindo questões inativas para revisão.
- `.streamlit/secrets.toml.example`: modelo das configurações locais, sem credenciais reais.

## Configuração

1. Configure o projeto Supabase já usado pela implantação. Não crie outro projeto para esta atualização.
2. Se as tabelas ainda não existirem, execute `supabase_schema.sql`. A aplicação não altera o esquema.
3. Copie `.streamlit/secrets.toml.example` para `.streamlit/secrets.toml` e preencha os valores localmente. No Streamlit Cloud, use **App settings → Secrets**.
4. Mantenha `SUPABASE_SERVICE_ROLE_KEY` somente nos Secrets do servidor. Nunca publique o arquivo `secrets.toml` nem envie chaves pelo chat.
5. Na área **Organização**, revise as perguntas, defina o período e abra a campanha. A importação inicial só aparece quando a tabela de perguntas está vazia; ela não limpa nem substitui registros existentes.

## Participação

As trilhas filtram as perguntas existentes por categoria: desafio completo, História MQS, Conhecimento técnico e Cultura e valores. A pessoa escolhe 5, 10, 15 ou todas as perguntas elegíveis da trilha. Se a quantidade pedida não estiver disponível, o app explica quantas questões podem ser usadas; não repete perguntas.

O banco inicial tem questões ativas e questões que precisam de revisão. Rodadas incluem somente perguntas ativas com gabarito e alternativa correspondente. A pontuação é o número de respostas corretas. O ranking ordena por aproveitamento e depois por pontuação; empates nos dois critérios compartilham a posição.

O esquema atual limita a uma participação por combinação de nome e setor por meio de `participant_key`. Essa regra foi preservada e também evita inserir uma conclusão duas vezes em reruns do Streamlit.

## Tatu original

O arquivo de referência `Desafio_MQS_Editavel_Ranking.html` e a imagem original do Tatu não estão presentes neste repositório. O app deixou de exibir o banner legado `tatu_mqs_banner.png` e não substitui o personagem por outra ilustração. Para concluir a integração do mascote, disponibilize a imagem oficial do Tatu da Máquina Solo (camisa branca e tênis amarelos) como `assets/tatu_original.png`.

## Administração e segurança

- A senha administrativa é lida de `MQS_ADMIN_PASSWORD` nos Secrets e não aparece na interface pública.
- A chave de serviço do Supabase é usada apenas pelo processo Python do Streamlit.
- Ações de exclusão de perguntas e participações exigem confirmação explícita na tela administrativa.
- Não há limpeza automática, reinicialização ou migração de dados nesta versão.

Para executar localmente, instale as dependências de `requirements.txt` e inicie com `streamlit run app.py` depois de configurar os Secrets.
