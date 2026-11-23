# Prévia — definição (rascunho)

**Status:** rascunho 2026-11-22 ~23:04 — em definição com a usuária.
**Base:** regras ditadas pela usuária 2026-11-22 ~11:41 + Modo A
(2026-11-11/12) + fluxo da Biblioteca de assets (2026-11-12).

## O que já está decidido

1. A prévia é normalmente entregue em **dias úteis**.
2. Excepcionalmente o humano pode entregar **fora do horário
   comercial** — só para registro interno; a Ana **NUNCA** informa
   isso às leads.
3. O agente tem que saber **quando a prévia foi entregue**, porque
   vai para o repositório (registro no CRM).
4. No início, as prévias são **feitas pela usuária**.
5. **Modo A:** a Ana oferece a prévia como pergunta, de forma amena
   ("Quer que eu monte uma prévia para você ver como fica na fita?
   É uma simulação que eu preparo para você visualizar antes de
   confirmar..."), sem dizer "é IA" de forma seca; dispara quando os
   dados da personalização já são conhecidos; monta quando a pessoa
   aceita; envia só após o usuário aprovar a imagem exata.
6. **Biblioteca:** Muse gera → `Pendentes/` → humano aprova a imagem
   exata → pasta da ocasião + "Aprovado" na planilha + bucket → Ana
   envia.

## Fluxo (como está hoje)

1. Lead dá os dados da personalização → Ana oferece a prévia (Modo A).
2. Lead aceita → Muse gera a imagem → vai para `Pendentes/`.
3. Usuária aprova a imagem exata (ou pede outra).
4. Ana envia a prévia aprovada no canal onde a pessoa escreveu.
5. **Registro da entrega — A DECIDIR (pergunta 1).**
6. Depois da entrega: a Ana acompanha (o cliente aprovou? quer
   ajustes?) — texto A DECIDIR (pergunta 2).

## Perguntas abertas

1. **Onde fica o registro da entrega?**
   - (a) Tabela própria `previas` no CRM (lead, data/hora da
     entrega, imagem, quem aprovou) — o mais estruturado: o agente
     consulta "a prévia foi entregue? quando? qual imagem?".
   - (b) Resumo na conversa + campo na lead — o mais leve.
   - (c) Coluna na planilha da Biblioteca + resumo no CRM — a
     aprovação já vive na planilha.
2. **O que a Ana diz ao enviar a prévia?** (texto exato a aprovar.)
   **O que ela diz depois que o cliente vê?** (aprovação/ajustes.)
3. **Registro retroativo:** a entrega do Junior em 2026-11-17 08:05
   (imagem, por humano) ganha registro no formato novo? A entrega
   aconteceu de verdade; as mensagens de hoje (11:27 e PIX 19:10)
   eram teste e a prévia de segunda foi cancelada — não confundir.

## O que NÃO muda

- Nada é enviado sem a aprovação da imagem exata pela usuária.
- A Ana nunca informa às leads que uma prévia pode sair fora do
  horário comercial.
- Sem dado de comprador no repo; o registro da entrega guarda
  data/hora, imagem e lead — nada além do que o CRM já guarda.
