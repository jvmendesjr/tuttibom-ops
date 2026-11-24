import os
from pathlib import Path
import subprocess
import sys

import pytest

from tuttibom.mcp_ops.fila_persistente import FilaPersistente


def test_fila_preserva_pendencias_e_ack_entre_processos(tmp_path):
    banco = tmp_path / "lab.sqlite"
    fila = FilaPersistente(banco, inbox_ref="inbox-a")
    assert fila.registrar(message_id="m2", conversation_id="c1")
    assert fila.registrar(message_id="m1", conversation_id="c1")
    assert [p["message_id"] for p in fila.listar_pendentes()] == ["m2", "m1"]
    subprocess.run(
        [sys.executable, "-B", "-c",
         "import sys; from pathlib import Path; "
         "from tuttibom.mcp_ops.fila_persistente import FilaPersistente; "
         "assert FilaPersistente(Path(sys.argv[1]), inbox_ref='inbox-a')."
         "marcar_entregues(['m1', 'inexistente']) == ['m1']", str(banco)],
        env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")},
        check=True, timeout=5,
    )
    nova = FilaPersistente(banco, inbox_ref="inbox-a")
    assert not nova.registrar(message_id="m1", conversation_id="c1")
    assert nova.obter("m1")["estado"] == "entregue"
    assert [p["message_id"] for p in nova.listar_pendentes()] == ["m2"]
    assert nova.marcar_entregues(["m1"]) == []


def test_fila_escopo_de_inbox_e_mensagem_nao_troca_de_conversa(tmp_path):
    banco = tmp_path / "lab.sqlite"
    fila = FilaPersistente(banco, inbox_ref="inbox-a")
    outra = FilaPersistente(banco, inbox_ref="inbox-b")
    assert fila.registrar(message_id="m1", conversation_id="c1")
    assert outra.obter("m1") is None
    assert outra.marcar_entregues(["m1"]) == []
    assert fila.obter("m1")["estado"] == "pendente"
    with pytest.raises(ValueError, match="mensagem_em_outra_conversa"):
        fila.registrar(message_id="m1", conversation_id="c2")
    assert fila.obter("m1")["conversation_id"] == "c1"
