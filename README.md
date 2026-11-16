# TuttiBom — base no PC (caminho Paperclip)

Vendas no Cariri (Juazeiro do Norte / Crato / Barbalha): fitas de cetim
personalizadas e itens impressos em 3D, pelo Facebook no S10 via ADB,
orquestrados pelo Paperclip no PC.

| Campo | Valor |
|---|---|
| Diretório (PC) | `/home/pc/Workspace/tuttibom-ops` |
| Blueprint | `docs/blueprint-inicial.md` |
| Roadmap | `docs/roadmap.md` (F0–F8) |
| Paperclip | instância 3110 (empresa TuttiBom ainda não criada) |
| Modelos | 9Router `http://127.0.0.1:20128/v1` |
| Temporal | namespace `tuttibom` (a criar, F5) |
| Memória | Hindsight bank `tuttibom` · codebase-memory projeto `TUTTIBOM` |
| MCP manutenção | `tuttibom-mcp` (stdio, só leitura) |
| Conta da loja | S10 Lite, via ADB no PC; S10 principal, Camofox só teste |

## Árvore

```
company/            # .paperclip.yaml (empresa ainda não criada)
config/             # modelos_9router.json (sem segredos)
docs/               # blueprint, roadmap, decisões, operação
src/tuttibom/       # agents, contratos (F4), mcp, qa (Jev), workflows (F5)
scripts/            # tuttibom-mcp
tests/              # pytest (F4)
work/               # trabalho local (gitignored)
```

## Regras (não negociar)

- Nada é publicado, enviado ou combinado em preço sem aprovação do
  usuário ao texto exato.
- S10 principal; Camofox só secundário em teste, sem escrita na conta.
- Mídia 100% fictícia, gerada pelo Muse; zero foto/vídeo de cliente.
- Sem dado de comprador no repo, no painel ou no Hindsight.
- Sem segredos no git, logs, MCP ou Hindsight (só nomes de env/caminhos).
- Nunca IP/porta viva de ADB ou código de pareamento em arquivo.

Detalhe: `AGENTS.md`. Estado curto: `docs/ESTADO.md`.
