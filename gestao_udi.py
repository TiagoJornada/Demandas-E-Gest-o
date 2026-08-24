import streamlit as st
import requests
import pandas as pd
import os
import time
from datetime import datetime, timedelta


# ===============================
# CONFIGURAÇÃO
# ===============================

st.set_page_config(
    page_title="Livro Digital de Registros",
    page_icon="icone.png",
    layout="wide"
)


URL_APPS_SCRIPT = (
"https://script.google.com/macros/s/"
"AKfycbxzDDKTmJxvLaQWgmR4PlihlpVlSHA57viHzSA5s7sw0tNDR3a_oi8yJmVxUrAdJv-G"
"/exec"
)


CATEGORIAS = [
    "Administrativa(o)",
    "Enfermeira(o)",
    "Farmacêutica(o)",
    "Física(o) Médica(o)",
    "Médica(o)",
    "Residente",
    "Técnica(o) em Enfermagem",
    "Técnica(o) em Radiologia",
]


# Senha para gerenciar usuários (adicionar solicitantes à lista).
# Reaproveita a variável SENHA_CHEFIA já configurada no Render, caso
# SENHA_ADMIN não exista — assim não é preciso cadastrar nada novo agora.
SENHA_ADMIN = os.getenv("SENHA_ADMIN", "") or os.getenv("SENHA_CHEFIA", "")




# ===============================
# FUNÇÕES GOOGLE SHEETS
# ===============================

def salvar_google(aba, linha, tentativas=3):

    dados = {
        "aba": aba,
        "linha": linha
    }

    for tentativa in range(tentativas):
        try:
            resposta = requests.post(
                URL_APPS_SCRIPT,
                json=dados,
                timeout=20
            )
            return resposta.text
        except requests.RequestException:
            if tentativa < tentativas - 1:
                time.sleep(2)
                continue
            raise



def definir_senha_usuario(nome, senha, tentativas=3):
    """Grava a senha individual de um usuário já existente na aba
    'Usuarios', localizando a linha pelo nome."""

    dados = {
        "aba": "Usuarios",
        "acao": "definir_senha",
        "nome": nome,
        "senha": senha
    }

    ultimo_erro = None

    for tentativa in range(tentativas):

        try:
            resposta = requests.post(URL_APPS_SCRIPT, json=dados, timeout=20)
        except requests.RequestException as erro:
            ultimo_erro = f"falha de conexão: {erro}"
            time.sleep(2)
            continue

        try:
            resultado = resposta.json()
        except ValueError:
            trecho = resposta.text[:200] if resposta.text else "(vazio)"
            ultimo_erro = (
                f"resposta inválida do Apps Script (status HTTP {resposta.status_code}). "
                f"Trecho recebido: {trecho}"
            )
            time.sleep(2)
            continue

        if resultado.get("status") == "OK":
            return True, ""

        return False, resultado.get("motivo", "erro desconhecido")

    return False, f"{ultimo_erro} (tentei {tentativas} vezes)"



def ler_google(aba, tentativas=3):

    ultimo_erro = None

    for tentativa in range(tentativas):

        try:
            resposta = requests.get(
                URL_APPS_SCRIPT,
                params={"aba": aba},
                timeout=20
            )
        except requests.RequestException as erro:
            ultimo_erro = f"falha de conexão: {erro}"
            time.sleep(2)
            continue

        try:
            dados = resposta.json()
        except ValueError:
            ultimo_erro = (
                "O Google Apps Script não retornou dados em formato válido "
                f"para leitura (status HTTP {resposta.status_code})."
            )
            time.sleep(2)
            continue

        if len(dados) > 1:
            return pd.DataFrame(
                dados[1:],
                columns=dados[0]
            )

        return pd.DataFrame()

    raise RuntimeError(
        f"{ultimo_erro} (tentei {tentativas} vezes). Isso costuma acontecer "
        "logo depois do sistema ficar um tempo sem uso — aguarde alguns "
        "segundos e tente de novo."
    )



def listar_usuarios():
    """Busca a lista de solicitantes cadastrados na aba 'Usuarios'.
    Devolve (lista_de_nomes, motivo_se_vazia)."""

    try:
        df = ler_google("Usuarios")
    except RuntimeError as erro:
        return [], f"erro ao ler a aba: {erro}"

    if df.empty:
        return [], "a aba \"Usuarios\" está vazia ou não foi encontrada"

    if "Nome" not in df.columns:
        return [], f"não encontrei a coluna \"Nome\" (colunas encontradas: {list(df.columns)})"

    nomes = sorted(
        [n for n in df["Nome"].unique() if n and str(n).strip()]
    )

    if not nomes:
        return [], "a coluna \"Nome\" existe, mas não tem nenhum valor preenchido"

    return nomes, None



