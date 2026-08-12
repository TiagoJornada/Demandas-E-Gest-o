import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime, timedelta


# ===============================
# CONFIGURAÇÃO
# ===============================

st.set_page_config(
    page_title="Gestão UDI",
    page_icon="📋",
    layout="wide"
)


URL_APPS_SCRIPT = (
"https://script.google.com/macros/s/"
"AKfycbyiXsKrvhVW0mMig394R4280TSd-Jif0tUYaxh259Wjk58M3bihGVgZRIf0i8UIoWff"
"/exec"
)


CATEGORIAS = [
    "Médico",
    "Residente",
    "Físico Médico",
    "Farmacêutico",
    "Técnico em Radiologia",
    "Técnico em Enfermagem",
    "Enfermagem",
    "Administrativo",
]


# Senha de acesso à área confidencial (chefia/supervisão).
# Configurada como variável de ambiente no Render (Settings > Environment),
# nunca escrita diretamente aqui no código.
SENHA_CHEFIA = os.getenv("SENHA_CHEFIA", "")


# ===============================
# FUNÇÕES GOOGLE SHEETS
# ===============================

def salvar_google(aba, linha):

    dados = {
        "aba": aba,
        "linha": linha
    }

    resposta = requests.post(
        URL_APPS_SCRIPT,
        json=dados
    )

    return resposta.text



def ler_google(aba):

    resposta = requests.get(
        URL_APPS_SCRIPT,
        params={"aba": aba}
    )

    try:
        dados = resposta.json()
    except ValueError:
        raise RuntimeError(
            "O Google Apps Script não retornou dados em formato válido "
            "para leitura (status HTTP "
            f"{resposta.status_code}). "
            "É provável que o script publicado ainda não tenha suporte "
            "para leitura (função doGet)."
        )

    if len(dados) > 1:
        return pd.DataFrame(
            dados[1:],
            columns=dados[0]
        )

    return pd.DataFrame()



# ===============================
# ESTILO
# ===============================

st.markdown("""
<style>

.titulo{
font-size:32px;
font-weight:700;
}

.card{
background:#f1f3f6;
padding:20px;
border-radius:12px;
text-align:center;
}

.numero{
font-size:30px;
font-weight:bold;
}

</style>
""", unsafe_allow_html=True)


st.markdown(
"""
<div class="titulo">
📋 Gestão UDI
</div>

Livro de registro de ocorrências do setor

""",
unsafe_allow_html=True
)



# ===============================
# TELA DE CONSULTA (reutilizável)
# ===============================

def tela_consulta(aba):

    col_periodo, col_categoria = st.columns([1, 2])

    with col_periodo:
        periodo = st.radio(
            "Período",
            ["Hoje", "Ontem", "Últimos 7 dias", "Personalizado"],
            horizontal=False,
            key=f"periodo_{aba}"
        )

        if periodo == "Personalizado":
            data_inicio = st.date_input(
                "De",
                value=datetime.now().date() - timedelta(days=1),
                key=f"data_inicio_{aba}"
            )
            data_fim = st.date_input(
                "Até",
                value=datetime.now().date(),
                key=f"data_fim_{aba}"
            )
        elif periodo == "Hoje":
            data_inicio = data_fim = datetime.now().date()
        elif periodo == "Ontem":
            data_inicio = data_fim = datetime.now().date() - timedelta(days=1)
        else:  # Últimos 7 dias
            data_inicio = datetime.now().date() - timedelta(days=6)
            data_fim = datetime.now().date()

    df = pd.DataFrame()
    erro_leitura = False
    try:
        df = ler_google(aba)
    except RuntimeError as erro:
        st.error(str(erro))
        erro_leitura = True

    if erro_leitura:
        return
    elif df.empty:
        st.info("Nenhuma ocorrência registrada ainda.")
        return

    # Identifica a coluna de data/hora de forma flexível
    col_data = None
    for c in df.columns:
        if "data" in c.lower():
            col_data = c
            break

    if col_data is None:
        st.warning(
            "Não foi possível identificar a coluna de data na planilha."
        )
        return

    df["_data_convertida"] = pd.to_datetime(
        df[col_data],
        format="%d/%m/%Y %H:%M",
        errors="coerce"
    )

    with col_categoria:
        if "Categoria" in df.columns:
            categorias_disponiveis = sorted(
                [c for c in df["Categoria"].unique() if c]
            )
            filtro_categoria = st.multiselect(
                "Categoria",
                categorias_disponiveis,
                default=categorias_disponiveis,
                key=f"categoria_{aba}"
            )
        else:
            filtro_categoria = None
            st.caption(
                "Coluna \"Categoria\" ainda não encontrada na planilha "
                "(adicione o cabeçalho para habilitar este filtro)."
            )

    filtrado = df[
        (df["_data_convertida"] >= pd.Timestamp(data_inicio))
        & (df["_data_convertida"] < pd.Timestamp(data_fim) + pd.Timedelta(days=1))
    ]

    if filtro_categoria:
        filtrado = filtrado[filtrado["Categoria"].isin(filtro_categoria)]

    filtrado = filtrado.sort_values(
        "_data_convertida", ascending=False
    ).drop(columns=["_data_convertida"])

    st.markdown(f"**{len(filtrado)} ocorrência(s) encontrada(s)**")

    st.dataframe(
        filtrado,
        use_container_width=True,
        hide_index=True
    )

    if st.button("🔄 Atualizar agora", key=f"atualizar_{aba}"):
        st.rerun()



