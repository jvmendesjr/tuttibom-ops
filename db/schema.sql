-- tuttibom-ops — esquema Supabase Postgres (RASCUNHO, v1)
-- Uso: revisar com o usuário antes de criar o projeto Supabase.
-- Regras: sem segredo, sem endpoint, sem dado pessoal de comprador na v1.
-- Drive = arquivo. Banco = índice (ponteiro, ficha, histórico).
-- Leads ficam FORA desta v1, por decisão de privacidade; notas por lead
-- continuam no Drive privado (CRM TuttiBom) até decisão separada.

create table if not exists contas (
  id uuid primary key default gen_random_uuid(),
  marca text not null,
  rede text not null, -- ex.: facebook, instagram, outra (sem fixar lista)
  nome_exibicao text not null,
  executor text not null check (executor in ('adb_s10','conector_pagina','manual')),
  created_at timestamptz not null default now(),
  unique (marca, rede, nome_exibicao)
);

create table if not exists produtos (
  id uuid primary key default gen_random_uuid(),
  nome text not null,
  tipo text not null, -- ex.: impressao_3d, fita_cetim
  especificacoes jsonb not null default '{}'::jsonb, -- medidas, cores, prazo; sem preço inventado
  created_at timestamptz not null default now()
);

create table if not exists criativos (
  id uuid primary key default gen_random_uuid(),
  produto_id uuid references produtos(id),
  nome_arquivo text not null, -- ex.: 20261030_fita-cetim_video-processo_facebook_v01.mp4
  drive_pasta text not null, -- ex.: TuttiBom/02_Criativos/
  drive_id text, -- ponteiro, nunca o arquivo em si
  formato text not null, -- imagem, video_curto, carrossel, stories
  descricao text not null,
  versao int not null default 1,
  created_at timestamptz not null default now()
);

create table if not exists publicacoes (
  id uuid primary key default gen_random_uuid(),
  conta_id uuid not null references contas(id),
  criativo_id uuid references criativos(id),
  tipo text not null check (tipo in ('anuncio','post','stories','video')),
  estado text not null check (estado in ('rascunho','aprovado','publicado','atrasado','cancelado')),
  aprovado_em timestamptz,
  publicado_em timestamptz,
  created_at timestamptz not null default now()
);

create table if not exists usos_criativo (
  id uuid primary key default gen_random_uuid(),
  criativo_id uuid not null references criativos(id),
  publicacao_id uuid references publicacoes(id),
  usado_em timestamptz not null default now()
);

create table if not exists falhas (
  id uuid primary key default gen_random_uuid(),
  tipo text not null, -- ex.: adb_fora, prompt_rede, verificacao_facebook, render_falhou, jev_baixa_confianca
  severidade text not null check (severidade in ('critica','nao_critica')),
  interrompe boolean not null,
  modulo text not null, -- marketplace, publicacoes, interacoes, painel, dispositivo
  conta_id uuid references contas(id),
  causa text, -- conhecida ou 'desconhecida'; nunca inventada
  proxima_acao text not null,
  created_at timestamptz not null default now()
);

create table if not exists metricas (
  id uuid primary key default gen_random_uuid(),
  conta_id uuid references contas(id),
  publicacao_id uuid references publicacoes(id),
  provedor text not null, -- muse, jev, notebooklm, render_local, supabase
  metrica text not null, -- tokens, custo_estimado, confianca_jev, tempo_render_s, alcance, engajamento
  valor numeric not null,
  periodo date not null,
  created_at timestamptz not null default now()
);

create table if not exists tarefas (
  id uuid primary key default gen_random_uuid(),
  conta_id uuid references contas(id),
  titulo text not null,
  estado text not null check (estado in ('pendente','em_andamento','aguardando_aprovacao','concluida','cancelada')),
  proxima_acao text,
  vencimento date,
  created_at timestamptz not null default now()
);

-- Consultas que o painel v1 vai precisar (exemplos):
-- Falhas por dia: select date_trunc('day', created_at) d, severidade, count(*) from falhas group by 1,2;
-- Falhas por período: mesma consulta com filtro created_at >= ...;
-- Usos por criativo: select criativo_id, count(*) from usos_criativo group by 1;
-- Fila por módulo/estado: select modulo/estado via publicacoes + tarefas (na v1, via ops/ até o banco entrar).
