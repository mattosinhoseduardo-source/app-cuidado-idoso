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
    /* Ajuste para ícones menores e na mesma linha */
    .stButton > button { padding: 0px 1px !important; font-size: 10px !important; height: 18px !important; min-height: 18px !important; background: transparent !important; border: none !important; }
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
# CORREÇÃO PONTO 2: Lista completa de turnos
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
            # CORREÇÃO PONTO 3: Ordenação Cronológica Decrescente Real
            items = sorted(data.items(), key=lambda x: str(x[1].get('data', '')), reverse=True)
            for k, v in items:
                c_i, c_t = st.columns([0.35, 0.65])
                with c_i:
                    i1, i2, i3 = st.columns(3)
                    # CORREÇÃO PONTO 1: Botões funcionais vinculados ao confirm_del
                    if i1.button("🗑️", key=f"dc{k}"): st.session_state.confirm_del = k; st.rerun()
                    i2.button("✏️", key=f"ec{k}")
                    i3.button("🔍", key=f"vc{k}")
                
                if st.session_state.confirm_del == k:
                    st.warning("Excluir?")
                    cy, cn = st.columns(2)
                    if cy.button("SIM", key=f"cyc{k}"):
                        db.reference('consultas').child(k).delete()
                        st.session_state.confirm_del = None; st.rerun()
                    if cn.button("NÃO", key=f"cnc{k}"):
                        st.session_state.confirm_del = None; st.rerun()

                dt = v['data'] if '-' not in v['data'] else datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                c_t.markdown(f"<p class='compact-row'><b>{dt}</b> | {v['especialidade'][:10]}.. | Dr. {v['medico'][:8]}</p>", unsafe_allow_html=True)

    with col_cad:
        with st.form("f_con", clear_on_submit=True):
            sub = st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            esp = st.selectbox("Especialidade", LISTA_ESP)
            dat = st.date_input("Data", format="DD/MM/YYYY")
            hor = st.text_input("Hora")
            med = st.text_input("Médico")
            loc = st.text_input("Local")
            if sub:
                db.reference('consultas').push({'especialidade': esp, 'data': str(dat), 'hora': hor, 'medico': med, 'local': loc, 'timestamp': datetime.datetime.now().timestamp()})
                st.success("Salvo!"); st.rerun()

# --- MÓDULO MEDICAMENTOS ---
elif st.session_state.page == "meds":
    st.title("💊 Medicamentos")
    col_lista_m, col_cad_m = st.columns([1, 1.3])
    with col_lista_m:
        if st.button("⬅ VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        meds = db.reference('medicamentos').get()
        if meds:
            # CORREÇÃO PONTO 2: Ordenação por todos os turnos
            sorted_m = sorted(meds.items(), key=lambda x: TURNOS.index(x[1].get('turno', 'NOITE')) if x[1].get('turno') in TURNOS else 99)
            for k, v in sorted_m:
                c_i, c_t = st.columns([0.35, 0.65])
                with c_i:
                    m1, m2, m3 = st.columns(3)
                    if m1.button("🗑️", key=f"dm{k}"): st.session_state.confirm_del = k; st.rerun()
                    m2.button("✏️", key=f"em{k}"); m3.button("🔍", key=f"vm{k}")

                if st.session_state.confirm_del == k:
                    st.warning("Excluir?")
                    my, mn = st.columns(2)
                    if my.button("SIM", key=f"sym{k}"):
                        db.reference('medicamentos').child(k).delete()
                        st.session_state.confirm_del = None; st.rerun()
                    if mn.button("NÃO", key=f"snm{k}"):
                        st.session_state.confirm_del = None; st.rerun()

                c_t.markdown(f"<p class='compact-row'><b>{v['turno'][:12]}..</b> | {v['nome']} ({v['mg']})</p>", unsafe_allow_html=True)

    with col_cad_m:
        with st.form("f_med", clear_on_submit=True):
            sub_m = st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            nome_med = st.text_input("Nome")
            mg_med = st.text_input("mg")
            c1, c2 = st.columns(2)
            dt_cad = c1.date_input("Data do Cadastro", format="DD/MM/YYYY")
            c2.checkbox("Data de Hoje", value=True)
            med_m = st.text_input("Médico")
            esp_m = st.selectbox("Especialidade", LISTA_ESP)
            turno_m = st.selectbox("Turno", TURNOS)
            if sub_m:
                db.reference('medicamentos').push({'nome': nome_med, 'mg': mg_med, 'medico': med_m, 'especialidade': esp_m, 'turno': turno_m, 'data_cadastro': str(dt_cad), 'timestamp': datetime.datetime.now().timestamp()})
                st.success("Salvo!"); st.rerun()

# --- MÓDULO EXAMES ---
elif st.session_state.page == "exames":
    st.title("🧪 Exames")
    col_lista_e, col_cad_e = st.columns([1, 1.3])
    with col_lista_e:
        if st.button("⬅ VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.caption("CADASTRADOS")
        exames = db.reference('exames').get()
        if exames:
            items_e = sorted(exames.items(), key=lambda x: str(x[1].get('data', '')), reverse=True)
            for k, v in items_e:
                ci, ct = st.columns([0.35, 0.65])
                with ci:
                    e1, e2, e3 = st.columns(3)
                    if e1.button("🗑️", key=f"de{k}"): st.session_state.confirm_del = k; st.rerun()
                    e2.button("✏️", key=f"ee{k}"); e3.button("🔍", key=f"ve{k}")
                
                if st.session_state.confirm_del == k:
                    st.warning("Excluir?")
                    ey, en = st.columns(2)
                    if ey.button("SIM", key=f"sye{k}"):
                        db.reference('exames').child(k).delete()
                        st.session_state.confirm_del = None; st.rerun()
                    if en.button("NÃO", key=f"sne{k}"):
                        st.session_state.confirm_del = None; st.rerun()

                dt_e = v['data'] if '-' not in v['data'] else datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                ct.markdown(f"<p class='compact-row'><b>{dt_e}</b> | {v['nome'][:12]}.. | Dr. {v['medico'][:8]}</p>", unsafe_allow_html=True)

    with col_cad_e:
        with st.form("f_exame", clear_on_submit=True):
            sub_e = st.form_submit_button("CADASTRAR ➕", use_container_width=True)
            n_exame = st.text_input("Nome do Exame")
            med_sol = st.text_input("Médico Solicitante")
            esp_sol = st.selectbox("Especialidade", LISTA_ESP)
            data_ex = st.date_input("Data da Realização", format="DD/MM/YYYY")
            local_ex = st.text_input("Laboratório / Clínica")
            preparo = st.checkbox("Necessário Preparo (Jejum, etc.)?")
            # CORREÇÃO PONTO 4: Campo condicional de preparo
            desc_prep = ""
            if preparo:
                desc_prep = st.text_area("Descreva o preparo:")
            
            if sub_e:
                db.reference('exames').push({'nome': n_exame, 'medico': med_sol, 'especialidade': esp_sol, 'data': str(data_ex), 'local': local_ex, 'preparo': desc_prep, 'timestamp': datetime.datetime.now().timestamp()})
                st.success("Exame salvo!"); st.rerun()

elif st.session_state.page in ["cadastro", "relatorios"]:
    st.title(st.session_state.page.upper())
    if st.button("VOLTAR"): mudar_pagina("dashboard")
