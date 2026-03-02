import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
from fpdf import FPDF 

# --- CONFIGURAÇÃO DA PÁGINA (OTIMIZAÇÃO MOBILE-FIRST) ---
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

# --- CSS MOBILE-FIRST (PARA NÃO PRECISAR DE ZOOM NO CELULAR) ---
st.markdown("""
    <style>
    html, body, [data-testid="stMarkdownContainer"] p { font-size: 16px !important; }
    .stButton > button {
        width: 100% !important;
        height: 50px !important;
        font-size: 16px !important;
        border-radius: 8px !important;
        margin-bottom: 5px !important;
    }
    .stTextInput input, .stSelectbox div, .stDateInput input {
        height: 45px !important;
        font-size: 16px !important;
    }
    .compact-row { 
        font-size: 14px !important; 
        line-height: 1.4 !important; 
        padding: 10px 0px; 
        border-bottom: 1px solid #eee;
    }
    .block-container { padding: 1rem 0.5rem !important; }
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
TURNOS = ["MANHÃ", "MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "TARDE", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "NOITE"]

# --- 1ª TELA: LOGIN ---
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
                sucesso = False
                if users:
                    for v in users.values():
                        if v.get('email', '').lower() == email and v.get('senha') == senha:
                            st.session_state.user_email = email
                            sucesso = True
                            mudar_pagina("dashboard")
                            break
                if not sucesso: st.error("Acesso Negado ou Usuário Pendente.")
    with c_can: st.button("CANCELAR")
    st.divider()
    if st.button("Cadastrar Novo Usuário"): mudar_pagina("cadastro")
    st.button("Esqueci a Senha")

# --- DASHBOARD ---
elif st.session_state.page == "dashboard":
    st.title("Painel Principal")
    if st.session_state.user_email == "admin@teste.com":
        with st.expander("🔔 Usuários Pendentes"):
            pendentes = db.reference('usuarios_pendentes').get()
            if pendentes:
                for k, v in pendentes.items():
                    st.write(f"**{v.get('nome')}** ({v.get('email')})")
                    if st.button("Aprovar", key=f"apr_{k}"):
                        db.reference('usuarios_aprovados').child(k).set(v)
                        db.reference('usuarios_pendentes').child(k).delete()
                        st.success("Aprovado!"); st.rerun()
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
    n_cad = st.text_input("Nome Completo")
    e_cad = st.text_input("E-mail").lower().strip()
    s_cad = st.text_input("Senha", type="password")
    if st.button("ENVIAR SOLICITAÇÃO"):
        if n_cad and e_cad and s_cad:
            db.reference('usuarios_pendentes').push({'nome': n_cad, 'email': e_cad, 'senha': s_cad, 'status': 'pendente'})
            st.success("Solicitado! O admin precisa aprovar.")
        else: st.warning("Preencha tudo.")
    if st.button("VOLTAR"): mudar_pagina("login")

# --- CONSULTAS ---
elif st.session_state.page == "consultas":
    st.title("📅 Consultas")
    if st.button("⬅ VOLTAR"): mudar_pagina("dashboard")
    col_c, col_l = st.columns([1, 1])
    with col_c:
        edit_mode = st.session_state.edit_item_data is not None
        v_e = st.session_state.edit_item_data[1] if edit_mode else {}
        with st.form("f_con", clear_on_submit=not edit_mode):
            esp = st.selectbox("Especialidade", LISTA_ESP, index=LISTA_ESP.index(v_e['especialidade']) if edit_mode else 0)
            dat = st.date_input("Data", value=datetime.datetime.strptime(v_e['data'], '%Y-%m-%d') if edit_mode else datetime.date.today(), format="DD/MM/YYYY")
            med = st.text_input("Médico", value=v_e.get('medico',''))
            loc = st.text_input("Local", value=v_e.get('local',''))
            if st.form_submit_button("SALVAR"):
                p = {'especialidade': esp, 'data': str(dat), 'medico': med, 'local': loc, 'timestamp': datetime.datetime.now().timestamp()}
                if edit_mode: db.reference('consultas').child(st.session_state.edit_item_data[0]).update(p)
                else: db.reference('consultas').push(p)
                mudar_pagina("consultas")
    with col_l:
        data = db.reference('consultas').get()
        if data:
            for k, v in sorted(data.items(), key=lambda x: str(x[1].get('data','')), reverse=True):
                dt = datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y') if '-' in v['data'] else v['data']
                st.markdown(f"<div class='compact-row'><b>{dt}</b> - {v['especialidade']}</div>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                if c1.button("🗑️", key=f"dc{k}"): db.reference('consultas').child(k).delete(); st.rerun()
                if c2.button("✏️", key=f"ec{k}"): st.session_state.edit_item_data = (k, v); st.rerun()
                if c3.button("🔍", key=f"vc{k}"): st.session_state.view_item_id = k if st.session_state.view_item_id != k else None; st.rerun()
                if st.session_state.view_item_id == k: st.info(f"Dr: {v.get('medico')} | Local: {v.get('local')}")

# --- MEDICAMENTOS ---
elif st.session_state.page == "meds":
    st.title("💊 Medicamentos")
    if st.button("⬅ VOLTAR"): mudar_pagina("dashboard")
    col_c, col_l = st.columns([1, 1])
    with col_c:
        edit_m = st.session_state.edit_item_data is not None
        v_m = st.session_state.edit_item_data[1] if edit_m else {}
        with st.form("f_med", clear_on_submit=not edit_m):
            nome = st.text_input("Nome", value=v_m.get('nome',''))
            mg = st.text_input("mg", value=v_m.get('mg',''))
            turno = st.selectbox("Turno", TURNOS, index=TURNOS.index(v_m['turno']) if edit_m else 0)
            if st.form_submit_button("SALVAR"):
                p = {'nome': nome, 'mg': mg, 'turno': turno, 'data_cadastro': str(datetime.date.today()), 'timestamp': datetime.datetime.now().timestamp()}
                if edit_m: db.reference('medicamentos').child(st.session_state.edit_item_data[0]).update(p)
                else: db.reference('medicamentos').push(p)
                mudar_pagina("meds")
    with col_l:
        data = db.reference('medicamentos').get()
        if data:
            for k, v in data.items():
                st.markdown(f"<div class='compact-row'><b>{v['turno']}</b> - {v['nome']} ({v['mg']})</div>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                if c1.button("🗑️", key=f"dm{k}"): db.reference('medicamentos').child(k).delete(); st.rerun()
                if c2.button("✏️", key=f"em{k}"): st.session_state.edit_item_data = (k, v); st.rerun()
                if c3.button("🔍", key=f"vm{k}"): st.session_state.view_item_id = k if st.session_state.view_item_id != k else None; st.rerun()

# --- EXAMES ---
elif st.session_state.page == "exames":
    st.title("🧪 Exames")
    if st.button("⬅ VOLTAR"): mudar_pagina("dashboard")
    col_c, col_l = st.columns([1, 1])
    with col_c:
        edit_x = st.session_state.edit_item_data is not None
        v_x = st.session_state.edit_item_data[1] if edit_x else {}
        with st.form("f_ex", clear_on_submit=not edit_x):
            nome = st.text_input("Exame", value=v_x.get('nome',''))
            dat = st.date_input("Data", value=datetime.datetime.strptime(v_x['data'], '%Y-%m-%d') if edit_x else datetime.date.today(), format="DD/MM/YYYY")
            prep = st.text_area("Informações de Preparo", value=v_x.get('preparo',''))
            if st.form_submit_button("SALVAR"):
                p = {'nome': nome, 'data': str(dat), 'preparo': prep, 'timestamp': datetime.datetime.now().timestamp()}
                if edit_x: db.reference('exames').child(st.session_state.edit_item_data[0]).update(p)
                else: db.reference('exames').push(p)
                mudar_pagina("exames")
    with col_l:
        data = db.reference('exames').get()
        if data:
            for k, v in sorted(data.items(), key=lambda x: str(x[1].get('data','')), reverse=True):
                dt = datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                st.markdown(f"<div class='compact-row'><b>{dt}</b> - {v['nome']}</div>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                if c1.button("🗑️", key=f"dx{k}"): db.reference('exames').child(k).delete(); st.rerun()
                if c2.button("✏️", key=f"ex{k}"): st.session_state.edit_item_data = (k, v); st.rerun()
                if c3.button("🔍", key=f"vx{k}"): st.session_state.view_item_id = k if st.session_state.view_item_id != k else None; st.rerun()
                if st.session_state.view_item_id == k: st.info(f"Preparo: {v.get('preparo')}")

# --- RELATÓRIOS ---
elif st.session_state.page == "relatorios":
    st.title("📊 Relatórios")
    d_i = st.date_input("Período Inicial", format="DD/MM/YYYY", value=datetime.date.today() - datetime.timedelta(days=30))
    d_f = st.date_input("Período Final", format="DD/MM/YYYY")
    opcao = st.selectbox("Tipo", ["CONSOLIDADO", "MEDICAMENTOS", "CONSULTAS", "EXAMES"])
    if st.button("GERAR RELATÓRIO PDF"):
        try:
            pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Relatorio de Saude", 0, 1, "C")
            pdf_out = pdf.output()
            st.download_button("Baixar PDF", data=bytes(pdf_out), file_name="relatorio.pdf")
        except: st.error("Erro ao gerar PDF")
    if st.button("VOLTAR"): mudar_pagina("dashboard")

elif st.session_state.page == "relatorios":
    st.title("📊 Relatórios")
    # Este bloco foi unificado acima para evitar duplicação
    pass
