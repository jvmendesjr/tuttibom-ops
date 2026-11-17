# Contratos — F4

Contratos Pydantic v2 em `src/tuttibom/contratos/`. Nada que falhe
aqui segue para publicação ou para uma ficha no repositório.

| Contrato | O que trava |
|---|---|
| `Publicacao` | Texto exato com `texto_aprovado: true`, arte, formato `9:16` ou `4:5`, rede `facebook` ou `instagram`, data ISO, `rotulo_ia: true`, `foto_de_cliente: false`. Qualquer preço no texto ou na arte falha — inclusive preço do catálogo. A legenda social não leva valor. |
| `Criativo` | Formato, overlays curtos com `legivel: true` (a legenda longa é da Publicacao), zonas seguras, botões A e B com rótulos diferentes. No `9:16`, piso de topo 220 px, base 380 px e direita 140 px. No `4:5` o piso em px ainda não está documentado: a margem tem de ser declarada e o texto não pode estar na zona morta. |
| `Lead` | Estágios do CRM local (Novo → … → Fechado / Perdido / Adormecido). Próxima ação e `data_followup` obrigatórias. Perdido exige motivo. Sem e-mail, telefone, CPF ou endereço. Preço só se for um dos 18 da captura Shopee 2026-10-30. |

O texto do piloto aprovado em 2026-11-01 está em `TEXTO_PILOTO`
(`publicacao.py`), copiado de `templates/storyboard-publicacao-1.md`.
Ele passa. Um `R$ 99,90` no mesmo texto falha.

## Validador

Um CLI com subcomandos, em vez de três scripts iguais:

```bash
PYTHONPATH=src python3 scripts/validate_contratos.py publicacao peca.json
PYTHONPATH=src python3 scripts/validate_contratos.py criativo criativo.json
PYTHONPATH=src python3 scripts/validate_contratos.py lead ficha.json
```

Sem caminho, lê JSON pelo stdin. Exit 0 válido, 1 inválido, 2 uso.

```bash
make check
```

`make check` compila o MCP e os contratos e roda `pytest` em `tests/`.
Dependências: `pydantic>=2.14` e `pytest` (ver `requirements.txt`).
