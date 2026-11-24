# D-012 — CRM próprio e atendimento pelo Muse (nova vertente)

**Data:** 2026-11-21
**Decidido por:** usuário
**Status:** aprovada — em teste, em worktree paralela
**Supersede / relaciona:** reabertura do Paperclip (2026-11-20, agora pausada, só ideia);
caminho Deskcomm/Ana v12-B continua vivo em produção e intocado.

## Decisão

1. **Paperclip fica pausado.** O teste em que o Paperclip criaria do zero a
   organização do TuttiBom Ops com autonomia própria fica só como ideia /
   alternativa. Nada foi criado para ele, nenhum documento, nenhum agente,
   nenhum banco. Não reviver sem o usuário levantar o tema de novo.
2. **A nova frente é o CRM próprio + atendimento feito aqui, pelo Muse.**
   O Muse implementa tudo ele mesmo (regra "sempre com você", 2026-11-13);
   nada vai para o Cursor nem para outro agente até o usuário pedir
   explicitamente para delegar.
3. **Teste paralelo, produção intocada.** Tudo nasce em worktrees `exp/*`
   a partir da `main`. A Ana viva (v12-B, publicada 2026-11-17 ~23:35),
   o número do WhatsApp, a página do Facebook, o WAHA e o Zernio não
   mudam por causa deste teste. Nenhum lead real é migrado, nenhuma
   conversa real é tocada sem uma decisão separada e supervisionada.
4. **A operação se divide em 8 setores**, cada um com um documento
   próprio em `docs/setores/` (ver `docs/setores/README.md`). Cada setor
   tem objetivo, fronteira (faz / não faz), skill e diretório, aprovações
   e critério de "deu certo". Um setor só age dentro da sua fronteira e
   passa o resto ao setor dono, nunca improvisa por cima dele.
5. **Substituição só na promoção.** Enquanto um setor está em teste, o
   documento dele é um guia da vertente nova, não um substituto. Só
   quando o setor passar no teste definido no próprio documento é que
   ele é promovido — e aí sim o documento dele substitui o equivalente
   do caminho Deskcomm. Se não passar, a worktree morre e a produção
   nem percebe.

## O que muda em relação ao caminho Deskcomm

Aproveita-se o aprendizado, não o código:

- Funil Vendas com 7 etapas, as 4 skills de função (amostra-fita,
  frete-entrega, preco-catalogo, pos-venda), roteiro de atendimento,
  ack variado, memória por contato + roteador Jev (o Jev só rotula,
  nunca recebe PII), follow-ups de silêncio e de pagamento, e as
  regras duras (frete sem valor, endereço só após pagamento confirmado,
  desconto negado, amostra física vira handoff humano).
- Deixa-se para trás o que trava hoje: teto de 27 ferramentas por
  agente, limite de 20 mil caracteres de prompt, timeout de 120 s do
  painel de teste, custo cego do `core-medio` (fora de `ai_pricing`).

## O que NÃO muda por enquanto

- Ferramentas em uso: 9Router como provedor de modelos, Camofox como
  navegador único (D-004, perfis `profile-fb` e `profile-panel`
  separados), Jev como decisor tipado, Drive como arquivo de criativos
  e planilha de assets, WhatsApp via WAHA, Messenger via Zernio.
- Regras duras da casa: nada publica, envia ou combina preço sem a
  aprovação do usuário ao texto exato (e à imagem exata, quando houver);
  sem segredo no git; sem dado de comprador no repo, no painel ou no
  Hindsight; "produtor" (José), nunca "gestor", com clientes; conversas
  sempre em português brasileiro.
- O 'Testicon' / Vocero Lab segue só como referência de funcionalidades
  úteis (laboratório com personas fictícias, sem tocar em cliente real),
  não como estrutura a copiar passo a passo. Vocero Lab continua
  deixado de lado (2026-11-12) até o usuário levantar o tema.

## Worktrees e promoção

- Primeira worktree: `tuttibom-ops-setores`, branch
  `exp/setores-nova-vertente`, base `main` `7ef854b` — só documentos
  (esta decisão + os 8 setores).
- Depois da aprovação dos documentos, a implementação se divide nas
  worktrees já combinadas: `exp/atendimento-ana` (skill da Ana),
  `exp/crm-proprio` (CRM mínimo) e `exp/marketing-criativos`
  (marketing e criativos). Se um setor passar, promovem-se mais
  worktrees dedicadas a ele.
- Critério geral de promoção da vertente: skill da Ana pronta, CRM
  mínimo rodando, e uma conversa simulada de ponta a ponta no
  laboratório — lead novo até pago ou perdido, com persona fictícia,
  sem tocar em cliente real. Só depois disso se discute um teste real
  supervisionado.

## Próximo passo

Escrever os 8 documentos de setor e, em seguida, a skill da Ana
(`skills/ana-atendimento/SKILL.md`) na worktree de atendimento,
reaproveitando o prompt v12-B e as 4 skills de função.
