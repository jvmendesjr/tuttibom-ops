# Contratos — F4 (ainda não implementados)

Contratos Pydantic v2 puro para validação de saídas, espelhando o PQBR2
(`PautaEpisodio`, `RoteiroShort`, `Cena`) e adaptando para o TuttiBom:

- `Publicacao`: texto exato aprovado, arte, formato (`9:16` / `4:5`),
  rede, data, rótulo de IA ligado, sem foto de cliente, sem preço inventado.
- `Criativo`: formato, textos legíveis, zonas seguras, botões A/B.
- `Lead`: estágio do CRM (Novo → Fechado/Perdido/Adormecido), próxima
  ação + data de follow-up obrigatórias, sem dado pessoal no repo.

Validadores em `scripts/validate_*.py` e testes pytest, como no PQBR2.
Nada que falhe na validação chega à publicação.
