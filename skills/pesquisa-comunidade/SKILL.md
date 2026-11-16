# Skill: pesquisa-comunidade

Método de pesquisa multi-fonte, inspirado na agent-reach. É uma skill
de pesquisa, não de execução no S10.

## Método

1. **Procurar em várias fontes ao mesmo tempo**, não numa só: web,
   GitHub, dev.to, blogs técnicos e redes sociais. Uma fonte sozinha
   vira viés.
2. **Verificar antes de abstrair:** ler a fonte, anotar o que ela de
   fato diz, separar fato de marketing (especialmente em posts de
   ferramenta que vendem a si mesma).
3. **Abstrair, não copiar:** o que entra no repositório é o padrão
   (loop observar-agir-verificar, escada de destravamento, trava de
   escrita), não código ou comando copiado sem auditoria.
4. **Registrar a fonte** em `docs/referencias.md` com data e o que foi
   aproveitado — e o que foi descartado, com o motivo.

## O que procurar

- Soluções de navegação simulada em Android (AppAgent, Mobile-Agent,
  UI-TARS, Midscene, Maestro, Appium, Artemis e sucessores).
- Relatos de fracasso: são mais valiosos que demos. O que quebrou,
  em que tela, com que sintoma.
- Anti-padrões a descartar explicitamente (evasão de detecção,
  engajamento artificial, conta falsa).

## Limites

- Pesquisa não autoriza execução: achar uma ferramenta não significa
  instalá-la na conta principal.
- Ferramenta nova só entra no experimento após auditoria e teste na
  conta de laboratório, seguindo `docs/praticas-conta-laboratorio.md`.
