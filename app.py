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
    .stButton > button { padding: 0px 1px !important; font-size: 10px !important; height: 18px !important; min-height: 18px !important; background: transparent !important; border: none !important; }
    .main-btn > button { background-color: #f0f2f6 !important; border: 1px solid #ddd !important; height: 35px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO E ESTADOS ---
if 'page' not in st.session_state: st.session_state.page = "login"
if 'confirm_del' not in st.session_state: st.session_state.confirm_del = None
if 'edit_item_data' not in st.session_state: st.session_state.edit_item_data = None
if 'view_item_id' not in st.session_state: st.session_state.view_item_id = None

def mudar_pagina(n): 
    st.session_state.page = n
    st.session_state.edit_item_data = None
    st.session_state.view_item_id = None
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
                    if i1.button("🗑️", key=f"dc{k}"): st.session_state.confirm_del = k; st.rerun()
                    if i2.button("✏️", key=f"ec{k}"): 
                        st.session_state.edit_item_data = (k, v)
                        st.rerun()
                    if i3.button("🔍", key=f"vc{k}"): 
                        st.session_state.view_item_id = k if st.session_state.view_item_id != k else None
                        st.rerun()
                
                dt = v['data'] if '-' not in v['data'] else datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                c_t.markdown(f"<p class='compact-row'><b>{dt}</b> | {v['especialidade'][:10]}.. | Dr. {v['medico'][:8]}</p>", unsafe_allow_html=True)

                if st.session_state.view_item_id == k:
                    st.info(f"📍 {v.get('local', 'Não informado')}\n\n⏰ {v.get('hora', 'Não informada')}")

                if st.session_state.confirm_del == k:
                    st.warning("Excluir?"); cy, cn = st.columns(2)
                    if cy.button("SIM", key=f"cyc{k}"): 
                        db.reference('consultas').child(k).delete()
                        st.session_state.confirm_del = None; st.rerun()
                    if cn.button("NÃO", key=f"cnc{k}"): st.session_state.confirm_del = None; st.rerun()

    with col_cad:
        # Lógica de Edição vs Cadastro
        edit_mode = st.session_state.edit_item_data is not None
        titulo_btn = "SALVAR ALTERAÇÕES ✏️" if edit_mode else "CADASTRAR ➕"
        item_v = st.session_state.edit_item_data[1] if edit_mode else {}

        with st.form("f_con", clear_on_submit=not edit_mode):
            sub = st.form_submit_button(titulo_btn, use_container_width=True)
            esp = st.selectbox("Especialidade", LISTA_ESP, index=LISTA_ESP.index(item_v['especialidade']) if edit_mode else 0)
            dat = st.date_input("Data", value=datetime.datetime.strptime(item_v['data'], '%Y-%m-%d') if edit_mode else datetime.date.today())
            hor = st.text_input("Hora", value=item_v.get('hora', ''))
            med = st.text_input("Médico", value=item_v.get('medico', ''))
            loc = st.text_input("Local", value=item_v.get('local', ''))
            if sub:
                payload = {'especialidade': esp, 'data': str(dat), 'hora': hor, 'medico': med, 'local': loc, 'timestamp': datetime.datetime.now().timestamp()}
                if edit_mode:
                    db.reference('consultas').child(st.session_state.edit_item_data[0]).update(payload)
                    st.session_state.edit_item_data = None
                else:
                    db.reference('consultas').push(payload)
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
            sorted_m = sorted(meds.items(), key=lambda x: TURNOS.index(x[1].get('turno', 'NOITE')) if x[1].get('turno') in TURNOS else 99)
            for k, v in sorted_m:
                c_i, c_t = st.columns([0.35, 0.65])
                with c_i:
                    m1, m2, m3 = st.columns(3)
                    if m1.button("🗑️", key=f"dm{k}"): st.session_state.confirm_del = k; st.rerun()
                    if m2.button("✏️", key=f"em{k}"): st.session_state.edit_item_data = (k, v); st.rerun()
                    if m3.button("🔍", key=f"vm{k}"):
                        st.session_state.view_item_id = k if st.session_state.view_item_id != k else None
                        st.rerun()
                c_t.markdown(f"<p class='compact-row'><b>{v['turno'][:12]}..</b> | {v['nome']} ({v['mg']})</p>", unsafe_allow_html=True)
                
                if st.session_state.view_item_id == k:
                    st.info(f"👨‍⚕️ Médico: {v.get('medico', 'Não informado')}\n\n📅 Cadastrado em: {v.get('data_cadastro', 'N/A')}")

                if st.session_state.confirm_del == k:
                    st.warning("Excluir?"); my, mn = st.columns(2)
                    if my.button("SIM", key=f"sym{k}"): 
                        db.reference('medicamentos').child(k).delete()
                        st.session_state.confirm_del = None; st.rerun()
                    if mn.button("NÃO", key=f"snm{k}"): st.session_state.confirm_del = None; st.rerun()

    with col_r:
        edit_mode_m = st.session_state.edit_item_data is not None
        item_m = st.session_state.edit_item_data[1] if edit_mode_m else {}
        with st.form("f_med", clear_on_submit=not edit_mode_m):
            sub_m = st.form_submit_button("SALVAR ALTERAÇÕES ✏️" if edit_mode_m else "CADASTRAR ➕", use_container_width=True)
            n_m = st.text_input("Nome", value=item_m.get('nome', ''))
            m_m = st.text_input("mg", value=item_m.get('mg', ''))
            med_m = st.text_input("Médico", value=item_m.get('medico', ''))
            t_m = st.selectbox("Forma de Uso", TURNOS, index=TURNOS.index(item_m['turno']) if edit_mode_m and item_m['turno'] in TURNOS else 0)
            if sub_m:
                payload_m = {'nome': n_m, 'mg': m_m, 'medico': med_m, 'turno': t_m, 'timestamp': datetime.datetime.now().timestamp()}
                if edit_mode_m:
                    db.reference('medicamentos').child(st.session_state.edit_item_data[0]).update(payload_m)
                    st.session_state.edit_item_data = None
                else:
                    db.reference('medicamentos').push(payload_m)
                st.rerun()

# --- MÓDULO EXAMES ---
elif st.session_state.page == "exames":
    st.title("🧪 Exames")
    col_le, col_ce = st.columns([1, 1.3])
    with col_le:
        if st.button("⬅ VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        exs = db.reference('exames').get()
        if exs:
            for k, v in sorted(exs.items(), key=lambda x: x[1].get('data', ''), reverse=True):
                ci, ct = st.columns([0.35, 0.65])
                with ci:
                    e1, e2, e3 = st.columns(3)
                    if e1.button("🗑️", key=f"de{k}"): st.session_state.confirm_del = k; st.rerun()
                    if e2.button("✏️", key=f"ee{k}"): st.session_state.edit_item_data = (k, v); st.rerun()
                    if e3.button("🔍", key=f"ve{k}"): 
                        st.session_state.view_item_id = k if st.session_state.view_item_id != k else None
                        st.rerun()
                
                dt_e = v['data'] if '-' not in v['data'] else datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                ct.markdown(f"<p class='compact-row'><b>{dt_e}</b> | {v['nome'][:12]}.. | Dr. {v['medico'][:8]}</p>", unsafe_allow_html=True)
                
                if st.session_state.view_item_id == k:
                    st.info(f"🏢 Local: {v.get('local', 'N/I')}\n\n📝 Preparo: {v.get('preparo', 'Nenhum')}")

                if st.session_state.confirm_del == k:
                    st.warning("Excluir?"); ey, en = st.columns(2)
                    if ey.button("SIM", key=f"sye{k}"): 
                        db.reference('exames').child(k).delete()
                        st.session_state.confirm_del = None; st.rerun()
                    if en.button("NÃO", key=f"sne{k}"): st.session_state.confirm_del = None; st.rerun()

    with col_ce:
        edit_mode_e = st.session_state.edit_item_data is not None
        item_e = st.session_state.edit_item_data[1] if edit_mode_e else {}
        
        with st.form("f_ex", clear_on_submit=not edit_mode_e):
            st.form_submit_button("SALVAR ALTERAÇÕES ✏️" if edit_mode_e else "CADASTRAR ➕", use_container_width=True)
            n_ex = st.text_input("Exame", value=item_e.get('nome', ''))
            m_ex = st.text_input("Médico", value=item_e.get('medico', ''))
            d_ex = st.date_input("Data", value=datetime.datetime.strptime(item_e['data'], '%Y-%m-%d') if edit_mode_e else datetime.date.today())
            l_ex = st.text_input("Local", value=item_e.get('local', ''))
            
            # CORREÇÃO PONTO PREPARO: Campo dinâmico
            prep_check = st.checkbox("Necessário Preparo (Jejum, etc.)?", value=bool(item_e.get('preparo')))
            desc_prep = ""
            if prep_check:
                desc_prep = st.text_area("Descreva o preparo:", value=item_e.get('preparo', ''))
            
            if st.form_submit_button("SALVAR DADOS"):
                payload_e = {'nome': n_ex, 'medico': m_ex, 'data': str(d_ex), 'local': l_ex, 'preparo': desc_prep, 'timestamp': datetime.datetime.now().timestamp()}
                if edit_mode_e:
                    db.reference('exames').child(st.session_state.edit_item_data[0]).update(payload_e)
                    st.session_state.edit_item_data = None
                else:
                    db.reference('exames').push(payload_e)
                st.rerun()

elif st.session_state.page in ["cadastro", "relatorios"]:
    st.title(st.session_state.page.upper())
    if st.button("VOLTAR"): mudar_pagina("dashboard")
