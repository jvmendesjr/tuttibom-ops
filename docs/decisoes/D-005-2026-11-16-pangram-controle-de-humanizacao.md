# D-005 — 2026-11-16 — Pangram (detector de IA) como controle de humanização

**Data:** 2026-11-16 ~10:25 (America/Fortaleza)
**Decisor:** usuário
**Status:** decidido (uso); integração técnica pendente

## Decisão

O Pangram (Pangram Labs, detector de conteúdo de IA, assinatura paga do usuário) entra como **etapa fixa de controle de qualidade**, não de criação:

1. **Criativos — texto público:** toda legenda, Sobre/bio, roteiro e texto na tela passa pelo Pangram **antes** de ir para a aprovação do usuário. Marcou "IA" → reescrever até soar como gente da loja. A ficha da peça registra o resultado.
2. **Ana — auditoria de tom:** amostra periódica das respostas da Ana avaliada no Pangram, gerando **relatório** para o usuário. Não altera modelo, prompt, roteador nem Jev em produção; qualquer ajuste sai como rascunho para o clique do usuário.
3. **Imagem/vídeo:** uso secundário. O conteúdo de IA já é declarado (rótulo nativo + bio), então "passar no detector" não é meta; peça com cara evidente de IA/banco de imagem é sinal para refazer com mais textura real.

## Guardrails

- Nunca enviar dado pessoal de comprador ao Pangram: amostras da Ana anonimizadas (nome, telefone, endereço removidos) antes da análise.
- Chave/API do Pangram no cofre, nunca no repo, log ou chat; um token por agente.
- O Pangram não substitui a aprovação do usuário.

## Pendente

- Confirmar se a assinatura tem API (e limites) ou só app web; definir o caminho (API no pipeline ou Camofox no app).
- Cadência e tamanho da amostra da auditoria da Ana.
