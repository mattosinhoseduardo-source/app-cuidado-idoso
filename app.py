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

# --- CSS PARA DIMINUIR FONTE E ESPAÇAMENTO ---
st.markdown("""
    <style>
    .compact-text { font-size: 13px !important; line-height: 1.2 !important; margin-bottom: 2px !important; }
    .stButton > button { padding: 2px 5px !important; font-size: 12px !important; }
    </style>
    """, unsafe_allow_html=True)

# --- ESTADO DA SESSÃO ---
if 'page' not in st.session_state: st.session_state.page = "login"
if 'user_email' not in st.session_state: st.session_state.user_email = ""
if 'form_reset' not in st.session_state: st.session_state.form_reset = 0
if 'item_selecionado' not in st.session_state: st.session_state.item_selecionado = None
if 'confirm_del' not in st.session_state: st.session_state.confirm_del = None

def mudar_pagina(nome, item=None):
    st.session_state.page = nome
    st.session_state.item_selecionado = item
    st.rerun()

def limpar_formulario():
    st.session_state.form_reset += 1

LISTA_ESP = ["Alergista", "Anestesiologia", "Angiologia", "Cardiologia", "Cirurgião", "Clínico Geral", "Coloproctologia", "Dermatologia", "Endocrinologia", "Gastroenterologia", "Geriatria", "Ginecologia e obstetrícia", "Hematologia e hemoterapia", "Infectologia", "Mastologia", "Nefrologia", "Neurocirurgia", "Neurologia", "Nutrologia", "Oftalmologia", "Ortopedia e traumatologia", "Otorrinolaringologia", "Pneumologia", "Psiquiatria", "Reumatologia", "Urologia"]

# --- LOGIN E DASHBOARD ---
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

