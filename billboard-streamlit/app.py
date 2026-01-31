import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from datetime import date
from dateutil.relativedelta import relativedelta, SA

from services.billboard import fetch_hot100
from services.links import best_spotify_link


# -----------------------------
# Identidade visual
# -----------------------------
ACCENT = "#E50914"
BG = "#0A0A0B"
PANEL = "#0F0F12"
TEXT = "#FFFFFF"
MUTED = "rgba(255,255,255,0.70)"
BORDER = "rgba(255,255,255,0.12)"

st.set_page_config(page_title="🔥 Hot Music", layout="wide")

st.markdown(
f"""
<style>
.stApp {{
  background:
    radial-gradient(900px 420px at 30% 20%, rgba(229,9,20,0.18), transparent 60%),
    radial-gradient(700px 380px at 70% 15%, rgba(229,9,20,0.10), transparent 55%),
    {BG};
  color: {TEXT};
}}

h1,h2,h3,h4,h5,h6,p,span,div,label {{ color: {TEXT}; }}
small {{ color: {MUTED}; }}

a {{ color: {TEXT} !important; text-decoration: none; }}
a:hover {{ text-decoration: underline; }}

/* Sidebar separada */
section[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, {PANEL}, rgba(15,15,18,0.90));
  border-right: 1px solid {BORDER};
}}
section[data-testid="stSidebar"] * {{ color: {TEXT}; }}

/* Topbar */
.topbar {{
  border: 1px solid {BORDER};
  background: linear-gradient(90deg, rgba(229,9,20,0.28), rgba(255,255,255,0.03));
  border-radius: 16px;
  padding: 10px 14px;
  margin-bottom: 14px;
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap: 10px;
}}
.topbar .left {{
  display:flex;
  align-items:center;
  gap: 12px;
}}
.brand {{
  font-weight: 900;
  letter-spacing: 0.2px;
}}
.pill {{
  display:inline-flex;
  align-items:center;
  gap: 8px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid {BORDER};
  background: rgba(255,255,255,0.03);
  color: {MUTED};
  font-size: 12px;
}}

/* Botão */
button[kind="primary"] {{
  background: rgba(229,9,20,0.94) !important;
  border: 1px solid rgba(255,255,255,0.12) !important;
}}
button[kind="primary"]:hover {{ filter: brightness(1.05); }}

/* Dataframe */
div[data-testid="stDataFrame"] {{
  border: 1px solid {BORDER};
  border-radius: 16px;
  overflow: hidden;
}}
</style>
""",
unsafe_allow_html=True,
)


# -----------------------------
# Helpers
# -----------------------------
@st.cache_data(ttl=60 * 60, show_spinner=False)
def cached_hot100(date_str: str, top_n: int):
    return fetch_hot100(date_str, limit=top_n)

@st.cache_data(ttl=60 * 60 * 6, show_spinner=False)
def cached_spotify_link(title: str, artist: str):
    res = best_spotify_link(title, artist)
    return res.url, res.method

def month_saturdays(year: int, month: int):
    first_day = date(year, month, 1)
    next_month = first_day + relativedelta(months=1)
    sats = []
    d = first_day + relativedelta(weekday=SA(1))
    while d < next_month:
        sats.append(d)
        d = d + relativedelta(weeks=1)
    return sats


# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.markdown("## 🔥 Hot Music")
    st.markdown("<small>As músicas e sucessos que fizeram história em cada ano.</small>", unsafe_allow_html=True)
    st.markdown("---")

    st.markdown("### Escolha a época")
    ano = st.number_input("Ano", min_value=1958, max_value=2100, value=2015, step=1)
    mes = st.selectbox("Mês", list(range(1, 13)), index=0)

    sats = month_saturdays(int(ano), int(mes))
    semana = st.selectbox("Semana (Billboard é semanal)", sats, format_func=lambda x: x.strftime("%Y-%m-%d"))

    qtd = st.selectbox("Quantidade", [10, 20, 50, 100], index=0)

    st.markdown("---")
    buscar = st.button("Buscar músicas", type="primary", use_container_width=True)

    st.markdown("<small>Observação: se o Billboard mudar o HTML, a extração pode falhar.</small>", unsafe_allow_html=True)


# -----------------------------
# Topbar (sem “Sem Spotify API”)
# -----------------------------
date_str = semana.strftime("%Y-%m-%d")

st.markdown(
f"""
<div class="topbar">
  <div class="left">
    <div class="brand">🔥 Hot Music</div>
    <span class="pill">Fonte: Billboard Hot 100</span>
  </div>
  <div class="pill">Semana: <b style="color:{TEXT};">{date_str}</b></div>
</div>
""",
unsafe_allow_html=True,
)


