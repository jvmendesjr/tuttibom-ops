# tests/ — pytest dos contratos F4

`make check` roda esta pasta. Cada trava de `Publicacao`, `Criativo`
e `Lead` tem caso que passa e caso que falha. O texto do piloto passa;
preço inventado (`R$ 99,90`) falha no modelo e no CLI.

Os 18 códigos `FITA-<mm>-<m>-<COR>` e os preços da captura
2026-10-30 estão em `test_precos_catalogo.py`. Isso não consulta o
Deskcomm.
