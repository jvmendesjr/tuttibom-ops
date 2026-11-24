"""Handoff humano da Ana no Chatwoot (nova vertente, D-013).

Duas partes:

(a) ``detectar_handoff(texto)`` — função PURA, sem I/O, testável.
    Regras determinísticas a partir da skill da Ana
    (``skills/ana-atendimento/SKILL.md``, seção "Handoff humano"):
    só o que dá para detectar por texto, sem LLM.

(b) ``aplicar_handoff(conversation_id, motivo)`` — ação concreta via
    ``chatwoot_client``: criar a etiqueta ``handoff-humano`` se não
    existir, etiquetar a conversa, atribuir ao agente humano (id 2,
    tutibom) e adicionar nota privada com motivo + data/hora.

Regras duras:
- O handoff NUNCA envia mensagem ao cliente. Não existe função de
  envio neste módulo nem no ``chatwoot_client`` — de propósito.
- GUARDA PRIMEIRO: se o contato da conversa estiver em
  ``ignorados.py`` (empresas conhecidas, ex.: Mercado Livre), NÃO
  fazer nada e devolver ``{"ignorado": True}``.
- Nenhum texto de mensagem de cliente vai para log, nota ou repo:
  a nota registra só o motivo e a data/hora.

O que NÃO é detectável por regra (fica para o julgamento do agente):
- sentimento claramente negativo — "estou decepcionada", "que
  absurdo" etc. são juízo de tom, não palavra-chave;
- "Ana não souber responder" — só quem responde sabe que não sabe;
- fora de escopo genérico — "vocês fazem X?" exige conhecer o
  catálogo, não uma lista de palavras;
- assunto sensível (pagamento, dado pessoal, tema religioso de
  festa, criança) — "pagamento" aparece em conversa normal (Pix é
  o padrão); só o contexto diz se é sensível;
- suspeita de golpe sem o padrão conhecido — link estranho, pressa
  para pagar fora, pedido de código fora do padrão abaixo;
- amostra física como dúvida residual na iminência de fechar —
  só o pedido explícito de amostra é detectável; a dúvida depois
  da amostra em imagem é julgamento da conversa.
Nada disso é adivinhado por palavra-chave solta aqui.
"""

from __future__ import annotations

import os
import re
import sys
import unicodedata
from datetime import datetime, timezone

ETIQUETA = "handoff-humano"
HUMANO_ID = 2
HUMANO_NOME = "tutibom"

MOTIVOS = ("humano-explicito", "amostra-fisica", "suspeita-golpe", "pos-venda")


# ------------------------------------------------------------ normalizar
def _normalizar(texto: str) -> str:
    """Minúsculas, sem acento, só letras/números/espaços."""
    sem_acento = unicodedata.normalize("NFKD", texto or "")
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    limpo = re.sub(r"[^a-z0-9 ]", " ", sem_acento.lower())
    return re.sub(r"\s+", " ", limpo).strip()


# ------------------------------------------------------------- padrões
# Cada motivo: lista de regex (sobre o texto normalizado) ou, no caso
# do golpe, um par (âncora, palavras que precisam acompanhar a âncora).
_HUMANO_EXPLICITO = [
    r"falar com (o |a |um |uma )?(humano|atendente|pessoa real|alguem|jose|produtor|equipe)",
    r"quero (falar com )?(o |a |um |uma )?(humano|atendente|pessoa real|alguem)",
    r"posso falar com (o |a |um |uma )?(humano|atendente|pessoa real|alguem)",
    r"preciso (falar )?com (o |a |um |uma )?(humano|atendente|pessoa real)",
    r"me (passa|transfere|conecta) (para |pra )(o |a |um |uma )?(humano|atendente|pessoa real|alguem|jose|produtor|equipe)",
    r"chama (o |a |um |uma )?(humano|atendente|jose|produtor)",
    r"tem alguem (ai|que possa|para|pra)",
    r"atendimento humano",
    r"pessoa de verdade",
    r"quero um humano",
    r"quero uma pessoa real",
]

_AMOSTRA_FISICA = [
    r"amostra fisica",
    r"amostra real",
    r"amostra de verdade",
    r"manda(r)? uma amostra",
    r"me manda uma amostra",
    r"pode mandar uma amostra",
    r"envia(r)? uma amostra",
    r"quero uma amostra fisica",
]

_POS_VENDA = [
    r"nao chegou",
    r"onde esta (o )?meu pedido",
    r"cade meu pedido",
    r"rastreio",
    r"rastrear( meu pedido| o pedido)?",
    r"nao recebi (o )?meu pedido",
    r"nao recebi o pedido",
]

# Golpe: âncora + palavras que precisam aparecer junto, no mesmo texto.
_GOLPE_MERCADO_LIVRE = ("mercado livre", (
    "alerta", "acesso", "seguranca", "confira", "verifique",
    "bloqueio", "bloqueado",
))
_GOLPE_CODIGO = (
    "codigo",
    ("pagar", "pix"),
    ("agora", "urgente", "rapido", "imediatamente", "senao", "hoje"),
)


