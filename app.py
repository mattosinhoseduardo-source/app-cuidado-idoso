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
if 'edit_item_data' not in st.session_state: st.session_state.edit_item_data = None
if 'view_item_id' not in st.session_state: st.session_state.view_item_id = None
if 'user_email' not in st.session_state: st.session_state.user_email = ""

def mudar_pagina(n): 
    st.session_state.page = n
    st.session_state.edit_item_data = None
    st.session_state.view_item_id = None
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
            items = sorted(data.items(), key=lambda x: str(x[1].get('data', '')), reverse=True)
            for k, v in items:
                c_i, c_t = st.columns([0.35, 0.65])
                with c_i:
                    i1, i2, i3 = st.columns(3)
                    if i1.button("🗑️", key=f"d{k}"): st.session_state.confirm_del = k; st.rerun()
                    if i2.button("✏️", key=f"e{k}"): st.session_state.edit_item_data = (k, v); st.rerun()
                    if i3.button("🔍", key=f"v{k}"): st.session_state.view_item_id = k if st.session_state.view_item_id != k else None; st.rerun()
                
                # FORMATO DATA: DD/MM/AAAA
                dt = v['data'] if '-' not in v['data'] else datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                c_t.markdown(f"<p class='compact-row'><b>{dt}</b> | {v['especialidade'][:10]}.. | Dr. {v['medico'][:8]}</p>", unsafe_allow_html=True)
                if st.session_state.view_item_id == k: st.info(f"Local: {v.get('local', 'N/I')} | Hora: {v.get('hora', 'N/I')}")
                if st.session_state.confirm_del == k:
                    if st.button("SIM", key=f"sy{k}"): db.reference('consultas').child(k).delete(); st.session_state.confirm_del = None; st.rerun()
                    st.button("NÃO", key=f"sn{k}")

    with col_cad:
        edit_mode = st.session_state.edit_item_data is not None
        v_edit = st.session_state.edit_item_data[1] if edit_mode else {}
        with st.form("f_con", clear_on_submit=not edit_mode):
            btn_txt = "SALVAR ALTERAÇÕES ✏️" if edit_mode else "CADASTRAR ➕"
            sub = st.form_submit_button(btn_txt, use_container_width=True)
            esp = st.selectbox("Especialidade", LISTA_ESP, index=LISTA_ESP.index(v_edit['especialidade']) if edit_mode else 0)
            dat = st.date_input("Data", value=datetime.datetime.strptime(v_edit['data'], '%Y-%m-%d') if edit_mode else datetime.date.today(), format="DD/MM/YYYY")
            hor = st.text_input("Hora", value=v_edit.get('hora', ''))
            med = st.text_input("Médico", value=v_edit.get('medico', ''))
            loc = st.text_input("Local", value=v_edit.get('local', ''))
            if sub:
                payload = {'especialidade': esp, 'data': str(dat), 'hora': hor, 'medico': med, 'local': loc, 'timestamp': datetime.datetime.now().timestamp()}
                if edit_mode: db.reference('consultas').child(st.session_state.edit_item_data[0]).update(payload); st.session_state.edit_item_data = None
                else: db.reference('consultas').push(payload)
                st.rerun()

