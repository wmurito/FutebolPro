"""
logic.py - Algoritmos de sorteio de times e cálculo de ranking
FutManager Pro MVP
"""

from itertools import combinations
from typing import Optional
import pandas as pd


# ─────────────────────── TIPOS ───────────────────────

type JogadorDict = dict[str, int | str | float]
type TimeResult = tuple[list[JogadorDict], list[JogadorDict], int]


# ─────────────────────── MATCHMAKING ───────────────────────

def _score_time(jogadores: list[JogadorDict]) -> int:
    """Soma do nível técnico dos jogadores do time."""
    return sum(int(j["nivel"]) for j in jogadores)


def gerar_times_equilibrados(
    jogadores: list[JogadorDict],
    tamanho_time: int = 6,
    max_iter: int = 924,  # C(12,6) = 924
) -> TimeResult:
    """
    Divide uma lista de jogadores em dois times equilibrados pelo score total.
    
    Utiliza força bruta para listas pequenas (≤12) e greedy para maiores.
    
    Args:
        jogadores: Lista de dicts com campos 'id', 'nome', 'nivel'.
        tamanho_time: Número de jogadores por time (default=6).
        max_iter: Limite de iterações para força bruta.
    
    Returns:
        Tuple (time_a, time_b, diferenca_score).
    
    Raises:
        ValueError: Se número de jogadores for insuficiente.
    """
    n = len(jogadores)
    esperado = tamanho_time * 2

    if n < esperado:
        raise ValueError(
            f"Necessário {esperado} jogadores de linha, recebido {n}."
        )

    # Usa apenas os primeiros `esperado` jogadores (prioridade por presença)
    pool = jogadores[:esperado]

    # Força Bruta: testa todas as combinações possíveis de tamanho_time
    melhor_dif = float("inf")
    melhor_a: list[JogadorDict] = []
    melhor_b: list[JogadorDict] = []

    indices = list(range(esperado))
    for combo in combinations(indices, tamanho_time):
        time_a = [pool[i] for i in combo]
        time_b = [pool[i] for i in indices if i not in combo]
        dif = abs(_score_time(time_a) - _score_time(time_b))

        if dif < melhor_dif:
            melhor_dif = dif
            melhor_a = time_a
            melhor_b = time_b

        if melhor_dif == 0:
            break  # Perfeito, não precisa continuar

    return melhor_a, melhor_b, melhor_dif


def gerar_times_greedy(jogadores: list[JogadorDict]) -> TimeResult:
    """
    Algoritmo greedy para equilíbrio de times.
    
    Ordena por nível decrescente e distribui alternadamente (zig-zag).
    Mais rápido que força bruta para listas grandes, qualidade levemente inferior.
    
    Args:
        jogadores: Lista de dicts com campo 'nivel'.
    
    Returns:
        Tuple (time_a, time_b, diferenca_score).
    """
    ordenados = sorted(jogadores, key=lambda j: int(j["nivel"]), reverse=True)
    time_a, time_b = [], []

    for i, jogador in enumerate(ordenados):
        if _score_time(time_a) <= _score_time(time_b):
            time_a.append(jogador)
        else:
            time_b.append(jogador)

    dif = abs(_score_time(time_a) - _score_time(time_b))
    return time_a, time_b, dif


def selecionar_algoritmo(
    jogadores: list[JogadorDict],
    tamanho_time: int = 6,
) -> TimeResult:
    """
    Seleciona o algoritmo adequado conforme tamanho do pool.
    
    - Força Bruta para ≤ 14 jogadores (C(12,6)=924 combinações).
    - Greedy para > 14 jogadores.
    """
    if len(jogadores) <= 14:
        return gerar_times_equilibrados(jogadores, tamanho_time)
    return gerar_times_greedy(jogadores)


# ─────────────────────── PRESENÇA ───────────────────────

def separar_por_posicao(
    jogadores: list[JogadorDict],
) -> tuple[list[JogadorDict], list[JogadorDict]]:
    """
    Separa lista em goleiros e jogadores de linha.
    
    Returns:
        Tuple (goleiros, linha).
    """
    goleiros = [j for j in jogadores if j.get("posicao") == "Goleiro"]
    linha = [j for j in jogadores if j.get("posicao") != "Goleiro"]
    return goleiros, linha


def validar_presenca(
    presentes: list[JogadorDict],
) -> dict[str, bool | str]:
    """
    Valida se o grupo de presentes tem configuração válida para partida.
    
    Returns:
        Dict com 'valido' (bool) e 'mensagem' (str).
    """
    goleiros, linha = separar_por_posicao(presentes)

    if len(goleiros) < 2:
        return {"valido": False, "mensagem": f"Necessário mínimo 2 goleiros. Presentes: {len(goleiros)}."}

    if len(linha) < 12:
        return {
            "valido": False,
            "mensagem": f"Necessário mínimo 12 jogadores de linha. Presentes: {len(linha)}.",
        }

    return {"valido": True, "mensagem": f"✅ Configuração válida! {len(linha)} jogadores de linha + {len(goleiros)} goleiros."}


# ─────────────────────── RANKING ───────────────────────

def calcular_nivel_sugerido(
    gols: int,
    assists: int,
    jogos: int,
    win_rate: float,
) -> int:
    """
    Sugere nível técnico (1-5) com base nas estatísticas do jogador.
    
    Útil para atualizar níveis periodicamente.
    
    Args:
        gols: Total de gols marcados.
        assists: Total de assistências.
        jogos: Total de jogos disputados.
        win_rate: Taxa de vitória (0.0 a 1.0).
    
    Returns:
        Nível sugerido entre 1 e 5.
    """
    if jogos == 0:
        return 3  # Nível neutro para rookies

    media_gols = gols / jogos
    media_assists = assists / jogos
    score = media_gols * 0.5 + media_assists * 0.3 + win_rate * 0.2

    # Thresholds empíricos baseados em futebol amador
    if score >= 0.85:
        return 5
    elif score >= 0.60:
        return 4
    elif score >= 0.35:
        return 3
    elif score >= 0.15:
        return 2
    else:
        return 1


def summary_times(
    time_a: list[JogadorDict],
    time_b: list[JogadorDict],
) -> dict:
    """
    Gera resumo comparativo dos dois times.
    
    Returns:
        Dict com score, média e diferença de cada time.
    """
    score_a = _score_time(time_a)
    score_b = _score_time(time_b)

    return {
        "score_a": score_a,
        "score_b": score_b,
        "media_a": round(score_a / len(time_a), 2) if time_a else 0,
        "media_b": round(score_b / len(time_b), 2) if time_b else 0,
        "diferenca": abs(score_a - score_b),
        "equilibrado": abs(score_a - score_b) <= 1,
    }
