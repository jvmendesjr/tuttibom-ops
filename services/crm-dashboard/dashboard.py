#!/usr/bin/env python3
"""crm-dashboard — dashboard só leitura do CRM próprio, para embutir no Chatwoot.

Serve a página do funil (GET /) com os leads do CRM vivo agrupados
pelas 7 etapas, mais o resumo do catálogo e os follow-ups pendentes.
SÓ LEITURA: nenhum botão nem endpoint de escrita; o SQLite é aberto
sempre em modo read-only (`mode=ro`).

Autenticação por token na URL (`?token=...`) em GET / — o token vive
SÓ no `.env` ao lado deste arquivo (`CRM_DASHBOARD_TOKEN=...`, chmod
600, fora do git) ou na variável de ambiente de mesmo nome. O serviço
SE RECUSA a subir sem token (nunca há token padrão). GET /health é
aberto, sem token, para o systemd/monitoramento.

Somente stdlib, sem dependências.

Version: 0.2.0
"""

import hmac
import html
import json
import logging
import os
import sqlite3
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

VERSION = "0.2.0"
HERE = os.path.dirname(os.path.abspath(__file__))
HOST = os.environ.get("CRM_DASHBOARD_HOST", "0.0.0.0")
PORT = int(os.environ.get("CRM_DASHBOARD_PORT", "3022"))
DB_PATH = os.environ.get("CRM_DASHBOARD_DB", "crm.sqlite3")

ETAPAS = (
    "Novo contato",
    "Já respondi",
    "Escolhendo o produto",
    "Vai levar",
    "Aguardando pagamento",
    "Pedido pago",
    "Não comprou",
)

log = logging.getLogger("crm-dashboard")


def _load_dotenv():
    """Lê HERE/.env (KEY=valor, uma por linha) sem sobrescrever o ambiente."""
    path = os.path.join(HERE, ".env")
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip())
    except FileNotFoundError:
        pass
    except OSError as exc:
        log.warning("nao foi possivel ler .env: %s", exc)


_load_dotenv()
TOKEN = os.environ.get("CRM_DASHBOARD_TOKEN", "")


def _connect_ro(db_path):
    """Abre o SQLite SEMPRE em modo read-only, com timeout p/ escrita concorrente."""
    return sqlite3.connect(
        "file:{}?mode=ro".format(db_path), uri=True, timeout=10
    )


def read_data(db_path=DB_PATH):
    """Lê tudo que o dashboard mostra. Levanta sqlite3.Error se o DB falhar."""
    conn = _connect_ro(db_path)
    try:
        conn.row_factory = sqlite3.Row
        leads = [
            dict(r)
            for r in conn.execute(
                "SELECT id, referencia, contato_ref, canal, etapa,"
                " produto_sku, interesse, motivo_perda, proxima_acao,"
                " data_followup, previa_status, previa_entregue_em,"
                " previa_imagem_ref, endereco_coletado, criado_em,"
                " atualizado_em FROM leads ORDER BY atualizado_em DESC"
            )
        ]
        produtos = {
            r["sku"]: dict(r)
            for r in conn.execute(
                "SELECT sku, tipo, largura_mm, metragem_m,"
                " cor_impressao, preco_centavos FROM produtos ORDER BY sku"
            )
        }
        mensagens = {}
        for r in conn.execute(
            "SELECT lead_id, direcao, resumo, criado_em FROM mensagens"
            " ORDER BY criado_em, id"
        ):
            mensagens.setdefault(r["lead_id"], []).append(dict(r))
        memoria = {
            r["contato_ref"]: dict(r)
            for r in conn.execute(
                "SELECT contato_ref, interesse, ultimo_produto_sku,"
                " atualizado_em FROM memoria_contato"
            )
        }
        followups = [
            dict(r)
            for r in conn.execute(
                "SELECT f.id, f.lead_id, f.tipo, f.agendado_para,"
                " f.estado, f.criado_em, l.contato_ref, l.etapa"
                " FROM followups f JOIN leads l ON l.id = f.lead_id"
                " WHERE f.estado = 'pendente'"
                " ORDER BY f.agendado_para"
            )
        ]
    finally:
        conn.close()
    return {
        "leads": leads,
        "produtos": produtos,
        "mensagens": mensagens,
        "memoria": memoria,
        "followups": followups,
    }


