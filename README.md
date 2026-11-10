# DataPilot

> Dashboard interativo de vendas com métricas calculadas em Python e um assistente de IA para interpretar os resultados.

O DataPilot reúne indicadores de vendas, filtros e um gráfico mensal em uma aplicação feita com Streamlit. O usuário pode explorar os dados por categoria, cidade, canal e status e fazer perguntas em linguagem natural ao agente conectado ao OpenRouter.

## Funcionalidades

- Filtros laterais por **Categoria**, **Cidade**, **Canal** e **Status**, com opção **Todos**.
- Indicadores atualizados conforme os filtros:
  - **Receita total** dos pedidos concluídos.
  - **Pedidos concluídos**.
  - **Ticket médio** dos pedidos concluídos.
  - **Clientes únicos** com pedidos concluídos.
  - **Taxa de cancelamento** no conjunto filtrado.
- Gráfico de linha da receita mensal dos pedidos concluídos.
- Chat com agente de IA, usando o conjunto filtrado como contexto.
- Cálculos das métricas feitos em Python; o agente usa os resultados para interpretar e explicar os dados.

## Tecnologias

- Python e pandas para leitura, tratamento e cálculo dos dados.
- Streamlit para a interface do dashboard.
- Plotly para o gráfico de receita mensal.
- OpenRouter para o chat com IA, por meio do cliente OpenAI.

## Estrutura do projeto

```text
Data-Pilot/
├── app.py                 # Dashboard Streamlit
├── src/
│   ├── metrics.py         # Cálculos das métricas de vendas
│   └── chat.py            # Integração do agente com o OpenRouter
├── data/
│   ├── sales.csv          # Dataset sintético provisório
│   └── sales_clean.csv    # Dados tratados usados pelo dashboard
├── .env.example           # Modelo de configuração da chave de API
├── .gitignore             # Evita versionar o arquivo .env
├── requirements.txt       # Dependências principais do dashboard
├── test_metrics.py        # Testes das métricas
└── README.md
```

## Dados

O dashboard carrega `data/sales_clean.csv`. O arquivo usa `;` como separador e vírgula como separador decimal. Entre as colunas utilizadas estão `pedido_id`, `data`, `categoria`, `cliente_id`, `cidade`, `canal`, `status` e `receita`.

`data/sales.csv` é um dataset sintético provisório, criado para reproduzir a estrutura do projeto da aula. Ele poderá ser substituído pelo dataset original quando estiver disponível. `data/sales_clean.csv` contém os dados tratados consumidos atualmente pelo aplicativo.

## Instalação e execução

Requer Python instalado. No terminal, acesse a pasta do projeto e instale as dependências. O `requirements.txt` lista as bibliotecas principais do dashboard; `openai` e `python-dotenv` são usados pelo chat:

```bash
cd Data-Pilot
python -m pip install -r requirements.txt
python -m pip install openai python-dotenv
```

Inicie o dashboard:

```bash
python -m streamlit run app.py
```

O Streamlit abrirá o endereço local da aplicação no navegador.

## Configuração do agente de IA

Para usar o chat, configure uma chave de API do OpenRouter:

1. Copie `.env.example` para `.env`.
2. Preencha `OPENROUTER_API_KEY` no arquivo `.env` com sua chave.
3. Execute o dashboard conforme as instruções acima.

O arquivo `.env` está listado no `.gitignore`; mantenha sua chave fora do controle de versão. A integração usa o modelo `openrouter/free` definido em `src/chat.py`.

## Exemplos de perguntas

- Qual foi a receita total dos pedidos concluídos?
- Quantos pedidos foram concluídos?
- Qual é o ticket médio?
- Quantos clientes únicos fizeram pedidos concluídos?
- Qual é a taxa de cancelamento?
- Qual é o ticket médio na categoria selecionada?

As respostas consideram os filtros selecionados na barra lateral. As métricas disponíveis são calculadas pelo Python; o agente interpreta esses resultados em linguagem natural.

## Arquitetura resumida

1. `app.py` lê `data/sales_clean.csv` e apresenta os filtros, indicadores, gráfico e chat.
2. Os filtros são aplicados ao DataFrame e esse mesmo conjunto é usado para atualizar os indicadores, o gráfico e o contexto enviado ao agente.
3. `src/metrics.py` calcula as métricas localmente com pandas.
4. `src/chat.py` envia a pergunta e o contexto ao OpenRouter. Quando necessário, o agente solicita as ferramentas de métricas; o Python calcula os valores e devolve os resultados para a resposta em linguagem natural.