def _casa(padrao: str, texto: str):
    """Devolve o trecho que casou, ou None."""
    achado = re.search(padrao, texto)
    return achado.group(0) if achado else None


def _contem_palavra(texto: str, palavra: str) -> bool:
    return re.search(r"\b" + re.escape(palavra) + r"\b", texto) is not None


def _detectar_golpe(texto: str):
    ancora, palavras = _GOLPE_MERCADO_LIVRE
    if ancora in texto and any(_contem_palavra(texto, p) for p in palavras):
        detalhe = next(p for p in palavras if _contem_palavra(texto, p))
        return "mercado livre + " + detalhe
    ancora, pagamento, pressa = _GOLPE_CODIGO
    if (
        _contem_palavra(texto, ancora)
        and any(_contem_palavra(texto, p) for p in pagamento)
        and any(_contem_palavra(texto, p) for p in pressa)
    ):
        return "codigo + pagar/pix com pressa"
    return None


# -------------------------------------------------------------- detectar
def detectar_handoff(texto: str) -> dict | None:
    """Detecta handoff por regra. Devolve {"motivo", "regra"} ou None.

    Ordem de prioridade: suspeita de golpe primeiro (segurança),
    depois pedido explícito de humano, pós-venda e amostra física.
    """
    texto = _normalizar(texto)
    if not texto:
        return None

    regra = _detectar_golpe(texto)
    if regra:
        return {"motivo": "suspeita-golpe", "regra": regra}

    for padrao in _HUMANO_EXPLICITO:
        achado = _casa(padrao, texto)
        if achado:
            return {"motivo": "humano-explicito", "regra": achado}

    for padrao in _POS_VENDA:
        achado = _casa(padrao, texto)
        if achado:
            return {"motivo": "pos-venda", "regra": achado}

    for padrao in _AMOSTRA_FISICA:
        achado = _casa(padrao, texto)
        if achado:
            return {"motivo": "amostra-fisica", "regra": achado}

    return None


# --------------------------------------------------------------- aplicar
class _ResultadoHandoff(dict):
    """Dict do resultado de aplicar_handoff, com verdade booleana.

    O contrato deste módulo devolve dict (o que foi feito, passo a
    passo). O ouvinte (`listener.py`, do outro builder) usa o valor
    só em `if aplicado:` — e o stub que ele escreveu documentava
    `aplicar_handoff(...) -> bool`. Para os dois contratos valerem,
    o dict é falso quando nada foi aplicado (ignorado ou conversa
    não encontrada) e verdadeiro quando o handoff foi aplicado.
    """

    def __bool__(self):
        return bool(self.get("aplicado"))


def aplicar_handoff(conversation_id, motivo):
    """Aplica o handoff na conversa. Nunca envia mensagem ao cliente.

    Passos: guarda de ignorados -> criar etiqueta (se não existir)
    -> etiquetar -> atribuir ao agente 2 (tutibom) -> nota privada
    com motivo + data/hora. Devolve dict com o que foi feito.
    """
    # Import tardio de propósito: este módulo precisa ser importável
    # (para testar detectar_handoff) sem o PAT do Chatwoot.
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import chatwoot_client as client  # noqa: PLC0415
    from ignorados import is_ignorado  # noqa: PLC0415

    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    base = {
        "conversation_id": conversation_id,
        "motivo": motivo,
        "registrado_em": agora,
    }

    conversa = client.obter_conversa(conversation_id)
    if not conversa:
        return _ResultadoHandoff({**base, "ignorado": False,
                                  "aplicado": False,
                                  "erro": "conversa-nao-encontrada"})

    remetente = (conversa.get("meta") or {}).get("sender") or {}
    telefone = remetente.get("phone_number")
    identifier = remetente.get("identifier")
    nome = remetente.get("name")
    if not (telefone or identifier) and conversa.get("contact_id"):
        contato = client.obter_contato(conversa["contact_id"]) or {}
        telefone = telefone or contato.get("phone_number")
        identifier = identifier or contato.get("identifier")
        nome = nome or contato.get("name")

    empresa = is_ignorado(telefone=telefone, identifier=identifier, nome=nome)
    if empresa:
        return _ResultadoHandoff({**base, "ignorado": True,
                                  "empresa": empresa, "aplicado": False})

    etiqueta_ok = client.criar_etiqueta(ETIQUETA)
    etiquetada = client.etiquetar_conversa(conversation_id, [ETIQUETA])
    atribuida = client.atribuir_conversa(conversation_id, HUMANO_ID)
    nota_texto = (
        f"Handoff humano — motivo: {motivo}. "
        f"Registrado em {agora} (UTC) pelo handoff da Ana. "
        f"Responsável: {HUMANO_NOME} (agente {HUMANO_ID})."
    )
    nota_ok = client.adicionar_nota(conversation_id, nota_texto)

    return _ResultadoHandoff({
        **base,
        "ignorado": False,
        "aplicado": True,
        "etiqueta": ETIQUETA,
        "etiqueta_criada_ou_existente": etiqueta_ok,
        "etiquetada": etiquetada,
        "atribuida": atribuida,
        "assignee_id": HUMANO_ID,
        "nota": nota_ok,
    })
