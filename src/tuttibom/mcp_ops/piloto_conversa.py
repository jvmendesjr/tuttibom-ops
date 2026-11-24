"""Cerca de uma conversa para injeção sintética; não é um listener/webhook."""
from __future__ import annotations

import re
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from .atendimento import EnvioNaoEfetuado
from .chatwoot_backend_lab import ChatwootBackendLab, LeituraLab
from .chatwoot_isolado import ChatwootIsolado
from .fila_persistente import FilaPersistente

_ID_ROTA = re.compile(r"[1-9][0-9]{0,8}")
_ID_MSG = re.compile(r"[1-9][0-9]{0,17}")
_CAMPOS_EVENTO = frozenset({
    "account_id", "inbox_id", "conversation_id", "message_id", "message_type", "private",
})


def _id(valor: object, formato: re.Pattern[str] = _ID_ROTA) -> str | None:
    if type(valor) is int and 0 < valor < 10**18:
        valor = str(valor)
    if type(valor) is str and formato.fullmatch(valor):
        return valor
    return None


@dataclass(frozen=True, init=False)
class EscopoPiloto:
    conta_id: str
    inbox_id: str
    conversa_id: str

    def __init__(self, conta_id: int | str, inbox_id: int | str, conversa_id: int | str) -> None:
        conta, inbox, conversa = map(_id, (conta_id, inbox_id, conversa_id))
        if conta is None or inbox is None or conversa is None:
            raise ValueError("escopo_piloto_invalido")
        object.__setattr__(self, "conta_id", conta)
        object.__setattr__(self, "inbox_id", inbox)
        object.__setattr__(self, "conversa_id", conversa)

    def corresponde(self, conta_id: object, inbox_id: object, conversa_id: object) -> bool:
        return (_id(conta_id), _id(inbox_id), _id(conversa_id)) == (
            self.conta_id, self.inbox_id, self.conversa_id,
        )

    @property
    def fila_ref(self) -> str:
        # A unicidade (inbox_ref, message_id) da fila fica no escopo todo.
        return f"piloto-{self.conta_id}-{self.inbox_id}-{self.conversa_id}"


def permite_envio_legado(
    escopo_ativo: EscopoPiloto | None, *,
    conta_id: object, inbox_id: object, conversa_id: object,
) -> bool:
    """Consultar config confiável e chamar no último ponto antes de enviar.

    None é desativação explícita. Rota/config malformada não autoriza envio.
    Para config válida, só a rota exata do piloto é recusada.
    """
    rota = (_id(conta_id), _id(inbox_id), _id(conversa_id))
    if None in rota:
        return False
    if escopo_ativo is None:
        return True
    return type(escopo_ativo) is EscopoPiloto and not escopo_ativo.corresponde(*rota)


class EntradaPiloto:
    """Injeta apenas metadados normalizados de uma fonte sintética confiável.

    Não autentica webhooks e não consulta a existência de mensagens. O host
    fornece o escopo ativo a cada operação; None suspende a fila sem apagá-la.
    """

    def __init__(
        self, caminho_fila: Path, *, escopo: EscopoPiloto,
        obter_escopo_ativo: Callable[[], EscopoPiloto | None],
    ) -> None:
        if type(escopo) is not EscopoPiloto or not callable(obter_escopo_ativo):
            raise ValueError("escopo_piloto_invalido")
        self._escopo = escopo
        self._obter_escopo_ativo = obter_escopo_ativo
        self._fila = FilaPersistente(caminho_fila, inbox_ref=escopo.fila_ref)

    @property
    def escopo(self) -> EscopoPiloto:
        return self._escopo

    def ativo(self) -> bool:
        try:
            atual = self._obter_escopo_ativo()
        except Exception:
            # A recusa ocorre antes de qualquer tentativa de envio ou entrada.
            return False
        return type(atual) is EscopoPiloto and atual == self._escopo

    def receber(self, evento: object) -> dict:
        if not self.ativo():
            return {"ok": False, "inserido": False, "codigo": "piloto_inativo"}
        if not isinstance(evento, Mapping) or evento.keys() != _CAMPOS_EVENTO:
            return {"ok": False, "inserido": False, "codigo": "evento_invalido"}
        if not self._escopo.corresponde(evento["account_id"], evento["inbox_id"], evento["conversation_id"]):
            return {"ok": False, "inserido": False, "codigo": "fora_do_piloto"}
        mensagem = _id(evento["message_id"], _ID_MSG)
        if mensagem is None:
            return {"ok": False, "inserido": False, "codigo": "evento_invalido"}
        tipo = evento["message_type"]
        incoming = (type(tipo) is int and tipo == 0) or (type(tipo) is str and tipo == "incoming")
        if evento["private"] is not False or not incoming:
            return {"ok": False, "inserido": False, "codigo": "evento_nao_publico_incoming"}
        inserido = self._fila.registrar(message_id=mensagem, conversation_id=self._escopo.conversa_id)
        return {"ok": True, "inserido": inserido, "codigo": None}

    def listar_pendentes(self, limite: int = 20) -> list[dict]:
        return self._fila.listar_pendentes(limite) if self.ativo() else []

    def obter(self, message_id: str) -> dict | None:
        return self._fila.obter(message_id) if self.ativo() else None

    def marcar_entregues(self, message_ids: Sequence[str]) -> list[str]:
        return self._fila.marcar_entregues(message_ids) if self.ativo() else []


class BackendPilotoChatwoot:
    """Leitura, mídia e destino do núcleo, com o Chatwoot isolado já escopado."""

    def __init__(self, entrada: EntradaPiloto, chatwoot: ChatwootIsolado) -> None:
        self._entrada = entrada
        self._chatwoot = chatwoot
        if not self._mesmo_escopo(entrada.escopo.conversa_id):
            raise ValueError("chatwoot_fora_do_piloto")
        self._backend = ChatwootBackendLab(chatwoot, conversa_ref=entrada.escopo.conversa_id)

    def _mesmo_escopo(self, conversa_ref: str) -> bool:
        return self._entrada.escopo.corresponde(
            self._chatwoot.conta_id, self._chatwoot.inbox_id, conversa_ref,
        )

    def _permite(self, conversa_ref: str) -> bool:
        return self._mesmo_escopo(conversa_ref) and self._entrada.ativo()

    def ler_mensagens(self, conversa_ref: str) -> list[dict] | None:
        if not self._permite(conversa_ref):
            return None
        return self._backend.ler_mensagens(self._entrada.escopo.conversa_id)

    def geracao(self, conversa_ref: str) -> int:
        if not self._permite(conversa_ref):
            raise LeituraLab("conversa_fora_do_piloto")
        return self._backend.geracao(self._entrada.escopo.conversa_id)

    def obter_audio(self, midia_ref: str) -> bytes:
        if not self._permite(self._entrada.escopo.conversa_id):
            raise LeituraLab("conversa_fora_do_piloto")
        return self._backend.obter_audio(midia_ref)

    def obter_imagem(self, midia_ref: str) -> bytes:
        if not self._permite(self._entrada.escopo.conversa_id):
            raise LeituraLab("conversa_fora_do_piloto")
        return self._backend.obter_imagem(midia_ref)

    def enviar(
        self, *, conversa_ref: str, texto: str, imagem: bytes | None, idempotency_key: str,
    ) -> dict:
        if not self._permite(conversa_ref):
            raise EnvioNaoEfetuado("conversa_fora_do_piloto")
        return self._backend.enviar(
            conversa_ref=self._entrada.escopo.conversa_id, texto=texto, imagem=imagem,
            idempotency_key=idempotency_key,
        )
