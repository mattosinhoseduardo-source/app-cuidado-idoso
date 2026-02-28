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

# --- CSS CUSTOMIZADO (FONTES PEQUENAS E BOTÕES MINI) ---
st.markdown("""
    <style>
    .compact-text { font-size: 12px !important; line-height: 1.1 !important; margin: 0px !important; color: #333; }
    .stButton > button { 
        padding: 1px 4px !important; 
        font-size: 10px !important; 
        height: auto !important;
        min-height: 20px !important;
    }
    div[data-testid="stVerticalBlock"] > div { border-bottom: 0.5px solid #eee; padding-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- CONTROLE DE NAVEGAÇÃO ---
if 'page' not in st.session_state: st.session_state.page = "login"
if 'user_email' not in st.session_state: st.session_state.user_email = ""
if 'confirm_del' not in st.session_state: st.session_state.confirm_del = None
if 'edit_item' not in st.session_state: st.session_state.edit_item = None
if 'view_item' not in st.session_state: st.session_state.view_item = None

def mudar_pagina(nome):
    st.session_state.page = nome
    st.rerun()

LISTA_ESP = ["Alergista", "Anestesiologia", "Angiologia", "Cardiologia", "Cirurgião", "Clínico Geral", "Coloproctologia", "Dermatologia", "Endocrinologia", "Gastroenterologia", "Geriatria", "Ginecologia e obstetrícia", "Hematologia e hemoterapia", "Infectologia", "Mastologia", "Nefrologia", "Neurocirurgia", "Neurologia", "Nutrologia", "Oftalmologia", "Ortopedia e traumatologia", "Otorrinolaringologia", "Pneumologia", "Psiquiatria", "Reumatologia", "Urologia"]

# --- LOGIN E DASHBOARD (ESTRUTURA PADRÃO) ---
if st.session_state.page == "login":
    st.title("🏥 Gestão de Cuidados")
    email = st.text_input("E-mail").lower().strip()
    senha = st.text_input("Senha", type="password")
    if st.button("OK", use_container_width=True):
        if email == "admin@teste.com" and senha == "123":
            st.session_state.user_email = email
            mudar_pagina("dashboard")
        else:
            usuarios = db.reference('usuarios_aprovados').get()
            if usuarios and any(v['email'].lower() == email and v['senha'] == senha for v in usuarios.values()):
                st.session_state.user_email = email
                mudar_pagina("dashboard")
            else: st.error("Acesso negado.")
    if st.button("Cadastrar Novo Usuário"): mudar_pagina("cadastro")

elif st.session_state.page == "dashboard":
    st.title("Página Inicial")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💊 MEDICAMENTOS", use_container_width=True): mudar_pagina("meds")
        if st.button("📅 CONSULTAS", use_container_width=True): mudar_pagina("consultas")
    with c2:
        if st.button("🧪 EXAMES", use_container_width=True): mudar_pagina("exames")
        if st.button("📊 RELATÓRIOS", use_container_width=True): mudar_pagina("relatorios")
    if st.button("Sair"): mudar_pagina("login")

# --- MÓDULO CONSULTAS (ESTRUTURA CONSOLIDADA) ---
elif st.session_state.page == "consultas":
    st.title("📅 Consultas")
    col_lista, col_cad = st.columns([1, 1.2])

    with col_lista:
        # Botão VOLTAR no topo da coluna esquerda
        if st.button("VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.subheader("CADASTRADOS")
        
        raw_cons = db.reference('consultas').get()
        if raw_cons:
            # Ordenação cronológica decrescente
            items = sorted(raw_cons.items(), key=lambda x: x[1].get('timestamp', 0), reverse=True)
            for k, v in items:
                c_tools, c_txt = st.columns([0.3, 0.7])
                
                # Botões Miniatura
                if c_tools.button("🗑️", key=f"del_{k}"): st.session_state.confirm_del = k; st.rerun()
                if c_tools.button("✏️", key=f"ed_{k}"): st.session_state.edit_item = (k, v, 'consultas'); mudar_pagina("editar")
                if c_tools.button("🔍", key=f"det_{k}"): st.session_state.view_item = v; mudar_pagina("detalhes")
                
                # Confirmação de exclusão integrada
                if st.session_state.confirm_del == k:
                    st.warning("Excluir?")
                    if st.button("SIM", key=f"y_{k}"):
                        db.reference('consultas').child(k).delete()
                        st.session_state.confirm_del = None; st.rerun()
                    if st.button("NÃO", key=f"n_{k}"): st.session_state.confirm_del = None; st.rerun()
                
                dt = v['data'] if '-' not in v['data'] else datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                c_txt.markdown(f"<p class='compact-text'><b>{dt}</b> - {v['hora']}<br>{v['especialidade']}<br>Dr. {v['medico']}</p>", unsafe_allow_html=True)

    with col_cad:
        with st.form("form_con", clear_on_submit=True):
            # Botão CADASTRAR no topo da coluna direita
            submit = st.form_submit_button("CADASTRAR", use_container_width=True)
            esp = st.selectbox("Especialidade", LISTA_ESP)
            data_c = st.date_input("Data da Consulta", format="DD/MM/YYYY")
            hora_c = st.text_input("Hora da Consulta")
            medico = st.text_input("Nome do Médico")
            local = st.text_input("Local / Hospital")
            
            if submit:
                db.reference('consultas').push({
                    'especialidade': esp, 'data': str(data_c), 'hora': hora_c,
                    'medico': medico, 'local': local, 'timestamp': datetime.datetime.now().timestamp()
                })
                st.success("Cadastrado com sucesso!")
                st.rerun()

# --- MÓDULO MEDICAMENTOS (ESTRUTURA CONSOLIDADA) ---
elif st.session_state.page == "meds":
    st.title("💊 Medicamentos")
    col_lista_m, col_cad_m = st.columns([1, 1.2])

    with col_lista_m:
        if st.button("VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.subheader("CADASTRADOS")
        
        raw_meds = db.reference('medicamentos').get()
        if raw_meds:
            turnos_ordem = ["MANHÃ", "MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "TARDE", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "NOITE"]
            items_m = sorted(raw_meds.items(), key=lambda x: turnos_ordem.index(x[1].get('turno', 'NOITE')))
            for k, v in items_m:
                ct, cx = st.columns([0.3, 0.7])
                if ct.button("🗑️", key=f"dm_{k}"): st.session_state.confirm_del = k; st.rerun()
                if ct.button("✏️", key=f"em_{k}"): st.session_state.edit_item = (k, v, 'medicamentos'); mudar_pagina("editar")
                if ct.button("🔍", key=f"vm_{k}"): st.session_state.view_item = v; mudar_pagina("detalhes")
                
                if st.session_state.confirm_del == k:
                    if st.button("SIM", key=f"sy_{k}"):
                        db.reference('medicamentos').child(k).delete()
                        st.session_state.confirm_del = None; st.rerun()
                    st.button("NÃO", key=f"sn_{k}")

                cx.markdown(f"<p class='compact-text'><b>{v['turno']}</b><br>{v['nome']} ({v['mg']})</p>", unsafe_allow_html=True)

    with col_cad_m:
        with st.form("form_med", clear_on_submit=True):
            st.form_submit_button("CADASTRAR", use_container_width=True)
            n_m = st.text_input("Nome")
            mg = st.text_input("Dosagem (mg)")
            medico_m = st.text_input("Médico")
            esp_m = st.selectbox("Especialidade", LISTA_ESP)
            turno = st.selectbox("Forma de Uso", ["MANHÃ", "MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "TARDE", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "NOITE"])
            
            if st.form_submit_button("OK"):
                db.reference('medicamentos').push({
                    'nome': n_m, 'mg': mg, 'medico': medico_m, 'especialidade': esp_m,
                    'turno': turno, 'timestamp': datetime.datetime.now().timestamp()
                })
                st.success("Salvo!")
                st.rerun()

# --- TELAS DE SUPORTE (DETALHES E EDIÇÃO) ---
elif st.session_state.page == "detalhes":
    st.title("🔍 Informações Completas")
    v = st.session_state.view_item
    for chave, valor in v.items():
        if chave != 'timestamp': st.write(f"**{chave.capitalize()}:** {valor}")
    if st.button("VOLTAR"): mudar_pagina("dashboard")

elif st.session_state.page == "editar":
    st.title("✏️ Alterar Cadastro")
    k, v, path = st.session_state.edit_item
    # Simplificado para exemplo, pode ser expandido com todos os campos
    novo_nome = st.text_input("Alterar Nome/Especialidade", value=v.get('nome') or v.get('especialidade'))
    if st.button("SALVAR"):
        db.reference(path).child(k).update({'nome': novo_nome} if path == 'medicamentos' else {'especialidade': novo_nome})
        st.success("Atualizado!")
        mudar_pagina("dashboard")
    if st.button("VOLTAR"): mudar_pagina("dashboard")

# --- PLACEHOLDERS ---
elif st.session_state.page in ["cadastro", "exames", "relatorios"]:
    st.title(st.session_state.page.upper())
    if st.button("VOLTAR"): mudar_pagina("dashboard")
