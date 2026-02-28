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
    .stButton > button { padding: 0px 2px !important; font-size: 12px !important; height: 22px !important; min-height: 22px !important; background: transparent !important; }
    .login-btn > button { background-color: #f0f2f6 !important; border: 1px solid #ddd !important; height: 38px !important; font-size: 14px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO E ESTADOS ---
if 'page' not in st.session_state: st.session_state.page = "login"
if 'user_email' not in st.session_state: st.session_state.user_email = ""
if 'confirm_del' not in st.session_state: st.session_state.confirm_del = None
if 'edit_item' not in st.session_state: st.session_state.edit_item = None
if 'view_item' not in st.session_state: st.session_state.view_item = None

def mudar_pagina(n): 
    st.session_state.page = n
    st.rerun()

LISTA_ESP = ["Alergista", "Anestesiologia", "Angiologia", "Cardiologia", "Cirurgião", "Clínico Geral", "Coloproctologia", "Dermatologia", "Endocrinologia", "Gastroenterologia", "Geriatria", "Ginecologia e obstetrícia", "Hematologia e hemoterapia", "Infectologia", "Mastologia", "Nefrologia", "Neurocirurgia", "Neurologia", "Nutrologia", "Oftalmologia", "Ortopedia e traumatologia", "Otorrinolaringologia", "Pneumologia", "Psiquiatria", "Reumatologia", "Urologia"]
TURNOS = ["MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "MANHÃ", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "TARDE", "NOITE"]

# --- 1ª TELA: LOGIN (CONDIÇÃO ANTERIOR RESTAURADA) ---
if st.session_state.page == "login":
    st.title("🏥 Gestão de Cuidados")
    email = st.text_input("E-mail").lower().strip()
    senha = st.text_input("Senha", type="password")
    
    col_ok, col_can = st.columns(2)
    with col_ok:
        if st.button("OK", use_container_width=True, key="btn_login_ok"):
            if email == "admin@teste.com" and senha == "123":
                st.session_state.user_email = email
                mudar_pagina("dashboard")
            else:
                users = db.reference('usuarios_aprovados').get()
                if users and any(v['email'].lower() == email and v['senha'] == senha for v in users.values()):
                    st.session_state.user_email = email
                    mudar_pagina("dashboard")
                else: st.error("Acesso Negado.")
    with col_can:
        st.button("CANCELAR", use_container_width=True, key="btn_login_cancel")

    st.divider()
    if st.button("Cadastrar Novo Usuário", use_container_width=True, key="btn_ir_cadastro"): 
        mudar_pagina("cadastro")
    st.button("Esqueci a Senha", use_container_width=True, key="btn_esqueci_senha")

# --- DASHBOARD ---
elif st.session_state.page == "dashboard":
    st.title("Painel Principal")
    c1, c2 = st.columns(2)
    if c1.button("💊 MEDICAMENTOS", use_container_width=True): mudar_pagina("meds")
    if c1.button("📅 CONSULTAS", use_container_width=True): mudar_pagina("consultas")
    if c2.button("🧪 EXAMES", use_container_width=True): mudar_pagina("exames")
    if c2.button("📊 RELATÓRIOS", use_container_width=True): mudar_pagina("relatorios")
    st.divider()
    if st.button("Sair"): 
        st.session_state.user_email = ""
        mudar_pagina("login")

# --- MÓDULO CONSULTAS ---
elif st.session_state.page == "consultas":
    st.title("📅 Consultas")
    col_lista, col_cad = st.columns([1, 1.3])
    with col_lista:
        if st.button("⬅ VOLTAR", use_container_width=True, key="back_c"): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        data = db.reference('consultas').get()
        if data:
            items = sorted(data.items(), key=lambda x: x[1].get('data', ''), reverse=True)
            for k, v in items:
                c_i, c_t = st.columns([0.35, 0.65])
                with c_i:
                    if st.button("🗑️", key=f"d_c{k}"): st.session_state.confirm_del = ('consultas', k); st.rerun()
                    if st.button("✏️", key=f"e_c{k}"): st.session_state.edit_item = ('consultas', k, v); mudar_pagina("editar")
                    if st.button("🔍", key=f"v_c{k}"): st.session_state.view_item = v; mudar_pagina("detalhes")
                dt_f = datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y') if '-' in v['data'] else v['data']
                c_t.markdown(f"<p class='compact-row'><b>{dt_f}</b> | {v['especialidade'][:10]}.. | Dr. {v['medico'][:8]}</p>", unsafe_allow_html=True)
                if st.session_state.confirm_del == ('consultas', k):
                    st.error("Excluir?"); cy, cn = st.columns(2)
                    if cy.button("SIM", key=f"cy_c{k}"): db.reference('consultas').child(k).delete(); st.session_state.confirm_del = None; st.rerun()
                    if cn.button("NÃO", key=f"cn_c{k}"): st.session_state.confirm_del = None; st.rerun()

    with col_cad:
        with st.form("f_con", clear_on_submit=True):
            st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            esp = st.selectbox("Especialidade", LISTA_ESP)
            dat = st.date_input("Data da Consulta")
            hor = st.text_input("Hora")
            med = st.text_input("Médico")
            loc = st.text_input("Local/Endereço")
            if st.form_submit_button("SALVAR"):
                db.reference('consultas').push({'especialidade': esp, 'data': str(dat), 'hora': hor, 'medico': med, 'local': loc, 'timestamp': datetime.datetime.now().timestamp()})
                st.rerun()

# --- MÓDULO MEDICAMENTOS ---
elif st.session_state.page == "meds":
    st.title("💊 Medicamentos")
    col_l, col_c = st.columns([1, 1.3])
    with col_l:
        if st.button("⬅ VOLTAR", use_container_width=True, key="back_m"): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        meds = db.reference('medicamentos').get()
        if meds:
            sorted_m = sorted(meds.items(), key=lambda x: TURNOS.index(x[1].get('turno', 'NOITE')) if x[1].get('turno') in TURNOS else 99)
            for k, v in sorted_m:
                ci, ct = st.columns([0.35, 0.65])
                with ci:
                    if st.button("🗑️", key=f"d_m{k}"): st.session_state.confirm_del = ('medicamentos', k); st.rerun()
                    if st.button("✏️", key=f"e_m{k}"): st.session_state.edit_item = ('medicamentos', k, v); mudar_pagina("editar")
                    if st.button("🔍", key=f"v_m{k}"): st.session_state.view_item = v; mudar_pagina("detalhes")
                ct.markdown(f"<p class='compact-row'><b>{v['turno'][:12]}..</b> | {v['nome']} ({v['mg']})</p>", unsafe_allow_html=True)
                if st.session_state.confirm_del == ('medicamentos', k):
                    st.error("Excluir?"); my, mn = st.columns(2)
                    if my.button("SIM", key=f"my_m{k}"): db.reference('medicamentos').child(k).delete(); st.session_state.confirm_del = None; st.rerun()
                    if mn.button("NÃO", key=f"mn_m{k}"): st.session_state.confirm_del = None; st.rerun()

    with col_c:
        with st.form("f_med", clear_on_submit=True):
            st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            n_m = st.text_input("Nome")
            m_m = st.text_input("mg")
            med_m = st.text_input("Médico")
            t_m = st.selectbox("Forma de Uso", TURNOS)
            if st.form_submit_button("OK"):
                db.reference('medicamentos').push({'nome': n_m, 'mg': m_m, 'medico': med_m, 'turno': t_m, 'timestamp': datetime.datetime.now().timestamp()})
                st.rerun()

# --- MÓDULO EXAMES ---
elif st.session_state.page == "exames":
    st.title("🧪 Exames")
    col_le, col_ce = st.columns([1, 1.3])
    with col_le:
        if st.button("⬅ VOLTAR", use_container_width=True, key="back_e"): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        exs = db.reference('exames').get()
        if exs:
            for k, v in sorted(exs.items(), key=lambda x: x[1].get('data', ''), reverse=True):
                ci, ct = st.columns([0.35, 0.65])
                with ci:
                    if st.button("🗑️", key=f"d_e{k}"): st.session_state.confirm_del = ('exames', k); st.rerun()
                    if st.button("✏️", key=f"e_e{k}"): st.session_state.edit_item = ('exames', k, v); mudar_pagina("editar")
                    if st.button("🔍", key=f"v_e{k}"): st.session_state.view_item = v; mudar_pagina("detalhes")
                dt_e = datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y') if '-' in v['data'] else v['data']
                ct.markdown(f"<p class='compact-row'><b>{dt_e}</b> | {v['nome'][:10]}.. | {v['medico'][:8]}</p>", unsafe_allow_html=True)
                if st.session_state.confirm_del == ('exames', k):
                    st.error("Excluir?"); ey, en = st.columns(2)
                    if ey.button("SIM", key=f"ey_e{k}"): db.reference('exames').child(k).delete(); st.session_state.confirm_del = None; st.rerun()
                    if en.button("NÃO", key=f"en_e{k}"): st.session_state.confirm_del = None; st.rerun()

    with col_ce:
        with st.form("f_ex", clear_on_submit=True):
            st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            n_ex = st.text_input("Exame")
            m_ex = st.text_input("Médico")
            d_ex = st.date_input("Data")
            prep_check = st.checkbox("Necessário Preparo?")
            desc_prep = st.text_area("Descreva o preparo:") if prep_check else ""
            if st.form_submit_button("SALVAR EXAME"):
                db.reference('exames').push({'nome': n_ex, 'medico': m_ex, 'data': str(d_ex), 'preparo': desc_prep, 'timestamp': datetime.datetime.now().timestamp()})
                st.rerun()

# --- TELAS DE SUPORTE ---
elif st.session_state.page == "detalhes":
    st.title("🔍 Informações")
    v = st.session_state.view_item
    for c, val in v.items():
        if c != 'timestamp': st.info(f"**{c.upper()}:** {val}")
    if st.button("VOLTAR"): mudar_pagina("dashboard")

elif st.session_state.page == "editar":
    st.title("✏️ Editar")
    path, kid, old_v = st.session_state.edit_item
    new_name = st.text_input("Nome/Especialidade", value=old_v.get('nome') or old_v.get('especialidade'))
    if st.button("SALVAR"):
        db.reference(path).child(kid).update({'nome': new_name} if 'nome' in old_v else {'especialidade': new_name})
        mudar_pagina(path)
    if st.button("CANCELAR"): mudar_pagina(path)

elif st.session_state.page == "cadastro":
    st.title("📝 Novo Cadastro")
    # Lógica de cadastro de usuário aqui
    if st.button("VOLTAR"): mudar_pagina("login")
