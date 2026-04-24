"""
Coletor de Ranking - GrindHero Online
Coleta dados de todos os tipos de ranking do servidor Endora (PvP)
e salva em banco SQLite + JSON.
"""
import requests
import sqlite3
import json
import time
import os
import sys
import logging
from datetime import datetime

# ─── Configuração ───────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "ranking.db")
JSON_PATH = os.path.join(BASE_DIR, "ranking_latest.json")
LOG_PATH = os.path.join(BASE_DIR, "logs", "coleta.log")

API_BASE = "https://api.grindhero.online/api/ranking"
API_CODE = "eqnEyx1GstjnFX"
SERVERS = {
    3: "Endora (PvP)",
    # 1: "Relaqua (non-PvP)",  # Adicionar se necessário
}
RANKING_TYPES = ["Experience", "Melee", "Shielding", "Magic", "Distance", "Taming"]

DELAY_ENTRE_REQUISICOES = 10  # segundos entre rankings — evitar rate limit acumulado
MAX_RETRIES = 5
RETRY_BASE_DELAY = 45  # backoff exponencial: 45s, 90s, 180s, 360s...

# ─── Logging ────────────────────────────────────────────────────────────────
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_PATH, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


# ─── Banco de dados ──────────────────────────────────────────────────────────
def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            collected_at    TEXT NOT NULL,
            server_id       INTEGER NOT NULL,
            server_name     TEXT NOT NULL,
            ranking_type    TEXT NOT NULL,
            rank            INTEGER NOT NULL,
            player_id       INTEGER NOT NULL,
            name            TEXT NOT NULL,
            level           INTEGER,
            experience      INTEGER
        );

        CREATE INDEX IF NOT EXISTS idx_snapshots_date
            ON snapshots(collected_at, ranking_type, server_id);

        CREATE INDEX IF NOT EXISTS idx_snapshots_player
            ON snapshots(player_id, ranking_type);

        CREATE TABLE IF NOT EXISTS coletas (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at      TEXT NOT NULL,
            finished_at     TEXT,
            status          TEXT,
            total_registros INTEGER DEFAULT 0,
            erros           TEXT
        );
    """)
    conn.commit()


def registrar_coleta(conn, started_at, finished_at, status, total, erros=None):
    conn.execute(
        "INSERT INTO coletas (started_at, finished_at, status, total_registros, erros) VALUES (?,?,?,?,?)",
        (started_at, finished_at, status, total, erros),
    )
    conn.commit()


def salvar_snapshot(conn, collected_at, server_id, server_name, ranking_type, registros):
    rows = [
        (
            collected_at,
            server_id,
            server_name,
            ranking_type,
            r["Rank"],
            r["PlayerId"],
            r["Name"],
            r.get("Level"),
            r.get("Experience"),
        )
        for r in registros
    ]
    conn.executemany(
        """INSERT INTO snapshots
           (collected_at, server_id, server_name, ranking_type, rank, player_id, name, level, experience)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        rows,
    )
    conn.commit()
    return len(rows)


# ─── API ─────────────────────────────────────────────────────────────────────
def fetch_ranking(server_id: int, ranking_type: str) -> list:
    url = f"{API_BASE}/{server_id}?code={API_CODE}&rankingType={ranking_type}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        wait = RETRY_BASE_DELAY * (2 ** (attempt - 1))  # 45, 90, 180, 360, 720s
        try:
            r = requests.get(url, headers=headers, timeout=20)

            if r.status_code == 429:
                log.warning(f"Rate limit em {ranking_type} (tentativa {attempt}/{MAX_RETRIES}). Aguardando {wait}s...")
                time.sleep(wait)
                continue

            r.raise_for_status()
            data = r.json()

            if data.get("HasError"):
                log.error(f"API retornou erro para {ranking_type}: {data}")
                return []

            return data.get("Object", [])

        except requests.exceptions.RequestException as e:
            log.error(f"Erro de rede em {ranking_type} (tentativa {attempt}): {e}")
            if attempt < MAX_RETRIES:
                time.sleep(wait)

    log.error(f"Falha apos {MAX_RETRIES} tentativas para {ranking_type}")
    return []


# ─── Coleta principal ─────────────────────────────────────────────────────────
def coletar() -> None:
    started_at = datetime.now().isoformat()
    collected_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log.info(f"=== Início da coleta: {collected_at} ===")

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    total_registros = 0
    erros = []
    todos_dados = {"coletado_em": collected_at, "servidores": {}}

    for server_id, server_name in SERVERS.items():
        log.info(f"Servidor: {server_name} (ID={server_id})")
        todos_dados["servidores"][server_name] = {}

        for i, ranking_type in enumerate(RANKING_TYPES):
            if i > 0:
                time.sleep(DELAY_ENTRE_REQUISICOES)

            log.info(f"  Coletando: {ranking_type}...")
            registros = fetch_ranking(server_id, ranking_type)

            if registros:
                n = salvar_snapshot(conn, collected_at, server_id, server_name, ranking_type, registros)
                total_registros += n
                todos_dados["servidores"][server_name][ranking_type] = registros
                log.info(f"    {n} registros salvos")
            else:
                erros.append(f"{server_name}/{ranking_type}")
                log.warning(f"    Sem dados para {ranking_type}")

    # Exportar JSON
    with open(JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(todos_dados, f, ensure_ascii=False, indent=2)
    log.info(f"JSON exportado: {JSON_PATH}")

    finished_at = datetime.now().isoformat()
    status = "sucesso" if not erros else f"parcial ({len(erros)} erros)"
    registrar_coleta(conn, started_at, finished_at, status, total_registros, json.dumps(erros) if erros else None)

    conn.close()
    log.info(f"=== Coleta finalizada: {total_registros} registros | Status: {status} ===")


if __name__ == "__main__":
    coletar()
