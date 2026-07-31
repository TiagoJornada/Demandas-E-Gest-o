import streamlit as st
import requests
import pandas as pd
from datetime import datetime


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
"AKfycbzcaCjVUdWD8rTna15_4v512oBd9KRIvU5R4S4QvVc6o1VXff4tBE1DJcTf5y2zTUv8"
"/exec"
)


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

    dados = resposta.json()

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

Sistema de registro e acompanhamento administrativo

""",
unsafe_allow_html=True
)



# ===============================
# MENU
# ===============================

menu = st.sidebar.selectbox(
    "Menu",
    [
        "📌 Demandas",
        "🏖 Férias",
        "📄 Abonos",
        "🚑 Afastamentos"
    ]
)



# ===============================
# DEMANDAS
# ===============================

if menu == "📌 Demandas":

    st.subheader("Registrar demanda")


    with st.form("demanda"):

        solicitante = st.text_input(
            "Solicitante"
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


        enviar = st.form_submit_button(
            "Registrar"
        )


        if enviar:

            salvar_google(
                "Demandas",
                [
                    datetime.now().strftime(
                        "%d/%m/%Y %H:%M"
                    ),
                    solicitante,
                    setor,
                    descricao,
                    "Aberto",
                    ""
                ]
            )

            st.success(
                "Demanda registrada!"
            )



# ===============================
# FÉRIAS
# ===============================

elif menu == "🏖 Férias":

    st.subheader(
        "Registro de férias"
    )


    with st.form("ferias"):

        servidor = st.text_input(
            "Servidor"
        )

        inicio = st.date_input(
            "Início"
        )

        fim = st.date_input(
            "Fim"
        )

        obs = st.text_input(
            "Observação"
        )


        if st.form_submit_button(
            "Salvar"
        ):

            salvar_google(
                "Ferias",
                [
                    servidor,
                    str(inicio),
                    str(fim),
                    obs
                ]
            )

            st.success(
                "Férias registradas"
            )



# ===============================
# ABONOS
# ===============================

elif menu == "📄 Abonos":

    st.subheader(
        "Registro de abono"
    )


    with st.form("abono"):

        servidor = st.text_input(
            "Servidor"
        )

        data = st.date_input(
            "Data"
        )

        motivo = st.text_input(
            "Motivo"
        )


        if st.form_submit_button(
            "Salvar"
        ):

            salvar_google(
                "Abonos",
                [
                    servidor,
                    str(data),
                    motivo
                ]
            )

            st.success(
                "Abono registrado"
            )



# ===============================
# AFASTAMENTOS
# ===============================

elif menu == "🚑 Afastamentos":

    st.subheader(
        "Registro de afastamento"
    )


    with st.form("afastamento"):

        servidor = st.text_input(
            "Servidor"
        )

        inicio = st.date_input(
            "Início"
        )

        fim = st.date_input(
            "Fim"
        )

        motivo = st.text_input(
            "Motivo"
        )


        if st.form_submit_button(
            "Salvar"
        ):

            salvar_google(
                "Afastamentos",
                [
                    servidor,
                    str(inicio),
                    str(fim),
                    motivo
                ]
            )

            st.success(
                "Afastamento registrado"
            )