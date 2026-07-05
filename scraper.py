# =============================================================================
# SCRAPER — Coleta de notícias via Google News RSS e Feed CVM
# =============================================================================

import feedparser
import requests
from datetime import datetime, timedelta, timezone
from time import mktime
from config import JANELA_HORAS, MAX_NOTICIAS_POR_ATIVO, NOMES
from dedup import gerar_hash, ja_foi_enviada

# Fuso horário de Brasília (UTC-3)
TZ_BR = timezone(timedelta(hours=-3))


def _agora_br() -> datetime:
    return datetime.now(tz=TZ_BR)


def _dentro_da_janela(data_entry) -> bool:
    """Verifica se a entrada está dentro da janela de tempo configurada."""
    if not data_entry:
        return True  # Se não tem data, inclui por precaução

    try:
        if hasattr(data_entry, "timetuple"):
            pub = datetime.fromtimestamp(mktime(data_entry.timetuple()), tz=TZ_BR)
        else:
            pub = datetime(*data_entry[:6], tzinfo=TZ_BR)
    except Exception:
        return True

    limite = _agora_br() - timedelta(hours=JANELA_HORAS)
    return pub >= limite


def _formatar_data(data_entry) -> str:
    """Converte data do feed para string legível."""
    if not data_entry:
        return "Data não disponível"
    try:
        pub = datetime.fromtimestamp(mktime(data_entry.timetuple()), tz=TZ_BR)
        return pub.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "Data não disponível"


# ─── GOOGLE NEWS RSS ──────────────────────────────────────────────────────────

def _buscar_google_news(ticker: str) -> list:
    """
    Busca notícias no Google News via RSS para um ticker específico.
    Combina busca pelo ticker e pelo nome amigável da empresa.
    """
    nome = NOMES.get(ticker, ticker)
    queries = [ticker, f"{ticker} {nome.split()[0]}"]
    resultados = []

    for query in queries:
        url = (
            f"https://news.google.com/rss/search"
            f"?q={requests.utils.quote(query)}+B3+ações"
            f"&hl=pt-BR&gl=BR&ceid=BR:pt-419"
        )
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:MAX_NOTICIAS_POR_ATIVO]:
                if not _dentro_da_janela(entry.get("published_parsed")):
                    continue

                titulo = entry.get("title", "").strip()
                link   = entry.get("link", "").strip()
                if not titulo or not link:
                    continue

                h = gerar_hash(titulo, link)
                if ja_foi_enviada(h):
                    continue

                resultados.append({
                    "ativo":  ticker,
                    "titulo": titulo,
                    "link":   link,
                    "data":   _formatar_data(entry.get("published_parsed")),
                    "fonte":  "Google News",
                    "hash":   h,
                })
        except Exception as e:
            print(f"[scraper] Erro Google News para {ticker}: {e}")

    # Remove duplicatas internas (mesmo hash de queries diferentes)
    vistos = set()
    unicos = []
    for n in resultados:
        if n["hash"] not in vistos:
            vistos.add(n["hash"])
            unicos.append(n)

    return unicos[:MAX_NOTICIAS_POR_ATIVO]


# ─── FEED CVM ─────────────────────────────────────────────────────────────────

# Códigos CVM dos ativos (CNPJ / código de negociação)
# O feed da CVM por empresa usa o código de negociação
CVM_FEED_BASE = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM.aspx"
CVM_RSS_BASE  = "https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM_Resultado.aspx"

def _buscar_cvm(ticker: str) -> list:
    """
    Busca fatos relevantes e comunicados ao mercado via feed RSS da CVM.
    Usa o endpoint público de busca por código de negociação.
    """
    url = (
        f"https://efts.cvm.gov.br/EFTS/full/text?"
        f"q=%22{ticker}%22&dateRange=custom"
        f"&startDate={( _agora_br() - timedelta(hours=JANELA_HORAS) ).strftime('%Y-%m-%d')}"
        f"&endDate={_agora_br().strftime('%Y-%m-%d')}"
        f"&category=Fato+Relevante,Comunicado+ao+Mercado,Aviso+aos+Acionistas"
    )

    # Alternativa via RSS do feed público da CVM
    rss_url = (
        f"https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM_Resultado.aspx?"
        f"tipo_participante=CIA_ABERTA&cod_negociacao={ticker}&categoria=&"
        f"data_ini={(  _agora_br() - timedelta(hours=JANELA_HORAS) ).strftime('%d/%m/%Y')}&"
        f"data_fim={_agora_br().strftime('%d/%m/%Y')}&formato=RSS"
    )

    resultados = []
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:3]:
            titulo = entry.get("title", "").strip()
            link   = entry.get("link", "").strip()
            if not titulo or not link:
                continue
            if not _dentro_da_janela(entry.get("published_parsed")):
                continue

            h = gerar_hash(titulo, link)
            if ja_foi_enviada(h):
                continue

            resultados.append({
                "ativo":  ticker,
                "titulo": f"[CVM] {titulo}",
                "link":   link,
                "data":   _formatar_data(entry.get("published_parsed")),
                "fonte":  "CVM — Fato Relevante",
                "hash":   h,
            })
    except Exception as e:
        print(f"[scraper] Erro CVM para {ticker}: {e}")

    return resultados


# ─── FUNÇÃO PRINCIPAL ─────────────────────────────────────────────────────────

def coletar_noticias(ativos: list) -> dict:
    """
    Coleta notícias de todas as fontes para todos os ativos.
    Retorna dicionário { ticker: [lista de notícias] }
    """
    resultado = {}
    total = 0

    for ticker in ativos:
        print(f"[scraper] Buscando notícias: {ticker}...")
        noticias_google = _buscar_google_news(ticker)
        noticias_cvm    = _buscar_cvm(ticker)

        # CVM tem prioridade — aparece primeiro
        todas = noticias_cvm + noticias_google

        if todas:
            resultado[ticker] = todas
            total += len(todas)
        else:
            resultado[ticker] = []

    print(f"[scraper] Total de notícias novas coletadas: {total}")
    return resultado
