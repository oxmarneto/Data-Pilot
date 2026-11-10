import argparse
import json
import os
import re
import unicodedata
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI

from src.metrics import (
    receita_total,
    total_pedidos,
    ticket_medio,
    clientes_unicos,
    taxa_cancelamento,
)


# Carrega as variáveis do arquivo .env sem exibir nem registrar a chave.
load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")

if not api_key:
    raise ValueError("OPENROUTER_API_KEY não encontrada no arquivo .env")


# Cliente e modelo do OpenRouter já usados pelo projeto.
client = OpenAI(
    api_key=api_key,
    base_url="https://openrouter.ai/api/v1",
)

MODEL = "openrouter/free"
DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "sales_clean.csv"

METRICAS = {
    "receita_total": receita_total,
    "total_pedidos": total_pedidos,
    "ticket_medio": ticket_medio,
    "clientes_unicos": clientes_unicos,
    "taxa_cancelamento": taxa_cancelamento,
}

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "receita_total",
            "description": "Calcula a receita total dos pedidos concluídos, em reais.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "total_pedidos",
            "description": "Conta os pedidos concluídos.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "ticket_medio",
            "description": "Calcula o ticket médio dos pedidos concluídos, em reais.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clientes_unicos",
            "description": "Conta os clientes únicos com pedidos concluídos.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "taxa_cancelamento",
            "description": "Calcula a taxa de cancelamento como proporção entre 0 e 1.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]


def testar_conexao():
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": "Responda apenas: conexão funcionando.",
            }
        ],
    )

    return response.choices[0].message.content


def _metricas_pedidas(pergunta):
    """Identifica métricas explicitamente pedidas para não aceitar resposta incompleta."""
    texto = unicodedata.normalize("NFKD", pergunta.casefold())
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))

    metricas = set()
    menciona_pedidos = "pedido" in texto
    if menciona_pedidos and any(
        termo in texto
        for termo in ("quantos", "quantidade", "numero de", "total de", "pedidos concluidos")
    ):
        metricas.add("total_pedidos")
    if "ticket medio" in texto or "ticketmedio" in texto:
        metricas.add("ticket_medio")
    return metricas


def _adicionar_resultados_de_ferramentas(messages, nomes, df):
    """Inclui resultados calculados pelo Python no formato esperado pelo ciclo de tools."""
    chamadas = []
    resultados = []
    for indice, nome in enumerate(sorted(nomes)):
        chamada_id = f"datapilot_{nome}_{indice}"
        chamadas.append(
            {
                "id": chamada_id,
                "type": "function",
                "function": {"name": nome, "arguments": "{}"},
            }
        )
        valor = METRICAS[nome](df)
        resultados.append(
            {
                "role": "tool",
                "tool_call_id": chamada_id,
                "content": json.dumps(
                    {"metrica": nome, "valor": valor}, ensure_ascii=False
                ),
            }
        )

    if chamadas:
        messages.append({"role": "assistant", "tool_calls": chamadas})
        messages.extend(resultados)


def _resposta_com_metricas(pergunta, resultados):
    """Fallback curto caso o modelo devolva placeholders após receber os dados."""
    metricas = _metricas_pedidas(pergunta)
    if {"total_pedidos", "ticket_medio"}.issubset(metricas):
        quantidade = resultados["total_pedidos"]
        ticket = f"{resultados['ticket_medio']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return f"Foram concluídos {quantidade} pedidos, com ticket médio de R$ {ticket}."
    return None


def responder_pergunta(pergunta, df=None, contexto=None):
    """Deixa o modelo escolher tools; as métricas são calculadas em Python.

    O CLI mantém o comportamento padrão de ler o CSV completo. A dashboard pode
    fornecer o dataframe já filtrado e um contexto para usar o mesmo agente com
    a categoria selecionada.
    """
    if df is None:
        df = pd.read_csv(DATA_PATH, sep=";", decimal=",")

    instrucao_sistema = (
        "Você é o DataPilot, um assistente de análise de vendas. "
        "Responda em português do Brasil. Para responder perguntas sobre "
        "as métricas disponíveis, use as ferramentas; não estime nem invente "
        "valores. Python calcula os resultados e você apenas os interpreta. "
        "Apresente valores monetários em reais."
    )
    if contexto:
        instrucao_sistema += f" Contexto da análise: {contexto}"

    messages = [
        {
            "role": "system",
            "content": instrucao_sistema,
        },
        {"role": "user", "content": pergunta},
    ]
    metricas_necessarias = _metricas_pedidas(pergunta)
    resultados = {}

    while True:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
        )
        message = response.choices[0].message
        if not message.tool_calls:
            faltantes = metricas_necessarias - resultados.keys()
            if faltantes:
                # Alguns modelos em openrouter/free finalizam após chamar apenas uma
                # ferramenta. Complete as métricas pedidas antes de solicitar a síntese.
                _adicionar_resultados_de_ferramentas(messages, faltantes, df)
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Use os resultados numéricos das ferramentas acima para responder "
                            "diretamente à pergunta, sem placeholders."
                        ),
                    }
                )
                for nome in faltantes:
                    resultados[nome] = METRICAS[nome](df)
                continue

            resposta = message.content or "Não foi possível gerar uma resposta."
            if re.search(r"\[[^\]]+\]", resposta):
                resposta = _resposta_com_metricas(pergunta, resultados) or resposta
            return resposta

        messages.append(message.model_dump(exclude_none=True))
        for tool_call in message.tool_calls:
            nome = tool_call.function.name
            if nome not in METRICAS:
                resultado = {"erro": f"Ferramenta desconhecida: {nome}"}
            else:
                # As métricas atuais não recebem argumentos; sempre usam o CSV limpo.
                valor = METRICAS[nome](df)
                resultado = {"metrica": nome, "valor": valor}
                resultados[nome] = valor

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(resultado, ensure_ascii=False),
                }
            )


def main():
    parser = argparse.ArgumentParser(description="Converse com o DataPilot.")
    parser.add_argument(
        "pergunta",
        nargs="?",
        help="Pergunta em linguagem natural. Se omitida, será solicitada no terminal.",
    )
    parser.add_argument(
        "--testar-conexao",
        action="store_true",
        help="Executa o teste simples de conexão com o OpenRouter.",
    )
    args = parser.parse_args()

    if args.testar_conexao:
        print(testar_conexao())
        return

    pergunta = args.pergunta or input("Faça uma pergunta sobre as vendas: ").strip()
    if not pergunta:
        parser.error("informe uma pergunta para o DataPilot")

    print(responder_pergunta(pergunta))


if __name__ == "__main__":
    main()
