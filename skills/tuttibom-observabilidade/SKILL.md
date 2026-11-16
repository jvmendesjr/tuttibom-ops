# Skill: tuttibom-observabilidade

- **Marca:** TuttiBom (painel agnóstico por módulo, instanciado aqui)
- **Função:** manter o painel só leitura atualizado, com falhas,
  tokens, disponibilidade e saúde do S10 — sem executar nada na conta.
- **Executor:** Muse na VM, lendo logs, `ops/` e, no futuro, Supabase.
  O painel nunca publica, responde, apaga, paga ou impulsiona.

## O que atualizar, e de onde vem

- **Mapa:** hierarquia e checkpoints, com status do último check.
- **Setores:** Marketplace, Publicações, Interações — rascunho,
  aprovado, publicado, atrasado, próxima ação.
- **Aprovações:** o que está parado esperando o usuário (título,
  produto, rede, formato). Aprovação continua na conversa.
- **Falhas:** tipo, severidade, módulo, conta/rede, horário, causa
  (conhecida ou "desconhecida", nunca inventada), impacto, próxima ação.
  Contadores por dia, semana e mês, por tipo e severidade.
- **Provedores e tokens:** status com último check (Muse, SSH, ADB,
  Facebook no S10, NotebookLM, Jev, Supabase, Drive, Mobbin, Magic
  Patterns, Figma) + tokens/custo por provedor e por tarefa.
- **Saúde do S10:** bateria, disco, memória, uptime, reinícios, último
  watchdog, último ADB FOUND, rede como "conhecida"/"nova" — nunca
  nome de rede sensível, nunca endpoint vivo.

## Regras

- **Crítica, interrompe:** ADB fora, prompt de rede sem resposta,
  verificação do Facebook, sessão expirada, publicação sem prova.
- **Não crítica, não interrompe:** métrica atrasada, Jev abaixo do
  limiar (vai para humano), render que falhou e pode ser refeito.
- **Degradação:** se custo por lote subir ou confiança do Jev cair,
  degrada para revisão humana — nunca acelera publicação.
- **Limiar a calibrar:** 3 falhas críticas do mesmo tipo em 7 dias
  disparam revisão da rotina, não retry em rajada.
- **Governança:** só o Muse edita o painel, após discussão e avaliação
  técnica, com versão registrada. Usuário só visualiza e discute.
- **Nunca no painel:** senha, token, chave, cookie, endpoint vivo,
  telefone/email/endereço de comprador, conteúdo de conversa, foto de
  cliente sem autorização.

## Saída

Snapshot do painel (`painel-v1/index.html` na v1, com dados mock
marcados até o contrato de dados reais ser aprovado) + entrada em
RELATORIO.md quando uma métrica muda de patamar (ex.: falha crítica
repetida, custo acima do limiar, S10 reiniciado).
