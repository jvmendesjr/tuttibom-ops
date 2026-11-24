"""Prepara a conta e o inbox API fictícios no Chatwoot de laboratório.

Só o contêiner ``tuttibom-chatwoot-lab-chatwoot-1``. Não publica porta,
não lê configuração de produção e não imprime token. O arquivo com o
token fica dentro do contêiner, modo 600.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import subprocess
import sys

CONTAINER = "tuttibom-chatwoot-lab-chatwoot-1"
PROJETO = "tuttibom-chatwoot-lab"
REDE = "tuttibom-chatwoot-lab_isolada"
RUBY = r"""
conta_nome = "TuttiBom Lab Ficticio"
inbox_nome = "Inbox API Lab Ficticio"
email = "operador-lab@example.invalid"
arquivo = ENV.fetch("TB_LAB_ATENDIMENTO_JSON")

def linha(msg)
  STDOUT.puts msg
end

account = Account.find_by(name: conta_nome)
if account.nil?
  if Account.count.positive?
    linha "erro=lab_nao_vazio"
    exit 0
  end
  account = Account.create!(name: conta_nome)
  senha = SecureRandom.hex(24) + "Aa1!"
  user = User.new(name: "Operador Lab", email: email, password: senha, password_confirmation: senha)
  user.skip_confirmation_notification! if user.respond_to?(:skip_confirmation_notification!)
  user.skip_confirmation! if user.respond_to?(:skip_confirmation!)
  user.save!
  AccountUser.create!(account: account, user: user, role: :administrator)
  channel = Channel::Api.create!(account: account)
  Inbox.create!(account: account, name: inbox_nome, channel: channel)
else
  user = User.find_by!(email: email)
  inbox = account.inboxes.find_by!(name: inbox_nome)
  channel = inbox.channel
end

File.open(arquivo, File::WRONLY | File::CREAT | File::EXCL, 0600) do |fh|
  fh.write(JSON.generate(
    conta_id: account.id,
    inbox_id: account.inboxes.find_by!(name: inbox_nome).id,
    inbox_identifier: channel.identifier,
    token: user.access_token.token
  ))
end
linha "preparado conta=#{account.id} inbox=#{account.inboxes.find_by!(name: inbox_nome).id} arquivo=sim"
"""


def _metadados(tipo: str, nome: str, campos: tuple[str, ...]) -> list:
    proc = subprocess.run(
        ["docker", "--context", "default", "inspect", "--type", tipo, nome, "--format",
         "\n".join("{{json " + campo + "}}" for campo in campos)],
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )
    if proc.returncode:
        raise ValueError("lab_indisponivel")
    return [json.loads(linha) for linha in proc.stdout.splitlines()]


def _lab_isolado() -> bool:
    try:
        labels, redes, portas, montagens, saude = _metadados("container", CONTAINER, (
            ".Config.Labels", ".NetworkSettings.Networks", ".NetworkSettings.Ports",
            ".Mounts", ".State.Health.Status",
        ))
        interna, ipv6, opcoes, labels_rede = _metadados("network", REDE, (
            ".Internal", ".EnableIPv6", ".Options", ".Labels",
        ))
        return (
            labels.get("com.docker.compose.project") == PROJETO
            and labels.get("com.docker.compose.service") == "chatwoot"
            and set(redes) == {REDE}
            and isinstance(portas, dict) and all(not valor for valor in portas.values())
            and all(m.get("Type") == "volume" and m.get("Name") == f"{PROJETO}_anexos" for m in montagens)
            and saude == "healthy"
            and interna is True and ipv6 is False
            and opcoes.get("com.docker.network.bridge.gateway_mode_ipv4") == "isolated"
            and labels_rede.get("com.docker.compose.project") == PROJETO
            and labels_rede.get("com.docker.compose.network") == "isolada"
        )
    except (OSError, subprocess.TimeoutExpired, ValueError, AttributeError, TypeError):
        return False


def main() -> int:
    if not _lab_isolado():
        print("erro=isolamento_lab_nao_confirmado", file=sys.stderr)
        return 1
    arquivo = os.environ.get("TB_LAB_ATENDIMENTO_JSON") or (
        f"/tmp/tb-lab-{secrets.token_hex(16)}.json"
    )
    if not re.fullmatch(r"/tmp/[A-Za-z0-9_-]+\.json", arquivo):
        print("erro=arquivo_lab_invalido", file=sys.stderr)
        return 1
    proc = subprocess.run(
        ["docker", "--context", "default", "exec", "-i",
         "-e", f"TB_LAB_ATENDIMENTO_JSON={arquivo}",
         CONTAINER, "bundle", "exec", "rails", "runner", "-"],
        input=RUBY.encode(),
        capture_output=True,
        timeout=60,
        check=False,
    )
    texto = proc.stdout.decode("utf-8", "replace")
    resumo = next((linha for linha in texto.splitlines() if linha.startswith(("preparado ", "erro="))), "")
    if not resumo.startswith("preparado "):
        print(resumo or "erro=fixture_sem_resumo")
        return 1
    print(resumo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
