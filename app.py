import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
from fpdf import FPDF 

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gestão de Cuidados",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

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

# --- CSS MOBILE-FIRST (FONTES E BOTÕES GRANDES) ---
st.markdown("""
    <style>
    html, body, [data-testid="stMarkdownContainer"] p { font-size: 16px !important; }
    .stButton > button {
        width: 100% !important;
        height: 50px !important;
        font-size: 16px !important;
        border-radius: 8px !important;
        margin-bottom: 8px !important;
    }
    .stTextInput input, .stSelectbox div, .stDateInput input, .stTextArea textarea {
        font-size: 16px !important;
    }
    .compact-row { 
        font-size: 14px !important; 
        line-height: 1.4 !important; 
        padding: 12px 0px; 
        border-bottom: 1px solid #eee;
    }
    .block-container { padding: 1rem 0.8rem !important; }
    @media (max-width: 768px) {
        div[data-testid="column"] { width: 100% !important; flex: 1 1 100% !important; }
    }
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
TURNOS = ["MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "MANHÃ", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "TARDE", "NOITE"]

# --- LOGIN ---
if st.session_state.page == "login":
    st.markdown("<h1 style='text-align: center;'>🏥 Gestão de Cuidados</h1>", unsafe_allow_html=True)
    email = st.text_input("E-mail").lower().strip()
    senha = st.text_input("Senha", type="password")
    c_ok, c_can = st.columns(2)
    with c_ok:
        if st.button("OK"):
            if email == "admin@teste.com" and senha == "123":
                st.session_state.user_email = email
                mudar_pagina("dashboard")
            else:
                users = db.reference('usuarios_aprovados').get()
                if users and any(v.get('email', '').lower() == email and v.get('senha') == senha for v in users.values()):
                    st.session_state.user_email = email
                    mudar_pagina("dashboard")
                else: st.error("Acesso Negado.")
    with c_can: st.button("CANCELAR")
    st.divider()
    if st.button("Cadastrar Novo Usuário"): mudar_pagina("cadastro")
    st.button("Esqueci a Senha")

# --- DASHBOARD ---
elif st.session_state.page == "dashboard":
    st.title("Painel Principal")
    if st.session_state.user_email == "admin@teste.com":
        with st.expander("🔔 Aprovar Usuários"):
            p = db.reference('usuarios_pendentes').get()
            if p:
                for k, v in p.items():
                    st.write(f"**{v.get('nome')}** ({v.get('email')})")
                    if st.button("Aprovar", key=f"apr_{k}"):
                        db.reference('usuarios_aprovados').child(k).set(v)
                        db.reference('usuarios_pendentes').child(k).delete()
                        st.rerun()
            else: st.write("Nenhum pendente.")
    
    st.button("💊 MEDICAMENTOS", on_click=mudar_pagina, args=("meds",))
    st.button("📅 CONSULTAS", on_click=mudar_pagina, args=("consultas",))
    st.button("🧪 EXAMES", on_click=mudar_pagina, args=("exames",))
    st.button("📊 RELATÓRIOS", on_click=mudar_pagina, args=("relatorios",))
    st.divider()
    if st.button("Sair"): mudar_pagina("login")

# --- CADASTRO ---
elif st.session_state.page == "cadastro":
    st.title("📝 Novo Registro")
    n = st.text_input("Nome Completo")
    e = st.text_input("E-mail").lower().strip()
    s = st.text_input("Senha", type="password")
    if st.button("ENVIAR SOLICITAÇÃO"):
        if n and e and s:
            db.reference('usuarios_pendentes').push({'nome': n, 'email': e, 'senha': s, 'status': 'pendente', 'data_solicitacao': str(datetime.date.today())})
            st.success("Solicitado! Aguarde aprovação.")
    if st.button("VOLTAR"): mudar_pagina("login")

# --- CONSULTAS (RESTAURAÇÃO COMPLETA) ---
elif st.session_state.page == "consultas":
    st.title("📅 Consultas")
    if st.button("⬅ VOLTAR"): mudar_pagina("dashboard")
    col_cad, col_lista = st.columns([1, 1])
    with col_cad:
        st.subheader("Cadastro")
        edit_mode = st.session_state.edit_item_data is not None
        v_e = st.session_state.edit_item_data[1] if edit_mode else {}
        with st.form("f_con", clear_on_submit=not edit_mode):
            esp = st.selectbox("Especialidade", LISTA_ESP, index=LISTA_ESP.index(v_e['especialidade']) if edit_mode else 0)
            dat = st.date_input("Data", value=datetime.datetime.strptime(v_e['data'], '%Y-%m-%d') if edit_mode else datetime.date.today(), format="DD/MM/YYYY")
            hor = st.text_input("Hora", value=v_e.get('hora',''))
            med = st.text_input("Médico", value=v_e.get('medico',''))
            loc = st.text_input("Clínica / Hospital", value=v_e.get('local',''))
            end = st.text_input("Endereço", value=v_e.get('endereco',''))
            if st.form_submit_button("SALVAR"):
                p = {'especialidade': esp, 'data': str(dat), 'hora': hor, 'medico': med, 'local': loc, 'endereco': end, 'timestamp': datetime.datetime.now().timestamp()}
                if edit_mode: db.reference('consultas').child(st.session_state.edit_item_data[0]).update(p)
                else: db.reference('consultas').push(p)
                mudar_pagina("consultas")
    with col_lista:
        st.subheader("Histórico")
        data = db.reference('consultas').get()
        if data:
            for k, v in sorted(data.items(), key=lambda x: str(x[1].get('data','')), reverse=True):
                dt = datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                st.markdown(f"<div class='compact-row'><b>{dt}</b> - {v['especialidade']}</div>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                if c1.button("🗑️", key=f"dc{k}"): db.reference('consultas').child(k).delete(); st.rerun()
                if c2.button("✏️", key=f"ec{k}"): st.session_state.edit_item_data = (k, v); st.rerun()
                if c3.button("🔍", key=f"vc{k}"): st.session_state.view_item_id = k if st.session_state.view_item_id != k else None; st.rerun()
                if st.session_state.view_item_id == k: st.info(f"Dr: {v.get('medico')} | Local: {v.get('local')} | End: {v.get('endereco')}")

# --- MEDICAMENTOS (RESTAURAÇÃO COMPLETA) ---
elif st.session_state.page == "meds":
    st.title("💊 Medicamentos")
    if st.button("⬅ VOLTAR"): mudar_pagina("dashboard")
    col_cad, col_lista = st.columns([1, 1])
    with col_cad:
        st.subheader("Cadastro")
        edit_mode = st.session_state.edit_item_data is not None
        v_m = st.session_state.edit_item_data[1] if edit_mode else {}
        with st.form("f_med", clear_on_submit=not edit_mode):
            nome = st.text_input("Nome", value=v_m.get('nome',''))
            mg = st.text_input("mg", value=v_m.get('mg',''))
            med = st.text_input("Médico", value=v_m.get('medico',''))
            esp = st.selectbox("Especialidade", LISTA_ESP, index=LISTA_ESP.index(v_m['especialidade']) if edit_mode and v_m.get('especialidade') in LISTA_ESP else 0)
            dat = st.date_input("Data Cadastro", value=datetime.datetime.strptime(v_m['data_cadastro'], '%Y-%m-%d') if edit_mode and v_m.get('data_cadastro') else datetime.date.today(), format="DD/MM/YYYY")
            turno = st.selectbox("Turno", TURNOS, index=TURNOS.index(v_m['turno']) if edit_mode and v_m.get('turno') in TURNOS else 0)
            obs = st.text_area("Observações/Lembrete", value=v_m.get('obs',''))
            if st.form_submit_button("SALVAR"):
                p = {'nome': nome, 'mg': mg, 'medico': med, 'especialidade': esp, 'data_cadastro': str(dat), 'turno': turno, 'obs': obs, 'timestamp': datetime.datetime.now().timestamp()}
                if edit_mode: db.reference('medicamentos').child(st.session_state.edit_item_data[0]).update(p)
                else: db.reference('medicamentos').push(p)
                mudar_pagina("meds")
    with col_lista:
        st.subheader("Lista")
        data = db.reference('medicamentos').get()
        if data:
            for k, v in data.items():
                st.markdown(f"<div class='compact-row'><b>{v['turno']}</b> - {v['nome']}</div>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                if c1.button("🗑️", key=f"dm{k}"): db.reference('medicamentos').child(k).delete(); st.rerun()
                if c2.button("✏️", key=f"em{k}"): st.session_state.edit_item_data = (k, v); st.rerun()
                if c3.button("🔍", key=f"vm{k}"): st.session_state.view_item_id = k if st.session_state.view_item_id != k else None; st.rerun()
                if st.session_state.view_item_id == k: st.info(f"Dose: {v.get('mg')} | Dr: {v.get('medico')} | Obs: {v.get('obs')}")

# --- EXAMES (RESTAURAÇÃO COMPLETA) ---
elif st.session_state.page == "exames":
    st.title("🧪 Exames")
    if st.button("⬅ VOLTAR"): mudar_pagina("dashboard")
    col_cad, col_lista = st.columns([1, 1])
    with col_cad:
        st.subheader("Cadastro")
        edit_mode = st.session_state.edit_item_data is not None
        v_x = st.session_state.edit_item_data[1] if edit_mode else {}
        with st.form("f_ex", clear_on_submit=not edit_mode):
            nome = st.text_input("Nome do Exame", value=v_x.get('nome',''))
            med = st.text_input("Médico Solicitante", value=v_x.get('medico',''))
            esp = st.selectbox("Especialidade", LISTA_ESP, index=LISTA_ESP.index(v_x['especialidade']) if edit_mode and v_x.get('especialidade') in LISTA_ESP else 0)
            dat = st.date_input("Data Realização", value=datetime.datetime.strptime(v_x['data'], '%Y-%m-%d') if edit_mode else datetime.date.today(), format="DD/MM/YYYY")
            loc = st.text_input("Laboratório", value=v_x.get('local',''))
            prep = st.text_area("Informações de Preparo", value=v_x.get('preparo',''))
            if st.form_submit_button("SALVAR"):
                p = {'nome': nome, 'medico': med, 'especialidade': esp, 'data': str(dat), 'local': loc, 'preparo': prep, 'timestamp': datetime.datetime.now().timestamp()}
                if edit_mode: db.reference('exames').child(st.session_state.edit_item_data[0]).update(p)
                else: db.reference('exames').push(p)
                mudar_pagina("exames")
    with col_lista:
        st.subheader("Histórico")
        data = db.reference('exames').get()
        if data:
            for k, v in sorted(data.items(), key=lambda x: str(x[1].get('data','')), reverse=True):
                dt = datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                st.markdown(f"<div class='compact-row'><b>{dt}</b> - {v['nome']}</div>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                if c1.button("🗑️", key=f"dx{k}"): db.reference('exames').child(k).delete(); st.rerun()
                if c2.button("✏️", key=f"ex{k}"): st.session_state.edit_item_data = (k, v); st.rerun()
                if c3.button("🔍", key=f"vx{k}"): st.session_state.view_item_id = k if st.session_state.view_item_id != k else None; st.rerun()
                if st.session_state.view_item_id == k: st.info(f"Lab: {v.get('local')} | Preparo: {v.get('preparo')}")

# --- RELATÓRIOS (PDF CORRIGIDO) ---
elif st.session_state.page == "relatorios":
    st.title("📊 Relatórios")
    d_i = st.date_input("Período Inicial", format="DD/MM/YYYY", value=datetime.date.today() - datetime.timedelta(days=30))
    d_f = st.date_input("Período Final", format="DD/MM/YYYY")
    opcao = st.selectbox("Tipo de Relatório", ["CONSOLIDADO", "MEDICAMENTOS", "CONSULTAS", "EXAMES"])
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("GERAR RELATÓRIO PDF"):
            try:
                pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", "B", 16)
                pdf.cell(0, 10, "Relatorio de Saude", 0, 1, "C")
                pdf.set_font("Arial", "", 10)
                pdf.cell(0, 10, f"Periodo: {d_i.strftime('%d/%m/%Y')} a {d_f.strftime('%d/%m/%Y')}", 0, 1, "C")
                
                def add_sec(title, path, fields):
                    res = db.reference(path).get()
                    if res:
                        pdf.ln(5); pdf.set_font("Arial", "B", 12); pdf.cell(0, 8, title, 1, 1, "L")
                        pdf.set_font("Arial", "", 9)
                        for k, v in res.items():
                            v_d = v.get('data') or v.get('data_cadastro')
                            if v_d and d_i <= datetime.datetime.strptime(v_d, '%Y-%m-%d').date() <= d_f:
                                info = " | ".join([f"{f}: {v.get(f.lower(), 'N/A')}" for f in fields])
                                pdf.multi_cell(0, 6, f"[{v_d}] {info}", border='B')
                
                if opcao in ["CONSOLIDADO", "MEDICAMENTOS"]: add_sec("MEDICAMENTOS", 'medicamentos', ["Nome", "mg", "Turno", "Medico"])
                if opcao in ["CONSOLIDADO", "CONSULTAS"]: add_sec("CONSULTAS", 'consultas', ["Especialidade", "Medico", "Local"])
                if opcao in ["CONSOLIDADO", "EXAMES"]: add_sec("EXAMES", 'exames', ["Nome", "Medico", "Local", "Preparo"])
                
                pdf_out = pdf.output()
                st.download_button("Baixar PDF", data=bytes(pdf_out), file_name=f"Relatorio_{opcao}.pdf")
            except Exception as e: st.error(f"Erro: {e}")
    with c2:
        if st.button("VOLTAR"): mudar_pagina("dashboard")
