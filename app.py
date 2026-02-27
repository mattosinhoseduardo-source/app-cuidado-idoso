import streamlit as st
import firebase_admin
from firebase_admin import credentials, db, auth

# 1. Configuração de Segurança e Firebase
if not firebase_admin._apps:
    # Tenta ler do Cofre de Segredos do Streamlit
    try:
        cred_dict = {
            "type": st.secrets["firebase"]["type"],
            "project_id": st.secrets["firebase"]["project_id"],
            "private_key_id": st.secrets["firebase"]["private_key_id"],
            "private_key": st.secrets["firebase"]["private_key"].replace('\\n', '\n'),
            "client_email": st.secrets["firebase"]["client_email"],
            "client_id": st.secrets["firebase"]["client_id"],
            "auth_uri": st.secrets["firebase"]["auth_uri"],
            "token_uri": st.secrets["firebase"]["token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
        }
        cred = credentials.Certificate(cred_dict)
        firebase_admin.initialize_app(cred, {
            'databaseURL': f'https://{st.secrets["firebase"]["project_id"]}-default-rtdb.firebaseio.com/'
        })
    except Exception as e:
        st.error(f"Erro ao conectar ao Firebase: {e}")

# --- CONFIGURAÇÃO DA INTERFACE ---
st.set_page_config(page_title="Cuidado Idoso", layout="centered")

if 'page' not in st.session_state:
    st.session_state.page = "login"

def mudar_pagina(nome):
    st.session_state.page = nome
    st.rerun()

# --- 1ª TELA: LOGIN ---
if st.session_state.page == "login":
    st.title("🏥 Gestão de Cuidados")
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("OK", use_container_width=True):
            # Login Simples (Pode ser expandido com Firebase Auth)
            if email == "admin@teste.com" and senha == "123":
                mudar_pagina("dashboard")
            else:
                st.error("Credenciais inválidas.")
    with col2:
        st.button("CANCELAR", use_container_width=True)
    
    st.divider()
    if st.button("Cadastrar Novo Usuário"): mudar_pagina("cadastro")

# --- 2ª TELA: SELEÇÃO ---
elif st.session_state.page == "dashboard":
    st.title("Página Inicial")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💊 MEDICAMENTOS", use_container_width=True): mudar_pagina("meds")
        if st.button("📅 CONSULTAS", use_container_width=True): mudar_pagina("consultas")
    with col_b:
        if st.button("🧪 EXAMES", use_container_width=True): mudar_pagina("exames")
        if st.button("📊 RELATÓRIOS", use_container_width=True): mudar_pagina("relatorios")
    st.divider()
    if st.button("Sair"): mudar_pagina("login")

# --- 3ª TELA: MEDICAMENTOS ---
elif st.session_state.page == "meds":
    st.title("💊 Medicamentos")
    with st.expander("Cadastrar Novo Medicamento", expanded=True):
        nome_med = st.text_input("Nome do Medicamento")
        mg = st.text_input("Miligramas")
        turnos = ["MANHÃ", "MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "TARDE", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "NOITE"]
        forma = st.selectbox("Forma de Uso", turnos)
        
        if st.button("Confirmar Cadastro"):
            st.success(f"{nome_med} cadastrado com sucesso!")
            
    if st.button("VOLTAR"): mudar_pagina("dashboard")

# --- 3.2 TELA: CONSULTAS ---
elif st.session_state.page == "consultas":
    st.title("📅 Consultas")
    especialidades = ["Alergista", "Anestesiologia", "Angiologia", "Cardiologia", "Cirurgião", "Clínico Geral", "Coloproctologia", "Dermatologia", "Endocrinologia", "Gastroenterologia", "Geriatria", "Ginecologia e obstetrícia", "Hematologia e hemoterapia", "Infectologia", "Mastologia", "Nefrologia", "Neurocirurgia", "Neurologia", "Nutrologia", "Oftalmologia", "Ortopedia e traumatologia", "Otorrinolaringologia", "Pneumologia", "Psiquiatria", "Reumatologia", "Urologia"]
    
    esp = st.selectbox("Especialidade", especialidades)
    medico = st.text_input("Nome do Médico")
    data_c = st.date_input("Data da Consulta")
    
    if st.button("Salvar Consulta"):
        st.success("Consulta agendada!")
        
    if st.button("VOLTAR"): mudar_pagina("dashboard")
