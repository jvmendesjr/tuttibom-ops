# Workflows Temporal — F5 (ainda não implementados)

Namespace próprio `tuttibom` no mesmo Temporal Server do host
(`localhost:7233`), task queue `tuttibom-publicar`, worker próprio.

Workflow `publicar_conteudo`, espelhando `produzir_short` do PQBR2:
`preparar_arte` → `validar_texto` → `montar_rascunho` →
`publicar_s10` → `confirmar_feed`.

Diferenças para o PQBR2 (decidido 2026-11-05):

- No lugar das activities de NotebookLM e Flow, uma única activity de
  polling, `solicitar_criativo_muse`: o Paperclip pede, o Muse entrega
  o criativo como rascunho. O Muse substitui os dois papéis.
- As activities começam como stub, com aprovação humana antes de
  `publicar_s10`, e só viram automação real depois de teste ponta a
  ponta com o PC como ponto de execução do ADB.
- Salvaguardas contra a instabilidade do ADB: UiAutomator2,
  localizadores estáveis, esperas explícitas, animações desligadas,
  retries, nova checagem por screencap, fallback `adb shell input tap`.
