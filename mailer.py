# =============================================================================
# MAILER — Formatação HTML e envio por SMTP via Gmail
# =============================================================================

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone
from config import (
    EMAIL_REMETENTE, SENHA_APP, EMAIL_DESTINATARIO,
    ACOES, FIIS, NOMES
)

TZ_BR = timezone(timedelta(hours=-3))

# ─── PALETA DE CORES ──────────────────────────────────────────────────────────
COR_NAVY   = "#1F3864"
COR_AZUL   = "#2E5F9E"
COR_TEAL   = "#1ABC9C"
COR_CINZA  = "#F4F6F8"
COR_TEXTO  = "#2C2C2C"
COR_ACAO   = "#1F3864"
COR_FII    = "#145A32"
COR_CVM    = "#922B21"


# ─── HTML DO E-MAIL ──────────────────────────────────────────────────────────

def _badge_fonte(fonte: str) -> str:
    if "CVM" in fonte:
        cor_bg = "#FADBD8"
        cor_tx = COR_CVM
    else:
        cor_bg = "#D6EAF8"
        cor_tx = COR_AZUL
    return (
        f'<span style="background:{cor_bg};color:{cor_tx};font-size:11px;'
        f'font-weight:bold;padding:2px 8px;border-radius:10px;">{fonte}</span>'
    )


def _card_noticia(n: dict) -> str:
    badge = _badge_fonte(n["fonte"])
    return f"""
    <div style="background:#fff;border:1px solid #e0e0e0;border-radius:8px;
                padding:14px 18px;margin-bottom:10px;
                border-left:4px solid {COR_AZUL};">
      <div style="margin-bottom:6px;">{badge}
        <span style="color:#888;font-size:11px;margin-left:10px;">🕐 {n['data']}</span>
      </div>
      <a href="{n['link']}" style="color:{COR_TEXTO};font-size:14px;
         font-weight:600;text-decoration:none;line-height:1.4;">
        {n['titulo']}
      </a>
      <div style="margin-top:8px;">
        <a href="{n['link']}" style="color:{COR_AZUL};font-size:12px;">
          Ler notícia completa →
        </a>
      </div>
    </div>"""


def _secao_ativo(ticker: str, noticias: list, tipo: str) -> str:
    if not noticias:
        return ""

    cor_header = COR_FII if tipo == "FII" else COR_ACAO
    nome = NOMES.get(ticker, ticker)
    cards = "".join(_card_noticia(n) for n in noticias)

    return f"""
    <div style="margin-bottom:28px;">
      <div style="background:{cor_header};color:#fff;padding:10px 16px;
                  border-radius:8px 8px 0 0;display:flex;align-items:center;">
        <span style="font-size:16px;font-weight:bold;">{ticker}</span>
        <span style="font-size:13px;margin-left:10px;opacity:0.85;">— {nome}</span>
        <span style="margin-left:auto;font-size:11px;background:rgba(255,255,255,0.2);
              padding:2px 8px;border-radius:10px;">{tipo}</span>
      </div>
      <div style="border:1px solid #e0e0e0;border-top:none;border-radius:0 0 8px 8px;
                  padding:14px;">
        {cards}
      </div>
    </div>"""


def _resumo_header(total_noticias: int, ativos_com_news: int, horario: str) -> str:
    return f"""
    <div style="background:linear-gradient(135deg,{COR_NAVY},{COR_AZUL});
                color:#fff;padding:24px 28px;border-radius:12px;margin-bottom:28px;">
      <div style="font-size:22px;font-weight:bold;margin-bottom:4px;">
        📊 Monitor de Notícias — Carteira B3
      </div>
      <div style="font-size:14px;opacity:0.85;">
        Disparo das {horario} &nbsp;|&nbsp; {datetime.now(TZ_BR).strftime('%d/%m/%Y')}
      </div>
      <div style="margin-top:16px;display:flex;gap:24px;flex-wrap:wrap;">
        <div style="background:rgba(255,255,255,0.15);padding:10px 18px;border-radius:8px;">
          <div style="font-size:24px;font-weight:bold;">{total_noticias}</div>
          <div style="font-size:12px;opacity:0.85;">notícias novas</div>
        </div>
        <div style="background:rgba(255,255,255,0.15);padding:10px 18px;border-radius:8px;">
          <div style="font-size:24px;font-weight:bold;">{ativos_com_news}</div>
          <div style="font-size:12px;opacity:0.85;">ativos com novidades</div>
        </div>
      </div>
    </div>"""


