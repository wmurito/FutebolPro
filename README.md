# ⚽ FutManager Pro — MVP

Sistema de gestão para grupos de futebol amador.

## 🚀 Como rodar

```bash
# Instalar dependências
pip install -r requirements.txt

# Iniciar aplicação
streamlit run app.py
```

## 📁 Estrutura

```
futebol_app/
├── .streamlit/
│   └── config.toml        # Tema escuro + verde
├── data/
│   └── jogadores.csv      # Seed inicial (14 atletas)
├── app.py                 # Interface Streamlit (UI)
├── logic.py               # Algoritmos de sorteio e ranking
├── database.py            # CRUD SQLite
└── requirements.txt
```

## 🧠 Algoritmo de Equilíbrio

O sorteio usa **Força Bruta** (C(12,6) = 924 combinações) para encontrar a divisão com menor diferença de score:

```
Score_Time = Σ Nivel_i    (i = 1..6)
Objetivo:   minimizar |Score_A − Score_B|
```

Para pools maiores que 14 jogadores, usa algoritmo **Greedy (zig-zag)**.

## 📊 Fórmula de Ranking

```
Ranking_Score = (Media_Gols × 0.5) + (Media_Assists × 0.3) + (Win_Rate × 0.2)
```

## 🗺️ Roadmap

- **MVP (atual):** Streamlit + SQLite
- **Fase 2:** Power BI / Fabric + Delta Tables
- **Fase 3:** PostgreSQL + autenticação + multi-tenant SaaS
