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
    email = st.text_input("E-mail").lower().strip()
    senha = st.text_input("Senha", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("OK", use_container_width=True):
            # Admin Master
            if email == "admin@teste.com" and senha == "123":
                st.session_state.user_email = email
                mudar_pagina("dashboard")
            else:
                # Verifica no Firebase se o usuário existe e está aprovado
                usuarios = db.reference('usuarios_aprovados').get()
                sucesso = False
                if usuarios:
                    for k, v in usuarios.items():
                        if v['email'].lower() == email and v['senha'] == senha:
                            st.session_state.user_email = email
                            sucesso = True
                            mudar_pagina("dashboard")
                
                if not sucesso:
                    st.error("Acesso negado: Usuário incorreto ou ainda Pendente de aprovação.")
    
    with col2:
        st.button("CANCELAR", use_container_width=True)

    st.divider()
    if st.button("Cadastrar Novo Usuário"): mudar_pagina("cadastro")

# --- TELA DE CADASTRO ---
elif st.session_state.page == "cadastro":
    st.title("📝 Cadastro de Usuário")
    nome = st.text_input("Nome Completo")
    email_cad = st.text_input("E-mail").lower().strip()
    tel = st.text_input("Telefone (com DDD)")
    senha_cad = st.text_input("Senha", type="password")

    if st.button("Confirmar Cadastro"):
        if nome and email_cad and senha_cad:
            db.reference('usuarios_pendentes').push({
                'nome': nome, 'email': email_cad, 'telefone': tel, 'senha': senha_cad, 'status': 'pendente'
            })
            st.success("Cadastro enviado! Solicite ao Administrador a liberação do seu acesso.")
            if st.button("Voltar ao Login"): mudar_pagina("login")
        else:
            st.warning("Preencha todos os campos.")
    
    if st.button("Voltar"): mudar_pagina("login")

# --- 2ª TELA: DASHBOARD ---
elif st.session_state.page == "dashboard":
    st.title("Página Inicial")
    
    # PAINEL DO ADMINISTRADOR
    if st.session_state.user_email == "admin@teste.com":
        with st.expander("🔔 GESTÃO DE ACESSOS (ADMIN)"):
            pendentes = db.reference('usuarios_pendentes').get()
            if pendentes:
                for key, val in pendentes.items():
                    st.write(f"**{val['nome']}** ({val['email']})")
                    if st.button(f"Aprovar {val['nome']}", key=key):
                        db.reference('usuarios_aprovados').child(key).set(val)
                        db.reference('usuarios_pendentes').child(key).delete()
                        st.success(f"Acesso liberado para {val['nome']}!")
                        st.rerun()
            else:
                st.write("Nenhum usuário aguardando aprovação.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("💊 MEDICAMENTOS", use_container_width=True): mudar_pagina("meds")
        if st.button("📅 CONSULTAS", use_container_width=True): mudar_pagina("consultas")
    with col2:
        if st.button("🧪 EXAMES", use_container_width=True): mudar_pagina("exames")
        if st.button("📊 RELATÓRIOS", use_container_width=True): mudar_pagina("relatorios")
    
    st.divider()
    if st.button("Sair"): 
        st.session_state.user_email = ""
        mudar_pagina("login")

# --- MÓDULO: MEDICAMENTOS (Mantido) ---
elif st.session_state.page == "meds":
    st.title("💊 Medicamentos")
    with st.form("cad_med"):
        n_med = st.text_input("Nome do Medicamento")
        mg = st.text_input("Miligramas")
        t_opcoes = ["MANHÃ", "MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "TARDE", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "NOITE"]
        turno = st.selectbox("Turno / Forma de Uso", t_opcoes)
        if st.form_submit_button("CADASTRAR"):
            db.reference('medicamentos').push({'nome': n_med, 'mg': mg, 'turno': turno, 'data': str(datetime.date.today())})
            st.success("Salvo!")
    
    lista = db.reference('medicamentos').get()
    if lista:
        for k, v in lista.items():
            c1, c2 = st.columns([4, 1])
            c1.write(f"{v['nome']} ({v['mg']}) - {v['turno']}")
            if c2.button("🗑️", key=k):
                db.reference('medicamentos').child(k).delete()
                st.rerun()
    if st.button("VOLTAR"): mudar_pagina("dashboard")

# --- MÓDULO: CONSULTAS (Novo) ---
elif st.session_state.page == "consultas":
    st.title("📅 Agendamento de Consultas")
    
    with st.form("cad_consulta"):
        especialidades = ["Alergista", "Anestesiologia", "Angiologia", "Cardiologia", "Cirurgião", "Clínico Geral", "Coloproctologia", "Dermatologia", "Endocrinologia", "Gastroenterologia", "Geriatria", "Ginecologia e obstetrícia", "Hematologia e hemoterapia", "Infectologia", "Mastologia", "Nefrologia", "Neurocirurgia", "Neurologia", "Nutrologia", "Oftalmologia", "Ortopedia e traumatologia", "Otorrinolaringologia", "Pneumologia", "Psiquiatria", "Reumatologia", "Urologia"]
        esp = st.selectbox("Especialidade", especialidades)
        data_c = st.date_input("Data da Consulta", format="DD/MM/YYYY")
        hora_c = st.time_input("Hora da Consulta")
        medico = st.text_input("Médico")
        local = st.text_input("Clínica / Hospital")
        end = st.text_input("Endereço")
        obs = st.text_area("Observações")
        
        if st.form_submit_button("OK"):
            db.reference('consultas').push({
                'especialidade': esp, 'data': str(data_c), 'hora': str(hora_c),
                'medico': medico, 'local': local, 'endereco': end, 'obs': obs
            })
            st.success("Consulta cadastrada com sucesso!")

    st.divider()
    st.subheader("Consultas Agendadas")
    cons = db.reference('consultas').get()
    if cons:
        # Ordenar por data (opcional)
        for k, v in cons.items():
            with st.container():
                st.write(f"**{v['data']} às {v['hora']}** - {v['especialidade']}")
                st.write(f"Dr(a). {v['medico']} | Local: {v['local']}")
                if st.button("Excluir", key=f"del_{k}"):
                    db.reference('consultas').child(k).delete()
                    st.rerun()
                st.divider()
    
    if st.button("VOLTAR"): mudar_pagina("dashboard")
