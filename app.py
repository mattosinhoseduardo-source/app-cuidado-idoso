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

# --- CSS PARA DESIGN PROFISSIONAL E COMPACTO ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    .compact-row { font-size: 11px !important; line-height: 1.1 !important; margin: 0px !important; color: #333; border-bottom: 0.5px solid #eee; padding: 3px 0px; display: flex; align-items: center; }
    .stButton > button { padding: 0px 2px !important; font-size: 10px !important; height: 20px !important; min-height: 20px !important; background: transparent !important; border: none !important; }
    .main-btn > button { background-color: #f0f2f6 !important; border: 1px solid #ddd !important; height: 38px !important; font-size: 14px !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO E ESTADOS ---
if 'page' not in st.session_state: st.session_state.page = "login"
if 'confirm_del' not in st.session_state: st.session_state.confirm_del = None
if 'user_email' not in st.session_state: st.session_state.user_email = ""

def mudar_pagina(n): 
    st.session_state.page = n
    st.rerun()

LISTA_ESP = ["Alergista", "Anestesiologia", "Angiologia", "Cardiologia", "Cirurgião", "Clínico Geral", "Coloproctologia", "Dermatologia", "Endocrinologia", "Gastroenterologia", "Geriatria", "Ginecologia e obstetrícia", "Hematologia e hemoterapia", "Infectologia", "Mastologia", "Nefrologia", "Neurocirurgia", "Neurologia", "Nutrologia", "Oftalmologia", "Ortopedia e traumatologia", "Otorrinolaringologia", "Pneumologia", "Psiquiatria", "Reumatologia", "Urologia"]
TURNOS = ["MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "MANHÃ", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "TARDE", "NOITE"]

# --- 1ª TELA: LOGIN ---
if st.session_state.page == "login":
    st.title("🏥 Gestão de Cuidados")
    email = st.text_input("E-mail").lower().strip()
    senha = st.text_input("Senha", type="password")
    c_ok, c_can = st.columns(2)
    with c_ok:
        if st.button("OK", use_container_width=True):
            if email == "admin@teste.com" and senha == "123":
                st.session_state.user_email = email
                mudar_pagina("dashboard")
            else: st.error("Acesso Negado.")
    with c_can: st.button("CANCELAR", use_container_width=True)
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
    st.divider()
    if st.button("Sair"): mudar_pagina("login")

# --- MÓDULO CONSULTAS ---
elif st.session_state.page == "consultas":
    st.title("📅 Consultas")
    col_l, col_r = st.columns([1, 1.3])
    with col_l:
        if st.button("⬅ VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        data = db.reference('consultas').get()
        if data:
            for k, v in sorted(data.items(), key=lambda x: x[1].get('data', ''), reverse=True):
                c_tools, c_text = st.columns([0.35, 0.65])
                with c_tools:
                    i1, i2, i3 = st.columns(3)
                    if i1.button("🗑️", key=f"dc{k}"): st.session_state.confirm_del = k; st.rerun()
                    i2.button("✏️", key=f"ec{k}"); i3.button("🔍", key=f"vc{k}")
                c_text.markdown(f"<p class='compact-row'><b>{v['data']}</b> | {v['especialidade'][:10]}.. | Dr. {v['medico'][:8]}</p>", unsafe_allow_html=True)
                if st.session_state.confirm_del == k:
                    st.error("Excluir?"); cy, cn = st.columns(2)
                    if cy.button("SIM", key=f"y{k}"): db.reference('consultas').child(k).delete(); st.session_state.confirm_del = None; st.rerun()
                    if cn.button("NÃO", key=f"n{k}"): st.session_state.confirm_del = None; st.rerun()
    with col_r:
        with st.form("f_con", clear_on_submit=True):
            st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            esp = st.selectbox("Especialidade", LISTA_ESP)
            dat = st.date_input("Data da Consulta")
            hor = st.text_input("Hora da Consulta")
            med = st.text_input("Nome do Médico")
            loc = st.text_input("Clínica / Hospital")
            end = st.text_input("Endereço")
            if st.form_submit_button("SALVAR"):
                db.reference('consultas').push({'especialidade': esp, 'data': str(dat), 'hora': hor, 'medico': med, 'local': loc, 'endereco': end, 'timestamp': datetime.datetime.now().timestamp()})
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
            for k, v in sorted(meds.items(), key=lambda x: TURNOS.index(x[1].get('turno', 'NOITE')) if x[1].get('turno') in TURNOS else 99):
                ci, ct = st.columns([0.35, 0.65])
                with ci:
                    m1, m2, m3 = st.columns(3)
                    if m1.button("🗑️", key=f"dm{k}"): st.session_state.confirm_del = k; st.rerun()
                    m2.button("✏️", key=f"em{k}"); m3.button("🔍", key=f"vm{k}")
                ct.markdown(f"<p class='compact-row'><b>{v['turno'][:12]}..</b> | {v['nome']} ({v['mg']})</p>", unsafe_allow_html=True)
                if st.session_state.confirm_del == k:
                    st.error("Excluir?"); my, mn = st.columns(2)
                    if my.button("SIM", key=f"my{k}"): db.reference('medicamentos').child(k).delete(); st.session_state.confirm_del = None; st.rerun()
                    if mn.button("NÃO", key=f"mn{k}"): st.session_state.confirm_del = None; st.rerun()
    with col_r:
        with st.form("f_med", clear_on_submit=True):
            st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            n_m = st.text_input("Nome do Medicamento")
            m_m = st.text_input("Miligramas (mg)")
            c1, c2 = st.columns(2)
            dt_cad = c1.date_input("Data do Cadastro")
            c2.checkbox("Data de Hoje", value=True)
            med_m = st.text_input("Médico")
            esp_m = st.selectbox("Especialidade", LISTA_ESP)
            t_m = st.selectbox("Forma de Uso", TURNOS)
            lembrete = st.checkbox("Necessário Lembrete?")
            if lembrete:
                tipo = st.radio("Tipo", ["Recorrente", "Personalizado"], horizontal=True)
                if tipo == "Recorrente": st.time_input("Horário do Despertador")
                else: st.text_area("Datas e Horas (Ex: 01/03 08h, 02/03 10h)")
            if st.form_submit_button("OK"):
                db.reference('medicamentos').push({'nome': n_m, 'mg': m_m, 'medico': med_m, 'especialidade': esp_m, 'turno': t_m, 'data_cadastro': str(dt_cad), 'timestamp': datetime.datetime.now().timestamp()})
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
                    e1, e2, e3 = st.columns(3)
                    if e1.button("🗑️", key=f"de{k}"): st.session_state.confirm_del = k; st.rerun()
                    e2.button("✏️", key=f"ee{k}"); e3.button("🔍", key=f"ve{k}")
                ct.markdown(f"<p class='compact-row'><b>{v['data']}</b> | {v['nome'][:10]}.. | Dr. {v['medico'][:8]}</p>", unsafe_allow_html=True)
    with col_r:
        with st.form("f_ex", clear_on_submit=True):
            st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            n_ex = st.text_input("Nome do Exame")
            med_sol = st.text_input("Médico Solicitante")
            esp_sol = st.selectbox("Especialidade", LISTA_ESP)
            data_ex = st.date_input("Data da Realização")
            loc_ex = st.text_input("Laboratório / Clínica")
            preparo = st.checkbox("Necessário Preparo?")
            if preparo: st.text_area("Descreva o preparo necessário")
            if st.form_submit_button("SALVAR"):
                db.reference('exames').push({'nome': n_ex, 'medico': med_sol, 'especialidade': esp_sol, 'data': str(data_ex), 'local': loc_ex, 'timestamp': datetime.datetime.now().timestamp()})
                st.rerun()
