-- CRM próprio — esquema SQLite (nova vertente, D-012, V2)
--
-- Por que este arquivo existe separado de `db/schema.sql`:
-- o `db/schema.sql` é o rascunho Supabase v1, e ele diz explicitamente
-- que "Leads ficam FORA desta v1, por decisão de privacidade". Este
-- arquivo é o esquema do CRM próprio, local, e NÃO toca naquele.
--
-- Regras de privacidade (não negociar sem decisão do usuário):
-- - Nenhuma coluna de nome, telefone, e-mail ou endereço. O endereço
--   do cliente NÃO é guardado: só o flag `endereco_coletado` (0/1).
-- - `contato_ref` é uma referência opaca (ex.: "contato-teste-01"),
--   nunca telefone ou @usuário. A memória por contato guarda só o
--   rótulo do interesse (fita / impressao_3d / preco), nunca PII —
--   o Jev e o roteador recebem só o rótulo.
-- - `mensagens.resumo` guarda um RESUMO escrito pelo atendimento, não
--   o texto cru do cliente. Texto com PII é rejeitado pelo serviço
--   (`afirmar_sem_pii`); a conversa crua vive no canal (WAHA/Zernio),
--   não neste repo.
-- - Preços só por SKU: `produtos` é semeado a partir de
--   `tuttibom.contratos.precos.PRECOS_SKU` (captura Shopee 2026-10-30).
--   Não existe preço fora do catálogo neste banco.

CREATE TABLE IF NOT EXISTS produtos (
  sku TEXT PRIMARY KEY,
  tipo TEXT NOT NULL CHECK (tipo IN ('fita_cetim', 'impressao_3d')),
  largura_mm INTEGER,
  metragem_m INTEGER,
  cor_impressao TEXT,
  preco_centavos INTEGER NOT NULL CHECK (preco_centavos > 0)
);

-- Funil Vendas (Deskcomm, 7 etapas — ver setor 2). Os estágios do
-- contrato F4 (`contratos/lead.py`: Novo, Contatado, Qualificado...)
-- são outro vocabulário, da triagem antiga, e NÃO entram aqui; a
-- divergência está registrada em `src/tuttibom/crm/README.md`.
CREATE TABLE IF NOT EXISTS leads (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  referencia TEXT NOT NULL UNIQUE,
  contato_ref TEXT NOT NULL,
  canal TEXT NOT NULL CHECK (canal IN ('whatsapp', 'messenger')),
  etapa TEXT NOT NULL CHECK (etapa IN (
    'Novo contato', 'Já respondi', 'Escolhendo o produto', 'Vai levar',
    'Aguardando pagamento', 'Pedido pago', 'Não comprou'
  )),
  produto_sku TEXT REFERENCES produtos(sku),
  interesse TEXT CHECK (interesse IN ('fita', 'impressao_3d', 'preco')),
  motivo_perda TEXT CHECK (motivo_perda IN (
    'preco', 'desistiu', 'sem_resposta', 'produto_indisponivel',
    'prazo_nao_atende'
  )),
  proxima_acao TEXT NOT NULL,
  data_followup TEXT,
  -- Prévia (Modo A, decisão AMBOS 2026-11-22): estágio do pedido da
  -- prévia. NULL = o lead nunca pediu prévia. 'pendente' = pediu e
  -- aguarda; 'entregue' = a Ana enviou a imagem aprovada, com a data
  -- e a referência da imagem na biblioteca (`PREV-<lead>-<ocasião>-<data>`).
  previa_status TEXT CHECK (previa_status IN ('pendente', 'entregue')),
  previa_entregue_em TEXT,
  previa_imagem_ref TEXT,
  endereco_coletado INTEGER NOT NULL DEFAULT 0,
  criado_em TEXT NOT NULL,
  atualizado_em TEXT NOT NULL,
  CHECK (etapa <> 'Não comprou' OR motivo_perda IS NOT NULL)
);

CREATE TABLE IF NOT EXISTS mensagens (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lead_id INTEGER NOT NULL REFERENCES leads(id),
  direcao TEXT NOT NULL CHECK (direcao IN ('inbound', 'outbound')),
  resumo TEXT NOT NULL,
  criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS followups (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  lead_id INTEGER NOT NULL REFERENCES leads(id),
  tipo TEXT NOT NULL CHECK (tipo IN ('silencio', 'pagamento')),
  agendado_para TEXT NOT NULL,
  estado TEXT NOT NULL DEFAULT 'pendente'
    CHECK (estado IN ('pendente', 'enviado', 'cancelado')),
  criado_em TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memoria_contato (
  contato_ref TEXT PRIMARY KEY,
  interesse TEXT NOT NULL CHECK (interesse IN ('fita', 'impressao_3d', 'preco')),
  ultimo_produto_sku TEXT REFERENCES produtos(sku),
  atualizado_em TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_leads_etapa ON leads(etapa);
CREATE INDEX IF NOT EXISTS idx_leads_contato ON leads(contato_ref);
CREATE INDEX IF NOT EXISTS idx_mensagens_lead ON mensagens(lead_id);
CREATE INDEX IF NOT EXISTS idx_followups_pendente
  ON followups(lead_id, estado);
