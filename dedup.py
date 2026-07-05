# =============================================================================
# DEDUPLICAÇÃO — Banco SQLite local para evitar repetição de notícias
# =============================================================================

import sqlite3
import hashlib
from datetime import datetime, timedelta
from config import DB_PATH


def _conectar():
    return sqlite3.connect(DB_PATH)


def inicializar_db():
    """Cria a tabela de hashes se não existir."""
    with _conectar() as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS enviadas (
                hash      TEXT PRIMARY KEY,
                titulo    TEXT,
                ativo     TEXT,
                enviado_em TEXT
            )
        """)
        con.commit()


def gerar_hash(titulo: str, link: str) -> str:
    """Gera hash único combinando título + link."""
    conteudo = (titulo + link).lower().strip()
    return hashlib.sha256(conteudo.encode("utf-8")).hexdigest()


def ja_foi_enviada(hash_noticia: str) -> bool:
    """Retorna True se a notícia já foi enviada anteriormente."""
    with _conectar() as con:
        cursor = con.execute(
            "SELECT 1 FROM enviadas WHERE hash = ?", (hash_noticia,)
        )
        return cursor.fetchone() is not None


def registrar_enviadas(noticias: list):
    """
    Registra lista de notícias como enviadas.
    Cada item: dict com 'hash', 'titulo', 'ativo'
    """
    agora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _conectar() as con:
        con.executemany(
            "INSERT OR IGNORE INTO enviadas (hash, titulo, ativo, enviado_em) VALUES (?,?,?,?)",
            [(n["hash"], n["titulo"], n["ativo"], agora) for n in noticias]
        )
        con.commit()


def limpar_antigas(dias: int = 30):
    """
    Remove registros com mais de N dias para não crescer indefinidamente.
    Chamado automaticamente a cada execução.
    """
    corte = (datetime.now() - timedelta(days=dias)).strftime("%Y-%m-%d %H:%M:%S")
    with _conectar() as con:
        deletadas = con.execute(
            "DELETE FROM enviadas WHERE enviado_em < ?", (corte,)
        ).rowcount
        con.commit()
    if deletadas:
        print(f"[dedup] {deletadas} registro(s) antigo(s) removido(s) do banco.")
