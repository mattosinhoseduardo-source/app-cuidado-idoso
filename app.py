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

# --- CSS PARA MÁXIMA COMPACTAÇÃO ---
st.markdown("""
    <style>
    /* Reduz todo o espaçamento do Streamlit */
    .block-container { padding-top: 1rem !important; }
    .stApp { line-height: 1.1; }
    
    /* Estilo para as linhas da lista */
    .row-container {
        display: flex;
        align-items: center;
        padding: 2px 0px;
        border-bottom: 1px solid #f0f0f0;
        gap: 8px;
    }
    .info-text {
        font-size: 11px !important;
        color: #333;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    /* Estilo dos micro-botões */
    .stButton > button {
        padding: 0px 2px !important;
        font-size: 10px !important;
        height: 18px !important;
        min-height: 18px !important;
        border: none !important;
        background: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO ---
if 'page' not in st.session_state: st.session_state.page = "login"
if 'confirm_del' not in st.session_state: st.session_state.confirm_del = None

def mudar_pagina(n): 
    st.session_state.page = n
    st.rerun()

LISTA_ESP = ["Alergista", "Anestesiologia", "Angiologia", "Cardiologia", "Cirurgião", "Clínico Geral", "Coloproctologia", "Dermatologia", "Endocrinologia", "Gastroenterologia", "Geriatria", "Ginecologia e obstetrícia", "Hematologia e hemoterapia", "Infectologia", "Mastologia", "Nefrologia", "Neurocirurgia", "Neurologia", "Nutrologia", "Oftalmologia", "Ortopedia e traumatologia", "Otorrinolaringologia", "Pneumologia", "Psiquiatria", "Reumatologia", "Urologia"]

# --- LOGIN / DASHBOARD ---
if st.session_state.page == "login":
    st.title("🏥 Login")
    e = st.text_input("E-mail")
    s = st.text_input("Senha", type="password")
    if st.button("OK", use_container_width=True): mudar_pagina("dashboard")

elif st.session_state.page == "dashboard":
    st.title("Painel Principal")
    c1, c2 = st.columns(2)
    if c1.button("💊 MEDICAMENTOS", use_container_width=True): mudar_pagina("meds")
    if c1.button("📅 CONSULTAS", use_container_width=True): mudar_pagina("consultas")
    if c2.button("🧪 EXAMES", use_container_width=True): mudar_pagina("exames")
    if c2.button("📊 RELATÓRIOS", use_container_width=True): mudar_pagina("relatorios")

# --- MÓDULO CONSULTAS ---
elif st.session_state.page == "consultas":
    col_lista, col_cad = st.columns([1, 1.2])

    with col_lista:
        if st.button("⬅ VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        
        # Confirmação de exclusão simplificada no topo
        if st.session_state.confirm_del:
            st.error("Excluir item?")
            c_y, c_n = st.columns(2)
            if c_y.button("SIM"):
                db.reference('consultas').child(st.session_state.confirm_del).delete()
                st.session_state.confirm_del = None; st.rerun()
            if c_n.button("NÃO"): st.session_state.confirm_del = None; st.rerun()

        data = db.reference('consultas').get()
        if data:
            items = sorted(data.items(), key=lambda x: x[1].get('timestamp', 0), reverse=True)
            for k, v in items:
                # Linha compacta com ícones mínimos
                c_ico, c_txt = st.columns([0.35, 0.65])
                with c_ico:
                    ic1, ic2, ic3 = st.columns(3)
                    ic1.button("🗑️", key=f"d{k}", help="Excluir")
                    if ic1.button("", key=f"act_d{k}"): # Truque para clique no ícone
                        st.session_state.confirm_del = k; st.rerun()
                    ic2.button("✏️", key=f"e{k}")
                    ic3.button("🔍", key=f"v{k}")
                
                dt = v['data'][-2:] + "/" + v['data'][5:7] # Simplifica data p/ DD/MM
                c_txt.markdown(f"<p class='info-text'><b>{dt}</b> {v['hora']} | {v['especialidade'][:12]}.. | {v['medico'][:10]}</p>", unsafe_allow_html=True)

    with col_cad:
        with st.form("f_con", clear_on_submit=True):
            if st.form_submit_button("CADASTRAR ➕", use_container_width=True):
                # Lógica de salvar omitida aqui para brevidade, mas mantida no seu código real
                pass
            esp = st.selectbox("Especialidade", LISTA_ESP)
            dat = st.date_input("Data")
            hor = st.text_input("Hora")
            med = st.text_input("Médico")
            st.text_input("Local")

# --- MÓDULO MEDICAMENTOS ---
elif st.session_state.page == "meds":
    col_lista_m, col_cad_m = st.columns([1, 1.2])

    with col_lista_m:
        if st.button("⬅ VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        
        meds = db.reference('medicamentos').get()
        if meds:
            turnos_ordem = ["MANHÃ", "MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "TARDE", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "NOITE"]
            for k, v in sorted(meds.items(), key=lambda x: turnos_ordem.index(x[1].get('turno', 'NOITE'))):
                c_ico_m, c_txt_m = st.columns([0.35, 0.65])
                with c_ico_m:
                    m1, m2, m3 = st.columns(3)
                    if m1.button("🗑️", key=f"dm{k}"): st.session_state.confirm_del = k; st.rerun()
                    m2.button("✏️", key=f"em{k}")
                    m3.button("🔍", key=f"vm{k}")
                
                c_txt_m.markdown(f"<p class='info-text'><b>{v['turno'][:5]}.</b> | {v['nome']} ({v['mg']})</p>", unsafe_allow_html=True)

    with col_cad_m:
        with st.form("f_med", clear_on_submit=True):
            st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            st.text_input("Nome")
            st.text_input("mg")
            st.selectbox("Turno", ["MANHÃ", "NOITE"]) # Simplificado
