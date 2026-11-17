# Fila de publicação

Uma linha por peça. O registro de 2026-11-01 está na seção
Histórico, sem corte. Linha nova entra só como `rascunho`, com
"Aprovado por" vazio. Esta página não aprova nada que já não
estivesse aprovado no histórico.

Estados: `rascunho` (linha nova, sem aprovação), `proposto`
(já estava na fila, sem aprovação), `aprovado`, `publicado`.

| Data | Peça | Tipo | Produto | Formato | Estado | Aprovado por | Link/identificador |
|------|------|------|---------|---------|--------|--------------|--------------------|
| 2026-11-01 | Dia 1 — piloto Feed | post (Feed) | Fita — Dourado vs. Prata | 4:5 | publicado | usuário, 2026-11-01 (texto do piloto; "Aprovado, pode publicar o Feed" — ver histórico) | Feed TuttiBom Novidade — "Conteúdo de IA · Público" |
| 2026-11-01 | Dia 1 — piloto Stories | Stories | Fita — Dourado vs. Prata | 9:16 | publicado | usuário, 2026-11-01 (mesmo texto do piloto; publicação registrada no histórico) | "Seu story" no Feed; rótulo de IA ligado |
| — | Dia 3 | Reels 15–20s + Stories | Fita de cetim — processo real em hotstamp | 9:16 | proposto | | Copy em `docs/plano-social-media-criativos.md`, seção 4. Aguardando decisão do vídeo (rosa ou branca) e aprovação. |
| — | Dia 5 | Carrossel de 3 fotos (Feed) | Combo 3D + fita — diferencial local | 4:5 | proposto | | Copy em `docs/plano-social-media-criativos.md`, seção 4. Aguardando aprovação, após Dia 1 e Dia 3. |

Publicação só depois da aprovação do texto e da mídia exatos.
Dia 3 e Dia 5 não estão aprovados.

## Histórico — Etapa 1 (Plano Diretor, 2026-11-01)

O bloco abaixo é o registro anterior, mantido. O título dizia
"NENHUMA aprovada ainda" e o fecho dizia que nenhuma linha era
publicação: isso foi escrito antes das atualizações do Dia 1
entrarem na mesma célula. A leitura atual é a tabela desta
página: Dia 1 publicado; Dia 3 e Dia 5 propostos.

## Etapa 1 (Plano Diretor, 2026-11-01) — propostas, NENHUMA aprovada ainda

| Ordem | Tipo | Produto / Tema | Estado | Texto / mídia |
|-------|------|----------------|--------|---------------|
| Dia 1 — PILOTO | Stories + Feed (foto/arte) | Fita — escolha Dourado vs. Prata | ARTE APROVADA 2026-11-01 — transferida para o S10, montagem PAUSADA, NÃO publicado, NÃO em rascunho no app | Storyboard em `templates/storyboard-publicacao-1.md`. Arte em `/sdcard/Download/tuttibom_fila/` (Stories 9:16 e Feed 4:5, JPG). SSH ok, ADB conectado ao endpoint mDNS então vigente (atualizado às 00:47, porta efêmera, não fixar), tela acordada, Facebook aberto como TuttiBom Novidade, composer aberto e fechado sem conteúdo (ponto seguro, Feed). Bloqueio 00:53: ao tocar em Galeria, o Facebook pediu "Permitir acesso ao rolo da câmera". Permissão NÃO concedida pelo Muse — aguarda decisão do usuário sobre o escopo (só fotos do piloto ou todas). Atualização 2026-11-01 ~01:16: permissão concedida pelo usuário (todas as fotos, verificada por dumpsys), arte do Feed selecionada, texto exato conferido no compositor (TuttiBom Novidade) e "Salvar como rascunho" tocado, telefone de volta ao Feed, NADA publicado. Limite honesto: ao reabrir o compositor, ele abriu vazio — a recuperação do rascunho a partir do compositor NÃO foi provada nesta sessão. Versão Stories ainda NÃO montada. Atualização 2026-11-01 ~01:49: FEED PUBLICADO. Aprovação "Aprovado, pode publicar o Feed" às 01:20, mas ADB caiu (offline, conexão recusada, mDNS NOT-FOUND 01:21 e 01:24, apesar do carregador); usuário confirmou depuração wifi ligada e ADB voltou com nova porta mDNS às 01:31:57. Rascunho de 01:16 NÃO foi recuperado (composer vazio, menu sem entrada de rascunhos), então o post foi remontado do zero com a mesma arte do Feed (cópia em /sdcard/Download/piloto-feed-hoje.jpg para aparecer no topo da galeria) e o mesmo texto exato, conferido caractere a caractere. Na tela de publicação: Público, comentários Público, publicar agora, sem story/grupos/produto/monetização, rótulo de IA LIGADO (Facebook: obrigatório para certos conteúdos realistas criados com IA; não altera texto nem imagem). COMPARTILHAR tocado, "Postando..." e post confirmado no Feed como TuttiBom Novidade, "Conteúdo de IA · Agora mesmo · Público", texto exato + arte do piloto. Primeira publicação provada via ADB. Atualização 2026-11-01 ~12:46 -03: STORIES 9:16 PUBLICADO via PC (ponto de execução ADB). Pareamento PC–S10 concluído com código do usuário às 12:35 -03; reconexão após mudança de porta via mDNS, SM-G770F confirmado; prévia 9:16 conferida (split Ateliê Celebra vs. Lembrança Especial, botões legíveis); rótulo de IA ligado antes de compartilhar; Público, WhatsApp desativado; confirmação "Seu story" no Feed. Telefone deixado no Feed, bateria 85% descarregando às 12:46 -03. Dia 1 completo nos dois formatos; calendário semanal desbloqueado. |
| Dia 3 | Reels 15–20s + Stories | Fita de cetim — processo real em hotstamp | Proposto — aguardando decisão do vídeo bruto (rosa ou branca) e aprovação | Vídeo bruto real de ~20s, com badge/máscara de privacidade se houver nome de terceiros. Copy base no `docs/plano-social-media-criativos.md`, seção 4. |
| Dia 5 | Carrossel de 3 fotos (Feed) | Combo 3D + fita — diferencial local | Proposto — aguardando aprovação, após Dia 1 e Dia 3 | Foto 1: rolos no carretel. Foto 2: detalhe 3D. Foto 3: caixa com laço genérico. Copy base no `docs/plano-social-media-criativos.md`, seção 4. |

Nenhuma linha acima é publicação, rascunho no app ou aprovação.
Publicação só via R-06, após aprovação do texto e da mídia exatos,
com screencap de prova — nos Stories, checkpoint final na
pré-visualização.

## Leitura atual

O fecho acima é o texto original do registro. A fila vigente é a
tabela no topo: Dia 1 publicado (Feed e Stories); Dia 3 e Dia 5
propostos, sem aprovador.
