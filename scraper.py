# =============================================================================
# SCRAPER V2 — Coleta de notícias via múltiplas fontes especializadas
# Google News RSS + Feeds diretos InfoMoney/Valor/Exame + CVM
# =============================================================================

import feedparser
import requests
from datetime import datetime, timedelta, timezone
from time import mktime
from config import JANELA_HORAS, MAX_NOTICIAS_POR_ATIVO, NOMES, ACOES, FIIS
from dedup import gerar_hash, ja_foi_enviada

TZ_BR = timezone(timedelta(hours=-3))

def _agora_br():
    return datetime.now(tz=TZ_BR)

def _dentro_da_janela(data_entry):
    if not data_entry:
        return True
    try:
        if hasattr(data_entry, "timetuple"):
            pub = datetime.fromtimestamp(mktime(data_entry.timetuple()), tz=TZ_BR)
        else:
            pub = datetime(*data_entry[:6], tzinfo=TZ_BR)
    except Exception:
        return True
    limite = _agora_br() - timedelta(hours=JANELA_HORAS)
    return pub >= limite

def _formatar_data(data_entry):
    if not data_entry:
        return "Data não disponível"
    try:
        pub = datetime.fromtimestamp(mktime(data_entry.timetuple()), tz=TZ_BR)
        return pub.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return "Data não disponível"

def _processar_feed(url, ticker, fonte, max_items=5):
    """Processa qualquer feed RSS e retorna notícias novas."""
    resultados = []
    try:
        feed = feedparser.parse(url)
        for entry in feed.entries[:max_items]:
            if not _dentro_da_janela(entry.get("published_parsed")):
                continue
            titulo = entry.get("title", "").strip()
            link   = entry.get("link", "").strip()
            if not titulo or not link:
                continue
            # Filtra por relevância — verifica se o ticker ou nome aparece
            nome = NOMES.get(ticker, ticker).split()[0].lower()
            texto_busca = (titulo + " " + entry.get("summary","")).lower()
            if ticker.lower() not in texto_busca and nome not in texto_busca:
                continue
            h = gerar_hash(titulo, link)
            if ja_foi_enviada(h):
                continue
            resultados.append({
                "ativo":  ticker,
                "titulo": titulo,
                "link":   link,
                "data":   _formatar_data(entry.get("published_parsed")),
                "fonte":  fonte,
                "hash":   h,
            })
    except Exception as e:
        print(f"[scraper] Erro feed {fonte} para {ticker}: {e}")
    return resultados


# ─── FONTES ESPECÍFICAS ───────────────────────────────────────────────────────

# Feeds RSS diretos dos portais financeiros brasileiros
FEEDS_FINANCEIROS = [
    ("https://www.infomoney.com.br/feed/", "InfoMoney"),
    ("https://valor.globo.com/rss/empresas.gxml", "Valor Econômico — Empresas"),
    ("https://valor.globo.com/rss/financas.gxml", "Valor Econômico — Finanças"),
    ("https://exame.com/invest/feed/", "Exame Invest"),
    ("https://br.investing.com/rss/news_301.rss", "Investing.com Brasil"),
]

def _buscar_feeds_diretos(ticker):
    """
    Varre feeds RSS dos portais financeiros buscando menção ao ticker ou empresa.
    Mais eficiente que o Google News para notícias em português.
    """
    resultados = []
    nome = NOMES.get(ticker, "").lower()

    for url_feed, nome_fonte in FEEDS_FINANCEIROS:
        try:
            feed = feedparser.parse(url_feed)
            for entry in feed.entries[:30]:  # Varre mais itens para filtrar por relevância
                if not _dentro_da_janela(entry.get("published_parsed")):
                    continue
                titulo   = entry.get("title", "").strip()
                link     = entry.get("link", "").strip()
                resumo   = entry.get("summary", "").lower()
                if not titulo or not link:
                    continue

                # Verifica relevância: ticker ou nome da empresa no título ou resumo
                texto = (titulo + " " + resumo).lower()
                if ticker.lower() not in texto and not any(
                    p in texto for p in nome.split()[:2] if len(p) > 3
                ):
                    continue

                h = gerar_hash(titulo, link)
                if ja_foi_enviada(h):
                    continue

                resultados.append({
                    "ativo":  ticker,
                    "titulo": titulo,
                    "link":   link,
                    "data":   _formatar_data(entry.get("published_parsed")),
                    "fonte":  nome_fonte,
                    "hash":   h,
                })
        except Exception as e:
            print(f"[scraper] Erro {nome_fonte} para {ticker}: {e}")

    return resultados[:MAX_NOTICIAS_POR_ATIVO]


def _buscar_google_news(ticker):
    """
    Google News RSS com queries otimizadas:
    - Usa ticker + nome da empresa para maior precisão
    - Queries em português explicitamente
    """
    nome = NOMES.get(ticker, ticker)
    # Usa as primeiras palavras do nome para maior precisão
    nome_curto = " ".join(nome.split()[:2])

    queries = [
        f'"{ticker}" ação bolsa',
        f'"{nome_curto}" dividendos resultados',
        f'"{ticker}" B3 investimento',
    ]

    resultados = []
    vistos = set()

    for query in queries:
        url = (
            f"https://news.google.com/rss/search"
            f"?q={requests.utils.quote(query)}"
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
                if ja_foi_enviada(h) or h in vistos:
                    continue
                vistos.add(h)
                resultados.append({
                    "ativo":  ticker,
                    "titulo": titulo,
                    "link":   link,
                    "data":   _formatar_data(entry.get("published_parsed")),
                    "fonte":  "Google News",
                    "hash":   h,
                })
        except Exception as e:
            print(f"[scraper] Erro Google News ({query}): {e}")

    return resultados[:MAX_NOTICIAS_POR_ATIVO]


def _buscar_cvm(ticker):
    """Feed RSS da CVM para fatos relevantes e comunicados."""
    rss_url = (
        f"https://www.rad.cvm.gov.br/ENET/frmConsultaExternaCVM_Resultado.aspx?"
        f"tipo_participante=CIA_ABERTA&cod_negociacao={ticker}&categoria=&"
        f"data_ini={(_agora_br()-timedelta(hours=JANELA_HORAS)).strftime('%d/%m/%Y')}&"
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

def coletar_noticias(ativos):
    """
    Coleta notícias de todas as fontes para todos os ativos.
    Ordem de prioridade: CVM → Feeds diretos → Google News
    """
    resultado = {}
    total = 0

    for ticker in ativos:
        print(f"[scraper] Buscando: {ticker}...")

        cvm     = _buscar_cvm(ticker)
        diretos = _buscar_feeds_diretos(ticker)
        google  = _buscar_google_news(ticker)

        # Deduplicação entre fontes pelo hash
        vistos = set()
        todas  = []
        for n in (cvm + diretos + google):
            if n["hash"] not in vistos:
                vistos.add(n["hash"])
                todas.append(n)

        # Limita o total por ativo
        todas = todas[:MAX_NOTICIAS_POR_ATIVO * 2]

        resultado[ticker] = todas
        total += len(todas)

    print(f"[scraper] Total de notícias novas: {total}")
    return resultado
