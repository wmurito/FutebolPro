"""
database.py - PHP United FutebolManager
Funções de acesso ao banco de dados via Supabase REST API (supabase-py).
Usa HTTPS (porta 443) - funciona em qualquer plataforma, sem restrições IPv4/IPv6.
"""

import pandas as pd
from typing import Optional
import logging
import streamlit as st
from supabase import create_client, Client

logger = logging.getLogger(__name__)


@st.cache_resource
def get_supabase() -> Client:
    """Retorna o cliente Supabase (cacheado para não recriar a cada rerun)."""
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)


def init_db() -> None:
    """Verifica conexão com o banco. As tabelas são criadas pelo schema.sql no Supabase."""
    try:
        sb = get_supabase()
        # Testa conexão lendo um registro
        sb.table("jogadores").select("id").limit(1).execute()
        logger.info("Conexão com Supabase OK!")
    except Exception as e:
        logger.error(f"Erro ao conectar ao Supabase: {e}")
        raise


def seed_jogadores_from_csv() -> bool:
    """Importa jogadores do CSV para o banco caso esteja vazio."""
    try:
        sb = get_supabase()
        result = sb.table("jogadores").select("id").limit(1).execute()
        if result.data:
            return False  # Já tem dados

        import os
        if not os.path.exists("data/jogadores.csv"):
            return False

        df = pd.read_csv("data/jogadores.csv")
        df.drop(columns=["id"], inplace=True, errors="ignore")

        rows = df.to_dict("records")
        sb.table("jogadores").insert(rows).execute()
        logger.info(f"Importados {len(rows)} jogadores do CSV.")
        return True
    except Exception as e:
        logger.error(f"Erro ao seed: {e}")
        return False


# ─────────────────────── JOGADORES ───────────────────────

def get_jogadores(apenas_ativos: bool = True) -> pd.DataFrame:
    """Retorna DataFrame com todos os jogadores."""
    sb = get_supabase()
    q = sb.table("jogadores").select("*").order("nome")
    if apenas_ativos:
        q = q.eq("ativo", 1)
    result = q.execute()
    return pd.DataFrame(result.data) if result.data else pd.DataFrame()


def get_jogador_by_id(jogador_id: int) -> Optional[dict]:
    """Retorna um jogador pelo ID."""
    sb = get_supabase()
    result = sb.table("jogadores").select("*").eq("id", jogador_id).execute()
    return result.data[0] if result.data else None


def upsert_jogador(
    nome: str,
    nivel: int,
    posicao: str = "Linha",
    jogador_id: Optional[int] = None,
) -> bool:
    """Cria ou atualiza um jogador."""
    try:
        sb = get_supabase()
        if jogador_id:
            sb.table("jogadores").update(
                {"nome": nome, "nivel": nivel, "posicao": posicao}
            ).eq("id", jogador_id).execute()
        else:
            sb.table("jogadores").insert(
                {"nome": nome, "nivel": nivel, "posicao": posicao}
            ).execute()
        return True
    except Exception as e:
        logger.error(f"Erro upsert_jogador: {e}")
        return False


def toggle_jogador_ativo(jogador_id: int) -> None:
    """Ativa/desativa um jogador."""
    sb = get_supabase()
    jogador = get_jogador_by_id(jogador_id)
    if jogador:
        novo_status = 0 if jogador["ativo"] else 1
        sb.table("jogadores").update({"ativo": novo_status}).eq("id", jogador_id).execute()


# ─────────────────────── PARTIDAS ───────────────────────

def criar_partida(
    data: str,
    dia_semana: str,
    time_a_ids: list,
    time_b_ids: list,
) -> int:
    """Cria uma nova partida no banco."""
    sb = get_supabase()
    result = sb.table("partidas").insert({
        "data": data,
        "dia_semana": dia_semana,
        "time_a_ids": ",".join(map(str, time_a_ids)),
        "time_b_ids": ",".join(map(str, time_b_ids)),
        "status": "em_andamento",
    }).execute()
    return result.data[0]["id"]


def get_partida(partida_id: int) -> Optional[dict]:
    """Retorna uma partida pelo ID."""
    sb = get_supabase()
    result = sb.table("partidas").select("*").eq("id", partida_id).execute()
    return result.data[0] if result.data else None


def get_partidas(limit: int = 20) -> pd.DataFrame:
    """Retorna as últimas partidas."""
    sb = get_supabase()
    result = sb.table("partidas").select("*").order("criado_em", desc=True).limit(limit).execute()
    return pd.DataFrame(result.data) if result.data else pd.DataFrame()


