import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import datetime
from fpdf import FPDF 

# --- CONFIGURAÇÃO DA PÁGINA (ESTRATÉGICA PARA MOBILE) ---
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

# --- CSS MOBILE-FIRST (O PULO DO GATO) ---
st.markdown("""
    <style>
    /* 1. Ajuste de Fonte Base para legibilidade sem zoom */
    html, body, [data-testid="stMarkdownContainer"] p {
        font-size: 16px !important;
    }

    /* 2. Deixar botões grandes o suficiente para o dedo (mínimo 44px de altura) */
    .stButton > button {
        width: 100% !important;
        height: 50px !important;
        font-size: 16px !important;
        margin-bottom: 10px !important;
        border-radius: 8px !important;
        background-color: #f0f2f6 !important;
        border: 1px solid #d1d5db !important;
    }

    /* 3. Estilo especial para os ícones de ação (Excluir/Editar/Lupa) */
    /* No mobile, eles precisam de espaço lateral para não clicar errado */
    div[data-testid="column"] .stButton > button {
        height: 40px !important;
        font-size: 18px !important;
    }

    /* 4. Inputs maiores para facilitar a digitação */
    .stTextInput input, .stSelectbox div, .stDateInput input {
        height: 45px !important;
        font-size: 16px !important;
    }

    /* 5. Linha compacta mais "gorda" para facilitar a leitura no celular */
    .compact-row { 
        font-size: 14px !important; 
        line-height: 1.4 !important; 
        padding: 10px 0px; 
        border-bottom: 1px solid #eee;
        color: #1f2937;
    }

    /* 6. Remover margens laterais excessivas que "espremem" o app */
    .block-container {
        padding: 1rem 0.5rem !important;
    }

    /* 7. Forçar empilhamento total em telas menores que 768px */
    @media (max-width: 768px) {
        div[data-testid="column"] {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
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
    
    col_ok, col_can = st.columns(2)
    with col_ok:
        if st.button("OK", key="login_ok"):
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
                if not sucesso: st.error("Acesso Negado.")
    with col_can:
        st.button("CANCELAR", key="login_cancel")

    st.divider()
    if st.button("Cadastrar Novo Usuário"): mudar_pagina("cadastro")
    st.button("Esqueci a Senha")

# --- DASHBOARD ---
elif st.session_state.page == "dashboard":
    st.title("Painel Principal")
    
    if st.session_state.user_email == "admin@teste.com":
        with st.expander("🔔 Aprovar Usuários"):
            pendentes = db.reference('usuarios_pendentes').get()
            if pendentes:
                for k, v in pendentes.items():
                    st.write(f"{v.get('nome')} ({v.get('email')})")
                    if st.button("Aprovar", key=f"apr_{k}"):
                        db.reference('usuarios_aprovados').child(k).set(v)
                        db.reference('usuarios_pendentes').child(k).delete()
                        st.rerun()
            else: st.write("Nenhum pendente.")

    # No mobile, esses botões ficarão um embaixo do outro ou em pares grandes
    st.button("💊 MEDICAMENTOS", on_click=mudar_pagina, args=("meds",))
    st.button("📅 CONSULTAS", on_click=mudar_pagina, args=("consultas",))
    st.button("🧪 EXAMES", on_click=mudar_pagina, args=("exames",))
    st.button("📊 RELATÓRIOS", on_click=mudar_pagina, args=("relatorios",))
    
    st.divider()
    if st.button("Sair"): mudar_pagina("login")

# --- MÓDULOS (CONSULTAS / MEDS / EXAMES) ---
# Aplicando a lógica de colunas que se empilham no mobile
elif st.session_state.page == "consultas":
    st.title("📅 Consultas")
    if st.button("⬅ VOLTAR"): mudar_pagina("dashboard")
    
    col_cad, col_lista = st.columns([1, 1]) # 50/50 para empilhar melhor
    
    with col_cad:
        st.subheader("Novo Cadastro")
        edit_mode = st.session_state.edit_item_data is not None
        v_edit = st.session_state.edit_item_data[1] if edit_mode else {}
        with st.form("f_con", clear_on_submit=not edit_mode):
            esp = st.selectbox("Especialidade", LISTA_ESP, index=LISTA_ESP.index(v_edit['especialidade']) if edit_mode else 0)
            dat = st.date_input("Data", value=datetime.datetime.strptime(v_edit['data'], '%Y-%m-%d') if edit_mode else datetime.date.today(), format="DD/MM/YYYY")
            hor = st.text_input("Hora", value=v_edit.get('hora', ''))
            med = st.text_input("Médico", value=v_edit.get('medico', ''))
            loc = st.text_input("Local", value=v_edit.get('local', ''))
            if st.form_submit_button("SALVAR ALTERAÇÕES ✏️" if edit_mode else "CADASTRAR ➕"):
                payload = {'especialidade': esp, 'data': str(dat), 'hora': hor, 'medico': med, 'local': loc, 'timestamp': datetime.datetime.now().timestamp()}
                if edit_mode: db.reference('consultas').child(st.session_state.edit_item_data[0]).update(payload)
                else: db.reference('consultas').push(payload)
                mudar_pagina("consultas")

    with col_lista:
        st.subheader("Histórico")
        data = db.reference('consultas').get()
        if data:
            for k, v in sorted(data.items(), key=lambda x: str(x[1].get('data', '')), reverse=True):
                dt = datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y') if '-' in v['data'] else v['data']
                st.markdown(f"<p class='compact-row'><b>{dt}</b> - {v['especialidade']}</p>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                if c1.button("🗑️", key=f"d{k}"): st.session_state.confirm_del = k; st.rerun()
                if c2.button("✏️", key=f"e{k}"): st.session_state.edit_item_data = (k, v); st.rerun()
                if c3.button("🔍", key=f"v{k}"): st.session_state.view_item_id = k if st.session_state.view_item_id != k else None; st.rerun()
                
                if st.session_state.view_item_id == k: st.info(f"Dr: {v.get('medico','N/I')}\nLocal: {v.get('local', 'N/I')}")
                if st.session_state.confirm_del == k:
                    if st.button("CONFIRMAR EXCLUSÃO", key=f"sy{k}"):
                        db.reference('consultas').child(k).delete()
                        st.session_state.confirm_del = None; st.rerun()

# --- MÓDULO EXAMES ---
elif st.session_state.page == "exames":
    st.title("🧪 Exames")
    if st.button("⬅ VOLTAR"): mudar_pagina("dashboard")
    
    col_cad_e, col_lista_e = st.columns([1, 1])
    
    with col_cad_e:
        edit_e = st.session_state.edit_item_data is not None
        v_e = st.session_state.edit_item_data[1] if edit_e else {}
        with st.form("f_ex", clear_on_submit=not edit_e):
            n_ex = st.text_input("Nome do Exame", value=v_e.get('nome', ''))
            m_sol = st.text_input("Médico", value=v_e.get('medico', ''))
            dat_ex = st.date_input("Data", value=datetime.datetime.strptime(v_e['data'], '%Y-%m-%d') if edit_e else datetime.date.today(), format="DD/MM/YYYY")
            desc_prep = st.text_area("Preparo", value=v_e.get('preparo', ''))
            if st.form_submit_button("SALVAR"):
                p_e = {'nome': n_ex, 'medico': m_sol, 'data': str(dat_ex), 'preparo': desc_prep, 'timestamp': datetime.datetime.now().timestamp()}
                if edit_e: db.reference('exames').child(st.session_state.edit_item_data[0]).update(p_e)
                else: db.reference('exames').push(p_e)
                mudar_pagina("exames")

    with col_lista_e:
        st.subheader("Cadastrados")
        exs = db.reference('exames').get()
        if exs:
            for k, v in sorted(exs.items(), key=lambda x: str(x[1].get('data', '')), reverse=True):
                dt_e = datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                st.markdown(f"<p class='compact-row'><b>{dt_e}</b> - {v['nome']}</p>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                if c1.button("🗑️", key=f"de{k}"): st.session_state.confirm_del = k; st.rerun()
                if c2.button("✏️", key=f"ee{k}"): st.session_state.edit_item_data = (k, v); st.rerun()
                if c3.button("🔍", key=f"ve{k}"): st.session_state.view_item_id = k if st.session_state.view_item_id != k else None; st.rerun()
                if st.session_state.view_item_id == k: st.info(f"Preparo: {v.get('preparo','N/I')}")

# --- MÓDULO MEDICAMENTOS ---
elif st.session_state.page == "meds":
    st.title("💊 Medicamentos")
    if st.button("⬅ VOLTAR"): mudar_pagina("dashboard")
    col_cad_m, col_lista_m = st.columns([1, 1])
    
    with col_cad_m:
        edit_m = st.session_state.edit_item_data is not None
        v_m = st.session_state.edit_item_data[1] if edit_m else {}
        with st.form("f_med", clear_on_submit=not edit_m):
            n_m = st.text_input("Nome", value=v_m.get('nome', ''))
            m_m = st.text_input("mg", value=v_m.get('mg', ''))
            turno_m = st.selectbox("Turno", TURNOS, index=TURNOS.index(v_m['turno']) if edit_m else 0)
            if st.form_submit_button("SALVAR"):
                payload_m = {'nome': n_m, 'mg': m_m, 'turno': turno_m, 'data_cadastro': str(datetime.date.today()), 'timestamp': datetime.datetime.now().timestamp()}
                if edit_m: db.reference('medicamentos').child(st.session_state.edit_item_data[0]).update(payload_m)
                else: db.reference('medicamentos').push(payload_m)
                mudar_pagina("meds")

    with col_lista_m:
        meds = db.reference('medicamentos').get()
        if meds:
            for k, v in meds.items():
                st.markdown(f"<p class='compact-row'><b>{v['turno']}</b> - {v['nome']} ({v['mg']})</p>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns(3)
                if c1.button("🗑️", key=f"dm{k}"): db.reference('medicamentos').child(k).delete(); st.rerun()
                c2.button("✏️", key=f"em{k}")
                c3.button("🔍", key=f"vm{k}")

# --- MÓDULO RELATÓRIOS ---
elif st.session_state.page == "relatorios":
    st.title("📊 Relatórios")
    if st.button("⬅ VOLTAR"): mudar_pagina("dashboard")
    
    d_ini = st.date_input("Início", format="DD/MM/YYYY", value=datetime.date.today() - datetime.timedelta(days=30))
    d_fim = st.date_input("Fim", format="DD/MM/YYYY")
    opcao = st.selectbox("Tipo", ["CONSOLIDADO", "MEDICAMENTOS", "CONSULTAS", "EXAMES"])
    
    if st.button("GERAR PDF 📄"):
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Relatorio de Saude", 0, 1, "C")
            pdf_out = pdf.output()
            st.download_button("Baixar PDF", data=bytes(pdf_out), file_name="relatorio.pdf")
        except: st.error("Erro ao gerar PDF")

elif st.session_state.page == "cadastro":
    st.title("Novo Cadastro")
    if st.button("Voltar"): mudar_pagina("login")
