"""Runner de follow-up automático da Ana no Chatwoot — MODO PROPOR-PRIMEIRO.

Lê os follow-ups pendentes e vencidos do CRM próprio, cruza com as
conversas abertas do Chatwoot (conta 2), verifica o silêncio real e
escreve RASCUNHOS de toque em JSON no diretório de rascunhos. O runner
NUNCA envia mensagem ao cliente: quem envia é o Muse, como Ana, depois
de revisar o rascunho — e marca o follow-up como 'enviado' no CRM.

Uso:
    python3 followup.py [--db PATH] [--drafts-dir DIR]

Padrões:
    --db         /home/pc/chatwoot/crm.sqlite3 (CRM vivo; criado via
                 classe CRM se não existir — nunca o banco de teste
                 /tmp/crm-v4.sqlite3)
    --drafts-dir /home/pc/chatwoot/ana-listener/followup-drafts/

Regras (ver docs/followup-textos-modelo.md):
- Só follow-up pendente com agendado_para vencido.
- Só lead em etapa não terminal ("Pedido pago" e "Não comprou" nunca).
- Só se houver conversa ABERTA no Chatwoot para o contato do lead.
- Contato ignorado (services/chatwoot-ana/ignorados.py) é pulado em
  silêncio: sem rascunho, sem log, sem tocar no follow-up.
- Silêncio real: a última mensagem relevante da conversa é outgoing
  da Ana E não há inbound depois do agendamento (cancelar-ao-responder:
  nesse caso o follow-up é marcado 'cancelado' no CRM e não gera
  rascunho).
- Teto: máx. 3 toques em 2 dias por lead e tipo (contam os follow-ups
  já 'enviado' e os rascunhos já escritos nas últimas 48 h). O
  pagamento tem 1 toque só. Acima do teto, não gera rascunho.
- Um rascunho por follow-up: se o arquivo followup-<id>.json já
  existe no diretório, não gera outro (o rascunho aguarda decisão
  humana).

O contato do lead (contato_ref, opaco) casa com o contato do Chatwoot
pelo identifier exato ou pelos dígitos do telefone embutidos no
contato_ref (ex.: contato_ref "contato-5588997111267" casa com o
telefone +5588997111267). Quem cria o lead grava o contato_ref com o
identifier ou com os dígitos do telefone; sem isso o runner não acha
a conversa e não gera rascunho.

Saída: uma linha por rascunho escrito ("rascunho: ...") e uma por
candidato pulado ("pulado: ..."). Sem rascunhos, imprime "sem-rascunhos"
e sai 0. Nada de texto de mensagem de cliente vai para log ou stdout.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import ignorados  # noqa: E402

JANELA_TOQUES_HORAS = 48
TETO_TOQUES = 3

DB_PADRAO = "/home/pc/chatwoot/crm.sqlite3"
DRAFTS_DIR_PADRAO = "/home/pc/chatwoot/ana-listener/followup-drafts"


# ------------------------------------------------------------------ tempo
def _parse_iso(valor):
    """ISO 8601 (com Z ou offset, ou naive) -> datetime aware UTC ou None."""
    if not valor:
        return None
    texto = str(valor).strip()
    try:
        if texto.endswith("Z"):
            texto = texto[:-1] + "+00:00"
        dt = datetime.fromisoformat(texto)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _parse_ts_chatwoot(valor):
    """created_at do Chatwoot: epoch (int) ou ISO -> datetime aware UTC."""
    if valor is None:
        return None
    if isinstance(valor, (int, float)):
        return datetime.fromtimestamp(valor, tz=timezone.utc)
    return _parse_iso(valor)


def _agora_utc() -> datetime:
    return datetime.now(timezone.utc)


# ------------------------------------------------------- contato <-> Chatwoot
def _digitos(valor) -> str:
    return re.sub(r"\D", "", str(valor or ""))


def _digitos_do_contato_ref(contato_ref: str):
    """Dígitos embutidos no contato_ref opaco (ex.: o telefone).

    Devolve o maior bloco de dígitos com 8+ dígitos, ou None quando o
    contato_ref não carrega telefone (ex.: só um identifier uuid).
    """
    blocos = re.findall(r"\d+", str(contato_ref or ""))
    longos = [b for b in blocos if len(b) >= 8]
    return max(longos, key=len) if longos else None


def contato_corresponde(contato_ref: str, sender: dict) -> bool:
    """True se o sender do Chatwoot é o contato do lead."""
    if not sender:
        return False
    identifier = sender.get("identifier")
    if identifier and str(identifier) == str(contato_ref):
        return True
    fone = _digitos(sender.get("phone_number"))
    ref_dig = _digitos_do_contato_ref(contato_ref)
    if fone and ref_dig and (fone.endswith(ref_dig) or ref_dig.endswith(fone)):
        return True
    return False


# ---------------------------------------------------------------- templates
def carregar_templates(caminho: Path | None = None) -> dict:
    caminho = caminho or (HERE / "templates_followup.json")
    with open(caminho, "r", encoding="utf-8") as fh:
        return json.load(fh)


def texto_para(templates: dict, tipo: str, toque_numero: int):
    """Texto-modelo do toque, ou None se o tipo não tem esse toque."""
    grupo = templates.get(tipo) or {}
    return grupo.get(str(toque_numero))


def teto_do_tipo(templates: dict, tipo: str) -> int:
    """Último toque previsto nos textos-modelo (silêncio: 3; pagamento: 1)."""
    grupo = templates.get(tipo) or {}
    numeros = [int(k) for k in grupo if str(k).isdigit()]
    return min(max(numeros) if numeros else 0, TETO_TOQUES)


# -------------------------------------------------------------------- CRM
def _resolver_src_repo() -> Path:
    """Acha o src/ do tuttibom-ops-crm (para importar tuttibom.crm)."""
    candidatos = []
    env = os.environ.get("TUTTIBOM_OPS_REPO")
    if env:
        candidatos.append(Path(env))
    candidatos.append(HERE.parents[1])  # services/chatwoot-ana -> repo
    candidatos.append(Path("/home/pc/Workspace/tuttibom-ops-crm"))
    for base in candidatos:
        src = base / "src"
        if (src / "tuttibom" / "crm" / "store.py").is_file():
            return src
    raise RuntimeError(
        "não achei o src do tuttibom-ops-crm; defina TUTTIBOM_OPS_REPO"
    )


def abrir_crm(db_path: str):
    src = _resolver_src_repo()
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from tuttibom.crm.store import CRM  # noqa: PLC0415

    return CRM(db_path)


# ------------------------------------------------------------- Chatwoot
def _mensagens_relevantes(mensagens: list) -> list:
    """Só incoming/outgoing visíveis (fora notas privadas e atividade)."""
    relevantes = []
    for msg in mensagens or []:
        if msg.get("private"):
            continue
        if msg.get("message_type") not in (0, 1):
            continue
        criado = _parse_ts_chatwoot(msg.get("created_at"))
        if criado is None:
            continue
        relevantes.append((criado, int(msg["message_type"])))
    relevantes.sort(key=lambda item: item[0])
    return relevantes


# ------------------------------------------------------------------- runner
def _rascunhos_existentes(drafts_dir: Path, agora: datetime) -> list[dict]:
    """Rascunhos já escritos nas últimas 48 h (para o teto de toques)."""
    inicio = agora - timedelta(hours=JANELA_TOQUES_HORAS)
    achados = []
    if not drafts_dir.is_dir():
        return achados
    for caminho in sorted(drafts_dir.glob("followup-*.json")):
        try:
            with open(caminho, "r", encoding="utf-8") as fh:
                dados = json.load(fh)
        except (OSError, ValueError):
            continue
        gerado = _parse_iso(dados.get("gerado_em"))
        if gerado is not None and gerado >= inicio:
            achados.append(dados)
    return achados


def executar(db_path, drafts_dir, client=None, agora=None, templates=None):
    """Uma passada do runner. Devolve a lista de rascunhos escritos.

    `client` é o módulo chatwoot_client (ou um fake com os mesmos dois
    métodos, nos testes). `agora` permite fixar o relógio nos testes.
    """
    agora = agora or _agora_utc()
    templates = templates or carregar_templates()
    drafts_dir = Path(drafts_dir)
    drafts_dir.mkdir(parents=True, exist_ok=True)
    crm = abrir_crm(db_path)
    try:
        if client is None:
            import chatwoot_client as client  # noqa: PLC0415

        inicio_janela = agora - timedelta(hours=JANELA_TOQUES_HORAS)
        rascunhos_previos = _rascunhos_existentes(drafts_dir, agora)
        conversas = client.listar_conversas_abertas()
        mensagens_cache: dict[int, list] = {}
        escritos: list[dict] = []

        def mensagens_de(conversa_id: int) -> list:
            if conversa_id not in mensagens_cache:
                mensagens_cache[conversa_id] = _mensagens_relevantes(
                    client.ler_mensagens(conversa_id)
                )
            return mensagens_cache[conversa_id]

        def pular(lead_ref, conversa_id, motivo):
            print(f"pulado: lead={lead_ref} conversa={conversa_id} motivo={motivo}")

        for followup in crm.followups_pendentes():
            agendado = _parse_iso(followup["agendado_para"])
            if agendado is None or agendado > agora:
                continue
            lead = crm.obter_lead(followup["lead_id"])
            lead_ref = lead["referencia"]
            tipo = followup["tipo"]
            if lead["etapa"] in ("Pedido pago", "Não comprou"):
                pular(lead_ref, "-", "lead-fechado")
                continue
            conversa = None
            sender = None
            for cand in conversas:
                remetente = (cand.get("meta") or {}).get("sender") or {}
                if contato_corresponde(lead["contato_ref"], remetente):
                    conversa, sender = cand, remetente
                    break
            if conversa is None:
                pular(lead_ref, "-", "sem-conversa-aberta")
                continue
            conversa_id = conversa.get("id")
            # Contato ignorado: pular em silêncio — sem rascunho, sem
            # log, sem tocar no follow-up. (Regra do usuário, 2026-11-21.)
            if ignorados.is_ignorado(
                telefone=sender.get("phone_number"),
                identifier=sender.get("identifier"),
                nome=sender.get("name"),
            ):
                continue
            arquivo = drafts_dir / f"followup-{followup['id']}.json"
            if arquivo.exists():
                pular(lead_ref, conversa_id, "rascunho-existente")
                continue
            relevantes = mensagens_de(conversa_id)
            if not relevantes:
                pular(lead_ref, conversa_id, "sem-mensagens")
                continue
            # Cancelar-ao-responder: inbound depois do agendamento torna
            # o toque obsoleto — cancela o follow-up e não gera rascunho.
            if any(criado > agendado and tipo_msg == 0 for criado, tipo_msg in relevantes):
                crm.marcar_followup(followup["id"], "cancelado")
                print(
                    f"cancelado: lead={lead_ref} followup={followup['id']}"
                    " motivo=inbound-depois-do-agendamento"
                )
                continue
            if relevantes[-1][1] != 1:
                pular(lead_ref, conversa_id, "sem-silencio")
                continue
            # Teto: 3 toques em 2 dias por lead e tipo. Contam os
            # follow-ups já 'enviado' (pelo agendado_para) e os
            # rascunhos já escritos (pelo gerado_em) nas últimas 48 h.
            enviados = [
                f
                for f in crm.followups_enviados(lead["id"], tipo)
                if (_parse_iso(f["agendado_para"]) or agora) >= inicio_janela
            ]
            previos = [
                d
                for d in rascunhos_previos
                if d.get("lead_ref") == lead_ref and d.get("tipo") == tipo
            ]
            toque_numero = len(enviados) + len(previos) + 1
            if toque_numero > teto_do_tipo(templates, tipo):
                pular(lead_ref, conversa_id, "teto-toques")
                continue
            texto = texto_para(templates, tipo, toque_numero)
            if texto is None:
                pular(lead_ref, conversa_id, "sem-texto-modelo")
                continue
            rascunho = {
                "lead_ref": lead_ref,
                "conversation_id": conversa_id,
                "inbox_id": conversa.get("inbox_id"),
                "tipo": tipo,
                "toque_numero": toque_numero,
                "texto": texto,
                "agendado_para": followup["agendado_para"],
                "gerado_em": agora.isoformat(timespec="seconds"),
                "followup_id": followup["id"],
            }
            with open(arquivo, "w", encoding="utf-8") as fh:
                json.dump(rascunho, fh, ensure_ascii=False, indent=2)
            rascunho["arquivo"] = str(arquivo)
            rascunhos_previos.append(rascunho)
            escritos.append(rascunho)
            print(
                f"rascunho: lead={lead_ref} conversa={conversa_id}"
                f" inbox={conversa.get('inbox_id')} tipo={tipo}"
                f" toque={toque_numero} arquivo={arquivo}"
            )
        return escritos
    finally:
        crm.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Runner de follow-up da Ana (só rascunhos, nunca envia)."
    )
    parser.add_argument("--db", default=DB_PADRAO)
    parser.add_argument("--drafts-dir", default=DRAFTS_DIR_PADRAO)
    args = parser.parse_args(argv)
    try:
        escritos = executar(args.db, args.drafts_dir)
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"erro: {exc}", file=sys.stderr)
        return 2
    if not escritos:
        print("sem-rascunhos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
