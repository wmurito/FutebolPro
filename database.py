"""
database.py - Funções de leitura/escrita de dados (SQLAlchemy + Supabase/PostgreSQL)
PHP United FutebolManager
"""

import pandas as pd
from typing import Optional
import logging
import streamlit as st
from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import URL
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

import ssl

def get_engine():
    try:
        db_url_str = st.secrets.get("SUPABASE_URL", None)
        
        if db_url_str and "supabase.co" in db_url_str:
            # Garante que a URL use o adaptador psicopg2 com SSL ativado para nuvem
            if db_url_str.startswith("postgres://"):
                db_url_str = db_url_str.replace("postgres://", "postgresql://", 1)
            
            # Força o SSL mode na URL para prevenir timeout na nuvem e no AWS Supabase
            if "?" not in db_url_str:
                db_url_str += "?sslmode=require"
            elif "sslmode" not in db_url_str:
                db_url_str += "&sslmode=require"
            
            engine = create_engine(
                db_url_str,
                pool_pre_ping=True
            )
            return engine
             
    except Exception as e:
        logger.warning(f"Erro ao inicializar DB Nuvem: {e}. Fallback local.")
        
    logger.info("Retornando SQLite")
    return create_engine("sqlite:///data/futmanager.db", connect_args={"check_same_thread": False})

engine = get_engine()

def get_connection():
    """Retorna conexão ativa com o banco (SQLAlchemy)."""
    return engine.connect()


