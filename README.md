# Monitor de Notícias B3 — Carteira de Renda Passiva

Sistema automatizado de coleta e envio de notícias sobre ações e FIIs,
executado duas vezes ao dia via GitHub Actions (09h00 e 16h00 — Brasília).

## Ativos Monitorados

**Ações:** BBDC4, KLBN11, BBAS3, CSMG3, BBSE3, CXSE3, TAEE11, CPLE3,
ITSA4, GOAU4, CMIG4, FIQE3, PETR4

**FIIs:** RECR11, CPTS11, VGHF11, GZIT11, BTLG11, CPSH11, GGRC11,
HSML11, GARE11, XPML11, RZAG11, VGIA11

## Fontes

- Google News RSS (cobertura ampla de veículos financeiros brasileiros)
- CVM — Fatos Relevantes e Comunicados ao Mercado

## Configuração dos Secrets

| Secret | Descrição |
|---|---|
| `EMAIL_REMETENTE` | Gmail utilizado para envio |
| `SENHA_APP` | Senha de aplicativo do Gmail |
| `EMAIL_DESTINATARIO` | E-mail de destino das notícias |

## Estrutura

```
.github/workflows/monitor.yml   → Agendamento e orquestração
config.py                       → Configurações e lista de ativos
main.py                         → Script principal
scraper.py                      → Coleta de notícias
dedup.py                        → Deduplicação via SQLite
mailer.py                       → Formatação e envio do e-mail
noticias_enviadas.db            → Banco de deduplicação (auto-commitado)
```
