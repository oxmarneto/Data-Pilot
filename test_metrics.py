import pandas as pd

from src.metrics import (
    receita_total,
    total_pedidos,
    ticket_medio,
    clientes_unicos,
    taxa_cancelamento,
)


# Carrega os dados já tratados
df = pd.read_csv(
    "data/sales_clean.csv",
    sep=";",
    decimal=","
)

print("=== MÉTRICAS DO DATAPILOT ===")

print(f"Receita total: R$ {receita_total(df):,.2f}")
print(f"Pedidos concluídos: {total_pedidos(df)}")
print(f"Ticket médio: R$ {ticket_medio(df):,.2f}")
print(f"Clientes únicos: {clientes_unicos(df)}")
print(f"Taxa de cancelamento: {taxa_cancelamento(df):.2%}")