# TuttiBom (PC) — alvos mínimos. Sem rede, sem segredos.
.PHONY: check mcp-test

check: ## sintaxe do MCP + teste de listagem de tools
	python3 -m py_compile src/tuttibom/mcp/server.py
	python3 -m py_compile src/tuttibom/__init__.py src/tuttibom/mcp/__init__.py
	@echo "check ok"

mcp-test: ## lista as tools do tuttibom-mcp via stdio (ver docs/operacao/mcp-clients.md)
	./scripts/tuttibom-mcp
