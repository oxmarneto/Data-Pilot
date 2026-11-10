import pandas as pd
import streamlit as st
import plotly.express as px

from src.metrics import (
    receita_total,
    total_pedidos,
    ticket_medio,
    clientes_unicos,
    taxa_cancelamento,
)


# =========================
# CONFIGURAÇÃO
# =========================

st.set_page_config(
    page_title="DataPilot",
    page_icon="📊",
    layout="wide",
)


# =========================
# CARREGAMENTO DOS DADOS
# =========================

@st.cache_data
def carregar_dados():
    df = pd.read_csv(
        "data/sales_clean.csv",
        sep=";",
        decimal=","
    )

    df["data"] = pd.to_datetime(df["data"], errors="coerce")

    return df


df = carregar_dados()


# =========================
# TÍTULO
# =========================

st.title("DataPilot")
st.subheader("Painel de vendas")


# =========================
# FILTROS
# =========================

colunas_filtros = {
    "Categoria": "categoria",
    "Cidade": "cidade",
    "Canal": "canal",
    "Status": "status",
}

filtros_selecionados = {}
with st.sidebar:
    st.header("Filtros")
    for rotulo, coluna in colunas_filtros.items():
        opcoes = ["Todos"] + sorted(
            df[coluna].dropna().unique().tolist(),
            key=str,
        )
        filtros_selecionados[coluna] = st.selectbox(
            rotulo,
            opcoes,
        )

df_filtrado = df.copy()
for coluna, valor in filtros_selecionados.items():
    if valor != "Todos":
        df_filtrado = df_filtrado[df_filtrado[coluna] == valor]


# =========================
# MÉTRICAS
# =========================

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric(
    "Receita total",
    f"R$ {receita_total(df_filtrado):,.2f}"
)

col2.metric(
    "Pedidos concluídos",
    total_pedidos(df_filtrado)
)

col3.metric(
    "Ticket médio",
    f"R$ {ticket_medio(df_filtrado):,.2f}"
)

col4.metric(
    "Clientes únicos",
    clientes_unicos(df_filtrado)
)

col5.metric(
    "Taxa de cancelamento",
    f"{taxa_cancelamento(df_filtrado):.2%}"
)


# =========================
# RECEITA POR MÊS
# =========================

st.subheader("Receita por mês")

df_grafico = df_filtrado[
    df_filtrado["status"].isin(["concluido", "concluído"])
].copy()

df_grafico["mes"] = (
    df_grafico["data"]
    .dt.to_period("M")
    .astype(str)
)

receita_mensal = (
    df_grafico
    .groupby("mes", as_index=False)["receita"]
    .sum()
)

fig = px.line(
    receita_mensal,
    x="mes",
    y="receita",
    markers=True,
    labels={
        "mes": "Mês",
        "receita": "Receita"
    },
    title="Receita mensal"
)

fig.update_layout(
    xaxis_title="Mês",
    yaxis_title="Receita (R$)"
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# =========================
# CHAT COM O DATAPILOT
# =========================

st.subheader("Converse com o DataPilot")
st.caption(
    "Faça perguntas sobre as vendas. As respostas usam os dados filtrados "
    "pelas opções da barra lateral."
)

if "historico_chat" not in st.session_state:
    st.session_state.historico_chat = []

for mensagem in st.session_state.historico_chat:
    with st.chat_message(mensagem["role"]):
        st.markdown(mensagem["content"])

pergunta = st.chat_input("Ex.: Qual é o ticket médio?")

if pergunta:
    st.session_state.historico_chat.append(
        {"role": "user", "content": pergunta}
    )
    with st.chat_message("user"):
        st.markdown(pergunta)

    filtros_contexto = ", ".join(
        f"{rotulo.lower()}: {filtros_selecionados[coluna]}"
        for rotulo, coluna in colunas_filtros.items()
    )

    with st.chat_message("assistant"):
        with st.spinner("Analisando os dados..."):
            try:
                # Importação sob demanda mantém o dashboard disponível mesmo
                # quando a integração de IA não está configurada.
                from src.chat import responder_pergunta

                resposta = responder_pergunta(
                    pergunta,
                    df=df_filtrado,
                    contexto=f"Filtros aplicados — {filtros_contexto}",
                )
            except Exception:
                resposta = (
                    "Não foi possível consultar o assistente agora. "
                    "Verifique a configuração do OpenRouter e tente novamente."
                )
        st.markdown(resposta)

    st.session_state.historico_chat.append(
        {"role": "assistant", "content": resposta}
    )
