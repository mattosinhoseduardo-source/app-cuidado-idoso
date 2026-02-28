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

# --- ESTADO DA SESSÃO ---
if 'page' not in st.session_state: st.session_state.page = "login"
if 'user_email' not in st.session_state: st.session_state.user_email = ""
if 'form_reset' not in st.session_state: st.session_state.form_reset = 0

def mudar_pagina(nome):
    st.session_state.page = nome
    st.rerun()

def limpar_formulario():
    st.session_state.form_reset += 1

LISTA_ESP = ["Alergista", "Anestesiologia", "Angiologia", "Cardiologia", "Cirurgião", "Clínico Geral", "Coloproctologia", "Dermatologia", "Endocrinologia", "Gastroenterologia", "Geriatria", "Ginecologia e obstetrícia", "Hematologia e hemoterapia", "Infectologia", "Mastologia", "Nefrologia", "Neurocirurgia", "Neurologia", "Nutrologia", "Oftalmologia", "Ortopedia e traumatologia", "Otorrinolaringologia", "Pneumologia", "Psiquiatria", "Reumatologia", "Urologia"]

# --- LOGIN E DASHBOARD (Mantidos conforme última versão) ---
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
            else:
                st.error("Acesso negado.")
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

# --- MÓDULO CONSULTAS (AJUSTADO) ---
elif st.session_state.page == "consultas":
    st.title("📅 Agendamento de Consultas")
    
    col_lista, col_cad = st.columns([1, 1.5])

    with col_lista:
        # Botão VOLTAR acima da coluna de cadastrados
        if st.button("VOLTAR", key="back_cons", use_container_width=True): mudar_pagina("dashboard")
        st.subheader("CADASTRADOS")
        # Busca sem ordenar no Firebase para evitar o erro, ordenamos no Python
        cons_raw = db.reference('consultas').get()
        if cons_raw:
            # Ordenação cronológica decrescente no Python
            sorted_cons = sorted(cons_raw.items(), key=lambda x: x[1].get('timestamp', 0), reverse=True)
            for k, v in sorted_cons:
                try:
                    d_fmt = datetime.datetime.strptime(v['data'], '%Y-%m-%d').strftime('%d/%m/%Y')
                except:
                    d_fmt = v['data']
                st.info(f"📅 {d_fmt} - {v['hora']}\n\n**{v['especialidade']}**\n\nDr(a). {v['medico']}")
                if st.button("🗑️", key=f"del_{k}"):
                    db.reference('consultas').child(k).delete()
                    st.rerun()

    with col_cad:
        with st.form(key=f"form_con_{st.session_state.form_reset}"):
            # Botão CADASTRAR acima dos campos
            submit = st.form_submit_button("CADASTRAR", use_container_width=True)
            esp = st.selectbox("Especialidade", LISTA_ESP)
            data_c = st.date_input("Data da Consulta", format="DD/MM/YYYY")
            hora_c = st.text_input("Hora da Consulta (ex: 14:30)")
            medico = st.text_input("Nome do Médico")
            local = st.text_input("Clínica / Hospital")
            
            if submit:
                db.reference('consultas').push({
                    'especialidade': esp, 'data': str(data_c), 'hora': hora_c,
                    'medico': medico, 'local': local, 'timestamp': datetime.datetime.now().timestamp()
                })
                st.success("Confirmação de cadastro realizada!")
                limpar_formulario()
                st.rerun()

# --- MÓDULO MEDICAMENTOS (AJUSTADO) ---
elif st.session_state.page == "meds":
    st.title("💊 Medicamentos")
    
    col_lista_m, col_cad_m = st.columns([1, 1.5])

    with col_lista_m:
        # Botão VOLTAR acima da lista
        if st.button("VOLTAR", key="back_meds", use_container_width=True): mudar_pagina("dashboard")
        st.subheader("CADASTRADOS")
        meds_raw = db.reference('medicamentos').get()
        if meds_raw:
            turnos_ordem = ["MANHÃ", "MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "TARDE", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "NOITE"]
            ordem_map = {t: i for i, t in enumerate(turnos_ordem)}
            # Ordena por turno conforme pedido
            sorted_meds = sorted(meds_raw.items(), key=lambda x: ordem_map.get(x[1].get('turno', ''), 99))
            for k, v in sorted_meds:
                st.warning(f"💊 **{v['turno']}**\n\n{v['nome']} ({v['mg']})")
                if st.button("🗑️", key=f"del_m_{k}"):
                    db.reference('medicamentos').child(k).delete()
                    st.rerun()

    with col_cad_m:
        with st.form(key=f"form_med_{st.session_state.form_reset}"):
            # Botão CADASTRAR acima dos campos
            submit_m = st.form_submit_button("CADASTRAR", use_container_width=True)
            nome_m = st.text_input("Nome do Medicamento")
            mg = st.text_input("Dosagem (mg)")
            
            c_data1, c_data2 = st.columns(2)
            data_cad = c_data1.date_input("Data do Cadastro", format="DD/MM/YYYY")
            hoje = c_data2.checkbox("Data de Hoje", value=True)
            
            medico_m = st.text_input("Médico")
            esp_m = st.selectbox("Especialidade", LISTA_ESP)
            
            t_lista = ["MANHÃ", "MANHÃ ANTES DO CAFÉ", "MANHÃ APÓS O CAFÉ", "TARDE", "TARDE ANTES DO ALMOÇO", "TARDE DEPOIS DO ALMOÇO", "NOITE"]
            turno_sel = st.selectbox("Forma de Uso", t_lista)
            
            lembrete = st.checkbox("Necessário Lembrete?")
            if lembrete:
                tipo_l = st.radio("Tipo", ["Recorrente", "Personalizado"], horizontal=True)
                if tipo_l == "Recorrente":
                    st.time_input("Horário do Despertador")
                else:
                    st.text_area("Datas e Horas do Despertador")
            
            if submit_m:
                db.reference('medicamentos').push({
                    'nome': nome_m, 'mg': mg, 'medico': medico_m, 'especialidade': esp_m,
                    'turno': turno_sel, 'data_cadastro': str(data_cad), 'timestamp': datetime.datetime.now().timestamp()
                })
                st.success("Confirmação de cadastro realizada!")
                limpar_formulario()
                st.rerun()

elif st.session_state.page in ["cadastro", "exames", "relatorios"]:
    st.title(st.session_state.page.upper())
    if st.button("VOLTAR"): mudar_pagina("dashboard")
