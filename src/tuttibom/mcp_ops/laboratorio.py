"""Composição do MCP Ops. Somente dados sintéticos, sem backends de rede."""
from __future__ import annotations

import base64
import binascii
import hashlib
import re
import secrets
from dataclasses import asdict, dataclass
from pathlib import Path

from tuttibom.contratos.precos import PRECOS_SKU

from .atendimento import (
    AdaptadorAtendimento,
    FilaPendencias,
    LeituraConversa,
    MidiaEDestino,
    Transcritor,
    VerificadorAprovacaoServidor,
    montar_laboratorio,
)
from .catalogo import normalizar_funcoes
from .entregas_duraveis import DiarioEntregas
from .erros import ClienteJaAtivo, ErroOps, ErroValidacao, FuncaoIndisponivel
from .fila_persistente import FilaPersistente
from .identidade import FronteiraIdentidadeLaboratorio, RegistroIdentidade
from .nucleo import ServidorOps, SessaoOps
from .skills_operacionais import skills_para_funcao

FUNCOES_LAB = frozenset({"01.01", "01.02", "03.01"})
CLIENTES_LAB = ("ana-01", "ana-02")
CONVERSA = "conv-lab-01"
IMAGEM_REF = "img-lab-01"
TEXTO_AUDIO = "No cenário de laboratório, a pessoa pede uma fita de 22 mm."
# Cartão sintético: triângulo vermelho, círculo azul e retângulo verde.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAANgAAABkCAMAAADT9g7RAAAADFBMVEX////cIjQfZN8hjE"
    "WlytKJAAABLElEQVR42u3bsW7FIBQEUWbz//+cJk2kOJIvzxewZnoXR3SwHsPMzMzMzMzM"
    "zN4Ywg5zgbCLsqmrLsvvXgLLX+3lqshy1eGwZG8ZlGT5v8vvvu7WDEuKsjYYVGRJVdYFg4"
    "osKcu2hiV1WRMMCrJkQrYxLJmR9cCgIHsrLJmStcDgviyZkwmbgMF9WTIpa4BBQSZsHQwK"
    "smRWJqwKg4pM2DIYlGTCVsGgJnsrLJmWPQuDPlnniUFVJmwJDMoyYStgUJcJWwCDVtkQNg"
    "mDKdm2MOiVDWFzMOiVjYNgW97dQ++RnQXb8H0MWmXjONhub9DQKRtHwrbaeUCjrHGZA5+V"
    "bbOl+jhsHO66fTG8auT2SdhYvzCFp2Q/vrGop2FHunjt/wZmZmZmZmZmZvZ43xT7MGK2rK"
    "FeAAAAAElFTkSuQmCC"
)


class _TranscritorLab:
    def transcrever(self, audio: bytes, *, idioma: str = "pt") -> str:
        if audio != b"audio-sintetico-lab" or idioma != "pt":
            raise ValueError("audio_lab_desconhecido")
        return TEXTO_AUDIO


class RecusaLab(ErroOps):
    def __init__(self, codigo: str) -> None:
        self.codigo = codigo
        super().__init__()


@dataclass
class _PilhaAtendimento:
    inbox_id: str | None
    atendimento: AdaptadorAtendimento
    chat: LeituraConversa
    destino: MidiaEDestino
    verificador: VerificadorAprovacaoServidor
    envios_ficticios: list[dict]


@dataclass
class _Rascunho:
    dono: SessaoOps
    ref_interna: str
    inbox_id: str | None
    pilha: _PilhaAtendimento
    conversa: str
    geracao: int
    texto: str
    imagem: bytes | None
    chave_envio: str
    message_ids: tuple[str, ...]
    aprovacao: str | None = None
    prova_interna: str | None = None


@dataclass(frozen=True)
class BackendsAtendimento:
    fila: FilaPendencias
    chat: LeituraConversa
    destino: MidiaEDestino
    transcritor: Transcritor | None
    diario: DiarioEntregas


