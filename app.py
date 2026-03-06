"""
app.py - PHP United FutebolManager
Interface principal Streamlit para gestão de grupos de futebol amador.
"""

import streamlit as st
import pandas as pd
import time
from datetime import datetime, date
from typing import Optional

import database as db
import logic
from streamlit_autorefresh import st_autorefresh

# ─────────────────────── CONFIG ───────────────────────

st.set_page_config(
    page_title="PHP United FutebolManager",
    page_icon="🐘",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────── INIT ───────────────────────

@st.cache_resource
def inicializar_banco():
    db.init_db()
    db.seed_jogadores_from_csv()

inicializar_banco()

# Session state defaults
def _init_state():
    defaults = {
        "partida_ativa": None,
        "time_a": [],
        "time_b": [],
        "goleiro_a": None,
        "goleiro_b": None,
        "cronometro_rodando": False,
        "tempo_inicio": None,
        "tempo_total_seg": 45 * 60,
        "gols_a": 0,
        "gols_b": 0,
        "presentes": [],
        "pagina_atual": "🏠 Dashboard",
        "tema": "light",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()

# CSS customizado - Dark Mode Premium
tema = "dark"

hex_bg = "#0F0C1A"
hex_text = "#F0E6FF"
hex_glass_bg = "rgba(30, 20, 50, 0.85)"
hex_glass_border = "rgba(150, 100, 255, 0.2)"
css_root = """
:root {
    --color-bg-deep: #0F0C1A;
    --color-neon-g: #7C3AED;
    --color-neon-b: #A855F7;
    --color-text-main: #F0E6FF;
    --color-text-muted: #9D86C4;
    --color-glass-bg: rgba(30, 20, 50, 0.85);
    --color-glass-border: rgba(150, 100, 255, 0.2);
    --font-display: 'Bebas Neue', sans-serif;
    --font-body: 'Chakra Petch', sans-serif;
}
"""

st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Chakra+Petch:wght@400;500;600;700&display=swap');

    {css_root}

    .stApp {{
        background-color: var(--color-bg-deep) !important;
        background-image:
            radial-gradient(circle at 20% 30%, rgba(124, 58, 237, 0.12), transparent 40%),
            radial-gradient(circle at 80% 70%, rgba(168, 85, 247, 0.08), transparent 40%) !important;
    }}

    h1, h2, h3, p, div, span, label, .stMarkdown, .stText {{
        font-family: var(--font-body);
        color: var(--color-text-main) !important;
    }}

    /* Força o fundo escuro nos inputs Streamlit */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stSelectbox > div > div {{
        background-color: rgba(30, 20, 50, 0.9) !important;
        color: var(--color-text-main) !important;
        border-color: var(--color-glass-border) !important;
    }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
    /* Ocultar header padrão e ajustar padding */
    header { background: transparent !important; }

    /* Header principal */
    .fut-header {
        background: var(--color-glass-bg);
        padding: 3rem;
        border-radius: 20px;
        margin-bottom: 2rem;
        display: flex;
        align-items: center;
        gap: 2rem;
        border: 1px solid var(--color-glass-border);
        box-shadow: 0 0 30px rgba(0,0,0,0.1), inset 0 0 20px rgba(178, 102, 255, 0.05);
        backdrop-filter: blur(16px);
        position: relative;
        overflow: hidden;
    }
    .fut-header::after {
        content: '';
        position: absolute;
        top: 0; left: 0; width: 100%; height: 2px;
        background: linear-gradient(90deg, transparent, var(--color-neon-g), transparent);
        opacity: 0.5;
    }
    .fut-header h1 {
        font-family: var(--font-display);
        font-size: 4.5rem;
        color: var(--color-text-main);
        letter-spacing: 5px;
        margin: 0;
        line-height: 1;
        text-shadow: 0 0 15px rgba(255,255,255,0.3);
    }
    .fut-header p {
        color: var(--color-text-muted);
        margin: 0.5rem 0 0;
        font-size: 1.1rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* Cards de stat / Dashboard */
    .stat-card {
        background: var(--color-glass-bg);
        border: 1px solid var(--color-glass-border);
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        backdrop-filter: blur(12px);
        position: relative;
        overflow: hidden;
    }
    .stat-card::before {
        content: '';
        position: absolute;
        bottom: 0; left: 0; width: 100%; height: 2px;
        background: var(--color-neon-g);
        transform: scaleX(0);
        transition: transform 0.3s ease;
    }
    .stat-card:hover { 
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
        border-color: rgba(178, 102, 255, 0.3);
    }
    .stat-card:hover::before { transform: scaleX(1); }
    
    .stat-card .value {
        font-family: var(--font-display);
        font-size: 3.5rem;
        color: var(--color-text-main);
        line-height: 1;
        text-shadow: 0 0 15px rgba(255,255,255,0.2);
    }
    .stat-card .label {
        font-family: var(--font-body);
        font-size: 0.85rem;
        color: var(--color-text-muted);
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-top: 0.5rem;
        font-weight: 700;
    }

    /* Times sorteados - Dark Card */
    .team-card {
        background: rgba(25, 15, 45, 0.9);
        border-radius: 16px;
        padding: 1rem;
        backdrop-filter: blur(12px);
        position: relative;
    }
    .team-a { border: 1px solid rgba(124, 58, 237, 0.5); }
    .team-b { border: 1px solid rgba(168, 85, 247, 0.4); }
    
    .team-header {
        font-family: var(--font-display);
        font-size: 1.4rem;
        letter-spacing: 3px;
        margin-bottom: 0.8rem;
        text-transform: uppercase;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }
    .team-a .team-header { color: #A78BFA; }
    .team-b .team-header { color: #C4B5FD; }

    /* Player row dark */
    .player-pill {
        background: rgba(30, 20, 55, 0.7);
        border: 1px solid rgba(120, 80, 220, 0.2);
        border-left: 3px solid var(--color-neon-g);
        border-radius: 8px;
        padding: 0.5rem 0.7rem;
        margin: 0.3rem 0;
        font-size: 0.88rem;
        color: var(--color-text-main);
        font-weight: 600;
    }
    .player-pill .nivel {
        background: var(--color-neon-g);
        color: #fff;
        border-radius: 4px;
        padding: 0.1rem 0.4rem;
        font-size: 0.7rem;
        font-weight: 700;
    }
    .player-pill-b { border-left-color: var(--color-neon-b); }
    .player-pill-b .nivel { background: var(--color-neon-b); }

    /* Botões de ação compactos por jogador (Gol / Assist / Cartão) */
    .action-btn {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.2rem 0.55rem;
        border-radius: 6px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid;
        cursor: pointer;
        transition: all 0.15s;
        margin-right: 0.2rem;
        text-decoration: none;
    }
    .btn-gol  { background: rgba(34,197,94,0.15);  border-color: #22C55E; color: #86EFAC; }
    .btn-assist { background: rgba(124,58,237,0.15); border-color: #7C3AED; color: #C4B5FD; }
    .btn-cartao { background: rgba(234,179,8,0.15);  border-color: #CA8A04; color: #FDE68A; }

    /* Cronômetro Arena */
    .cronometro {
        font-family: var(--font-display);
        font-size: 7rem;
        color: var(--color-neon-g);
        text-align: center;
        letter-spacing: 12px;
        line-height: 1;
        padding: 1rem 0;
        text-shadow: 0 0 10px rgba(178, 102, 255, 0.3);
        margin: 0.5rem 0;
    }
    .cronometro.urgente { 
        color: #FF2A2A; 
        text-shadow: 0 0 15px rgba(255, 42, 42, 0.5);
        animation: pulse_neon 1s infinite;
    }
    @keyframes pulse_neon {
        0%, 100% { opacity: 1; text-shadow: 0 0 15px rgba(255, 42, 42, 0.5); }
        50% { opacity: 0.6; text-shadow: 0 0 30px rgba(255, 42, 42, 0.8); }
    }

    /* Metric placar overrides */
    [data-testid="metric-container"] {
        background: var(--color-glass-bg);
        border: 1px solid var(--color-glass-border);
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        backdrop-filter: blur(8px);
    }
    [data-testid="metric-container"] label {
        color: var(--color-text-muted) !important;
        font-family: var(--font-body);
        font-weight: 700;
        letter-spacing: 2px;
    }
    [data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: var(--color-text-main) !important;
        font-family: var(--font-display);
        font-size: 3rem !important;
    }

    /* Ranking table */
    .rank-row {
        display: flex;
        align-items: center;
        padding: 0.8rem 1.2rem;
        border-radius: 8px;
        margin-bottom: 0.5rem;
        background: var(--color-glass-bg);
        border: 1px solid var(--color-glass-border);
        gap: 1.5rem;
        transition: all 0.2s;
    }
    .rank-row:hover {
        background: var(--color-bg-deep);
        border-color: rgba(255,255,255,0.3);
        transform: translateX(5px);
    }
    .rank-pos {
        font-family: var(--font-display);
        font-size: 1.5rem;
        color: var(--color-text-muted);
        width: 2.5rem;
        text-align: center;
    }
    .rank-pos.top { 
        color: #FFD700; 
        text-shadow: 0 0 10px rgba(255, 215, 0, 0.5);
    }
    .rank-nome { 
        flex: 1; 
        font-weight: 600; 
        color: var(--color-text-main); 
        letter-spacing: 1px;
    }
    .nivel-badge {
        padding: 0.2rem 0.8rem;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 2px;
    }
    .nivel-5 { background: var(--color-neon-g); color: var(--color-bg-deep); box-shadow: 0 0 10px rgba(178, 102, 255, 0.5); }
    .nivel-4 { background: #64DD17; color: var(--color-bg-deep); }
    .nivel-3 { background: #FFD600; color: var(--color-bg-deep); }
    .nivel-2 { background: #FF6D00; color: var(--color-bg-deep); }
    .nivel-1 { background: #FF2A2A; color: var(--color-bg-deep); box-shadow: 0 0 10px rgba(255, 42, 42, 0.5); }

    /* Sidebar escura */
    [data-testid="stSidebar"] {
        background-color: #080512 !important;
        border-right: 1px solid rgba(120,80,220,0.2);
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] div, [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stMarkdown {
        color: #E9D5FF !important;
    }

    /* Botões padrão dark */
    .stButton > button {
        background: rgba(30, 20, 55, 0.9) !important;
        color: #C4B5FD !important;
        border: 1px solid rgba(124, 58, 237, 0.6) !important;
        border-radius: 8px !important;
        font-family: var(--font-body) !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button:hover {
        background: var(--color-neon-g) !important;
        color: #FFFFFF !important;
        border-color: var(--color-neon-g) !important;
        transform: translateY(-2px);
    }
    /* Botão Primary */
    .stButton > button[data-testid="baseButton-primary"] {
        background: var(--color-neon-g) !important;
        border: none !important;
        color: #FFFFFF !important;
    }
    .stButton > button[data-testid="baseButton-primary"]:hover {
        background: var(--color-neon-b) !important;
        transform: translateY(-2px);
    }

    /* Tabs compactas escuras */
    .stTabs [data-baseweb="tab-list"] {
        background: transparent !important;
        gap: 0.2rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: rgba(25, 15, 50, 0.7) !important;
        color: var(--color-text-muted) !important;
        font-family: var(--font-body);
        font-size: 0.85rem !important;
        font-weight: 600;
        padding: 0.4rem 1rem !important;
        border-radius: 8px 8px 0 0 !important;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(124, 58, 237, 0.25) !important;
        color: #C4B5FD !important;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: var(--color-neon-g) !important;
    }

    /* Divider */
    hr {
        border-color: var(--color-glass-border) !important;
        margin: 2rem 0 !important;
    }
    .stDivider {
        border-color: var(--color-glass-border) !important;
    }

    /* Tabelas e Dataframes (Gestão de Jogadores / Histórico) - Hardcoded variables to pierce Shadow DOMs */
    [data-testid="stDataFrame"] div, 
    [data-testid="stDataFrame"] span,
    [data-testid="stTable"] div,
    [data-testid="stTable"] span,
    table, th, td {
        color: {hex_text} !important;
        border-color: {hex_glass_border} !important;
    }
    
    [data-testid="stDataFrame"] {
        background-color: {hex_glass_bg} !important;
    }

    /* Force Table cells background transparent so it inherits */
    [data-testid="stDataFrame"] [data-testid="stTable"] th,
    [data-testid="stDataFrame"] [data-testid="stTable"] td,
    [data-testid="stDataFrame"] [class*="StyledTableCell"] {
        background-color: transparent !important;
    }
    
    [data-testid="stDataFrame"] [data-testid="stTable"] th {
        background-color: {hex_glass_bg} !important;
        color: {hex_text} !important;
        font-family: var(--font-display) !important;
        letter-spacing: 1px;
    }

    /* =========================================
       RESPONSIVIDADE (Mobile First Optimization)
       ========================================= */
    @media (max-width: 768px) {
        .fut-header {
            flex-direction: column;
            text-align: center;
            padding: 2rem 1rem;
            gap: 1rem;
        }
        .fut-header h1 {
            font-size: 2.5rem;
            letter-spacing: 2px;
        }
        .fut-header p {
            font-size: 0.9rem;
        }
        .stat-card {
            padding: 1rem;
        }
        .stat-card .value {
            font-size: 2rem;
        }
        .stat-card .label {
            font-size: 0.75rem;
        }
        .cronometro {
            font-size: 2.5rem;
            letter-spacing: 4px;
            padding: 0.5rem 0;
            margin: 0;
        }
        .team-header {
            font-size: 1.8rem;
        }
        .team-card {
            padding: 1rem;
        }
        .player-pill {
            font-size: 0.85rem;
            padding: 0.5rem;
        }
        .rank-pos {
            font-size: 1.2rem;
            width: 1.5rem;
        }
        [data-testid="metric-container"] div[data-testid="stMetricValue"] {
            font-size: 2rem !important;
        }
    }

</style>
""", unsafe_allow_html=True)



# ─────────────────────── HELPERS ───────────────────────

def nivel_badge(nivel: int) -> str:
    estrelas = "★" * nivel + "☆" * (5 - nivel)
    return f'<span class="nivel-badge nivel-{nivel}">{estrelas}</span>'


def formatar_tempo(segundos: int) -> str:
    m = segundos // 60
    s = segundos % 60
    return f"{m:02d}:{s:02d}"


def tempo_decorrido() -> int:
    if st.session_state.tempo_inicio is None:
        return 0
    return int(time.time() - st.session_state.tempo_inicio)


def tempo_restante() -> int:
    decorrido = tempo_decorrido()
    return max(0, st.session_state.tempo_total_seg - decorrido)


# ─────────────────────── SIDEBAR ───────────────────────

with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding: 1rem 0;">
        <div style="font-family:var(--font-display); font-size:2.5rem; color:var(--color-neon-g); letter-spacing:4px; text-shadow:0 0 15px var(--color-neon-g);">
            🐘 PHP UNITED
        </div>
        <div style="color:var(--color-text-muted); font-size:0.9rem; font-family:var(--font-body); font-weight:700; letter-spacing:3px;">PRO MVP v1.0</div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Handle Redirect before instantiating the widget
    if st.session_state.get('redirect_to'):
        st.session_state['pagina_atual'] = st.session_state['redirect_to']
        del st.session_state['redirect_to']

    pagina = st.radio(
        "Navegar",
        ["🏠 Dashboard", "📋 Gestão de Jogadores", "🎲 Sorteio de Times", "⚽ Partida ao Vivo", "📊 Ranking & Stats"],
        label_visibility="collapsed",
        key="pagina_atual"
    )

    st.divider()

    # Status partida ativa
    if st.session_state.partida_ativa:
        st.success(f"**Partida #{st.session_state.partida_ativa} ativa**")
        st.write(f"🟢 {st.session_state.gols_a} × {st.session_state.gols_b} 🔵")
    else:
        st.info("Nenhuma partida ativa")

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("PHP United FutebolManager © 2025")


# ─────────────────────── PAGES ───────────────────────

# ── DASHBOARD ──
if pagina == "🏠 Dashboard":
    st.markdown("""
    <div class="fut-header">
        <div style="font-size:4rem;">🐘</div>
        <div>
            <h1>PHP UNITED</h1>
            <p>Futebol Manager Oficial do PHP United</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    jogadores = db.get_jogadores()
    partidas = db.get_partidas()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="stat-card">
            <div class="value">{len(jogadores)}</div>
            <div class="label">Jogadores Ativos</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        goleiros = len(jogadores[jogadores["posicao"] == "Goleiro"]) if not jogadores.empty else 0
        st.markdown(f"""
        <div class="stat-card">
            <div class="value">{goleiros}</div>
            <div class="label">Goleiros</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        total_partidas = len(partidas)
        st.markdown(f"""
        <div class="stat-card">
            <div class="value">{total_partidas}</div>
            <div class="label">Partidas Registradas</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        hoje = datetime.now().strftime("%d/%m")
        dia_sem = ["Seg","Ter","Qua","Qui","Sex","Sáb","Dom"][datetime.now().weekday()]
        st.markdown(f"""
        <div class="stat-card">
            <div class="value">{hoje}</div>
            <div class="label">{dia_sem} — Hoje</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<hr class='verde-line'>", unsafe_allow_html=True)

    col_a, col_b = st.columns([2, 1])
    with col_a:
        st.subheader("🗓️ Próximas sessões")
        agora = datetime.now()
        dia_semana = agora.weekday()

        sessoes = [
            {"dia": "Quarta-feira", "horario": "18:00 – 19:00", "icone": "🌆"},
            {"dia": "Sábado", "horario": "09:00 – 11:15", "icone": "☀️"},
        ]
        for s in sessoes:
            st.markdown(f"""
            <div style="background:var(--color-glass-bg); border:1px solid var(--color-glass-border); border-left:3px solid var(--color-neon-g); border-radius:10px; padding:1.2rem; margin-bottom:0.8rem; display:flex; align-items:center; gap:1.5rem; backdrop-filter:blur(8px); transition:all 0.3s ease;">
                <div style="font-size:2.5rem; text-shadow:0 0 15px rgba(255,255,255,0.2);">{s['icone']}</div>
                <div>
                    <div style="font-weight:700; color:var(--color-text-main); font-size:1.1rem; letter-spacing:1px;">{s['dia']}</div>
                    <div style="color:var(--color-neon-g); font-size:0.9rem; font-weight:600; text-shadow:0 0 5px rgba(178,102,255,0.5);">⏰ {s['horario']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    with col_b:
        st.subheader("🏆 Top 3 Jogadores")
        ranking = db.calcular_ranking()
        if not ranking.empty:
            medais = ["🥇", "🥈", "🥉"]
            for i, (_, row) in enumerate(ranking.head(3).iterrows()):
                st.markdown(f"""
                <div style="background:var(--color-glass-bg); border:1px solid var(--color-glass-border); border-radius:8px; padding:0.8rem 1.2rem; margin-bottom:0.5rem; display:flex; align-items:center; box-shadow:0 0 10px rgba(0,0,0,0.3); backdrop-filter:blur(5px); transition:transform 0.2s;">
                    <span style="font-size:1.5rem; margin-right:1rem;">{medais[i]}</span>
                    <strong style="color:var(--color-text-main); font-size:1.1rem; letter-spacing:1px; flex:1;">{row['nome']}</strong>
                    <span style="color:var(--color-neon-g); font-weight:700; text-shadow:0 0 5px rgba(178,102,255,0.3);">Nível {row['nivel']}</span>
                </div>
                """, unsafe_allow_html=True)

    # Histórico recente
    if not partidas.empty:
        st.markdown("<hr class='verde-line'>", unsafe_allow_html=True)
        st.subheader("📜 Histórico de Partidas")
        partidas_show = partidas[["id", "data", "dia_semana", "score_a", "score_b", "status"]].head(10).copy()
        partidas_show.columns = ["ID", "Data", "Dia", "Gols Time A", "Gols Time B", "Status"]
        # Convertendo id para string para evitar formatação com vírgula de milhar (se for int)
        partidas_show['ID'] = partidas_show['ID'].astype(str)
        st.table(partidas_show.set_index('ID'))


# ── GESTÃO DE JOGADORES ──
elif pagina == "📋 Gestão de Jogadores":
    st.title("📋 Gestão de Jogadores")

    tab_lista, tab_add, tab_edit = st.tabs(["Lista Completa", "Adicionar Jogador", "Editar / Ativar"])

    with tab_lista:
        jogadores = db.get_jogadores(apenas_ativos=False)
        if jogadores.empty:
            st.info("Nenhum jogador cadastrado.")
        else:
            filtro_pos = st.selectbox("Filtrar por posição", ["Todos", "Linha", "Goleiro"])
            filtro_ativo = st.checkbox("Apenas ativos", value=True)

            df = jogadores.copy()
            if filtro_pos != "Todos":
                df = df[df["posicao"] == filtro_pos]
            if filtro_ativo:
                df = df[df["ativo"] == 1]

            st.markdown(f"**{len(df)} jogadores** encontrados")
            
            df_table = df[["id", "nome", "nivel", "posicao", "gols_total", "assistencias_total", "jogos_total", "vitorias_total"]].copy()
            df_table.columns = ["ID", "Nome", "Nível", "Posição", "Gols", "Assists", "Jogos", "Vitórias"]
            df_table['ID'] = df_table['ID'].astype(str)
            st.table(df_table.set_index("ID"))

    with tab_add:
        with st.form("form_add_jogador"):
            nome = st.text_input("Nome do jogador *")
            col1, col2 = st.columns(2)
            with col1:
                nivel = st.slider("Nível técnico", 1, 5, 3, help="1=Iniciante, 5=Craque")
            with col2:
                posicao = st.selectbox("Posição", ["Linha", "Goleiro"])

            st.markdown(f"**Nível selecionado:** {'★' * nivel + '☆' * (5-nivel)}")

            submitted = st.form_submit_button("✅ Adicionar Jogador", use_container_width=True, type="primary")
            if submitted:
                if not nome.strip():
                    st.error("Nome é obrigatório.")
                else:
                    ok = db.upsert_jogador(nome.strip(), nivel, posicao)
                    if ok:
                        st.success(f"Jogador **{nome}** adicionado com sucesso!")
                        st.balloons()
                    else:
                        st.error("Erro ao adicionar (nome pode já existir).")

    with tab_edit:
        jogadores_todos = db.get_jogadores(apenas_ativos=False)
        if jogadores_todos.empty:
            st.info("Nenhum jogador.")
        else:
            opcoes = {f"{row['nome']} (ID:{row['id']})": row["id"] for _, row in jogadores_todos.iterrows()}
            selecionado_label = st.selectbox("Selecionar jogador", list(opcoes.keys()))
            jid = opcoes[selecionado_label]
            jogador = db.get_jogador_by_id(jid)

            if jogador:
                with st.form("form_edit"):
                    nome_edit = st.text_input("Nome", value=jogador["nome"])
                    col1, col2 = st.columns(2)
                    with col1:
                        nivel_edit = st.slider("Nível", 1, 5, int(jogador["nivel"]))
                    with col2:
                        pos_edit = st.selectbox("Posição", ["Linha", "Goleiro"],
                                                index=0 if jogador["posicao"] == "Linha" else 1)
                    col_s, col_t = st.columns(2)
                    with col_s:
                        salvar = st.form_submit_button("💾 Salvar", use_container_width=True, type="primary")
                    with col_t:
                        toggle = st.form_submit_button(
                            "🔴 Desativar" if jogador["ativo"] else "🟢 Ativar",
                            use_container_width=True
                        )

                    if salvar:
                        db.upsert_jogador(nome_edit, nivel_edit, pos_edit, jid)
                        st.success("Atualizado!")
                        st.rerun()
                    if toggle:
                        db.toggle_jogador_ativo(jid)
                        st.success("Status alterado!")
                        st.rerun()


# ── SORTEIO DE TIMES ──
elif pagina == "🎲 Sorteio de Times":
    st.title("🎲 Sorteio de Times Equilibrados")

    jogadores = db.get_jogadores()
    if jogadores.empty:
        st.warning("Nenhum jogador ativo cadastrado.")
        st.stop()

    st.subheader("1️⃣ Selecionar Presentes")
    st.caption("Selecione no mínimo 14 jogadores (2 goleiros + 12 de linha). Pode ter reservas!")

    col_linha, col_goleiro = st.columns([3, 1])

    with col_goleiro:
        st.markdown("**🧤 Goleiros**")
        goleiros_df = jogadores[jogadores["posicao"] == "Goleiro"]
        goleiros_presentes = []
        for _, g in goleiros_df.iterrows():
            if st.checkbox(g["nome"], key=f"gol_{g['id']}"):
                goleiros_presentes.append(g.to_dict())

    with col_linha:
        st.markdown("**👟 Jogadores de Linha**")
        linha_df = jogadores[jogadores["posicao"] == "Linha"]
        linha_presentes = []
        cols = st.columns(3)
        for i, (_, j) in enumerate(linha_df.iterrows()):
            with cols[i % 3]:
                if st.checkbox(f"{j['nome']} {'★'*int(j['nivel'])}", key=f"lin_{j['id']}"):
                    linha_presentes.append(j.to_dict())

    todos_presentes = goleiros_presentes + linha_presentes
    validacao = logic.validar_presenca(todos_presentes)

    st.divider()
    if validacao["valido"]:
        st.success(validacao["mensagem"])
    else:
        st.warning(validacao["mensagem"])

    st.markdown(f"Selecionados: **{len(goleiros_presentes)} goleiros** | **{len(linha_presentes)} de linha** | Total: {len(todos_presentes)}")

    col_btn, col_info = st.columns([1, 2])
    with col_btn:
        sortear = st.button(
            "⚡ SORTEAR TIMES",
            use_container_width=True,
            type="primary",
            disabled=not validacao["valido"],
        )

    if sortear and validacao["valido"]:
        with st.spinner("Calculando combinação ideal..."):
            tamanho_time_dinamico = len(linha_presentes) // 2
            time_a, time_b, dif = logic.selecionar_algoritmo(linha_presentes, tamanho_time=tamanho_time_dinamico)
            st.session_state.time_a = time_a
            st.session_state.time_b = time_b
            st.session_state.goleiro_a = goleiros_presentes[0] if goleiros_presentes else None
            st.session_state.goleiro_b = goleiros_presentes[1] if len(goleiros_presentes) > 1 else None

    if st.session_state.time_a and st.session_state.time_b:
        summary = logic.summary_times(st.session_state.time_a, st.session_state.time_b)

        # Exibir resultado
        st.markdown("---")
        st.subheader("2️⃣ Times Sorteados")

        equil_badge = "✅ Perfeitamente equilibrado!" if summary["equilibrado"] else f"⚠️ Diferença: {summary['diferenca']} ponto(s)"
        st.markdown(f"**{equil_badge}**")

        col_a, col_sep, col_b = st.columns([5, 1, 5])

        with col_a:
            st.markdown(f"""
            <div class="team-card team-a">
                <div class="team-header">🟢 TIME A</div>
                <div style="color:#6B21A8;font-size:0.9rem;margin-bottom:1rem;font-weight:600;">
                    Score Total: <strong>{summary['score_a']}</strong> | Média: {summary['media_a']}
                </div>
                <div style="margin-bottom:0.5rem;color:#666;font-size:0.85rem;font-weight:600;">🧤 GOLEIRO</div>
                <div class="player-pill">{st.session_state.goleiro_a['nome'] if st.session_state.goleiro_a else 'N/D'}</div>
                <div style="margin:0.8rem 0 0.5rem;color:#666;font-size:0.85rem;font-weight:600;">👟 LINHA</div>
            """, unsafe_allow_html=True)
            for j in st.session_state.time_a:
                st.markdown(f'<div class="player-pill">{j["nome"]} <span class="nivel">N{j["nivel"]}</span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col_sep:
            st.markdown("<div style='display:flex;align-items:center;justify-content:center;height:100%;font-family:var(--font-display);font-size:3rem;color:var(--color-text-muted);text-shadow:0 0 10px rgba(255,255,255,0.1);padding-top:5rem;'>VS</div>", unsafe_allow_html=True)

        with col_b:
            st.markdown(f"""
            <div class="team-card team-b">
                <div class="team-header">🔵 TIME B</div>
                <div style="color:var(--color-text-muted);font-size:0.9rem;margin-bottom:1rem;font-weight:600;letter-spacing:1px;">
                    Score Total: <strong>{summary['score_b']}</strong> | Média: {summary['media_b']}
                </div>
                <div style="margin-bottom:0.5rem;color:var(--color-neon-b);font-family:var(--font-display);font-size:0.8rem;letter-spacing:2px;">🧤 GOLEIRO</div>
                <div class="player-pill player-pill-b">{st.session_state.goleiro_b['nome'] if st.session_state.goleiro_b else 'N/D'}</div>
                <div style="margin:1rem 0 0.5rem;color:var(--color-neon-b);font-family:var(--font-display);font-size:0.8rem;letter-spacing:2px;">👟 LINHA</div>
            """, unsafe_allow_html=True)
            for j in st.session_state.time_b:
                st.markdown(f'<div class="player-pill player-pill-b">{j["nome"]} <span class="nivel">N{j["nivel"]}</span></div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        st.divider()
        st.subheader("3️⃣ Iniciar Partida")
        
        col_data, col_dia, col_ini = st.columns([2, 2, 1])
        with col_data:
            data_partida = st.date_input("Data", value=date.today())
        with col_dia:
            dia_semana_op = st.selectbox("Sessão", ["Quarta-feira", "Sábado"])
        with col_ini:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🟢 Iniciar", type="primary", use_container_width=True, key="btn_iniciar_partida"):
                ids_a = [j["id"] for j in st.session_state.time_a]
                ids_b = [j["id"] for j in st.session_state.time_b]
                pid = db.criar_partida(
                    data=data_partida.strftime("%Y-%m-%d"),
                    dia_semana=dia_semana_op,
                    time_a_ids=ids_a,
                    time_b_ids=ids_b,
                )
                st.session_state.partida_ativa = pid
                st.session_state.gols_a = 0
                st.session_state.gols_b = 0
                st.session_state.cronometro_rodando = False
                st.session_state.tempo_inicio = None
                st.success(f"✅ Partida #{pid} criada! Vá para **Partida ao Vivo**.")
                st.balloons()
                time.sleep(1)
                st.session_state['redirect_to'] = "⚽ Partida ao Vivo"
                st.rerun()


# ── PARTIDA AO VIVO ──
elif pagina == "⚽ Partida ao Vivo":
    st.title("⚽ Partida ao Vivo")

    if not st.session_state.partida_ativa:
        st.warning("Nenhuma partida ativa. Vá até **Sorteio de Times** para iniciar uma.")
        st.stop()

    pid = st.session_state.partida_ativa
    partida = db.get_partida(pid)

    if not partida or partida["status"] == "finalizada":
        st.info("Esta partida já foi finalizada.")
        if st.button("Limpar partida ativa"):
            st.session_state.partida_ativa = None
            st.rerun()
        st.stop()

    # ── HEADER DO PLACAR (ESTILO SOFASCORE) ──
    restante = tempo_restante() if st.session_state.cronometro_rodando or st.session_state.tempo_inicio else st.session_state.tempo_total_seg
    urgente = restante <= 120
    badge_bg = "#FF2A2A" if urgente else "var(--color-neon-b)"
    
    st.markdown(f"""
    <div style="background: var(--color-glass-bg); border-radius: 16px; padding: 1.5rem 1rem; margin-bottom: 2rem; border: 1px solid var(--color-glass-border); box-shadow: 0 4px 15px rgba(0,0,0,0.1);">
        <div style="text-align: center; margin-bottom: 1rem;">
            <span style="background: {badge_bg}; color: #fff; padding: 0.3rem 1rem; border-radius: 20px; font-weight: 700; font-size: 0.9rem; letter-spacing: 1px; {'animation: pulse_neon 1s infinite;' if urgente else ''}">
                {formatar_tempo(restante)}
            </span>
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div style="text-align: center; flex: 1;">
                <div style="font-size: 3rem; margin-bottom: 0.5rem; filter: drop-shadow(0 0 10px var(--color-neon-g));">🛡️</div>
                <div style="color: var(--color-text-main); font-weight: 700; font-size: 1.2rem; letter-spacing: 1px;">TIME A</div>
            </div>
            <div style="text-align: center; flex: 1;">
                <div style="font-family: var(--font-display); font-size: 4rem; color: var(--color-text-main); line-height: 1;">
                    {st.session_state.gols_a} - {st.session_state.gols_b}
                </div>
            </div>
            <div style="text-align: center; flex: 1;">
                <div style="font-size: 3rem; margin-bottom: 0.5rem; filter: drop-shadow(0 0 10px var(--color-neon-b));">🦅</div>
                <div style="color: var(--color-text-main); font-weight: 700; font-size: 1.2rem; letter-spacing: 1px;">TIME B</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.cronometro_rodando:
        st_autorefresh(interval=1000, key="cronometro_refresh")


    # ── ABAS (TABS) ──
    tab_partida, tab_escalacao, tab_stats = st.tabs(["Partida", "Escalações", "Estatísticas"])

    # ABA 1: PARTIDA (Controles e Log)
    with tab_partida:
        st.subheader("⏱️ Controles de Jogo")
        col_ctrl = st.columns([1.5, 1, 1])
        
        with col_ctrl[0]:
            duracao_min = st.number_input("Duração (min)", min_value=5, max_value=90, value=45, step=5, key="duracao_partida_inp")
            st.session_state.tempo_total_seg = duracao_min * 60

        with col_ctrl[1]:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("▶️ Iniciar / ⏸️ Pausar", use_container_width=True):
                if not st.session_state.cronometro_rodando:
                    if st.session_state.tempo_inicio is None:
                        st.session_state.tempo_inicio = time.time()
                    st.session_state.cronometro_rodando = True
                else:
                    st.session_state.cronometro_rodando = False

        with col_ctrl[2]:
            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔄 Resetar Temp.", use_container_width=True):
                st.session_state.cronometro_rodando = False
                st.session_state.tempo_inicio = None

        # Feed de scouts
        st.divider()
        st.subheader("📋 Feed de Eventos")
        scouts = db.get_scouts_partida(pid)
        if not scouts.empty:
            for _, s in scouts.iterrows():
                icone = "⚽" if s["tipo"] == "gol" else "🅰️"
                cor = "var(--color-neon-g)" if s["time"] == "A" else "var(--color-neon-b)"
                time_label = "A" if s["time"] == "A" else "B"
                st.markdown(
                    f'<div style="background:var(--color-glass-bg); border-left:4px solid {cor}; border-radius:6px; padding:0.6rem 1rem; margin-bottom:0.4rem; font-size: 0.95rem;">'
                    f'<span style="font-size:1.1rem; margin-right: 0.5rem;">{icone}</span> <strong style="color:var(--color-text-main);">{s["jogador_nome"]}</strong> '
                    f'<span style="color:var(--color-text-muted); float: right; font-size:0.8rem;">Time {time_label}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("Nenhum evento registrado nesta partida ainda.")

        # FINALIZAR
        st.divider()
        if st.button("🏁 FINALIZAR PARTIDA", type="primary", use_container_width=True):
            db.finalizar_partida(pid, st.session_state.gols_a, st.session_state.gols_b)
            st.session_state.cronometro_rodando = False
            st.session_state.partida_ativa = None
            st.success("✅ Partida finalizada! Ranking atualizado.")
            st.balloons()
            time.sleep(2)
            st.rerun()

    # ABA 2: ESCALAÇÕES E SCOUTS RÁPIDOS
    with tab_escalacao:
        st.markdown("<h3 style='margin-bottom: 2rem;'>Escalações & Adicionar Eventos</h3>", unsafe_allow_html=True)
        
        col_sa, col_sb = st.columns(2)
        
        def render_lineup(time_jogadores: list, time_key: str, color_hex: str):
            st.markdown(f"**TIME {time_key}**", unsafe_allow_html=True)
            if not time_jogadores:
                return
                
            for j in time_jogadores:
                c1, c2, c3 = st.columns([2.5, 1, 1])
                # Botões super compactos para adicionar gol ou assistência sem form
                c1.markdown(f"<div style='padding-top:0.4rem; font-size: 0.95rem; font-weight: 500;'>{j['nome']}</div>", unsafe_allow_html=True)
                
                if c2.button("⚽", key=f"btn_gol_{time_key}_{j['id']}", help=f"Gol para {j['nome']}"):
                    db.registrar_scout(partida_id=pid, jogador_id=j['id'], tipo="gol", time=time_key)
                    if time_key == "A":
                        st.session_state.gols_a += 1
                    else:
                        st.session_state.gols_b += 1
                    st.rerun()
                
                if c3.button("🅰️", key=f"btn_ass_{time_key}_{j['id']}", help=f"Assistência para {j['nome']}"):
                    db.registrar_scout(partida_id=pid, jogador_id=j['id'], tipo="assistencia", time=time_key)
                    st.rerun()
                    
                st.markdown("<hr style='margin: 0.2rem 0; border-color: rgba(255,255,255,0.05);'>", unsafe_allow_html=True)

        with col_sa:
            render_lineup(st.session_state.time_a, "A", "#6B21A8")
        with col_sb:
            render_lineup(st.session_state.time_b, "B", "#536DFE")

    # ABA 3: ESTATÍSTICAS
    with tab_stats:
        st.markdown("<h3 style='margin-bottom: 2rem;'>Estatísticas do Jogo</h3>", unsafe_allow_html=True)
        
        # Gerando dados simulados com base nos gols para ficar visualmente estimulante
        import random
        random.seed(pid) # Semente fixa por partida pra não piscar
        
        total_gols = st.session_state.gols_a + st.session_state.gols_b
        chutes_a = st.session_state.gols_a * 3 + random.randint(2, 6)
        chutes_b = st.session_state.gols_b * 3 + random.randint(2, 6)
        
        posse_a = 50 + (chutes_a - chutes_b) * 2
        posse_a = max(20, min(80, posse_a))
        posse_b = 100 - posse_a
        
        esc_a = int(chutes_a / 2) + random.randint(0, 3)
        esc_b = int(chutes_b / 2) + random.randint(0, 3)

        def render_stat_bar(label: str, val_a: int, val_b: int, is_percent: bool = False):
            total = val_a + val_b if (val_a + val_b) > 0 else 1
            pct_a = (val_a / total) * 100
            pct_b = (val_b / total) * 100
            
            sufixo = "%" if is_percent else ""
            
            st.markdown(f"""
            <div style="margin-bottom: 1.5rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.9rem; font-weight: 600; margin-bottom: 0.3rem;">
                    <span>{val_a}{sufixo}</span>
                    <span style="color: var(--color-text-muted);">{label}</span>
                    <span>{val_b}{sufixo}</span>
                </div>
                <div style="display: flex; height: 8px; border-radius: 4px; overflow: hidden; background: #333;">
                    <div style="width: {pct_a}%; background: var(--color-neon-g);"></div>
                    <div style="width: {pct_b}%; background: var(--color-neon-b);"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        render_stat_bar("Posse de Bola", posse_a, posse_b, True)
        render_stat_bar("Total de Chutes", chutes_a, chutes_b)
        render_stat_bar("Chutes no Gol", st.session_state.gols_a + random.randint(0, 3), st.session_state.gols_b + random.randint(0, 3))
        render_stat_bar("Escanteios", esc_a, esc_b)
        render_stat_bar("Faltas", random.randint(3, 10), random.randint(3, 10))


# ── RANKING & STATS ──
elif pagina == "📊 Ranking & Stats":
    st.title("📊 Ranking & Estatísticas")

    ranking = db.calcular_ranking()

    if ranking.empty:
        st.info("Nenhum dado de ranking disponível.")
        st.stop()

    # Top Cards
    if len(ranking) >= 3:
        col1, col2, col3 = st.columns(3)
        for col, i, medal, cor in [
            (col1, 0, "🥇", "#FFD700"),
            (col2, 1, "🥈", "#C0C0C0"),
            (col3, 2, "🥉", "#CD7F32"),
        ]:
            row = ranking.iloc[i]
            with col:
                st.markdown(f"""
                <div style="background:var(--color-glass-bg); border:1px solid var(--color-glass-border); border-top:3px solid {cor}; border-radius:12px; padding:1.5rem; text-align:center; box-shadow:0 10px 30px rgba(0,0,0,0.4); backdrop-filter:blur(8px); transition:transform 0.3s;">
                    <div style="font-size:2.5rem; text-shadow:0 0 15px {cor};">{medal}</div>
                    <div style="font-weight:700; font-size:1.3rem; color:var(--color-text-main); margin:0.8rem 0; letter-spacing:1px;">{row['nome']}</div>
                    <div style="color:{cor}; font-family:var(--font-display); font-size:1.8rem; text-shadow:0 0 5px {cor};">Nível {row['nivel']}</div>
                    <div style="color:var(--color-text-muted); font-size:0.9rem; margin-top:0.8rem; font-weight:600; font-family:var(--font-body);">
                        ⚽ {int(row['gols_total'])} gols | 🅰️ {int(row['assistencias_total'])} assists
                    </div>
                    <div style="color:var(--color-neon-g); font-size:0.9rem; font-weight:700; margin-top:0.3rem; text-shadow:0 0 5px var(--color-neon-g);">
                        Win Rate: {row['win_rate']*100:.0f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("<hr class='verde-line'>", unsafe_allow_html=True)

    # Ranking completo
    st.subheader("📋 Ranking Completo")
    medais_map = {0: "🥇", 1: "🥈", 2: "🥉"}

    for i, (_, row) in enumerate(ranking.iterrows()):
        pos_icon = medais_map.get(i, f"#{i+1}")
        top_class = "top" if i < 3 else ""
        nivel = int(row["nivel"])
        estrelas = "★" * nivel + "☆" * (5 - nivel)
        win_pct = f"{row['win_rate']*100:.0f}%"

        st.markdown(f"""
        <div class="rank-row">
            <div class="rank-pos {top_class}">{pos_icon}</div>
            <div class="rank-nome">{row['nome']}</div>
            <span class="nivel-badge nivel-{nivel}">{estrelas}</span>
            <div style="color:var(--color-text-main); font-size:0.95rem; min-width:80px; text-align:right; font-weight:700;">⚽ {int(row['gols_total'])}</div>
            <div style="color:var(--color-text-main); font-size:0.95rem; min-width:80px; text-align:right; font-weight:700;">🅰️ {int(row['assistencias_total'])}</div>
            <div style="color:var(--color-neon-g); font-size:0.95rem; min-width:60px; text-align:right; font-weight:700; text-shadow:0 0 5px rgba(178,102,255,0.5);">🏆 {win_pct}</div>
            <div style="color:var(--color-neon-b); font-family:var(--font-display); font-size:1.2rem; min-width:60px; text-align:right; text-shadow:0 0 5px rgba(223,179,255,0.5);">{row['ranking_score']:.3f}</div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()

    # Gráficos
    st.subheader("📈 Visualizações")
    col_g1, col_g2 = st.columns(2)

    with col_g1:
        st.caption("Gols por Jogador (Top 8)")
        chart_data = ranking.head(8)[["nome", "gols_total"]].set_index("nome")
        st.bar_chart(chart_data, color="#B266FF")

    with col_g2:
        st.caption("Assistências por Jogador (Top 8)")
        chart_data2 = ranking.head(8)[["nome", "assistencias_total"]].set_index("nome")
        st.bar_chart(chart_data2, color="#DFB3FF")

    # Win Rate chart
    st.caption("Win Rate dos Jogadores (%)")
    wr_data = ranking.head(8)[["nome", "win_rate"]].copy()
    wr_data["win_rate_pct"] = wr_data["win_rate"] * 100
    st.bar_chart(wr_data.set_index("nome")[["win_rate_pct"]], color="#FFD600")

    # Tabela exportável
    st.divider()
    st.subheader("📤 Exportar Dados")
    export_df = ranking[["nome", "nivel", "gols_total", "assistencias_total", "jogos_total", "vitorias_total", "win_rate", "ranking_score"]].copy()
    export_df.columns = ["Nome", "Nível", "Gols", "Assistências", "Jogos", "Vitórias", "Win Rate", "Score Ranking"]
    export_df["Win Rate"] = (export_df["Win Rate"] * 100).round(1).astype(str) + "%"

    st.download_button(
        "⬇️ Baixar Ranking CSV",
        data=export_df.to_csv(index=False).encode("utf-8"),
        file_name=f"ranking_futmanager_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True,
    )
