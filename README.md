# Billboard_Minerva

Dashboard em **Python + Streamlit** para explorar o **Billboard Hot 100** por semana e abrir cada faixa no **Spotify sem usar a API do Spotify**.

A app coleta o ranking do Billboard, extrai as músicas (preferindo JSON‑LD para ser mais resiliente a mudanças no HTML) e gera links do Spotify usando:
- melhor caso: **iTunes → Odesli → Spotify**
- fallback: **Spotify Search URL**

---

## O que você consegue fazer

- Selecionar **ano / mês / semana (sábado)** e visualizar o **Top N** (10/20/50/100).
- Ver tabela com **Rank, Música, Artista** e um link “Abrir” para o Spotify.
- Cache inteligente no Streamlit para não refazer requisições o tempo todo.

---

## Como funciona

### 1) Coleta do Billboard Hot 100
- Implementação: [`services.billboard.fetch_hot100`](billboard-streamlit/services/billboard.py)
- Estratégia:
  1. tenta extrair via **JSON‑LD** (mais estável): [`services.billboard._parse_jsonld`](billboard-streamlit/services/billboard.py) + [`services.billboard._parse_jsonld_itemlist`](billboard-streamlit/services/billboard.py)
  2. se falhar, usa um **fallback de HTML**: [`services.billboard._parse_html_fallback`](billboard-streamlit/services/billboard.py)
- Rede resiliente com retries: [`services.billboard._build_session`](billboard-streamlit/services/billboard.py)

### 2) Geração de link do Spotify (sem API)
- Implementação: [`services.links.best_spotify_link`](billboard-streamlit/services/links.py)
- Fluxo:
  - busca um track no iTunes: [`services.links.itunes_find_track_url`](billboard-streamlit/services/links.py)
  - converte via Odesli e pega URL do Spotify: [`services.links.odesli_get_spotify_url`](billboard-streamlit/services/links.py)
  - se não der, monta link de busca: [`services.links.spotify_search_url`](billboard-streamlit/services/links.py)

### 3) Interface Streamlit
- Arquivo: [billboard-streamlit/app.py](billboard-streamlit/app.py)
- Cache:
  - ranking semanal: `cached_hot100()` (TTL 1h)
  - links Spotify: `cached_spotify_link()` (TTL 6h)

---

## Estrutura do projeto

- [billboard-streamlit/app.py](billboard-streamlit/app.py) — UI Streamlit
- [billboard-streamlit/services/billboard.py](billboard-streamlit/services/billboard.py) — scraping/parsing do Billboard
- [billboard-streamlit/services/links.py](billboard-streamlit/services/links.py) — geração do “melhor link” do Spotify
- [billboard-streamlit/tests/](billboard-streamlit/tests/) — testes com `pytest`

---

## Requisitos

Veja [billboard-streamlit/requirements.txt](billboard-streamlit/requirements.txt):
- streamlit, requests, beautifulsoup4, pandas, python-dateutil
- pytest, ruff

---

## Rodando localmente

No terminal do VS Code, a partir da pasta `billboard-streamlit/`:

### Windows (PowerShell)
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run app.py
```

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m streamlit run app.py
```

---

## Testes

Os testes já incluem um parser “offline” para evitar depender da rede:

```bash
pytest -q
```

Principais arquivos:
- [billboard-streamlit/tests/test_billboard_parser_offline.py](billboard-streamlit/tests/test_billboard_parser_offline.py)
- [billboard-streamlit/tests/test_links_basic.py](billboard-streamlit/tests/test_links_basic.py)
- [billboard-streamlit/tests/test_links.py](billboard-streamlit/tests/test_links.py)

---

## Observações e limitações

- O Billboard pode mudar o HTML; por isso o parser prioriza JSON‑LD e tem fallback.
- A geração de links depende de serviços externos (iTunes/Odesli). Quando falham, o projeto ainda entrega um link de busca do Spotify.