# -----------------------------
# HERO bonito e visível (CSS dentro do iframe)
# -----------------------------
hero_iframe = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8" />
<style>
  :root {{
    --text: {TEXT};
    --muted: {MUTED};
    --border: {BORDER};
    --accent: {ACCENT};
  }}
  body {{
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
    background: transparent;
    color: var(--text);
  }}
  .card {{
    border: 1px solid var(--border);
    border-radius: 18px;
    padding: 18px;
    background: rgba(255,255,255,0.03);
    box-shadow: 0 10px 30px rgba(0,0,0,0.25);
  }}
  .row {{
    display:flex;
    align-items:flex-start;
    gap: 14px;
  }}
  .icon {{
    font-size: 44px;
    line-height: 1;
    filter: drop-shadow(0 6px 18px rgba(0,0,0,0.35));
  }}
  .title {{
    font-size: 46px;
    font-weight: 950;
    line-height: 1.05;
    margin: 0;
  }}
  .sub {{
    margin-top: 10px;
    font-size: 16px;
    color: var(--muted);
    max-width: 980px;
  }}
  .chips {{
    display:flex;
    flex-wrap:wrap;
    gap: 10px;
    margin-top: 16px;
  }}
  .chip {{
    display:inline-flex;
    align-items:center;
    gap: 8px;
    padding: 8px 12px;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: rgba(255,255,255,0.02);
    color: var(--muted);
    font-size: 13px;
  }}
  .chip b {{
    color: var(--text);
  }}
  .highlight {{
    display:inline-block;
    margin-top: 10px;
    padding: 8px 12px;
    border-radius: 14px;
    border: 1px solid var(--border);
    background: linear-gradient(90deg, rgba(229,9,20,0.20), rgba(255,255,255,0.02));
    color: var(--muted);
    font-size: 13px;
  }}
</style>
</head>
<body>
  <div class="card">
    <div class="row">
      <div class="icon">🔥</div>
      <div>
        <div class="title">Hot Music</div>
        <div class="sub">
          As músicas e sucessos que fizeram história nos EUA.
          Escolha um mês e abra cada faixa direto no Spotify.
        </div>

        <div class="chips">
          <span class="chip">Semana selecionada: <b>{date_str}</b></span>
          <span class="chip">Ano: <b>{int(ano)}</b></span>
          <span class="chip">Mês: <b>{int(mes)}</b></span>
          <span class="chip">Exibição: <b>Top {int(qtd)}</b></span>
        </div>

        <div class="highlight">Dica: experimente trocar a semana do mês para ver variações do ranking.</div>
      </div>
    </div>
  </div>
</body>
</html>
"""

# altura maior pra garantir visibilidade total
components.html(hero_iframe, height=240, scrolling=False)

st.markdown("<div style='height:14px;'></div>", unsafe_allow_html=True)

if not buscar:
    st.markdown(
        "<div style='border:1px solid rgba(255,255,255,0.12); background: rgba(255,255,255,0.03); border-radius: 18px; padding: 18px;'>"
        "<b>Dica rápida:</b> ajuste os filtros na barra lateral e clique em <b>Buscar músicas</b>.</div>",
        unsafe_allow_html=True,
    )
    st.stop()


# -----------------------------
# Buscar + tabela (sem CSV)
# -----------------------------
with st.spinner("Coletando ranking do Billboard..."):
    try:
        songs = cached_hot100(date_str, int(qtd))
    except Exception as e:
        st.error(f"Falha ao buscar o Billboard: {e}")
        st.stop()

if not songs:
    st.error("Não foi possível extrair as músicas do ranking para essa semana. Tente outra semana do mês.")
    st.stop()

with st.spinner("Gerando links do Spotify..."):
    rows = []
    for s in songs:
        sp_url, method = cached_spotify_link(s.get("title", ""), s.get("artist", ""))
        rows.append(
            {
                "Rank": s.get("rank"),
                "Música": s.get("title"),
                "Artista": s.get("artist"),
                "Spotify": sp_url,
                "Método": method,
            }
        )

df = pd.DataFrame(rows)

st.markdown(
f"""
<div style="border:1px solid {BORDER}; background: rgba(255,255,255,0.03); border-radius: 18px; padding: 18px;">
  <div style="display:flex; justify-content:space-between; align-items:end; gap:12px;">
    <div>
      <div style="font-size:18px; font-weight:900;">Resultado</div>
      <div style="color:{MUTED}; font-size:13px;">Exibindo {len(df)} posições do ranking.</div>
    </div>
    <div class="pill">Clique em “Abrir” para ir ao Spotify</div>
  </div>
</div>
""",
unsafe_allow_html=True,
)

st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)

st.dataframe(
    df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Spotify": st.column_config.LinkColumn("Spotify", display_text="Abrir"),
    },
)