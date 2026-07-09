# =============================================================================
# MONITOR DE NOTÍCIAS B3 — CONFIGURAÇÃO
# Versão GitHub Actions: variáveis sensíveis lidas via variáveis de ambiente
# (definidas como Secrets no repositório GitHub)
# =============================================================================

import os

# ── E-MAIL ────────────────────────────────────────────────────────────────────
# Lidos dos Secrets do GitHub — NÃO edite aqui, configure no repositório
EMAIL_REMETENTE    = os.environ.get("EMAIL_REMETENTE", "")
SENHA_APP          = os.environ.get("SENHA_APP", "")
EMAIL_DESTINATARIO = os.environ.get("EMAIL_DESTINATARIO", "anderson.azelha@gmail.com")

# ── ATIVOS MONITORADOS ────────────────────────────────────────────────────────
ACOES = [
    "BBDC4",  "KLBN11", "BBAS3",  "CSMG3", "BBSE3",  "CXSE3",
    "TAEE11", "CPLE3",  "ITSA4",  "GOAU4", "CMIG4",  "FIQE3", "PETR4",
]

FIIS = [
    "RECR11", "CPTS11", "VGHF11", "GZIT11", "BTLG11", "CPSH11",
    "GGRC11", "HSML11", "GARE11", "XPML11", "RZAG11", "VGIA11",
]

# Nomes amigáveis para o e-mail
NOMES = {
    "BBDC4":  "Bradesco PN",
    "KLBN11": "Klabin Units",
    "BBAS3":  "Banco do Brasil ON",
    "CSMG3":  "Copasa ON",
    "BBSE3":  "BB Seguridade ON",
    "CXSE3":  "Caixa Seguridade ON",
    "TAEE11": "Taesa Units",
    "CPLE3":  "Copel ON",
    "ITSA4":  "Itaúsa PN",
    "GOAU4":  "Gerdau Met. PN",
    "CMIG4":  "Cemig PN",
    "FIQE3":  "Unifique ON",
    "PETR4":  "Petrobras PN",
    "RECR11": "Rec Recebíveis Imobiliários",
    "CPTS11": "Capitânia Securities II",
    "VGHF11": "Valora Hedge Fund",
    "GZIT11": "Galapagos Recebíveis",
    "BTLG11": "BTG Logística",
    "CPSH11": "Capitânia Hedge",
    "GGRC11": "GGR Covepi Renda",
    "HSML11": "HSI Malls",
    "GARE11": "Autonomy Renda Urbana",
    "XPML11": "XP Malls",
    "RZAG11": "Riza Agrofiagri",
    "VGIA11": "Vgia11",
}

# ── PARÂMETROS DE BUSCA ───────────────────────────────────────────────────────
# Janela de tempo: quantas horas atrás buscar notícias
JANELA_HORAS = 5

# Número máximo de notícias por ativo por disparo
MAX_NOTICIAS_POR_ATIVO = 5

# ── BANCO DE DADOS ────────────────────────────────────────────────────────────
# Arquivo SQLite commitado no repositório para persistência entre execuções
DB_PATH = "noticias_enviadas.db"
