"""
database.py - Funções de leitura/escrita de dados (SQLite + Pandas)
FutManager Pro MVP
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)

DB_PATH = Path("data/futmanager.db")
CSV_PATH = Path("data/jogadores.csv")


def get_connection() -> sqlite3.Connection:
    """Retorna conexão com o banco SQLite."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)


def init_db() -> None:
    """Inicializa o banco de dados com as tabelas necessárias."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS jogadores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

        CREATE TABLE IF NOT EXISTS partidas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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

        CREATE TABLE IF NOT EXISTS scouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partida_id INTEGER NOT NULL,
            jogador_id INTEGER NOT NULL,
            tipo TEXT NOT NULL CHECK(tipo IN ('gol', 'assistencia')),
            minuto INTEGER,
            time TEXT NOT NULL CHECK(time IN ('A', 'B')),
            criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (partida_id) REFERENCES partidas(id),
            FOREIGN KEY (jogador_id) REFERENCES jogadores(id)
        );
    """)

    conn.commit()
    conn.close()


def seed_jogadores_from_csv() -> bool:
    """
    Importa jogadores do CSV para o banco caso esteja vazio.
    
    Returns:
        True se importou, False se já havia dados.
    """
    conn = get_connection()
    try:
        count = pd.read_sql("SELECT COUNT(*) as c FROM jogadores", conn).iloc[0]["c"]
        if count > 0:
            return False

        df = pd.read_csv(CSV_PATH)
        df.drop(columns=["id"], inplace=True, errors="ignore")
        df.to_sql("jogadores", conn, if_exists="append", index=False)
        conn.commit()
        logger.info(f"Importados {len(df)} jogadores do CSV.")
        return True
    except Exception as e:
        logger.error(f"Erro ao seed: {e}")
        return False
    finally:
        conn.close()


# ─────────────────────── JOGADORES ───────────────────────

def get_jogadores(apenas_ativos: bool = True) -> pd.DataFrame:
    """Retorna DataFrame com todos os jogadores."""
    conn = get_connection()
    query = "SELECT * FROM jogadores"
    if apenas_ativos:
        query += " WHERE ativo = 1"
    query += " ORDER BY nome"
    df = pd.read_sql(query, conn)
    conn.close()
    return df


def get_jogador_by_id(jogador_id: int) -> Optional[dict]:
    """Retorna um jogador pelo ID."""
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM jogadores WHERE id = ?", conn, params=(jogador_id,))
    conn.close()
    return df.to_dict("records")[0] if not df.empty else None


def upsert_jogador(
    nome: str,
    nivel: int,
    posicao: str = "Linha",
    jogador_id: Optional[int] = None,
) -> bool:
    """
    Cria ou atualiza um jogador.
    
    Args:
        nome: Nome do jogador.
        nivel: Nível técnico (1-5).
        posicao: 'Linha' ou 'Goleiro'.
        jogador_id: ID para atualização (None = inserção).
    
    Returns:
        True em caso de sucesso.
    """
    conn = get_connection()
    try:
        if jogador_id:
            conn.execute(
                "UPDATE jogadores SET nome=?, nivel=?, posicao=? WHERE id=?",
                (nome, nivel, posicao, jogador_id),
            )
        else:
            conn.execute(
                "INSERT INTO jogadores (nome, nivel, posicao) VALUES (?,?,?)",
                (nome, nivel, posicao),
            )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Erro upsert_jogador: {e}")
        return False
    finally:
        conn.close()


def toggle_jogador_ativo(jogador_id: int) -> None:
    """Ativa/desativa um jogador."""
    conn = get_connection()
    conn.execute("UPDATE jogadores SET ativo = NOT ativo WHERE id = ?", (jogador_id,))
    conn.commit()
    conn.close()


# ─────────────────────── PARTIDAS ───────────────────────

def criar_partida(
    data: str,
    dia_semana: str,
    time_a_ids: list[int],
    time_b_ids: list[int],
) -> int:
    """
    Cria uma nova partida no banco.
    
    Returns:
        ID da partida criada.
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO partidas (data, dia_semana, time_a_ids, time_b_ids)
           VALUES (?, ?, ?, ?)""",
        (
            data,
            dia_semana,
            ",".join(map(str, time_a_ids)),
            ",".join(map(str, time_b_ids)),
        ),
    )
    partida_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return partida_id


def get_partida(partida_id: int) -> Optional[dict]:
    """Retorna uma partida pelo ID."""
    conn = get_connection()
    df = pd.read_sql("SELECT * FROM partidas WHERE id = ?", conn, params=(partida_id,))
    conn.close()
    return df.to_dict("records")[0] if not df.empty else None