class Laboratorio:
    def __init__(
        self, clientes: tuple[str, ...] = CLIENTES_LAB, *,
        backends: BackendsAtendimento | None = None,
        estado_dir: Path | None = None,
        backends_por_inbox: dict[str, BackendsAtendimento] | None = None,
        clientes_http: frozenset[str] = frozenset(),
        ambiente: str = "laboratorio",
    ) -> None:
        if ambiente not in {"laboratorio", "operacao"}:
            raise ValueError("ambiente_invalido")
        if ((backends is not None and estado_dir is not None)
                or (backends_por_inbox is not None
                    and (backends is not None or estado_dir is not None))):
            raise ValueError("duas_configuracoes_de_backend")
        self.ambiente = ambiente
        self._multi_inbox = backends_por_inbox is not None
        if not all(skills_para_funcao(funcao) for funcao in FUNCOES_LAB):
            raise ValueError("funcao_sem_skill_operacional")
        self._pilhas: dict[str, _PilhaAtendimento] = {}
        if backends_por_inbox is not None:
            self._validar_backends_por_inbox(backends_por_inbox)
            for inbox_id, pilha_backends in backends_por_inbox.items():
                self._pilhas[inbox_id] = self._montar_pilha(inbox_id, pilha_backends)
            self._envios_ficticios = []
        elif backends is None:
            (self._atendimento, fila, chat, destino,
             self._verificador, _) = montar_laboratorio(transcritor=_TranscritorLab())
            self._fixture(fila, chat, destino)
            if estado_dir is not None:
                persistente = FilaPersistente(estado_dir / "fila.sqlite", inbox_ref="inbox-lab")
                for item in fila.listar_pendentes():
                    persistente.registrar(
                        message_id=item["message_id"], conversation_id=item["conversation_id"],
                    )
                diario = DiarioEntregas(estado_dir / "entregas.sqlite")
                diario.recuperar_reservas()
                self._atendimento = AdaptadorAtendimento(
                    fila=persistente, chatwoot=chat, simulador=destino,
                    transcritor=_TranscritorLab(), verificador=self._verificador, diario=diario,
                )
            self._envios_ficticios = destino.envios
            self._chat, self._destino = chat, destino
            self._pilha = _PilhaAtendimento(
                None, self._atendimento, chat, destino, self._verificador, destino.envios,
            )
        else:
            self._envios_ficticios = []
            self._chat, self._destino = backends.chat, backends.destino
            self._verificador = VerificadorAprovacaoServidor()
            self._atendimento = AdaptadorAtendimento(
                fila=backends.fila, chatwoot=self._chat, simulador=self._destino,
                transcritor=backends.transcritor, verificador=self._verificador,
                diario=backends.diario,
            )
            self._pilha = _PilhaAtendimento(
                self._inbox_dos_backends(backends), self._atendimento,
                self._chat, self._destino, self._verificador, [],
            )
        self._leituras: dict[tuple[str, str | None, str], tuple[int, frozenset[str]]] = {}
        self._rascunhos: dict[str, _Rascunho] = {}
        self._refs: dict[tuple[str, str | None, str], str] = {}
        self._envio_por_mensagem: dict[tuple[str | None, str], str] = {}
        self._envio_duravel = backends is not None or estado_dir is not None or self._multi_inbox
        self._vinculos_http = dict.fromkeys(clientes_http, "pendente")
        identidades = {nome: RegistroIdentidade(nome) for nome in clientes}
        identidades["operador-lab"] = RegistroIdentidade("operador-lab", administrador=True)
        self.servidor = ServidorOps(
            ":memory:", FronteiraIdentidadeLaboratorio(identidades),
            handlers={"ops_produto_consultar": self._produto},
            fluxos={
                "ops_atendimento_ler_conversa": self._leitura,
                "ops_atendimento_responder": self._escrita,
            },
        )
        self.clientes = {nome: self.servidor.configurar_cliente(nome) for nome in clientes}
        self._admin = self.servidor.configurar_administrador("operador-lab")

    @staticmethod
    def _validar_backends_por_inbox(
        backends_por_inbox: dict[str, BackendsAtendimento],
    ) -> None:
        if type(backends_por_inbox) is not dict or not backends_por_inbox:
            raise ValueError("backends_por_inbox_invalidos")
        backends_vistos: set[int] = set()
        diarios_vistos: set[int] = set()
        componentes_vistos: set[int] = set()
        caminhos_persistentes: list[Path] = []
        for inbox_id, backends in backends_por_inbox.items():
            if not isinstance(inbox_id, str) or re.fullmatch(r"[1-9][0-9]*", inbox_id) is None:
                raise ValueError("inbox_id_invalido")
            if not isinstance(backends, BackendsAtendimento):
                raise ValueError("backends_por_inbox_invalidos")
            if any(componente is None for componente in (
                backends.fila, backends.chat, backends.destino, backends.diario,
            )):
                raise ValueError("backends_por_inbox_invalidos")
            if id(backends) in backends_vistos:
                raise ValueError("backends_compartilhados")
            backends_vistos.add(id(backends))
            for componente in (backends.fila, backends.chat, backends.destino):
                inbox_backend = getattr(componente, "inbox_id", None)
                if inbox_backend is not None and inbox_backend != inbox_id:
                    raise ValueError("inbox_backend_divergente")
            if id(backends.diario) in diarios_vistos:
                raise ValueError("diario_compartilhado")
            diarios_vistos.add(id(backends.diario))
            recursos = [(
                backends.diario._caminho, "diario_compartilhado",
                "diario_isolamento_indeterminado",
            )]
            if getattr(backends.fila, "_caminho", None) is not None:
                recursos.append((
                    backends.fila._caminho, "fila_compartilhada",
                    "fila_isolamento_indeterminado",
                ))
            for caminho_bruto, compartilhado, indeterminado in recursos:
                try:
                    caminho = Path(caminho_bruto).resolve()
                except (OSError, TypeError, ValueError) as exc:
                    raise ValueError(indeterminado) from exc
                for anterior in caminhos_persistentes:
                    try:
                        mesmo_arquivo = caminho.samefile(anterior)
                    except FileNotFoundError:
                        mesmo_arquivo = False
                    except OSError as exc:
                        raise ValueError(indeterminado) from exc
                    if caminho == anterior or mesmo_arquivo:
                        raise ValueError(compartilhado)
                caminhos_persistentes.append(caminho)
            componentes = {
                id(backends.fila), id(backends.chat), id(backends.destino), id(backends.diario),
            }
            if componentes & componentes_vistos:
                raise ValueError("backends_compartilhados")
            componentes_vistos.update(componentes)

    @staticmethod
    def _montar_pilha(inbox_id: str, backends: BackendsAtendimento) -> _PilhaAtendimento:
        verificador = VerificadorAprovacaoServidor()
        atendimento = AdaptadorAtendimento(
            fila=backends.fila, chatwoot=backends.chat, simulador=backends.destino,
            transcritor=backends.transcritor, verificador=verificador, diario=backends.diario,
        )
        return _PilhaAtendimento(
            inbox_id, atendimento, backends.chat, backends.destino, verificador, [],
        )

    @staticmethod
    def _inbox_dos_backends(backends: BackendsAtendimento) -> str | None:
        inbox_ids = set()
        for componente in (backends.chat, backends.fila):
            inbox_id = getattr(componente, "inbox_id", None)
            if inbox_id is None:
                continue
            if not isinstance(inbox_id, str) or re.fullmatch(r"[1-9][0-9]*", inbox_id) is None:
                return None
            inbox_ids.add(inbox_id)
        return inbox_ids.pop() if len(inbox_ids) == 1 else None

    def _pilha_para(self, inbox_id: str | None) -> _PilhaAtendimento:
        if not self._multi_inbox:
            if inbox_id is not None and (
                not isinstance(inbox_id, str)
                or self._pilha.inbox_id is None
                or inbox_id != self._pilha.inbox_id
            ):
                raise RecusaLab("inbox_invalido")
            return self._pilha
        if inbox_id is None:
            raise RecusaLab("inbox_obrigatorio")
        if not isinstance(inbox_id, str) or inbox_id not in self._pilhas:
            raise RecusaLab("inbox_invalido")
        return self._pilhas[inbox_id]

    def _saida(self, pilha: _PilhaAtendimento, resultado: dict) -> dict:
        if self._multi_inbox:
            resultado["inbox_id"] = pilha.inbox_id
        return resultado

    def _ref_rascunho(self, chave: tuple[str, str | None, str]) -> str:
        ref = self._refs.get(chave)
        if ref is not None:
            return ref
        while True:
            ref = f"ras_{secrets.token_hex(16)}"
            if ref not in self._rascunhos:
                break
        self._refs[chave] = ref
        return ref

    def cliente_http_ativo(self, cliente: str) -> bool:
        return self._vinculos_http.get(cliente) == "ativo"

    @staticmethod
    def _fixture(fila, chat, destino) -> None:
        destino.registrar_imagem(IMAGEM_REF, PNG)
        chat.registrar_audio("aud-lab-01", b"audio-sintetico-lab")
        # Um cumprimento anterior e duas entradas sem legenda. Não são eventos reais.
        chat.registrar_mensagem(CONVERSA, direcao="outgoing", texto="Olá! [LAB]")
        for numero, tipo, ref in ((1, "image", IMAGEM_REF), (2, "audio", "aud-lab-01")):
            chat.registrar_mensagem(
                CONVERSA, direcao="incoming", anexos=[{"file_type": tipo, "midia_ref": ref}]
            )
            fila.enfileirar(
                message_id=f"msg-lab-{numero:02d}", conversation_id=CONVERSA,
                inbox_id="inbox-lab", contato_ref="contato-lab", recebido_em="2026-01-01T00:00:00Z",
                cumprimento={"texto": "Olá! [LAB]", "variante": 1,
                             "enviado_em": "2026-01-01T00:00:00Z"},
            )

    def limpar_sessao(self, sessao: SessaoOps) -> None:
        try:
            sessao.desconectar()
        finally:
            for chave in [c for c in self._leituras if c[0] == sessao.id]:
                del self._leituras[chave]
            for chave in [c for c in self._refs if c[0] == sessao.id]:
                ref = self._refs.pop(chave)
                del self._rascunhos[ref]

    def administrar(self, acao: str, args: dict) -> dict:
        if acao == "listar-atribuicoes":
            return {"funcoes": [
                {**f.como_dict(), "executavel_no_lab": f.id in FUNCOES_LAB}
                for f in self._admin.listar_atribuicoes()
            ]}
        if acao == "autorizar":
            ids = normalizar_funcoes(args["funcoes"])
            if not FUNCOES_LAB.issuperset(ids):
                raise FuncaoIndisponivel()
            if "01.02" in ids and "01.01" not in ids:
                raise RecusaLab("resposta_requer_leitura")
            agente = args["agente"]
            if agente not in self.clientes:
                raise ErroValidacao()
            cliente = self.clientes[agente]
            vinculo = self._vinculos_http.get(agente)
            if vinculo == "revogado":
                raise RecusaLab("credencial_http_revogada")
            if vinculo == "ativo":
                raise ClienteJaAtivo()
            aut = self._admin.autorizar(agente_id=agente, cliente=cliente, funcoes=ids)
            if vinculo == "pendente":
                recibo = cliente.ativar(aut.referencia, ids)
                self._vinculos_http[agente] = "ativo"
                return {"agente_id": agente, "funcoes": list(ids),
                        "manifesto_hash": recibo.manifesto_hash}
            return asdict(aut)
        if acao == "revogar":
            agente = args["agente"]
            revogados = self._admin.revogar_agente(agente)
            if agente in self._vinculos_http:
                self._vinculos_http[agente] = "revogado"
            return {"revogados": revogados}
        if acao == "listar-rascunhos":
            return {"rascunhos": self._listar_rascunhos()}
        if acao == "inspecionar-rascunho":
            return self._inspecionar_rascunho(**args)
        if acao == "aprovar-resposta":
            return self._aprovar(**args)
        if acao == "auditoria":
            return {"eventos": self._admin.auditoria()}
        if acao == "reconciliar-acks":
            dados = dict(args)
            inbox_id = dados.pop("inbox_id", None)
            if dados:
                raise ErroValidacao()
            pilha = self._pilha_para(inbox_id)
            if not self._multi_inbox:
                return pilha.atendimento.reconciliar_acks()
            return self._saida(pilha, pilha.atendimento.reconciliar_acks())
        raise ErroValidacao()

    @staticmethod
    def _produto(args: dict) -> dict:
        sku = args["sku"]
        preco = PRECOS_SKU.get(sku)
        if preco is None:
            raise RecusaLab("sku_desconhecido")
        return {"ok": True, "sku": sku, "preco": str(preco), "moeda": "BRL",
                "fonte": "catalogo_versionado", "disponibilidade": "nao_verificada"}

    def _listar_pendencias(self, args: dict) -> dict:
        dados = dict(args)
        inbox_id = dados.pop("inbox_id", None)
        pilha = self._pilha_para(inbox_id) if not self._multi_inbox or inbox_id is not None else None
        if not self._multi_inbox:
            return pilha.atendimento.listar_pendencias(**dados)
        limite = dados.get("limite", 20)
        if set(dados) - {"limite"}:
            return {"ok": False, "codigo": "argumento_invalido"}
        if type(limite) is not int or not 1 <= limite <= 100:
            return {"ok": False, "codigo": "argumento_invalido"}
        selecionada = pilha
        inbox_ids = ([selecionada.inbox_id] if selecionada is not None
                     else sorted(self._pilhas, key=int))
        por_inbox = {}
        for inbox in inbox_ids:
            pilha = self._pilhas[inbox]
            resultado = pilha.atendimento.listar_pendencias(limite=limite)
            if not resultado["ok"]:
                return self._saida(pilha, resultado)
            por_inbox[inbox] = [
                {**item, "inbox_id": inbox} for item in resultado["pendencias"]
            ]
        pendentes = []
        posicoes = dict.fromkeys(inbox_ids, 0)
        while len(pendentes) < limite:
            adicionou = False
            for inbox in inbox_ids:
                posicao = posicoes[inbox]
                if posicao >= len(por_inbox[inbox]):
                    continue
                pendentes.append(por_inbox[inbox][posicao])
                posicoes[inbox] += 1
                adicionou = True
                if len(pendentes) == limite:
                    break
            if not adicionou:
                break
        return {"ok": True, "codigo": None, "pendencias": pendentes}

    def _leitura(self, sessao: SessaoOps, etapa: str, args: dict) -> dict:
        if etapa == "fila":
            return self._listar_pendencias(args)
        if etapa != "executar":
            raise FuncaoIndisponivel()
        dados = dict(args)
        pilha = self._pilha_para(dados.pop("inbox_id", None))
        conversa = dados["conversa_ref"]
        result = pilha.atendimento.ler_conversa(conversa)
        chave = (sessao.id, pilha.inbox_id, conversa)
        if result["ok"]:
            digests = frozenset(
                anexo["sha256"] for msg in result["mensagens"] for anexo in msg["anexos"]
                if anexo["file_type"] == "image"
            )
            self._leituras[chave] = (pilha.atendimento.geracao_lida(conversa), digests)
            for envio in pilha.envios_ficticios:
                if envio["conversa_ref"] != conversa:
                    continue
                imagem = envio["imagem"]
                anexos = [] if imagem is None else [{
                    "file_type": "image", "midia_ref": envio["envio_ref"],
                    "bytes": len(imagem), "sha256": hashlib.sha256(imagem).hexdigest(),
                    "conteudo": imagem,
                }]
                result["mensagens"].append({
                    "direcao": "outgoing", "texto": envio["texto"], "anexos": anexos,
                })
        else:
            self._leituras.pop(chave, None)
        return self._saida(pilha, result)

    def _escrita(self, sessao: SessaoOps, etapa: str, args: dict) -> dict:
        if etapa == "preparar":
            dados = dict(args)
            pilha = self._pilha_para(dados.pop("inbox_id", None))
            hashes = frozenset(dados.pop("imagens_lidas", ()))
            conversa = dados["conversa_ref"]
            leitura = self._leituras.get((sessao.id, pilha.inbox_id, conversa))
            if leitura is None:
                raise RecusaLab("leitura_obrigatoria")
            geracao, esperados = leitura
            if pilha.chat.geracao(conversa) != geracao:
                raise RecusaLab("leitura_obsoleta")
            if hashes != esperados:
                raise RecusaLab("imagens_pendentes")
            if not dados["texto"].strip():
                raise ErroValidacao()
            chave_envio = dados["idempotency_key"]
            ids = tuple(dados["message_ids"])
            self._exigir_intento(pilha.inbox_id, chave_envio, ids)
            result = pilha.atendimento.preparar_resposta(**dados)
            if result["ok"]:
                ref_interna = result["rascunho_ref"]
                chave = (sessao.id, pilha.inbox_id, ref_interna)
                ref = self._ref_rascunho(chave)
                anterior = self._rascunhos.get(ref)
                if anterior is not None and (
                    anterior.geracao != geracao or anterior.pilha is not pilha
                ):
                    raise RecusaLab("rascunho_obsoleto")
                if anterior is None:
                    imagem = (pilha.destino.obter_imagem(dados["imagem_ref"])
                              if dados.get("imagem_ref") else None)
                    self._rascunhos[ref] = _Rascunho(
                        dono=sessao, ref_interna=ref_interna, inbox_id=pilha.inbox_id,
                        pilha=pilha, conversa=conversa, geracao=geracao,
                        texto=dados["texto"], imagem=imagem, chave_envio=chave_envio,
                        message_ids=ids,
                    )
                result["rascunho_ref"] = ref
            return self._saida(pilha, result)
        if etapa != "executar":
            raise FuncaoIndisponivel()
        ref = args["rascunho_ref"]
        rascunho = self._rascunhos.get(ref)
        if rascunho is None or rascunho.dono is not sessao:
            raise RecusaLab("rascunho_ausente")
        self._exigir_atual(rascunho)
        prova = args.get("aprovacao_ref")
        if not prova or prova != rascunho.aprovacao or rascunho.prova_interna is None:
            raise RecusaLab("aprovacao_exata_necessaria")
        self._exigir_intento(rascunho.inbox_id, rascunho.chave_envio, rascunho.message_ids)
        result = rascunho.pilha.atendimento.responder(
            rascunho_ref=rascunho.ref_interna, aprovacao_ref=rascunho.prova_interna,
        )
        if not self._envio_duravel and result.get("enviado"):
            for msg in rascunho.message_ids:
                self._envio_por_mensagem[(rascunho.inbox_id, msg)] = rascunho.chave_envio
        return self._saida(rascunho.pilha, result)

    def _exigir_intento(
        self, inbox_id: str | None, chave: str, ids: tuple[str, ...],
    ) -> None:
        if not self._envio_duravel and any(
            self._envio_por_mensagem.get((inbox_id, msg), chave) != chave for msg in ids
        ):
            raise RecusaLab("mensagem_ja_vinculada_a_envio")

    def _exigir_atual(self, rascunho: _Rascunho) -> None:
        if rascunho.geracao != rascunho.pilha.chat.geracao(rascunho.conversa):
            raise RecusaLab("rascunho_obsoleto")

    def _listar_rascunhos(self) -> list[dict]:
        itens = []
        for ref, rascunho in self._rascunhos.items():
            item = {
                "rascunho_ref": ref,
                "conversa_ref": rascunho.conversa,
                "message_ids": list(rascunho.message_ids),
                "chars": len(rascunho.texto),
                "imagem_sha256": (hashlib.sha256(rascunho.imagem).hexdigest()
                                  if rascunho.imagem is not None else None),
                "aprovado": rascunho.aprovacao is not None,
            }
            if self._multi_inbox:
                item["inbox_id"] = rascunho.inbox_id
            itens.append(item)
        return itens

    def _inspecionar_rascunho(self, *, rascunho_ref: str) -> dict:
        rascunho = self._rascunhos.get(rascunho_ref)
        if rascunho is None:
            raise RecusaLab("rascunho_ausente")
        resultado = {
            "ok": True,
            "rascunho_ref": rascunho_ref,
            "conversa_ref": rascunho.conversa,
            "message_ids": list(rascunho.message_ids),
            "texto": rascunho.texto,
            "imagem_sha256": (hashlib.sha256(rascunho.imagem).hexdigest()
                              if rascunho.imagem is not None else None),
            "imagem_base64": (base64.b64encode(rascunho.imagem).decode("ascii")
                              if rascunho.imagem is not None else None),
            "aprovado": rascunho.aprovacao is not None,
            "aprovacao_ref": rascunho.aprovacao,
        }
        return self._saida(rascunho.pilha, resultado)

    def _aprovar(
        self, *, rascunho_ref: str, conversa_ref: str, texto: str,
        imagem_base64: str | None = None, inbox_id: str | None = None,
    ) -> dict:
        pilha = self._pilha_para(inbox_id)
        rascunho = self._rascunhos.get(rascunho_ref)
        if (rascunho is None or rascunho.conversa != conversa_ref
                or rascunho.pilha is not pilha):
            raise RecusaLab("rascunho_ausente")
        if "01" not in rascunho.dono.estado()["areas"]:
            raise RecusaLab("lease_perdido")
        self._exigir_atual(rascunho)
        try:
            imagem = base64.b64decode(imagem_base64, validate=True) if imagem_base64 is not None else None
        except (ValueError, binascii.Error):
            raise ErroValidacao() from None
        if texto != rascunho.texto or imagem != rascunho.imagem:
            raise RecusaLab("conteudo_divergente")
        if rascunho.aprovacao is None:
            rascunho.prova_interna = pilha.verificador.registrar(texto=texto, imagem=imagem)
            rascunho.aprovacao = f"apr_{secrets.token_hex(16)}"
        resultado = {
            "aprovacao_ref": rascunho.aprovacao,
            "rascunho_ref": rascunho_ref,
            "imagem_sha256": hashlib.sha256(imagem).hexdigest() if imagem is not None else None,
        }
        return self._saida(pilha, resultado)