# --- MÓDULO MEDICAMENTOS ---
elif st.session_state.page == "meds":
    st.title("💊 Medicamentos")
    col_lista_m, col_cad_m = st.columns([1, 1.3])
    with col_lista_m:
        if st.button("⬅ VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        meds = db.reference('medicamentos').get()
        if meds:
            sorted_m = sorted(meds.items(), key=lambda x: TURNOS.index(x[1].get('turno', 'NOITE')) if x[1].get('turno') in TURNOS else 99)
            for k, v in sorted_m:
                c_i, c_t = st.columns([0.35, 0.65])
                with c_i:
                    m1, m2, m3 = st.columns(3)
                    if m1.button("🗑️", key=f"dm{k}"): st.session_state.confirm_del = k; st.rerun()
                    if m2.button("✏️", key=f"em{k}"): st.session_state.edit_item_data = (k, v); st.rerun()
                    if m3.button("🔍", key=f"vm{k}"): st.session_state.view_item_id = k if st.session_state.view_item_id != k else None; st.rerun()
                c_t.markdown(f"<p class='compact-row'><b>{v['turno'][:12]}..</b> | {v['nome']} ({v['mg']})</p>", unsafe_allow_html=True)
                if st.session_state.view_item_id == k: st.info(f"Médico: {v.get('medico', 'N/I')} | Especialidade: {v.get('especialidade', 'N/I')}")
                if st.session_state.confirm_del == k:
                    if st.button("SIM", key=f"sym{k}"): db.reference('medicamentos').child(k).delete(); st.session_state.confirm_del = None; st.rerun()
                    st.button("NÃO", key=f"snm{k}")

    with col_cad_m:
        edit_mode_m = st.session_state.edit_item_data is not None
        v_m = st.session_state.edit_item_data[1] if edit_mode_m else {}
        with st.form("f_med", clear_on_submit=not edit_mode_m):
            sub_m = st.form_submit_button("SALVAR ALTERAÇÕES ✏️" if edit_mode_m else "CADASTRAR ➕", use_container_width=True)
            nome_med = st.text_input("Nome", value=v_m.get('nome', ''))
            mg_med = st.text_input("mg", value=v_m.get('mg', ''))
            c1, c2 = st.columns(2)
            dt_cad = c1.date_input("Data do Cadastro", value=datetime.datetime.strptime(v_m['data_cadastro'], '%Y-%m-%d') if edit_mode_m else datetime.date.today(), format="DD/MM/YYYY")
            c2.checkbox("Data de Hoje", value=True)
            med_m = st.text_input("Médico", value=v_m.get('medico', ''))
            esp_m = st.selectbox("Especialidade", LISTA_ESP, index=LISTA_ESP.index(v_m['especialidade']) if edit_mode_m else 0)
            turno_m = st.selectbox("Turno", TURNOS, index=TURNOS.index(v_m['turno']) if edit_mode_m else 0)
            if sub_m:
                payload_m = {'nome': nome_med, 'mg': mg_med, 'medico': med_m, 'especialidade': esp_m, 'turno': turno_m, 'data_cadastro': str(dt_cad), 'timestamp': datetime.datetime.now().timestamp()}
                if edit_mode_m: db.reference('medicamentos').child(st.session_state.edit_item_data[0]).update(payload_m); st.session_state.edit_item_data = None
                else: db.reference('medicamentos').push(payload_m)
                st.rerun()

# --- MÓDULO EXAMES ---
elif st.session_state.page == "exames":
    st.title("🧪 Exames")
    col_lista_e, col_cad_e = st.columns([1, 1.3])
    with col_lista_e:
        if st.button("⬅ VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        exames = db.reference('exames').get()
        if exames:
            for k, v in sorted(exames.items(), key=lambda x: str(x[1].get('data', '')), reverse=True):
                ci, ct = st.columns([0.35, 0.65])
                with ci:
                    e1, e2, e3 = st.columns(3)
                    if e1.button("🗑️", key=f"de{k}"): st.session_state.confirm_del = k; st.rerun()
                    if e2.button("✏️", key=f"ee{k}"): st.session_state.edit_item_data = (k, v); st.rerun()
                    if e3.button("🔍", key=f"ve{k}"): st.session_state.view_item_id = k if st.session_state.view_item_id != k else None; st.rerun()
                
                # FORMATO DATA: DD/MM/AAAA
                dt_e = v['data'] if '-' not in v['data'] else datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                ct.markdown(f"<p class='compact-row'><b>{dt_e}</b> | {v['nome'][:12]}.. | Dr. {v['medico'][:8]}</p>", unsafe_allow_html=True)
                if st.session_state.view_item_id == k: st.info(f"Local: {v.get('local', 'N/I')} | Preparo: {v.get('preparo', 'Nenhum')}")
                if st.session_state.confirm_del == k:
                    if st.button("SIM", key=f"sye{k}"): db.reference('exames').child(k).delete(); st.session_state.confirm_del = None; st.rerun()
                    st.button("NÃO", key=f"sne{k}")

    with col_cad_e:
        edit_e = st.session_state.edit_item_data is not None
        v_e = st.session_state.edit_item_data[1] if edit_e else {}
        with st.form("f_exame", clear_on_submit=not edit_e):
            sub_e = st.form_submit_button("SALVAR ALTERAÇÕES ✏️" if edit_e else "CADASTRAR ➕", use_container_width=True)
            n_ex = st.text_input("Nome do Exame", value=v_e.get('nome', ''))
            m_sol = st.text_input("Médico Solicitante", value=v_e.get('medico', ''))
            esp_sol = st.selectbox("Especialidade", LISTA_ESP, index=LISTA_ESP.index(v_e['especialidade']) if edit_e else 0)
            dat_ex = st.date_input("Data da Realização", value=datetime.datetime.strptime(v_e['data'], '%Y-%m-%d') if edit_e else datetime.date.today(), format="DD/MM/YYYY")
            local_ex = st.text_input("Laboratório / Clínica", value=v_e.get('local', ''))
            
            # ALTERAÇÃO: Caixa de texto fixa para Informações de Preparo
            desc_prep = st.text_area("Informações de Preparo", value=v_e.get('preparo', ''))
            
            if sub_e:
                p_e = {'nome': n_ex, 'medico': m_sol, 'especialidade': esp_sol, 'data': str(dat_ex), 'local': local_ex, 'preparo': desc_prep, 'timestamp': datetime.datetime.now().timestamp()}
                if edit_e: db.reference('exames').child(st.session_state.edit_item_data[0]).update(p_e); st.session_state.edit_item_data = None
                else: db.reference('exames').push(p_e)
                st.rerun()

elif st.session_state.page in ["cadastro", "relatorios"]:
    st.title(st.session_state.page.upper())
    if st.button("VOLTAR"): mudar_pagina("dashboard")
