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
        st.error(f"Erro: {e}")

# --- CSS PARA ESSÊNCIA COMPACTA (MINIMALISTA) ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    .compact-row { font-size: 11px !important; line-height: 1.1 !important; margin: 0px !important; color: #333; border-bottom: 0.5px solid #eee; padding: 2px 0px; }
    .stButton > button { 
        padding: 0px 4px !important; 
        font-size: 11px !important; 
        height: 22px !important;
        min-height: 22px !important;
        background: transparent !important;
        border: none !important;
    }
    .main-btn > button { background-color: #f0f2f6 !important; border: 1px solid #ddd !important; height: 35px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO ---
if 'page' not in st.session_state: st.session_state.page = "login"
if 'confirm_del' not in st.session_state: st.session_state.confirm_del = None

def mudar_pagina(n): 
    st.session_state.page = n
    st.rerun()

LISTA_ESP = ["Alergista", "Anestesiologia", "Angiologia", "Cardiologia", "Cirurgião", "Clínico Geral", "Coloproctologia", "Dermatologia", "Endocrinologia", "Gastroenterologia", "Geriatria", "Ginecologia e obstetrícia", "Hematologia e hemoterapia", "Infectologia", "Mastologia", "Nefrologia", "Neurocirurgia", "Neurologia", "Nutrologia", "Oftalmologia", "Ortopedia e traumatologia", "Otorrinolaringologia", "Pneumologia", "Psiquiatria", "Reumatologia", "Urologia"]

# --- 1ª TELA: LOGIN (RESTAURADA) ---
if st.session_state.page == "login":
    st.title("🏥 Gestão de Cuidados")
    email = st.text_input("E-mail").lower().strip()
    senha = st.text_input("Senha", type="password")
    
    col_ok, col_canc = st.columns(2)
    with col_ok:
        if st.button("OK", use_container_width=True, key="login_ok"):
            if email == "admin@teste.com" and senha == "123":
                st.session_state.user_email = email
                mudar_pagina("dashboard")
            else:
                usuarios = db.reference('usuarios_aprovados').get()
                if usuarios and any(v['email'].lower() == email and v['senha'] == senha for v in usuarios.values()):
                    st.session_state.user_email = email
                    mudar_pagina("dashboard")
                else: st.error("Acesso Negado.")
    with col_canc:
        st.button("CANCELAR", use_container_width=True)

    st.divider()
    if st.button("Cadastrar Novo Usuário", use_container_width=True): mudar_pagina("cadastro")
    st.button("Esqueci a Senha", use_container_width=True)

# --- DASHBOARD ---
elif st.session_state.page == "dashboard":
    st.title("Painel Principal")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💊 MEDICAMENTOS", use_container_width=True): mudar_pagina("meds")
        if st.button("📅 CONSULTAS", use_container_width=True): mudar_pagina("consultas")
    with c2:
        if st.button("🧪 EXAMES", use_container_width=True): mudar_pagina("exames")
        if st.button("📊 RELATÓRIOS", use_container_width=True): mudar_pagina("relatorios")
    st.divider()
    if st.button("Sair"): mudar_pagina("login")

# --- MÓDULO CONSULTAS (COMPACTO) ---
elif st.session_state.page == "consultas":
    st.title("📅 Consultas")
    col_lista, col_cad = st.columns([1, 1.3])

    with col_lista:
        if st.button("⬅ VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        
        data = db.reference('consultas').get()
        if data:
            items = sorted(data.items(), key=lambda x: x[1].get('timestamp', 0), reverse=True)
            for k, v in items:
                c_ico, c_txt = st.columns([0.35, 0.65])
                with c_ico:
                    i1, i2, i3 = st.columns(3)
                    if i1.button("🗑️", key=f"d{k}"): 
                        st.session_state.confirm_del = k; st.rerun()
                    i2.button("✏️", key=f"e{k}")
                    i3.button("🔍", key=f"v{k}")
                
                # Confirmação simplificada
                if st.session_state.confirm_del == k:
                    st.warning("Excluir?")
                    if st.button("SIM", key=f"sy{k}"):
                        db.reference('consultas').child(k).delete()
                        st.session_state.confirm_del = None; st.rerun()
                    if st.button("NÃO", key=f"sn{k}"): st.session_state.confirm_del = None; st.rerun()

                dt = v['data'] if '-' not in v['data'] else datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                c_txt.markdown(f"<p class='compact-row'><b>{dt}</b> | {v['especialidade'][:10]}.. | Dr. {v['medico'][:8]}</p>", unsafe_allow_html=True)

    with col_cad:
        with st.form("f_con", clear_on_submit=True):
            st.markdown("<div class='main-btn'>", unsafe_allow_html=True)
            sub = st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)
            esp = st.selectbox("Especialidade", LISTA_ESP)
            dat = st.date_input("Data", format="DD/MM/YYYY")
            hor = st.text_input("Hora")
            med = st.text_input("Médico")
            if sub:
                db.reference('consultas').push({'especialidade': esp, 'data': str(dat), 'hora': hor, 'medico': med, 'timestamp': datetime.datetime.now().timestamp()})
                st.success("Cadastrado!")
                st.rerun()

# --- MÓDULO MEDICAMENTOS (COMPACTO) ---
elif st.session_state.page == "meds":
    st.title("💊 Medicamentos")
    col_lista_m, col_cad_m = st.columns([1, 1.3])

    with col_lista_m:
        if st.button("⬅ VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        meds = db.reference('medicamentos').get()
        if meds:
            turnos_ordem = ["MANHÃ", "MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "TARDE", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "NOITE"]
            sorted_m = sorted(meds.items(), key=lambda x: turnos_ordem.index(x[1].get('turno', 'NOITE')))
            for k, v in sorted_m:
                c_i, c_t = st.columns([0.35, 0.65])
                with c_i:
                    m1, m2, m3 = st.columns(3)
                    if m1.button("🗑️", key=f"dm{k}"): st.session_state.confirm_del = k; st.rerun()
                    m2.button("✏️", key=f"em{k}")
                    m3.button("🔍", key=f"vm{k}")
                c_t.markdown(f"<p class='compact-row'><b>{v['turno'][:5]}.</b> | {v['nome']} ({v['mg']})</p>", unsafe_allow_html=True)

    with col_cad_m:
        with st.form("f_med", clear_on_submit=True):
            st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            n = st.text_input("Nome")
            m = st.text_input("mg")
            t = st.selectbox("Turno", turnos_ordem)
            if st.form_submit_button("OK"):
                db.reference('medicamentos').push({'nome': n, 'mg': m, 'turno': t, 'timestamp': datetime.datetime.now().timestamp()})
                st.rerun()

# --- TELAS GENÉRICAS ---
elif st.session_state.page in ["cadastro", "exames", "relatorios"]:
    st.title(st.session_state.page.upper())
    if st.button("VOLTAR ao Início"): mudar_pagina("dashboard")