# --- MÓDULO CONSULTAS ---
elif st.session_state.page == "consultas":
    st.title("📅 Agendamento de Consultas")
    col_lista, col_cad = st.columns([1, 1.3])

    with col_lista:
        if st.button("VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.subheader("CADASTRADOS")
        
        # Diálogo de Confirmação de Exclusão
        if st.session_state.confirm_del:
            st.warning(f"Excluir este item?")
            c_sim, c_nao = st.columns(2)
            if c_sim.button("SIM"):
                db.reference('consultas').child(st.session_state.confirm_del).delete()
                st.session_state.confirm_del = None
                st.rerun()
            if c_nao.button("NÃO"):
                st.session_state.confirm_del = None
                st.rerun()

        cons_raw = db.reference('consultas').get()
        if cons_raw:
            sorted_cons = sorted(cons_raw.items(), key=lambda x: x[1].get('timestamp', 0), reverse=True)
            for k, v in sorted_cons:
                c_icones, c_info = st.columns([0.4, 1])
                # Botões compactos
                if c_icones.button("🗑️", key=f"del_{k}"): st.session_state.confirm_del = k; st.rerun()
                if c_icones.button("✏️", key=f"ed_{k}"): mudar_pagina("edit_consulta", (k, v))
                if c_icones.button("🔍", key=f"det_{k}"): mudar_pagina("det_consulta", v)
                
                d_fmt = v['data'] if '-' not in v['data'] else datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                c_info.markdown(f"<p class='compact-text'><b>{d_fmt} - {v['hora']}</b><br>{v['especialidade']}<br>Dr. {v['medico']}</p>", unsafe_allow_html=True)
                st.divider()

    with col_cad:
        with st.form(key=f"form_con_{st.session_state.form_reset}"):
            submit = st.form_submit_button("CADASTRAR", use_container_width=True)
            esp = st.selectbox("Especialidade", LISTA_ESP)
            data_c = st.date_input("Data da Consulta", format="DD/MM/YYYY")
            hora_c = st.text_input("Hora da Consulta")
            medico = st.text_input("Nome do Médico")
            local = st.text_input("Clínica / Hospital")
            if submit:
                db.reference('consultas').push({
                    'especialidade': esp, 'data': str(data_c), 'hora': hora_c,
                    'medico': medico, 'local': local, 'timestamp': datetime.datetime.now().timestamp()
                })
                st.success("Cadastrado com sucesso!")
                limpar_formulario(); st.rerun()

# --- TELAS DE DETALHE E EDIÇÃO (CONSULTAS) ---
elif st.session_state.page == "det_consulta":
    st.title("🔍 Detalhes da Consulta")
    v = st.session_state.item_selecionado
    st.write(f"**Especialidade:** {v['especialidade']}")
    st.write(f"**Médico:** {v['medico']}")
    st.write(f"**Data:** {v['data']} | **Hora:** {v['hora']}")
    st.write(f"**Local:** {v['local']}")
    if st.button("VOLTAR"): mudar_pagina("consultas")

elif st.session_state.page == "edit_consulta":
    st.title("✏️ Editar Consulta")
    k, v = st.session_state.item_selecionado
    with st.form("edit_con"):
        new_esp = st.selectbox("Especialidade", LISTA_ESP, index=LISTA_ESP.index(v['especialidade']))
        new_med = st.text_input("Médico", value=v['medico'])
        if st.form_submit_button("SALVAR ALTERAÇÕES"):
            db.reference('consultas').child(k).update({'especialidade': new_esp, 'medico': new_med})
            st.success("Alterado!")
            mudar_pagina("consultas")
    if st.button("CANCELAR"): mudar_pagina("consultas")

# --- MÓDULO MEDICAMENTOS (Estrutura similar) ---
elif st.session_state.page == "meds":
    st.title("💊 Medicamentos")
    col_lista_m, col_cad_m = st.columns([1, 1.3])
    
    with col_lista_m:
        if st.button("VOLTAR", use_container_width=True): mudar_pagina("dashboard")
        st.subheader("CADASTRADOS")
        
        if st.session_state.confirm_del:
            st.warning("Excluir?")
            if st.button("SIM"):
                db.reference('medicamentos').child(st.session_state.confirm_del).delete()
                st.session_state.confirm_del = None; st.rerun()
            if st.button("NÃO"): st.session_state.confirm_del = None; st.rerun()

        meds_raw = db.reference('medicamentos').get()
        if meds_raw:
            turnos_ordem = ["MANHÃ", "MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "TARDE", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "NOITE"]
            sorted_meds = sorted(meds_raw.items(), key=lambda x: turnos_ordem.index(x[1].get('turno', 'NOITE')))
            for k, v in sorted_meds:
                c1, c2 = st.columns([0.4, 1])
                if c1.button("🗑️", key=f"dm_{k}"): st.session_state.confirm_del = k; st.rerun()
                if c1.button("🔍", key=f"v_m_{k}"): mudar_pagina("det_med", v)
                c2.markdown(f"<p class='compact-text'><b>{v['turno']}</b><br>{v['nome']} ({v['mg']})</p>", unsafe_allow_html=True)
                st.divider()

    with col_cad_m:
        with st.form(key=f"f_m_{st.session_state.form_reset}"):
            st.form_submit_button("CADASTRAR", use_container_width=True)
            n_m = st.text_input("Nome")
            m_g = st.text_input("mg")
            t_s = st.selectbox("Turno", ["MANHÃ", "MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "TARDE", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "NOITE"])
            if st.form_submit_button("OK"):
                db.reference('medicamentos').push({'nome': n_m, 'mg': m_g, 'turno': t_s})
                limpar_formulario(); st.rerun()

# --- TELAS PLACEHOLDER PARA EXAMES E RELATÓRIOS ---
elif st.session_state.page in ["exames", "relatorios", "det_med", "cadastro"]:
    st.title(st.session_state.page.upper())
    if st.button("VOLTAR"): mudar_pagina("dashboard")