def init_db() -> None:
    """Inicializa o banco de dados com as tabelas necessárias."""
    
    # Se for SQLite fallback, usa autoincrement, se for Postgres, usa SERIAL
    is_sqlite = engine.dialect.name == "sqlite"
    id_type = "INTEGER PRIMARY KEY AUTOINCREMENT" if is_sqlite else "SERIAL PRIMARY KEY"
    
    with get_connection() as conn:
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS jogadores (
                id {id_type},
                nome TEXT NOT NULL UNIQUE,
                nivel INTEGER NOT NULL CHECK(nivel BETWEEN 1 AND 5),
                posicao TEXT NOT NULL DEFAULT 'Linha',
                gols_total INTEGER DEFAULT 0,
                assistencias_total INTEGER DEFAULT 0,
                jogos_total INTEGER DEFAULT 0,
                vitorias_total INTEGER DEFAULT 0,
                ativo INTEGER DEFAULT 1,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS partidas (
                id {id_type},
                data TEXT NOT NULL,
                dia_semana TEXT NOT NULL,
                time_a_ids TEXT NOT NULL,
                time_b_ids TEXT NOT NULL,
                score_a INTEGER DEFAULT 0,
                score_b INTEGER DEFAULT 0,
                gols_a INTEGER DEFAULT 0,
                gols_b INTEGER DEFAULT 0,
                status TEXT DEFAULT 'em_andamento',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """))
        
        conn.execute(text(f"""
            CREATE TABLE IF NOT EXISTS scouts (
                id {id_type},
                partida_id INTEGER NOT NULL,
                jogador_id INTEGER NOT NULL,
                tipo TEXT NOT NULL CHECK(tipo IN ('gol', 'assistencia')),
                minuto INTEGER,
                time TEXT NOT NULL CHECK(time IN ('A', 'B')),
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (partida_id) REFERENCES partidas(id),
                FOREIGN KEY (jogador_id) REFERENCES jogadores(id)
            );
        """))
        conn.commit()


def seed_jogadores_from_csv() -> bool:
    """
    Importa jogadores do CSV para o banco caso esteja vazio.
    """
    try:
        with get_connection() as conn:
            result = conn.execute(text("SELECT COUNT(*) as c FROM jogadores")).fetchone()
            count = result[0]
            if count > 0:
                return False

        # Como fallback caso exista arquivo local CSV
        import os
        if not os.path.exists("data/jogadores.csv"):
            return False

        df = pd.read_csv("data/jogadores.csv")
        df.drop(columns=["id"], inplace=True, errors="ignore")
        
        # Conexão engine pra to_sql
        df.to_sql("jogadores", engine, if_exists="append", index=False)
        logger.info(f"Importados {len(df)} jogadores do CSV.")
        return True
    except Exception as e:
        logger.error(f"Erro ao seed: {e}")
        return False


# ─────────────────────── JOGADORES ───────────────────────

def get_jogadores(apenas_ativos: bool = True) -> pd.DataFrame:
    """Retorna DataFrame com todos os jogadores."""
    query = "SELECT * FROM jogadores"
    if apenas_ativos:
        query += " WHERE ativo = 1"
    query += " ORDER BY nome"
    
    with get_connection() as conn:
        df = pd.read_sql(text(query), conn)
    return df


def get_jogador_by_id(jogador_id: int) -> Optional[dict]:
    """Retorna um jogador pelo ID."""
    with get_connection() as conn:
        df = pd.read_sql(text("SELECT * FROM jogadores WHERE id = :jid"), conn, params={"jid": jogador_id})
    return df.to_dict("records")[0] if not df.empty else None


def upsert_jogador(
    nome: str,
    nivel: int,
    posicao: str = "Linha",
    jogador_id: Optional[int] = None,
) -> bool:
    """
    Cria ou atualiza um jogador.
    """
    try:
        with get_connection() as conn:
            if jogador_id:
                conn.execute(
                    text("UPDATE jogadores SET nome=:n, nivel=:v, posicao=:p WHERE id=:jid"),
                    {"n": nome, "v": nivel, "p": posicao, "jid": jogador_id},
                )
            else:
                conn.execute(
                    text("INSERT INTO jogadores (nome, nivel, posicao) VALUES (:n,:v,:p)"),
                    {"n": nome, "v": nivel, "p": posicao},
                )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Erro upsert_jogador: {e}")
        return False


def toggle_jogador_ativo(jogador_id: int) -> None:
    """Ativa/desativa um jogador."""
    with get_connection() as conn:
        # SQLite converte NOT ativo direto mas Postgres/SQLAlchemy precisam ser precisos int vs boolean
        # SQLite armazena BOOLEAN como 0 ou 1, Postgres suporta type BOOL ou Int.
        conn.execute(
            text("UPDATE jogadores SET ativo = CASE WHEN ativo = 1 THEN 0 ELSE 1 END WHERE id = :jid"),
            {"jid": jogador_id},
        )
        conn.commit()


# ─────────────────────── PARTIDAS ───────────────────────

def criar_partida(
    data: str,
    dia_semana: str,
    time_a_ids: list[int],
    time_b_ids: list[int],
) -> int:
    """
    Cria uma nova partida no banco.
    """
    with get_connection() as conn:
        result = conn.execute(
            text("""INSERT INTO partidas (data, dia_semana, time_a_ids, time_b_ids)
               VALUES (:dt, :dia, :ta, :tb) RETURNING id"""),
            {
                "dt": data,
                "dia": dia_semana,
                "ta": ",".join(map(str, time_a_ids)),
                "tb": ",".join(map(str, time_b_ids)),
            },
        )
        partida_id = result.fetchone()[0]
        conn.commit()
        return partida_id


def get_partida(partida_id: int) -> Optional[dict]:
    """Retorna uma partida pelo ID."""
    with get_connection() as conn:
        df = pd.read_sql(text("SELECT * FROM partidas WHERE id = :pid"), conn, params={"pid": partida_id})
    return df.to_dict("records")[0] if not df.empty else None


def get_partidas(limit: int = 20) -> pd.DataFrame:
    """Retorna as últimas partidas."""
    with get_connection() as conn:
        df = pd.read_sql(
            text(f"SELECT * FROM partidas ORDER BY criado_em DESC LIMIT {limit}"), conn
        )
    return df


def finalizar_partida(partida_id: int, score_a: int, score_b: int) -> None:
    """Finaliza uma partida com o placar final."""
    with get_connection() as conn:
        conn.execute(
            text("""UPDATE partidas SET status='finalizada', score_a=:sa, score_b=:sb, gols_a=:ga, gols_b=:gb
               WHERE id=:pid"""),
            {"sa": score_a, "sb": score_b, "ga": score_a, "gb": score_b, "pid": partida_id},
        )
        conn.commit()
    _atualizar_stats_pos_partida(partida_id, score_a, score_b)


def _atualizar_stats_pos_partida(partida_id: int, score_a: int, score_b: int) -> None:
    """Atualiza gols, assistências e vitórias dos jogadores após partida."""
    partida = get_partida(partida_id)
    if not partida:
        return

    ids_a = [int(i) for i in partida["time_a_ids"].split(",")]
    ids_b = [int(i) for i in partida["time_b_ids"].split(",")]
    todos = ids_a + ids_b
    vencedores = ids_a if score_a > score_b else (ids_b if score_b > score_a else [])

    with get_connection() as conn:
        # Incrementa jogos
        for jid in todos:
            conn.execute(text("UPDATE jogadores SET jogos_total = jogos_total + 1 WHERE id=:jid"), {"jid": jid})

        # Incrementa vitórias
        for jid in vencedores:
            conn.execute(text("UPDATE jogadores SET vitorias_total = vitorias_total + 1 WHERE id=:jid"), {"jid": jid})

        # Gols e assistências via scouts
        scouts = pd.read_sql(text("SELECT * FROM scouts WHERE partida_id = :pid"), conn, params={"pid": partida_id})
        for _, scout in scouts.iterrows():
            col = "gols_total" if scout["tipo"] == "gol" else "assistencias_total"
            conn.execute(text(f"UPDATE jogadores SET {col} = {col} + 1 WHERE id=:jid"), {"jid": scout["jogador_id"]})

        conn.commit()


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
        with get_connection() as conn:
            conn.execute(
                text("""INSERT INTO scouts (partida_id, jogador_id, tipo, time, minuto)
                   VALUES (:pid, :jid, :tipo, :time, :min)"""),
                {"pid": partida_id, "jid": jogador_id, "tipo": tipo, "time": time, "min": minuto},
            )
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Erro registrar_scout: {e}")
        return False


def get_scouts_partida(partida_id: int) -> pd.DataFrame:
    """Retorna todos os scouts de uma partida."""
    with get_connection() as conn:
        df = pd.read_sql(
            text("""SELECT s.*, j.nome as jogador_nome
               FROM scouts s
               JOIN jogadores j ON s.jogador_id = j.id
               WHERE s.partida_id = :pid
               ORDER BY s.criado_em"""),
            conn,
            params={"pid": partida_id},
        )
    return df


def deletar_scout(scout_id: int) -> None:
    """Remove um scout pelo ID."""
    with get_connection() as conn:
        conn.execute(text("DELETE FROM scouts WHERE id = :sid"), {"sid": scout_id})
        conn.commit()


# ─────────────────────── RANKING ───────────────────────

def calcular_ranking() -> pd.DataFrame:
    """Calcula o ranking dos jogadores."""
    with get_connection() as conn:
        df = pd.read_sql(
            text("SELECT * FROM jogadores WHERE ativo=1 AND posicao='Linha'"), conn
        )

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
