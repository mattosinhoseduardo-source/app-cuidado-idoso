import streamlit as st
import firebase_admin
from firebase_admin import credentials, db, auth
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from fpdf import FPDF
import io
import json

# ==========================================
# CONFIGURAÇÃO DEVE SER O PRIMEIRO COMANDO
# ==========================================
st.set_page_config(page_title="Gestão de Cuidados", layout="centered", initial_sidebar_state="expanded")

# ==========================================
# CONFIGURAÇÃO DO BANCO (FIREBASE)
# ==========================================
if not firebase_admin._apps:
    try:
        # Tenta carregar as credenciais via Segredos do Streamlit Cloud (para Deploy)
        if "firebase" in st.secrets:
            # st.secrets["firebase"] actua como um dicionário
            cred_dict = dict(st.secrets["firebase"])
            # Removemos caracteres extras indesejados caso existam (ex: escape de quebra de linha)
            if 'private_key' in cred_dict:
                cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
            cred = credentials.Certificate(cred_dict)
        else:
            # Fallback para o arquivo local durante testes na máquina
            cred = credentials.Certificate("firebase_key.json")
            
        firebase_admin.initialize_app(cred, {
            'databaseURL': 'https://app-para-idosos-54ffd-default-rtdb.firebaseio.com/'
        })
    except Exception as e:
        st.warning(f"Atenção: Erro ao carregar Firebase Admin. Erro: {e}")

# Removido Pyrebase pois usaremos o Firebase Admin para tudo, simplificando a autenticação via Admin Auth
pyrebase_auth = None

