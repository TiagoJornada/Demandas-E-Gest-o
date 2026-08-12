import streamlit as st
import requests
import pandas as pd
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
"AKfycbzcaCjVUdWD8rTna15_4v512oBd9KRIvU5R4S4QvVc6o1VXff4tBE1DJcTf5y2zTUv8"
"/exec"
)


CATEGORIAS = [
    "Médico",
    "Residente",
    "Técnico em Radiologia",
    "Técnico em Enfermagem",
    "Enfermagem",
    "Administrativo",
]


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

Livro de registro de ocorrências do setor

""",
unsafe_allow_html=True
)



# ===============================
# MENU
# ===============================

menu = st.sidebar.selectbox(
    "Menu",
    [
        "📌 Registrar Demanda",
        "📖 Consultar Ocorrências"
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
                    "",
                    categoria
                ]
            )

            st.success(
                "Demanda registrada!"
            )



# ===============================
# CONSULTAR OCORRÊNCIAS
# ===============================

elif menu == "📖 Consultar Ocorrências":

    st.subheader("Consultar ocorrências")

    col_periodo, col_categoria = st.columns([1, 2])

    with col_periodo:
        periodo = st.radio(
            "Período",
            ["Hoje", "Ontem", "Últimos 7 dias", "Personalizado"],
            horizontal=False
        )

        if periodo == "Personalizado":
            data_inicio = st.date_input(
                "De",
                value=datetime.now().date() - timedelta(days=1)
            )
            data_fim = st.date_input(
                "Até",
                value=datetime.now().date()
            )
        elif periodo == "Hoje":
            data_inicio = data_fim = datetime.now().date()
        elif periodo == "Ontem":
            data_inicio = data_fim = datetime.now().date() - timedelta(days=1)
        else:  # Últimos 7 dias
            data_inicio = datetime.now().date() - timedelta(days=6)
            data_fim = datetime.now().date()

    df = ler_google("Demandas")

    if df.empty:
        st.info("Nenhuma ocorrência registrada ainda.")
    else:
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
        else:
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
                        default=categorias_disponiveis
                    )
                else:
                    filtro_categoria = None
                    st.caption(
                        "Coluna \"Categoria\" ainda não encontrada na planilha "
                        "(adicione o cabeçalho na aba Demandas para habilitar este filtro)."
                    )

            filtrado = df[
                (df["_data_convertida"].dt.date >= data_inicio)
                & (df["_data_convertida"].dt.date <= data_fim)
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

    if st.button("🔄 Atualizar agora"):
        st.rerun()
