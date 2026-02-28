import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

# --- CONFIGURAÇÃO DO FIREBASE ---
if not firebase_admin._apps:
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
        st.error(f"Erro de conexão: {e}")

# --- ESTADO DA SESSÃO ---
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
            # Lógica simples de Login (Busca no Firebase no futuro)
            if email == "admin@teste.com" and senha == "123":
                mudar_pagina("dashboard")
            else:
                st.error("Usuário não autorizado ou senha incorreta.")
    with col2:
        if st.button("CANCELAR", use_container_width=True):
            st.info("Operação cancelada.")

    st.divider()
    if st.button("Cadastrar Novo Usuário"):
        mudar_pagina("cadastro")
    st.button("Esqueci a Senha")

# --- TELA DE CADASTRO (Ajustada) ---
elif st.session_state.page == "cadastro":
    st.title("📝 Cadastro de Usuário")
    nome = st.text_input("Nome Completo")
    email_cad = st.text_input("E-mail")
    tel = st.text_input("Telefone (com DDD)")
    senha_cad = st.text_input("Senha", type="password")
    conf_senha = st.text_input("Confirmar Senha", type="password")

    if st.button("Confirmar Cadastro"):
        if senha_cad != conf_senha:
            st.error("As senhas não coincidem!")
        elif not nome or not email_cad:
            st.warning("Preencha os campos obrigatórios.")
        else:
            # Salva no Firebase
            try:
                ref = db.reference('usuarios_pendentes')
                ref.push({
                    'nome': nome,
                    'email': email_cad,
                    'telefone': tel,
                    'status': 'pendente'
                })
                st.success("Cadastro enviado! Aguarde aprovação do Administrador.")
                if st.button("Voltar ao Login"): mudar_pagina("login")
            except Exception as e:
                st.error(f"Erro ao salvar: {e}")
    
    if st.button("Voltar"):
        mudar_pagina("login")

# --- 2ª TELA: DASHBOARD (SELEÇÃO) ---
elif st.session_state.page == "dashboard":
    st.title("Página Inicial")
    st.subheader("Selecione um módulo:")
    
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("💊 MEDICAMENTOS", use_container_width=True): mudar_pagina("meds")
        if st.button("📅 CONSULTAS", use_container_width=True): mudar_pagina("consultas")
    with col_b:
        if st.button("🧪 EXAMES", use_container_width=True): mudar_pagina("exames")
        if st.button("📊 RELATÓRIOS", use_container_width=True): mudar_pagina("relatorios")
    
    st.divider()
    if st.button("Sair"): mudar_pagina("login")

# --- MÓDULOS (Placeholder para testes) ---
elif st.session_state.page in ["meds", "consultas", "exames", "relatorios"]:
    st.title(f"Módulo {st.session_state.page.upper()}")
    st.info("Em breve: Formulários completos de cadastro e listagem.")
    if st.button("VOLTAR"): mudar_pagina("dashboard")
