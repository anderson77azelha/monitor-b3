#!/usr/bin/env python3
# =============================================================================
# MONITOR DE NOTÍCIAS B3 — SCRIPT PRINCIPAL
# =============================================================================
# Execução:  python main.py
# Agendado pelo Windows Task Scheduler — 09h00 e 16h00
# =============================================================================

import sys
from datetime import datetime, timedelta, timezone
from config import ACOES, FIIS, HORARIOS
from dedup  import inicializar_db, registrar_enviadas, limpar_antigas
from scraper import coletar_noticias
from mailer  import enviar_email

TZ_BR = timezone(timedelta(hours=-3))


def determinar_horario() -> str:
    """Retorna o horário de disparo mais próximo (09:00 ou 16:00)."""
    hora_atual = datetime.now(TZ_BR).hour
    if hora_atual < 12:
        return "09:00"
    return "16:00"


def main():
    inicio = datetime.now(TZ_BR)
    print("=" * 60)
    print(f"MONITOR B3 — Iniciando em {inicio.strftime('%d/%m/%Y %H:%M:%S')}")
    print("=" * 60)

    # 1. Inicializar banco de dados
    inicializar_db()
    limpar_antigas(dias=30)

    # 2. Determinar horário do disparo
    horario = determinar_horario()
    print(f"[main] Disparo identificado: {horario}")

    # 3. Coletar notícias para todos os ativos
    todos_ativos = ACOES + FIIS
    print(f"[main] Monitorando {len(ACOES)} ações e {len(FIIS)} FIIs...")
    noticias = coletar_noticias(todos_ativos)

    # 4. Contar total de notícias novas
    total_novas = sum(len(v) for v in noticias.values())
    print(f"[main] Total de notícias novas: {total_novas}")

    # 5. Enviar e-mail (sempre envia, mesmo sem notícias — avisa que está tudo monitorado)
    sucesso = enviar_email(noticias, horario)

    # 6. Registrar como enviadas no banco (somente se o e-mail foi enviado)
    if sucesso and total_novas > 0:
        todas_noticias_flat = [n for lista in noticias.values() for n in lista]
        registrar_enviadas(todas_noticias_flat)
        print(f"[main] {total_novas} notícia(s) registrada(s) no banco de deduplicação.")

    fim = datetime.now(TZ_BR)
    duracao = (fim - inicio).seconds
    print(f"[main] Concluído em {duracao}s | {fim.strftime('%H:%M:%S')}")
    print("=" * 60)

    return 0 if sucesso else 1


if __name__ == "__main__":
    sys.exit(main())
