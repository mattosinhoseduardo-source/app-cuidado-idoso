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

# --- CSS ESSÊNCIA COMPACTA ---
st.markdown("""
    <style>
    .block-container { padding-top: 1rem !important; }
    .compact-row { font-size: 11px !important; line-height: 1.1 !important; margin: 0px !important; color: #333; border-bottom: 0.5px solid #eee; padding: 2px 0px; }
    .stButton > button { padding: 0px 4px !important; font-size: 11px !important; height: 22px !important; min-height: 22px !important; background: transparent !important; border: none !important; }
    .main-btn > button { background-color: #f0f2f6 !important; border: 1px solid #ddd !important; height: 35px !important; }
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
TURNOS = ["MANHÃ", "MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "TARDE", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "NOITE"]

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
            else:
                users = db.reference('usuarios_aprovados').get()
                if users and any(v['email'].lower() == email and v['senha'] == senha for v in users.values()):
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
    col_lista, col_cad = st.columns([1, 1.3])
    with col_lista:
        if st.button("⬅ VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        data = db.reference('consultas').get()
        if data:
            items = sorted(data.items(), key=lambda x: x[1].get('timestamp', 0), reverse=True)
            for k, v in items:
                c_i, c_t = st.columns([0.35, 0.65])
                with c_i:
                    i1, i2, i3 = st.columns(3)
                    if i1.button("🗑️", key=f"d{k}"): st.session_state.confirm_del = k; st.rerun()
                    i2.button("✏️", key=f"e{k}")
                    i3.button("🔍", key=f"v{k}")
                if st.session_state.confirm_del == k:
                    st.warning("Excluir?"); c_y, c_n = st.columns(2)
                    if c_y.button("SIM", key=f"sy{k}"): db.reference('consultas').child(k).delete(); st.session_state.confirm_del = None; st.rerun()
                    if c_n.button("NÃO", key=f"sn{k}"): st.session_state.confirm_del = None; st.rerun()
                dt = v['data'] if '-' not in v['data'] else datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                c_t.markdown(f"<p class='compact-row'><b>{dt}</b> | {v['especialidade'][:10]}.. | Dr. {v['medico'][:8]}</p>", unsafe_allow_html=True)

    with col_cad:
        with st.form("f_con", clear_on_submit=True):
            sub = st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            esp = st.selectbox("Especialidade", LISTA_ESP)
            dat = st.date_input("Data da Consulta", format="DD/MM/YYYY")
            hor = st.text_input("Hora da Consulta")
            med = st.text_input("Nome do Médico")
            loc = st.text_input("Clínica / Hospital")
            end = st.text_input("Endereço")
            if sub:
                db.reference('consultas').push({'especialidade': esp, 'data': str(dat), 'hora': hor, 'medico': med, 'local': loc, 'endereco': end, 'timestamp': datetime.datetime.now().timestamp()})
                st.success("Cadastrado!"); st.rerun()

# --- MÓDULO MEDICAMENTOS ---
elif st.session_state.page == "meds":
    st.title("💊 Medicamentos")
    col_lista_m, col_cad_m = st.columns([1, 1.3])
    with col_lista_m:
        if st.button("⬅ VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        meds = db.reference('medicamentos').get()
        if meds:
            sorted_m = sorted(meds.items(), key=lambda x: TURNOS.index(x[1].get('turno', 'NOITE')))
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
            sub_m = st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            nome_med = st.text_input("Nome do Medicamento")
            mg_med = st.text_input("Miligramas (mg)")
            c1, c2 = st.columns(2)
            dt_cad = c1.date_input("Data do Cadastro", format="DD/MM/YYYY")
            c2.checkbox("Data de Hoje", value=True)
            med_m = st.text_input("Médico")
            esp_m = st.selectbox("Especialidade", LISTA_ESP)
            turno_m = st.selectbox("Forma de Uso", TURNOS)
            lembrete = st.checkbox("Necessário Lembrete?")
            if lembrete:
                tipo = st.radio("Tipo", ["Recorrente", "Personalizado"], horizontal=True)
                if tipo == "Recorrente": st.time_input("Horário do Despertador")
                else: st.text_area("Datas e Horas do Despertador")
            if sub_m:
                db.reference('medicamentos').push({'nome': nome_med, 'mg': mg_med, 'medico': med_m, 'especialidade': esp_m, 'turno': turno_m, 'data_cadastro': str(dt_cad), 'timestamp': datetime.datetime.now().timestamp()})
                st.success("Salvo!"); st.rerun()

elif st.session_state.page in ["cadastro", "exames", "relatorios"]:
    st.title(st.session_state.page.upper())
    if st.button("VOLTAR"): mudar_pagina("dashboard")