def _previa_texto(lead):
    """Estágio da prévia (Modo A): — sem pedido, pendente, ou entregue
    com data e referência da imagem. NULL do banco vira '—'."""
    status = lead.get("previa_status")
    if not status:
        return "—"
    if status == "pendente":
        return "pendente"
    texto = "entregue"
    if lead.get("previa_entregue_em"):
        texto += " em {}".format(lead["previa_entregue_em"])
    if lead.get("previa_imagem_ref"):
        texto += " · {}".format(lead["previa_imagem_ref"])
    return texto


def _preco(preco_centavos):
    if preco_centavos is None:
        return "—"
    return "R$ {},{:02d}".format(preco_centavos // 100, preco_centavos % 100)


def _produto_descricao(sku, produtos):
    if not sku:
        return "—"
    prod = produtos.get(sku)
    if prod is None:
        return html.escape(sku)
    partes = [html.escape(sku)]
    if prod["tipo"] == "fita_cetim":
        partes.append(
            "fita {} mm / {} m / {}".format(
                prod["largura_mm"] or "—",
                prod["metragem_m"] or "—",
                html.escape(prod["cor_impressao"] or "—"),
            )
        )
    else:
        partes.append(html.escape(prod["tipo"]))
    partes.append(_preco(prod["preco_centavos"]))
    return " — ".join(partes)


def _campo(rotulo, valor):
    return "<p><strong>{}:</strong> {}</p>".format(
        html.escape(rotulo), valor if valor else "—"
    )


def _esc(valor):
    """html.escape que tolera NULL do banco."""
    if valor is None:
        return ""
    return html.escape(str(valor))


def render_html(data):
    """Monta a página. TODOS os valores vindos do banco passam por html.escape."""
    esc = html.escape
    leads = data["leads"]
    produtos = data["produtos"]
    mensagens = data["mensagens"]
    memoria = data["memoria"]
    followups = data["followups"]

    por_etapa = {etapa: [] for etapa in ETAPAS}
    for lead in leads:
        por_etapa.setdefault(lead["etapa"], []).append(lead)

    agora = datetime.now(timezone.utc).strftime("%d/%m/%Y %H:%M UTC")

    partes = []
    partes.append("<!DOCTYPE html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\">")
    partes.append("<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">")
    partes.append("<title>CRM TuttiBom</title>")
    partes.append("<style>")
    partes.append(
        "body{font-family:system-ui,sans-serif;margin:0 auto;max-width:760px;"
        "padding:12px;color:#222;background:#fff}"
        "h1{font-size:20px;margin:4px 0}h2{font-size:16px;margin:20px 0 6px;"
        "border-bottom:1px solid #ccc;padding-bottom:4px}"
        "h3{font-size:14px;margin:12px 0 4px}"
        ".lead{border:1px solid #ccc;border-radius:6px;padding:10px;margin:8px 0}"
        ".lead p{margin:4px 0;font-size:14px;overflow-wrap:break-word}"
        ".meta{color:#555;font-size:12px}"
        "table{border-collapse:collapse;font-size:13px;width:100%}"
        "td,th{border:1px solid #ccc;padding:4px 6px;text-align:left}"
        "ul{font-size:14px;padding-left:20px}li{margin:3px 0;overflow-wrap:break-word}"
        ".vazio{color:#555;font-size:14px}"
    )
    partes.append("</style></head><body>")
    partes.append("<h1>CRM TuttiBom</h1>")
    partes.append(
        "<p class=\"meta\">Só leitura — {} lead(s) · {} produto(s) no catálogo"
        " · atualizado em {}</p>".format(len(leads), len(produtos), esc(agora))
    )

    # --- follow-ups pendentes
    partes.append("<h2>Follow-ups pendentes</h2>")
    if followups:
        partes.append("<ul>")
        for f in followups:
            partes.append(
                "<li>{} — {} — agendado para {} (etapa: {})</li>".format(
                    esc(f["contato_ref"]),
                    esc(f["tipo"]),
                    esc(f["agendado_para"]),
                    esc(f["etapa"]),
                )
            )
        partes.append("</ul>")
    else:
        partes.append("<p class=\"vazio\">Nenhum follow-up pendente.</p>")

    # --- funil
    partes.append("<h2>Funil</h2>")
    for etapa in ETAPAS:
        da_etapa = por_etapa.get(etapa, [])
        partes.append("<h3>{} ({})</h3>".format(esc(etapa), len(da_etapa)))
        if not da_etapa:
            partes.append("<p class=\"vazio\">Sem leads nesta etapa.</p>")
            continue
        for lead in da_etapa:
            partes.append("<div class=\"lead\">")
            partes.append(
                _campo("Contato", esc(lead["contato_ref"]))
                + _campo("Canal", esc(lead["canal"]))
                + _campo(
                    "Produto",
                    _produto_descricao(lead["produto_sku"], produtos),
                )
                + _campo("Interesse", _esc(lead["interesse"]))
                + _campo("Prévia", _esc(_previa_texto(lead)))
                + _campo("Próxima ação", esc(lead["proxima_acao"]))
                + _campo("Follow-up em", _esc(lead["data_followup"]))
            )
            if lead["motivo_perda"]:
                partes.append(_campo("Motivo da perda", esc(lead["motivo_perda"])))
            partes.append(
                "<p class=\"meta\">Criado em {} · atualizado em {}</p>".format(
                    esc(lead["criado_em"]), esc(lead["atualizado_em"])
                )
            )
            mem = memoria.get(lead["contato_ref"])
            if mem:
                partes.append(
                    "<p><strong>Memória do contato:</strong> interesse {}"
                    " · último produto {}</p>".format(
                        esc(mem["interesse"]),
                        esc(mem["ultimo_produto_sku"] or "—"),
                    )
                )
            msgs = mensagens.get(lead["id"], [])
            if msgs:
                partes.append("<p><strong>Mensagens:</strong></p><ul>")
                for m in msgs:
                    partes.append(
                        "<li>[{}] {} — {}</li>".format(
                            esc(m["direcao"]),
                            esc(m["criado_em"]),
                            esc(m["resumo"]),
                        )
                    )
                partes.append("</ul>")
            partes.append("</div>")

    # --- catálogo
    partes.append("<h2>Catálogo ({} produtos)</h2>".format(len(produtos)))
    partes.append(
        "<table><tr><th>SKU</th><th>Tipo</th><th>Largura</th>"
        "<th>Metragem</th><th>Impressão</th><th>Preço</th></tr>"
    )
    for sku in sorted(produtos):
        p = produtos[sku]
        partes.append(
            "<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td>"
            "<td>{}</td><td>{}</td></tr>".format(
                esc(sku),
                esc(p["tipo"]),
                esc(str(p["largura_mm"])) if p["largura_mm"] is not None else "—",
                esc(str(p["metragem_m"])) if p["metragem_m"] is not None else "—",
                esc(p["cor_impressao"] or "—"),
                _preco(p["preco_centavos"]),
            )
        )
    partes.append("</table>")
    partes.append("</body></html>")
    return "".join(partes)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):  # log sem query string (nunca logar o token)
        log.info("%s %s", self.address_string(), self.path.split("?")[0])

    def _send(self, status, body, content_type="text/html; charset=utf-8"):
        data = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(data)

    def _unauthorized(self):
        self._send(401, "<h1>CRM TuttiBom</h1><p>Não autorizado.</p>")

    def _not_found(self):
        self._send(404, "<h1>CRM TuttiBom</h1><p>Página não encontrada.</p>")

    def _method_not_allowed(self):
        self._send(405, "<h1>CRM TuttiBom</h1><p>Método não permitido.</p>")

    def _serve_root(self):
        query = parse_qs(urlparse(self.path).query)
        token = query.get("token", [""])[0]
        if not TOKEN or not hmac.compare_digest(token, TOKEN):
            self._unauthorized()
            return
        try:
            data = read_data()
        except sqlite3.Error:
            log.exception("falha ao ler o CRM")
            self._send(
                503,
                "<h1>CRM TuttiBom</h1>"
                "<p>CRM indisponível no momento. Tente novamente.</p>",
            )
            return
        self._send(200, render_html(data))

    def _serve_health(self):
        self._send(
            200,
            json.dumps(
                {"ok": True, "service": "crm-dashboard", "version": VERSION}
            ),
            "application/json",
        )

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            self._serve_root()
        elif path == "/health":
            self._serve_health()
        else:
            self._not_found()

    def do_HEAD(self):
        self._method_not_allowed()

    def do_POST(self):
        self._method_not_allowed()

    def do_PUT(self):
        self._method_not_allowed()

    def do_PATCH(self):
        self._method_not_allowed()

    def do_DELETE(self):
        self._method_not_allowed()


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    if not TOKEN:
        print(
            "crm-dashboard: sem token — defina CRM_DASHBOARD_TOKEN no .env"
            " ou no ambiente; recusando subir sem autenticacao.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    log.info("crm-dashboard %s ouvindo em %s:%d", VERSION, HOST, PORT)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