# ===============================
# MENU
# ===============================

menu = st.sidebar.selectbox(
    "Menu",
    [
        "📌 Registrar Demanda",
        "📖 Consultar Ocorrências",
        "🔒 Confidenciais (chefia)"
    ]
)



# ===============================
# REGISTRAR DEMANDA
# ===============================

if menu == "📌 Registrar Demanda":

    st.subheader("Registrar demanda")


    with st.form("demanda"):

        solicitante = st.text_input(
            "Solicitante"
        )


        categoria = st.selectbox(
            "Categoria",
            CATEGORIAS
        )


        setor = st.selectbox(
            "Setor",
            [
                "Radiologia",
                "Tomografia",
                "Mamografia",
                "Ultrassom",
                "Densitometria",
                "Outros"
            ]
        )


        descricao = st.text_area(
            "Descrição da demanda"
        )


        confidencial = st.checkbox(
            "🔒 Ocorrência confidencial (visível apenas para chefia/supervisão)"
        )


        enviar = st.form_submit_button(
            "Registrar"
        )


        if enviar:

            aba_destino = "Confidenciais" if confidencial else "Demandas"

            salvar_google(
                aba_destino,
                [
                    datetime.now().strftime(
                        "%d/%m/%Y %H:%M"
                    ),
                    solicitante,
                    setor,
                    descricao,
                    "Aberto",
                    "",
                    categoria
                ]
            )

            if confidencial:
                st.success(
                    "Demanda registrada como confidencial — visível apenas "
                    "na área de chefia/supervisão."
                )
            else:
                st.success(
                    "Demanda registrada!"
                )



# ===============================
# CONSULTAR OCORRÊNCIAS
# ===============================

elif menu == "📖 Consultar Ocorrências":

    st.subheader("Consultar ocorrências")

    tela_consulta("Demandas")



# ===============================
# CONFIDENCIAIS (CHEFIA)
# ===============================

elif menu == "🔒 Confidenciais (chefia)":

    st.subheader("Ocorrências confidenciais")

    if not SENHA_CHEFIA:
        st.warning(
            "Área ainda não configurada: defina a variável de ambiente "
            "SENHA_CHEFIA nas configurações do serviço no Render."
        )
    else:
        senha_digitada = st.text_input(
            "Senha de acesso",
            type="password"
        )

        if senha_digitada == "":
            st.info("Digite a senha para acessar os registros confidenciais.")
        elif senha_digitada != SENHA_CHEFIA:
            st.error("Senha incorreta.")
        else:
            tela_consulta("Confidenciais")
