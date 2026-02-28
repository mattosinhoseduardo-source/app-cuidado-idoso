import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime

# --- CONFIGURAÇÃO DO FIREBASE (NÃO ALTERAR) ---
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

# --- CSS DEFINITIVO (COMPACTO E LIMPO) ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    .compact-row { font-size: 11px !important; line-height: 1.1 !important; margin: 0px !important; color: #333; border-bottom: 0.5px solid #eee; padding: 2px 0px; }
    .stButton > button { padding: 0px 2px !important; font-size: 12px !important; height: 22px !important; min-height: 22px !important; background: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADOS DE SESSÃO ---
if 'page' not in st.session_state: st.session_state.page = "login"
if 'confirm_del' not in st.session_state: st.session_state.confirm_del = None
if 'view_item' not in st.session_state: st.session_state.view_item = None

def mudar_pagina(n): 
    st.session_state.page = n
    st.rerun()

LISTA_ESP = ["Alergista", "Anestesiologia", "Angiologia", "Cardiologia", "Cirurgião", "Clínico Geral", "Coloproctologia", "Dermatologia", "Endocrinologia", "Gastroenterologia", "Geriatria", "Ginecologia e obstetrícia", "Hematologia e hemoterapia", "Infectologia", "Mastologia", "Nefrologia", "Neurocirurgia", "Neurologia", "Nutrologia", "Oftalmologia", "Ortopedia e traumatologia", "Otorrinolaringologia", "Pneumologia", "Psiquiatria", "Reumatologia", "Urologia"]
ORDEM_TURNOS = ["MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "MANHÃ", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "TARDE", "NOITE"]

# --- 1ª TELA: LOGIN (RESTAURADA CONFORME PEDIDO) ---
if st.session_state.page == "login":
    st.title("🏥 Gestão de Cuidados")
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")
    c_ok, c_can = st.columns(2)
    with c_ok:
        if st.button("OK", use_container_width=True):
            if email == "admin@teste.com" and senha == "123": mudar_pagina("dashboard")
            else: st.error("Login Inválido")
    with c_can:
        st.button("CANCELAR", use_container_width=True)
    st.divider()
    if st.button("Cadastrar Novo Usuário", use_container_width=True): mudar_pagina("cadastro")
    st.button("Esqueci a Senha", use_container_width=True)

# --- DASHBOARD ---
elif st.session_state.page == "dashboard":
    st.title("Painel Principal")
    c1, c2 = st.columns(2)
    if c1.button("💊 MEDICAMENTOS", use_container_width=True): mudar_pagina("meds")
    if c1.button("📅 CONSULTAS", use_container_width=True): mudar_pagina("consultas")
    if c2.button("🧪 EXAMES", use_container_width=True): mudar_pagina("exames")
    if c2.button("📊 RELATÓRIOS", use_container_width=True): mudar_pagina("relatorios")

# --- MÓDULO CONSULTAS ---
elif st.session_state.page == "consultas":
    st.title("📅 Consultas")
    col_l, col_r = st.columns([1, 1.3])
    with col_l:
        if st.button("⬅ VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        data = db.reference('consultas').get()
        if data:
            # Ordenação Cronológica Decrescente
            for k, v in sorted(data.items(), key=lambda x: x[1].get('data', ''), reverse=True):
                c_i, c_t = st.columns([0.35, 0.65])
                with c_i:
                    if st.button("🗑️", key=f"dc{k}"): st.session_state.confirm_del = ('consultas', k); st.rerun()
                    st.button("✏️", key=f"ec{k}"); st.button("🔍", key=f"vc{k}")
                c_t.markdown(f"<p class='compact-row'><b>{v['data']}</b> | {v['especialidade'][:10]}.. | Dr. {v['medico'][:8]}</p>", unsafe_allow_html=True)
                if st.session_state.confirm_del == ('consultas', k):
                    st.warning("Excluir?"); cy, cn = st.columns(2)
                    if cy.button("SIM", key=f"cy{k}"): db.reference('consultas').child(k).delete(); st.session_state.confirm_del = None; st.rerun()
                    if cn.button("NÃO", key=f"cn{k}"): st.session_state.confirm_del = None; st.rerun()

    with col_r:
        with st.form("f_con", clear_on_submit=True):
            st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            esp = st.selectbox("Especialidade", LISTA_ESP)
            dat = st.date_input("Data")
            hor = st.text_input("Hora")
            med = st.text_input("Médico")
            loc = st.text_input("Local")
            if st.form_submit_button("SALVAR"):
                db.reference('consultas').push({'especialidade': esp, 'data': str(dat), 'hora': hor, 'medico': med, 'local': loc, 'timestamp': datetime.datetime.now().timestamp()})
                st.rerun()

# --- MÓDULO MEDICAMENTOS ---
elif st.session_state.page == "meds":
    st.title("💊 Medicamentos")
    col_l, col_r = st.columns([1, 1.3])
    with col_l:
        if st.button("⬅ VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        meds = db.reference('medicamentos').get()
        if meds:
            # Ordenação por Turno
            for k, v in sorted(meds.items(), key=lambda x: ORDEM_TURNOS.index(x[1].get('turno', 'NOITE')) if x[1].get('turno') in ORDEM_TURNOS else 99):
                ci, ct = st.columns([0.35, 0.65])
                with ci:
                    if st.button("🗑️", key=f"dm{k}"): st.session_state.confirm_del = ('medicamentos', k); st.rerun()
                    st.button("✏️", key=f"em{k}"); st.button("🔍", key=f"vm{k}")
                ct.markdown(f"<p class='compact-row'><b>{v['turno'][:12]}..</b> | {v['nome']} ({v['mg']})</p>", unsafe_allow_html=True)
                if st.session_state.confirm_del == ('medicamentos', k):
                    st.warning("Excluir?"); my, mn = st.columns(2)
                    if my.button("SIM", key=f"my{k}"): db.reference('medicamentos').child(k).delete(); st.session_state.confirm_del = None; st.rerun()
                    if mn.button("NÃO", key=f"mn{k}"): st.session_state.confirm_del = None; st.rerun()

    with col_r:
        with st.form("f_med", clear_on_submit=True):
            st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            n_m = st.text_input("Nome")
            m_m = st.text_input("mg")
            med_m = st.text_input("Médico")
            t_m = st.selectbox("Forma de Uso", ORDEM_TURNOS)
            if st.form_submit_button("OK"):
                db.reference('medicamentos').push({'nome': n_m, 'mg': m_m, 'medico': med_m, 'turno': t_m, 'timestamp': datetime.datetime.now().timestamp()})
                st.rerun()

# --- MÓDULO EXAMES ---
elif st.session_state.page == "exames":
    st.title("🧪 Exames")
    col_l, col_r = st.columns([1, 1.3])
    with col_l:
        if st.button("⬅ VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        exs = db.reference('exames').get()
        if exs:
            for k, v in sorted(exs.items(), key=lambda x: x[1].get('data', ''), reverse=True):
                ci, ct = st.columns([0.35, 0.65])
                with ci:
                    if st.button("🗑️", key=f"de{k}"): st.session_state.confirm_del = ('exames', k); st.rerun()
                    st.button("✏️", key=f"ee{k}"); st.button("🔍", key=f"ve{k}")
                ct.markdown(f"<p class='compact-row'><b>{v['data']}</b> | {v['nome'][:10]}.. | {v['medico'][:8]}</p>", unsafe_allow_html=True)
                if st.session_state.confirm_del == ('exames', k):
                    st.warning("Excluir?"); ey, en = st.columns(2)
                    if ey.button("SIM", key=f"ey{k}"): db.reference('exames').child(k).delete(); st.session_state.confirm_del = None; st.rerun()
                    if en.button("NÃO", key=f"en{k}"): st.session_state.confirm_del = None; st.rerun()

    with col_r:
        with st.form("f_ex", clear_on_submit=True):
            st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            n_e = st.text_input("Exame")
            m_e = st.text_input("Médico")
            d_e = st.date_input("Data")
            prep = st.checkbox("Necessário Preparo?")
            if prep: st.text_area("Descreva o preparo:")
            if st.form_submit_button("SALVAR EXAME"):
                db.reference('exames').push({'nome': n_e, 'medico': m_e, 'data': str(d_e), 'timestamp': datetime.datetime.now().timestamp()})
                st.rerun()

# --- TELAS EXTRAS ---
elif st.session_state.page in ["cadastro", "relatorios"]:
    st.title(st.session_state.page.upper())
    if st.button("VOLTAR"): mudar_pagina("login" if st.session_state.page == "cadastro" else "dashboard")