def get_partidas(limit: int = 20) -> pd.DataFrame:
    """Retorna as últimas partidas."""
    conn = get_connection()
    df = pd.read_sql(
        f"SELECT * FROM partidas ORDER BY criado_em DESC LIMIT {limit}", conn
    )
    conn.close()
    return df


def finalizar_partida(partida_id: int, score_a: int, score_b: int) -> None:
    """Finaliza uma partida com o placar final."""
    conn = get_connection()
    vencedor = "A" if score_a > score_b else ("B" if score_b > score_a else "empate")
    conn.execute(
        """UPDATE partidas SET status='finalizada', score_a=?, score_b=?, gols_a=?, gols_b=?
           WHERE id=?""",
        (score_a, score_b, score_a, score_b, partida_id),
    )
    conn.commit()
    conn.close()
    _atualizar_stats_pos_partida(partida_id, score_a, score_b)


def _atualizar_stats_pos_partida(partida_id: int, score_a: int, score_b: int) -> None:
    """Atualiza gols, assistências e vitórias dos jogadores após partida."""
    conn = get_connection()
    partida = get_partida(partida_id)
    if not partida:
        conn.close()
        return

    ids_a = [int(i) for i in partida["time_a_ids"].split(",")]
    ids_b = [int(i) for i in partida["time_b_ids"].split(",")]
    todos = ids_a + ids_b

    # Incrementa jogos
    for jid in todos:
        conn.execute("UPDATE jogadores SET jogos_total = jogos_total + 1 WHERE id=?", (jid,))

    # Incrementa vitórias
    vencedores = ids_a if score_a > score_b else (ids_b if score_b > score_a else [])
    for jid in vencedores:
        conn.execute("UPDATE jogadores SET vitorias_total = vitorias_total + 1 WHERE id=?", (jid,))

    # Gols e assistências via scouts
    scouts = pd.read_sql(
        "SELECT * FROM scouts WHERE partida_id = ?", conn, params=(partida_id,)
    )
    for _, scout in scouts.iterrows():
        col = "gols_total" if scout["tipo"] == "gol" else "assistencias_total"
        conn.execute(f"UPDATE jogadores SET {col} = {col} + 1 WHERE id=?", (scout["jogador_id"],))

    conn.commit()
    conn.close()


# ─────────────────────── SCOUTS ───────────────────────

def registrar_scout(
    partida_id: int,
    jogador_id: int,
    tipo: str,
    time: str,
    minuto: Optional[int] = None,
) -> bool:
    """
    Registra um evento de scout (gol ou assistência).
    
    Args:
        partida_id: ID da partida.
        jogador_id: ID do jogador.
        tipo: 'gol' ou 'assistencia'.
        time: 'A' ou 'B'.
        minuto: Minuto do evento.
    
    Returns:
        True em caso de sucesso.
    """
    conn = get_connection()
    try:
        conn.execute(
            """INSERT INTO scouts (partida_id, jogador_id, tipo, time, minuto)
               VALUES (?, ?, ?, ?, ?)""",
            (partida_id, jogador_id, tipo, time, minuto),
        )
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"Erro registrar_scout: {e}")
        return False
    finally:
        conn.close()


def get_scouts_partida(partida_id: int) -> pd.DataFrame:
    """Retorna todos os scouts de uma partida com nome do jogador."""
    conn = get_connection()
    df = pd.read_sql(
        """SELECT s.*, j.nome as jogador_nome
           FROM scouts s
           JOIN jogadores j ON s.jogador_id = j.id
           WHERE s.partida_id = ?
           ORDER BY s.criado_em""",
        conn,
        params=(partida_id,),
    )
    conn.close()
    return df


def deletar_scout(scout_id: int) -> None:
    """Remove um scout pelo ID."""
    conn = get_connection()
    conn.execute("DELETE FROM scouts WHERE id = ?", (scout_id,))
    conn.commit()
    conn.close()


# ─────────────────────── RANKING ───────────────────────

def calcular_ranking() -> pd.DataFrame:
    """
    Calcula o ranking dos jogadores com base em:
    - Média de gols por jogo (peso 0.5)
    - Média de assistências por jogo (peso 0.3)
    - Win Rate (peso 0.2)
    
    Returns:
        DataFrame ordenado por score de ranking.
    """
    conn = get_connection()
    df = pd.read_sql(
        "SELECT * FROM jogadores WHERE ativo=1 AND posicao='Linha'", conn
    )
    conn.close()

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
