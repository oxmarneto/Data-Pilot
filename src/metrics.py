import pandas as pd


def pedidos_concluidos(df):
    """
    Retorna apenas os pedidos concluídos.
    """
    return df[df["status"].isin(["concluido", "concluído"])]


def receita_total(df):
    """
    Calcula a receita total dos pedidos concluídos.
    """
    pedidos = pedidos_concluidos(df)
    return pedidos["receita"].sum()


def total_pedidos(df):
    """
    Conta a quantidade de pedidos concluídos.
    """
    pedidos = pedidos_concluidos(df)
    return pedidos["pedido_id"].nunique()


def ticket_medio(df):
    """
    Calcula o ticket médio dos pedidos concluídos.
    """
    pedidos = total_pedidos(df)

    if pedidos == 0:
        return 0

    return receita_total(df) / pedidos


def clientes_unicos(df):
    """
    Conta clientes únicos que realizaram pedidos concluídos.
    """
    pedidos = pedidos_concluidos(df)
    return pedidos["cliente_id"].nunique()


def taxa_cancelamento(df):
    """
    Calcula a taxa de cancelamento.
    """
    total = len(df)

    if total == 0:
        return 0

    cancelados = len(
        df[df["status"] == "cancelado"]
    )

    return cancelados / total