-- ================================================
-- PHP United FutebolManager - Schema do Banco
-- Execute este script no Supabase SQL Editor
-- Project Settings > SQL Editor > New Query
-- ================================================

CREATE TABLE IF NOT EXISTS jogadores (
    id SERIAL PRIMARY KEY,
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
    id SERIAL PRIMARY KEY,
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
    id SERIAL PRIMARY KEY,
    partida_id INTEGER NOT NULL REFERENCES partidas(id),
    jogador_id INTEGER NOT NULL REFERENCES jogadores(id),
    tipo TEXT NOT NULL CHECK(tipo IN ('gol', 'assistencia')),
    minuto INTEGER,
    time TEXT NOT NULL CHECK(time IN ('A', 'B')),
    criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