def buscar_credenciais_usuarios():
    """Busca nome + senha individual de cada usuário cadastrado na aba
    'Usuarios'. Devolve (dicionario {nome: senha}, motivo_se_vazio)."""

    try:
        df = ler_google("Usuarios")
    except RuntimeError as erro:
        return {}, f"erro ao ler a aba: {erro}"

    if df.empty:
        return {}, "a aba \"Usuarios\" está vazia ou não foi encontrada"

    if "Nome" not in df.columns or "Senha" not in df.columns:
        return {}, (
            "não encontrei as colunas \"Nome\" e \"Senha\" "
            f"(colunas encontradas: {list(df.columns)})"
        )

    credenciais = {}
    for _, linha in df.iterrows():
        nome = str(linha["Nome"]).strip()
        senha = str(linha["Senha"]).strip()
        if nome:
            credenciais[nome] = senha

    if not credenciais:
        return {}, "não há usuários cadastrados"

    return credenciais, None



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


st.image("banner.png", width=220)

st.caption("Livro de registro de ocorrências do setor")


# ===============================
# PORTÃO DE ACESSO
# ===============================

if "acesso_liberado" not in st.session_state:
    st.session_state.acesso_liberado = False

if not st.session_state.acesso_liberado:

    st.subheader("Acesso restrito")
    st.caption("Este sistema é de uso exclusivo da equipe da UDI. Entre com seu nome e sua senha individual.")

    credenciais, motivo_credenciais = buscar_credenciais_usuarios()

    if not credenciais:
        st.warning(
            "Ainda não há usuários cadastrados "
            f"({motivo_credenciais}). Peça para a chefia cadastrar em "
            "\"👤 Gerenciar Usuários\", ou verifique a coluna \"Senha\" na "
            "aba \"Usuarios\" da planilha."
        )
        st.stop()

    nome_login = st.selectbox("Seu nome", sorted(credenciais.keys()), key="login_nome")
    senha_cadastrada = credenciais.get(nome_login, "")

    if not senha_cadastrada:

        st.info("Primeiro acesso: crie uma senha de 4 dígitos para começar a usar o sistema.")
        nova_senha = st.text_input(
            "Crie uma senha (4 dígitos)",
            type="password",
            max_chars=4,
            key="nova_senha"
        )
        confirmar_senha = st.text_input(
            "Confirme a senha",
            type="password",
            max_chars=4,
            key="confirmar_senha"
        )

        if st.button("Criar senha e entrar"):
            if not nova_senha or not confirmar_senha:
                st.error("Preencha os dois campos de senha.")
            elif not (nova_senha.isdigit() and len(nova_senha) == 4):
                st.error("A senha precisa ter exatamente 4 números (ex.: 4821).")
            elif nova_senha != confirmar_senha:
                st.error("As senhas não coincidem.")
            else:
                ok, erro = definir_senha_usuario(nome_login, nova_senha)
                if ok:
                    st.session_state.acesso_liberado = True
                    st.session_state.usuario_logado = nome_login
                    st.rerun()
                else:
                    st.error(f"Não foi possível criar a senha: {erro}")

    else:

        senha_login = st.text_input("Sua senha", type="password", key="login_senha")

        if st.button("Entrar"):
            if senha_login == senha_cadastrada:
                st.session_state.acesso_liberado = True
                st.session_state.usuario_logado = nome_login
                st.rerun()
            else:
                st.error("Senha incorreta.")

    st.stop()



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

    bruto = df[col_data]

    # O Google Sheets costuma converter automaticamente o texto em um valor
    # de data/hora de verdade, devolvido pelo Apps Script em UTC (ex.:
    # "2026-08-12T23:08:00.000Z"). Convertemos de volta para o horário de
    # Brasília para recuperar os mesmos números que foram digitados.
    convertido = pd.to_datetime(bruto, utc=True, errors="coerce")
    convertido = convertido.dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None)

    # Linhas que não são data "de verdade" (texto simples, formato antigo)
    # caem aqui como reserva.
    faltantes = convertido.isna()
    if faltantes.any():
        tentativa_texto = pd.to_datetime(
            bruto[faltantes], format="%d/%m/%Y %H:%M", errors="coerce"
        )
        convertido.loc[faltantes] = tentativa_texto

    df["_data_convertida"] = convertido

    with col_categoria:
        if "Categoria" in df.columns:
            categorias_disponiveis = sorted(
                [c for c in df["Categoria"].unique() if c]
            )
            categoria_escolhida = st.selectbox(
                "Categoria",
                ["Todas as categorias"] + categorias_disponiveis,
                key=f"categoria_{aba}"
            )
            filtro_categoria = (
                None
                if categoria_escolhida == "Todas as categorias"
                else categoria_escolhida
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
    ].copy()

    if filtro_categoria:
        filtrado = filtrado[filtrado["Categoria"] == filtro_categoria]

    filtrado = filtrado.sort_values("_data_convertida", ascending=False)

    # Mostra a data/hora já corrigida (dd/mm/aaaa hh:mm) em vez do valor
    # bruto vindo da planilha.
    filtrado[col_data] = filtrado["_data_convertida"].dt.strftime("%d/%m/%Y %H:%M")
    filtrado = filtrado.drop(columns=["_data_convertida"])

    st.markdown(f"**{len(filtrado)} ocorrência(s) encontrada(s)**")

    colunas_prioritarias = [
        c for c in [col_data, "Solicitante", "Setor", "Descrição"]
        if c in filtrado.columns
    ]
    colunas_restantes = [
        c for c in filtrado.columns if c not in colunas_prioritarias
    ]

    st.dataframe(
        filtrado,
        use_container_width=True,
        hide_index=True,
        column_order=colunas_prioritarias + colunas_restantes,
        column_config={
            col_data: st.column_config.TextColumn("Data/Hora", width="small"),
            "Solicitante": st.column_config.TextColumn(width="small"),
            "Setor": st.column_config.TextColumn(width="small"),
            "Descrição": st.column_config.TextColumn(width="large"),
        }
    )

    if st.button("🔄 Atualizar agora", key=f"atualizar_{aba}"):
        st.rerun()



