import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime

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
if 'user_email' not in st.session_state:
    st.session_state.user_email = ""

def mudar_pagina(nome):
    st.session_state.page = nome
    st.rerun()

# --- 1ª TELA: LOGIN ---
if st.session_state.page == "login":
    st.title("🏥 Gestão de Cuidados")
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")
    
    if st.button("OK", use_container_width=True):
        if email == "admin@teste.com" and senha == "123":
            st.session_state.user_email = email
            mudar_pagina("dashboard")
        else:
            st.error("Usuário não autorizado ou senha incorreta.")

    st.divider()
    if st.button("Cadastrar Novo Usuário"): mudar_pagina("cadastro")

# --- TELA DE CADASTRO ---
elif st.session_state.page == "cadastro":
    st.title("📝 Cadastro de Usuário")
    nome = st.text_input("Nome Completo")
    email_cad = st.text_input("E-mail")
    tel = st.text_input("Telefone")
    senha_cad = st.text_input("Senha", type="password")

    if st.button("Confirmar Cadastro"):
        db.reference('usuarios_pendentes').push({
            'nome': nome, 'email': email_cad, 'telefone': tel, 'status': 'pendente'
        })
        st.success("Cadastro enviado! Aguarde aprovação.")
        st.button("Voltar ao Login", on_click=lambda: mudar_pagina("login"))
    
    if st.button("Voltar"): mudar_pagina("login")

# --- 2ª TELA: DASHBOARD ---
elif st.session_state.page == "dashboard":
    st.title("Página Inicial")
    
    # PAINEL DO ADMINISTRADOR (Visível apenas para você)
    if st.session_state.user_email == "admin@teste.com":
        with st.expander("🔔 GESTÃO DE ACESSOS (ADMIN)"):
            pendentes = db.reference('usuarios_pendentes').get()
            if pendentes:
                for key, val in pendentes.items():
                    st.write(f"**{val['nome']}** ({val['email']})")
                    if st.button(f"Aprovar {val['nome']}", key=key):
                        db.reference('usuarios_aprovados').child(key).set(val)
                        db.reference('usuarios_pendentes').child(key).delete()
                        st.success("Usuário aprovado!")
                        st.rerun()
            else:
                st.write("Nenhum pedido de cadastro pendente.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💊 MEDICAMENTOS", use_container_width=True): mudar_pagina("meds")
        if st.button("📅 CONSULTAS", use_container_width=True): mudar_pagina("consultas")
    with col2:
        if st.button("🧪 EXAMES", use_container_width=True): mudar_pagina("exames")
        if st.button("📊 RELATÓRIOS", use_container_width=True): mudar_pagina("relatorios")
    
    st.divider()
    if st.button("Sair"): mudar_pagina("login")

# --- 3ª TELA: MEDICAMENTOS ---
elif st.session_state.page == "meds":
    st.title("💊 Controle de Medicamentos")
    
    with st.form("cad_med"):
        nome_m = st.text_input("Nome do Medicamento")
        dosagem = st.text_input("Dosagem (ex: 50mg)")
        turnos = ["MANHÃ", "MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "TARDE", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "NOITE"]
        turno = st.selectbox("Turno / Forma de Uso", turnos)
        obs = st.text_area("Observações")
        if st.form_submit_button("CADASTRAR"):
            db.reference('medicamentos').push({
                'nome': nome_m, 'dosagem': dosagem, 'turno': turno, 'obs': obs, 'data': str(datetime.date.today())
            })
            st.success("Medicamento salvo!")

    st.divider()
    st.subheader("Lista de Remédios")
    lista_meds = db.reference('medicamentos').get()
    if lista_meds:
        for k, v in lista_meds.items():
            col_med, col_del = st.columns([4, 1])
            col_med.write(f"**{v['nome']}** ({v['dosagem']}) - {v['turno']}")
            if col_del.button("🗑️", key=k):
                db.reference('medicamentos').child(k).delete()
                st.rerun()
    
    if st.button("VOLTAR"): mudar_pagina("dashboard")
