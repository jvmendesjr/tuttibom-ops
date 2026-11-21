"""CRM próprio mínimo — TuttiBom OPS (D-012, V2).

Só o que o fluxo baixo pede: lead, funil, mensagem (resumo),
follow-up e memória por contato. Sem Deskcomm, sem rede, sem PII.
"""

from .funil import ETAPAS, INTERESSES
from .store import CRM

__all__ = ["CRM", "ETAPAS", "INTERESSES"]