# ===============================
# MENU
# ===============================

menu = st.sidebar.selectbox(
    "Menu",
    [
        "📌 Registrar Relato",
        "📖 Consultar Ocorrências",
        "👤 Gerenciar Usuários"
    ]
)

st.sidebar.caption(f"Conectado como: {st.session_state.get('usuario_logado', '')}")
if st.sidebar.button("Sair"):
    st.session_state.acesso_liberado = False
    st.session_state.usuario_logado = None
    st.rerun()



# ===============================
# REGISTRAR RELATO
# ===============================

if menu == "📌 Registrar Relato":

    st.subheader("Registrar relato")

    usuarios, motivo = listar_usuarios()

    with st.form("relato"):

        if usuarios:
            nome_logado = st.session_state.get("usuario_logado")
            indice_padrao = (
                usuarios.index(nome_logado) if nome_logado in usuarios else 0
            )
            solicitante = st.selectbox(
                "Solicitante",
                usuarios,
                index=indice_padrao
            )
        else:
            solicitante = st.text_input(
                "Solicitante"
            )
            st.caption(
                f"Lista de solicitantes ainda vazia ({motivo}) — cadastre em "
                "\"👤 Gerenciar Usuários\" para virar lista suspensa."
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
                "Ressonância Magnética",
                "Medicina Nuclear",
                "PET/CT",
                "Iodoterapia",
                "Sala de Laudos",
                "Centro Cirúrgico",
                "Recepção",
                "Outros"
            ]
        )


        descricao = st.text_area(
            "Descrição do relato"
        )


        observacao = st.text_input(
            "Observação (opcional)",
            help="Ex.: número do chamado técnico aberto, encaminhamento dado, "
                 "ou qualquer complemento útil ao relato."
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
                    observacao,
                    categoria
                ]
            )

            st.success(
                "Relato registrado!"
            )



# ===============================
# CONSULTAR OCORRÊNCIAS
# ===============================

elif menu == "📖 Consultar Ocorrências":

    st.subheader("Consultar ocorrências")

    tela_consulta("Demandas")



# ===============================
# GERENCIAR USUÁRIOS
# ===============================

elif menu == "👤 Gerenciar Usuários":

    st.subheader("Gerenciar usuários")

    if not SENHA_ADMIN:
        st.warning(
            "Área ainda não configurada: defina a variável de ambiente "
            "SENHA_ADMIN (ou SENHA_CHEFIA) nas configurações do serviço "
            "no Render."
        )
    else:
        senha_digitada = st.text_input(
            "Senha de gerenciamento",
            type="password"
        )

        if senha_digitada == "":
            st.info("Digite a senha para gerenciar os usuários.")
        elif senha_digitada != SENHA_ADMIN:
            st.error("Senha incorreta.")
        else:
            usuarios, motivo = listar_usuarios()

            st.markdown("**Usuários cadastrados atualmente:**")
            if usuarios:
                st.write(", ".join(usuarios))
            else:
                st.caption(f"Nenhum usuário cadastrado ainda ({motivo}).")

            st.divider()

            with st.form("novo_usuario", clear_on_submit=True):
                novo_nome = st.text_input("Nome completo do novo usuário")
                adicionar = st.form_submit_button("Adicionar")

                if adicionar:
                    if not novo_nome.strip():
                        st.warning("Digite um nome antes de adicionar.")
                    elif novo_nome.strip() in usuarios:
                        st.warning("Esse nome já está cadastrado.")
                    else:
                        salvar_google("Usuarios", [novo_nome.strip(), ""])
                        st.success(
                            f"\"{novo_nome.strip()}\" adicionado! Na primeira vez que "
                            "essa pessoa acessar o sistema, ela vai criar a própria senha."
                        )

            st.caption(
                "Remover um usuário ainda precisa ser feito direto na "
                "planilha (aba \"Usuarios\"), apagando a linha correspondente."
            )
