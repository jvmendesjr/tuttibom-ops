# TuttiBom (PC) — alvos mínimos. Sem rede, sem segredos.
.PHONY: check mcp-test venv

VENV ?= .venv

venv: $(VENV)/bin/python ## cria o venv e instala requirements.txt

$(VENV)/bin/python: requirements.txt
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install -q -r requirements.txt

check: $(VENV)/bin/python ## sintaxe do MCP + contratos F4 + pytest
	python3 -m py_compile src/tuttibom/mcp/server.py
	python3 -m py_compile src/tuttibom/__init__.py src/tuttibom/mcp/__init__.py
	python3 -m py_compile src/tuttibom/contratos/__init__.py src/tuttibom/contratos/comum.py src/tuttibom/contratos/precos.py src/tuttibom/contratos/pii.py src/tuttibom/contratos/publicacao.py src/tuttibom/contratos/criativo.py src/tuttibom/contratos/lead.py scripts/validate_contratos.py
	PYTHONPATH=src $(VENV)/bin/python -m pytest -q tests
	@echo "check ok"

mcp-test: ## lista as tools do tuttibom-mcp via stdio (ver docs/operacao/mcp-clients.md)
	./scripts/tuttibom-mcp