def construir_html(noticias_por_ativo: dict, horario: str) -> str:
    """Monta o HTML completo do e-mail."""

    # Separa ações de FIIs e filtra apenas quem tem notícias
    secoes_acoes = ""
    secoes_fiis  = ""
    total = 0
    ativos_com_news = 0

    for ticker in ACOES:
        ns = noticias_por_ativo.get(ticker, [])
        if ns:
            secoes_acoes += _secao_ativo(ticker, ns, "Ação")
            total += len(ns)
            ativos_com_news += 1

    for ticker in FIIS:
        ns = noticias_por_ativo.get(ticker, [])
        if ns:
            secoes_fiis += _secao_ativo(ticker, ns, "FII")
            total += len(ns)
            ativos_com_news += 1

    # Se não há nenhuma notícia
    if total == 0:
        corpo_principal = """
        <div style="text-align:center;padding:40px;color:#888;">
          <div style="font-size:48px;">📭</div>
          <div style="font-size:18px;margin-top:12px;">
            Nenhuma notícia nova encontrada neste período.
          </div>
          <div style="font-size:13px;margin-top:8px;">
            Todas as notícias disponíveis já foram enviadas anteriormente.
          </div>
        </div>"""
    else:
        bloco_acoes = f"""
          <div style="font-size:18px;font-weight:bold;color:{COR_NAVY};
                      margin:0 0 16px 0;padding-bottom:8px;
                      border-bottom:2px solid {COR_TEAL};">
            📈 Ações
          </div>
          {secoes_acoes}
        """ if secoes_acoes else ""

        bloco_fiis = f"""
          <div style="font-size:18px;font-weight:bold;color:{COR_FII};
                      margin:24px 0 16px 0;padding-bottom:8px;
                      border-bottom:2px solid {COR_TEAL};">
            🏢 Fundos de Investimento Imobiliário
          </div>
          {secoes_fiis}
        """ if secoes_fiis else ""

        corpo_principal = bloco_acoes + bloco_fiis

    resumo = _resumo_header(total, ativos_com_news, horario)

    return f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#F0F2F5;font-family:Arial,Helvetica,sans-serif;">
  <div style="max-width:680px;margin:24px auto;padding:0 12px;">

    {resumo}

    <div style="background:#fff;border-radius:12px;padding:24px 28px;
                box-shadow:0 2px 8px rgba(0,0,0,0.06);">
      {corpo_principal}
    </div>

    <div style="text-align:center;padding:20px 0;color:#aaa;font-size:11px;">
      Monitor B3 — Carteira de Renda Passiva &nbsp;|&nbsp;
      Gerado automaticamente em {datetime.now(TZ_BR).strftime('%d/%m/%Y às %H:%M')} (Brasília)
      <br>As notícias são coletadas de fontes públicas. Verifique sempre as fontes originais.
    </div>
  </div>
</body>
</html>"""


# ─── ENVIO ────────────────────────────────────────────────────────────────────

def enviar_email(noticias_por_ativo: dict, horario: str) -> bool:
    """
    Monta e envia o e-mail com as notícias coletadas.
    Retorna True se enviado com sucesso.
    """
    html = construir_html(noticias_por_ativo, horario)
    data_str = datetime.now(TZ_BR).strftime("%d/%m/%Y")
    assunto = f"📊 Monitor B3 — {horario} | {data_str}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"]    = f"Monitor B3 <{EMAIL_REMETENTE}>"
    msg["To"]      = EMAIL_DESTINATARIO
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_REMETENTE, SENHA_APP)
            smtp.sendmail(EMAIL_REMETENTE, EMAIL_DESTINATARIO, msg.as_bytes())
        print(f"[mailer] E-mail enviado com sucesso para {EMAIL_DESTINATARIO}")
        return True
    except smtplib.SMTPAuthenticationError:
        print("[mailer] ERRO: Falha de autenticação. Verifique EMAIL_REMETENTE e SENHA_APP no config.py")
        return False
    except Exception as e:
        print(f"[mailer] ERRO ao enviar e-mail: {e}")
        return False