# ==========================================
# FUNÇÕES UTILITÁRIAS
# ==========================================
def enviar_alerta_email(destinatarios, assunto, corpo):
    remetente = "seu_email@gmail.com"
    senha = "sua_senha_de_app"
    
    msg = MIMEMultipart()
    msg['From'] = remetente
    msg['To'] = ", ".join(destinatarios)
    msg['Subject'] = assunto
    
    msg.attach(MIMEText(corpo, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(remetente, senha)
        text = msg.as_string()
        server.sendmail(remetente, destinatarios, text)
        server.quit()
        st.success("Alerta enviado com sucesso!")
    except Exception as e:
        st.error(f"Erro ao enviar o e-mail: {e}")

def gerar_pdf_relatorio(data_inicial, data_final):
    # Usando FPDF2 - suporta acentos nativamente se usar fontes adequadas ou padrão latin-1 default
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("helvetica", style="B", size=16)
    pdf.cell(0, 10, txt="Relatorio de Gestao de Cuidados para Idosos", new_x="LMARGIN", new_y="NEXT", align='C')
    
    pdf.ln(5)
    pdf.set_font("helvetica", size=12)
    pdf.cell(0, 10, txt=f"Período Analisado: {data_inicial.strftime('%d/%m/%Y')} a {data_final.strftime('%d/%m/%Y')}", new_x="LMARGIN", new_y="NEXT", align='C')
    pdf.ln(10)
    
    # ---------------- Medicamentos ----------------
    pdf.set_font("helvetica", style="B", size=14)
    pdf.cell(0, 10, txt="1. Medicamentos Cadastrados", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=12)
    # Aqui entraria a lófica de buscar do Firebase => items = db.reference('medicamentos').get()
    # Mock fallback
    pdf.multi_cell(0, 10, txt="- (Exemplo) Losartana 50mg - Uso: MANHÃ ANTES DO CAFÉ - Especialidade: Cardiologia\n- (Exemplo) Dipirona 500mg - Uso: TARDE DEPOIS DO ALMOÇO - Especialidade: Clínico Geral")
    pdf.ln(5)
    
    # ---------------- Consultas ----------------
    pdf.set_font("helvetica", style="B", size=14)
    pdf.cell(0, 10, txt="2. Consultas Agendadas", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=12)
    pdf.multi_cell(0, 10, txt="- (Exemplo) Cardiologia - Data: 15/05/2026 14:30 - Dr. Silva\n- (Exemplo) Geriatria - Data: 20/05/2026 09:00 - Dra. Souza")
    pdf.ln(5)
    
    # ---------------- Exames ----------------
    pdf.set_font("helvetica", style="B", size=14)
    pdf.cell(0, 10, txt="3. Exames Realizados/Agendados", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("helvetica", size=12)
    pdf.multi_cell(0, 10, txt="- (Exemplo) Hemograma Completo - Data: 10/05/2026 - Lab. Central\n- (Exemplo) Ecocardiograma - Data: 12/05/2026 - Clínica Diagnóstico")
    
    # fpdf2 .output() retorna bytearray
    return bytes(pdf.output())

# ==========================================
# GERENCIAMENTO DE ESTADO (Session State)
# ==========================================
if 'user_id' not in st.session_state:
    st.session_state['user_id'] = None
if 'user_role' not in st.session_state:
    st.session_state['user_role'] = None
if 'user_status' not in st.session_state:
    st.session_state['user_status'] = None
if 'current_view' not in st.session_state:
    st.session_state['current_view'] = 'Home'
if 'view_mode' not in st.session_state:
    st.session_state['view_mode'] = 'Login'

# ==========================================
# FASE 1: Autenticação e Gestão de Usuários
# ==========================================
def login_view():
    st.title("Acesso ao Sistema")
    with st.form("login_form"):
        email = st.text_input("E-mail")
        senha = st.text_input("Senha", type="password")
        col1, col2 = st.columns(2)
        btn_ok = col1.form_submit_button("OK")
        btn_cancelar = col2.form_submit_button("Cancelar")
        
    if btn_ok:
        try:
            # Login simplificado via Firebase Admin
            # O Admin SDK não tem 'sign_in_with_email_and_password'. Ele confia que o login local verifica 
            # Mas podemos buscar o usuário pelo email e mockar a verificação de senha, OU usar Pyrebase se o usuário forneceu API Key (ele não forneceu).
            # Como ele só forneceu as credenciais de Admin, buscaremos o usuário no db para validar a existência
            try:
                user_record = auth.get_user_by_email(email)
                uid = user_record.uid
                
                ref = db.reference(f'users/{uid}')
                user_data = ref.get()
                
                if user_data:
                    # NOTA: Para um login seguro real, precisaria da API Key do Firebase ou de uma solução de session cookies.
                    # Aqui vamos simular que a senha estava correta e focar na Regra de Negócio dos 5 usuários.
                    if user_data.get('senha_plana') == senha: # Apenas para fins didáticos neste escopo
                        st.session_state['user_id'] = uid
                        st.session_state['user_role'] = user_data.get('cargo', 'usuario')
                        st.session_state['user_status'] = user_data.get('status_aprovacao', 'pendente')
                        st.success("Login realizado!")
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")
                else:
                    st.error("Usuário não tem perfil gerado no banco de dados.")
            except Exception as e:
                st.error("Usuário não encontrado ou erro de conexão. Tente novamente.")
                
        except Exception as e:
            st.error(f"Erro no sistema: {e}")
            
    if btn_cancelar:
        st.info("Ação cancelada.")

    col1, col2 = st.columns(2)
    if col1.button("Não possui conta? Cadastre-se"):
        st.session_state['view_mode'] = 'Cadastro'
        st.rerun()
    if col2.button("Esqueci a Senha"):
        st.session_state['view_mode'] = 'EsqueciSenha'
        st.rerun()

def cadastro_view():
    st.title("Cadastro de Usuário")
    with st.form("cadastro_form"):
        nome_completo = st.text_input("Nome Completo")
        email = st.text_input("E-mail")
        telefone = st.text_input("Telefone")
        senha = st.text_input("Senha", type="password")
        confirma_senha = st.text_input("Confirmar Senha", type="password")
        btn_cadastrar = st.form_submit_button("Cadastrar")
        
    if btn_cadastrar:
        if senha != confirma_senha:
            st.error("As senhas não coincidem.")
        else:
            try:
                # Criando usuário no Firebase Authentication via Admin
                user_record = auth.create_user(
                    email=email,
                    password=senha,
                    display_name=nome_completo
                )
                uid = user_record.uid
                
                users_ref = db.reference('users')
                users = users_ref.get()
                if users is None:
                    cargo = "admin"
                    status_aprovacao = "ativo"
                else:
                    cargo = "usuario"
                    status_aprovacao = "pendente"

                # Salvando no Realtime DB
                users_ref.child(uid).set({
                    "perfil": {
                        "nome": nome_completo,
                        "email": email,
                        "telefone": telefone
                    },
                    "status_aprovacao": status_aprovacao,
                    "cargo": cargo,
                    "senha_plana": senha # Apenas para fins deste demo sem Client SDK
                })
                st.success("Cadastro realizado com sucesso! Faça login para continuar.")
                st.session_state['view_mode'] = 'Login'
                st.rerun()
            except Exception as e:
                st.error(f"Erro ao cadastrar. O e-mail pode já estar em uso. Erro: {e}")

    if st.button("Voltar ao Login"):
        st.session_state['view_mode'] = 'Login'
        st.rerun()

def esqueci_senha_view():
    st.title("Recuperação de Senha")
    with st.form("esqueci_senha_form"):
        email = st.text_input("E-mail cadastrado")
        btn_enviar = st.form_submit_button("Enviar E-mail de Recuperação")
        
    if btn_enviar:
        try:
            # O Admin SDK permite gerar um link que podemos enviar manualmente
            link = auth.generate_password_reset_link(email)
            st.info(f"Em um ambiente de produção, enviaríamos este link para o e-mail: {link}")
            st.success("Solicitação processada com sucesso!")
        except Exception as e:
            st.error(f"Erro ao processar a recuperação: {e}")
            
    if st.button("Voltar ao Login"):
        st.session_state['view_mode'] = 'Login'
        st.rerun()

def admin_panel():
    st.subheader("Painel de Administração")
    try:
        if not firebase_admin._apps:
            st.info("Mock: Sem Firebase, impossível listar usuários reais.")
            return

        users_ref = db.reference('users')
        users = users_ref.get()
        if users:
            for uid, data in users.items():
                if data.get('status_aprovacao') == 'pendente':
                    col1, col2 = st.columns([3, 1])
                    nome = data.get('perfil', {}).get('nome', 'Sem Nome')
                    email = data.get('perfil', {}).get('email', 'Sem Email')
                    col1.write(f"**{nome}** ({email})")
                    if col2.button("Aprovar", key=f"aprovar_{uid}"):
                        users_ref.child(uid).update({"status_aprovacao": "ativo"})
                        st.success(f"Usuário {nome} aprovado!")
                        st.rerun()
    except Exception as e:
        st.error(f"Erro ao acessar usuários: {e}")

# ==========================================
# FASE 2: Telas Principais da Aplicação
# ==========================================
def main_interface():
    if st.session_state['user_status'] == 'pendente':
        st.warning("Seu cadastro está pendente de aprovação.")
        if st.button("Sair"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        return

    with st.sidebar:
        st.write(f"Logado como: **{st.session_state['user_role'].upper()}**")
        if st.session_state['user_role'] == 'admin':
            admin_panel()
            
        st.markdown("---")
        if st.button("Tela Inicial", use_container_width=True):
            st.session_state['current_view'] = 'Home'
            st.rerun()
        if st.button("Sair / Logout", use_container_width=True, type="primary"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    if st.session_state['current_view'] == 'Home':
        st.title("Gestão de Cuidados - Início")
        st.write("Selecione o módulo:")
        
        st.markdown(
            \"\"\"
            <style>
            .stButton > button {
                width: 100%;
                height: 100px;
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 20px;
            }
            </style>
            \"\"\", unsafe_allow_html=True
        )
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💊 MEDICAMENTOS"):
                st.session_state['current_view'] = 'Medicamentos'
                st.rerun()
            if st.button("🩻 EXAMES"):
                st.session_state['current_view'] = 'Exames'
                st.rerun()
        with col2:
            if st.button("🩺 CONSULTAS"):
                st.session_state['current_view'] = 'Consultas'
                st.rerun()
            if st.button("📋 RELATÓRIOS"):
                st.session_state['current_view'] = 'Relatorios'
                st.rerun()
                
    elif st.session_state['current_view'] == 'Medicamentos':
        tela_medicamentos()
    elif st.session_state['current_view'] == 'Consultas':
        tela_consultas()
    elif st.session_state['current_view'] == 'Exames':
        tela_exames()
    elif st.session_state['current_view'] == 'Relatorios':
        tela_relatorios()

# ----------------- Sub-telas de Módulos -----------------
def tela_medicamentos():
    st.title("💊 Medicamentos")
    st.button("⬅ Voltar", on_click=voltar_home)
    
    with st.expander("Cadastrar Novo Medicamento"):
        with st.form("form_med"):
            nome = st.text_input("Nome do Medicamento")
            mg = st.text_input("Dosagem (mg)")
            
            # ATUALIZADO: Lista específica de formas de uso
            opcoes_uso = [
                "MANHÃ", 
                "MANHÃ ANTES DO CAFÉ", 
                "MANHÃ APÓS O CAFÉ", 
                "TARDE", 
                "TARDE ANTES DO ALMOÇO", 
                "TARDE DEPOIS DO ALMOÇO", 
                "NOITE"
            ]
            forma_uso = st.selectbox("Forma de Uso", opcoes_uso)
            
            tipo = st.selectbox("Tipo", ["Comprimido", "Líquido", "Injeção", "Gotas"])
            medico = st.text_input("Médico Prescritor")
            especialidade = st.text_input("Especialidade")
            necessario_lembrete = st.checkbox("Necessário Lembrete (Alerta Email)?")
            
            if st.form_submit_button("Salvar Medicamento"):
                st.success("Medicamento salvo com sucesso (mock).")

def tela_consultas():
    st.title("🩺 Consultas")
    st.button("⬅ Voltar", on_click=voltar_home)
    
    with st.expander("Agendar Nova Consulta"):
        with st.form("form_cons"):
            # ATUALIZADO: Lista exata com as 26 opções de Especialidade solicitadas
            lista_especialidades = [
                "Alergista", "Anestesiologia", "Angiologia", "Cardiologia", "Cirurgião", 
                "Clínico Geral", "Coloproctologia", "Dermatologia", "Endocrinologia", 
                "Gastroenterologia", "Geriatria", "Ginecologia e obstetrícia", 
                "Hematologia e hemoterapia", "Infectologia", "Mastologia", "Nefrologia", 
                "Neurocirurgia", "Neurologia", "Nutrologia", "Oftalmologia", 
                "Ortopedia e traumatologia", "Otorrinolaringologia", "Pneumologia", 
                "Psiquiatria", "Reumatologia", "Urologia"
            ]
            especialidade = st.selectbox("Especialidade", lista_especialidades)
            
            data = st.date_input("Data da Consulta")
            hora = st.time_input("Hora")
            medico = st.text_input("Médico")
            clinica = st.text_input("Clínica / Local")
            obs = st.text_area("Observações")
            necessario_lembrete = st.checkbox("Necessário Lembrete (Alerta Email)?")
            
            if st.form_submit_button("Salvar Consulta"):
                st.success("Consulta agendada com sucesso (mock).")

def tela_exames():
    st.title("🩻 Exames")
    st.button("⬅ Voltar", on_click=voltar_home)
    
    with st.expander("Agendar Novo Exame"):
        with st.form("form_exame"):
            nome = st.text_input("Nome do Exame")
            data = st.date_input("Data do Exame")
            hora = st.time_input("Hora")
            local = st.text_input("Local da Realização")
            endereco = st.text_input("Endereço Completo")
            obs = st.text_area("Observações / Preparo")
            
            if st.form_submit_button("Salvar Exame"):
                st.success("Exame salvo com sucesso (mock).")

def tela_relatorios():
    st.title("📋 Relatórios")
    st.button("⬅ Voltar", on_click=voltar_home)
    
    st.subheader("Gerar Relatório de Cuidados (PDF)")
    st.write("Selecione o período desejado para consolidar os dados registrados.")
    
    col1, col2 = st.columns(2)
    with col1:
        data_inicial = st.date_input("Data Inicial")
    with col2:
        data_final = st.date_input("Data Final")
        
    if st.button("Gerar PDF"):
        if data_inicial <= data_final:
            try:
                # Chama a função de gerar PDF e recebe os bytes
                pdf_bytes = gerar_pdf_relatorio(data_inicial, data_final)
                
                # Exibe o botão de Download direto no Streamlit
                st.download_button(
                    label="⬇️ Baixar Relatório PDF",
                    data=pdf_bytes,
                    file_name=f"Relatorio_Cuidados_{data_inicial.strftime('%Y%m%d')}_a_{data_final.strftime('%Y%m%d')}.pdf",
                    mime="application/pdf"
                )
                st.success("Relatório gerado com sucesso! Clique no botão acima para concluir o download.")
            except Exception as e:
                st.error(f"Ocorreu um erro ao gerar o PDF: {e}")
        else:
            st.error("A Data Inicial deve ser menor ou igual à Data Final.")

def voltar_home():
    st.session_state['current_view'] = 'Home'

# ==========================================
# PONTO DE ENTRADA PRINCIPAL
# ==========================================
if __name__ == "__main__":
    if st.session_state['user_id'] is None:
        if st.session_state['view_mode'] == 'Login':
            login_view()
        elif st.session_state['view_mode'] == 'Cadastro':
            cadastro_view()
        elif st.session_state['view_mode'] == 'EsqueciSenha':
            esqueci_senha_view()
    else:
        main_interface()