def finalizar_partida(partida_id: int, score_a: int, score_b: int) -> None:
    """Finaliza uma partida com o placar final."""
    sb = get_supabase()
    sb.table("partidas").update({
        "status": "finalizada",
        "score_a": score_a,
        "score_b": score_b,
        "gols_a": score_a,
        "gols_b": score_b,
    }).eq("id", partida_id).execute()
    _atualizar_stats_pos_partida(partida_id, score_a, score_b)


def _atualizar_stats_pos_partida(partida_id: int, score_a: int, score_b: int) -> None:
    """Atualiza gols, assistências e vitórias dos jogadores após partida."""
    partida = get_partida(partida_id)
    if not partida:
        return

    sb = get_supabase()
    ids_a = [int(i) for i in partida["time_a_ids"].split(",")]
    ids_b = [int(i) for i in partida["time_b_ids"].split(",")]
    todos = ids_a + ids_b
    vencedores = ids_a if score_a > score_b else (ids_b if score_b > score_a else [])

    # Incrementa jogos para todos
    for jid in todos:
        j = get_jogador_by_id(jid)
        if j:
            sb.table("jogadores").update(
                {"jogos_total": (j.get("jogos_total") or 0) + 1}
            ).eq("id", jid).execute()

    # Incrementa vitórias
    for jid in vencedores:
        j = get_jogador_by_id(jid)
        if j:
            sb.table("jogadores").update(
                {"vitorias_total": (j.get("vitorias_total") or 0) + 1}
            ).eq("id", jid).execute()

    # Gols e assistências via scouts
    scouts_result = sb.table("scouts").select("*").eq("partida_id", partida_id).execute()
    for scout in (scouts_result.data or []):
        col = "gols_total" if scout["tipo"] == "gol" else "assistencias_total"
        j = get_jogador_by_id(scout["jogador_id"])
        if j:
            sb.table("jogadores").update(
                {col: (j.get(col) or 0) + 1}
            ).eq("id", scout["jogador_id"]).execute()


# ─────────────────────── SCOUTS ───────────────────────

def registrar_scout(
    partida_id: int,
    jogador_id: int,
    tipo: str,
    time: str,
    minuto: Optional[int] = None,
) -> bool:
    """Registra um evento de scout."""
    try:
        sb = get_supabase()
        sb.table("scouts").insert({
            "partida_id": partida_id,
            "jogador_id": jogador_id,
            "tipo": tipo,
            "time": time,
            "minuto": minuto,
        }).execute()
        return True
    except Exception as e:
        logger.error(f"Erro registrar_scout: {e}")
        return False


def get_scouts_partida(partida_id: int) -> pd.DataFrame:
    """Retorna todos os scouts de uma partida com nome do jogador."""
    sb = get_supabase()
    # supabase-py suporta join com foreign key
    result = sb.table("scouts").select(
        "*, jogadores(nome)"
    ).eq("partida_id", partida_id).order("criado_em").execute()

    if not result.data:
        return pd.DataFrame()

    rows = []
    for s in result.data:
        rows.append({
            "id": s["id"],
            "partida_id": s["partida_id"],
            "jogador_id": s["jogador_id"],
            "tipo": s["tipo"],
            "time": s["time"],
            "minuto": s.get("minuto"),
            "criado_em": s.get("criado_em"),
            "jogador_nome": s.get("jogadores", {}).get("nome", "?") if s.get("jogadores") else "?",
        })
    return pd.DataFrame(rows)


def deletar_scout(scout_id: int) -> None:
    """Remove um scout pelo ID."""
    sb = get_supabase()
    sb.table("scouts").delete().eq("id", scout_id).execute()


# ─────────────────────── RANKING ───────────────────────

def calcular_ranking() -> pd.DataFrame:
    """Calcula o ranking dos jogadores."""
    sb = get_supabase()
    result = sb.table("jogadores").select("*").eq("ativo", 1).eq("posicao", "Linha").execute()
    df = pd.DataFrame(result.data) if result.data else pd.DataFrame()

    if df.empty:
        return df

    df["media_gols"] = df["gols_total"] / df["jogos_total"].replace(0, 1)
    df["media_assists"] = df["assistencias_total"] / df["jogos_total"].replace(0, 1)
    df["win_rate"] = df["vitorias_total"] / df["jogos_total"].replace(0, 1)

    df["ranking_score"] = (
        df["media_gols"] * 0.5
        + df["media_assists"] * 0.3
        + df["win_rate"] * 0.2
    ).round(3)

    return df.sort_values("ranking_score", ascending=False).reset_index(drop=True)
