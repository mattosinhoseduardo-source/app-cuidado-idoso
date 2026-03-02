# --- TELA DE CADASTRO (CORRIGIDA E REFORÇADA) ---
elif st.session_state.page == "cadastro":
    st.markdown("<h2 style='text-align: center;'>📝 Solicitar Acesso</h2>", unsafe_allow_html=True)
    
    # Usando container para garantir que no mobile não fique colado nas bordas
    with st.container():
        nome_cad = st.text_input("Nome Completo", placeholder="Digite seu nome")
        email_cad = st.text_input("E-mail", placeholder="seu@email.com").lower().strip()
        senha_cad = st.text_input("Crie uma Senha", type="password", placeholder="Mínimo 3 caracteres")
        
        st.write("##") # Espaçador
        
        col_cad1, col_cad2 = st.columns(2)
        
        with col_cad1:
            # Botão de envio com lógica direta de salvamento
            if st.button("ENVIAR SOLICITAÇÃO", key="btn_solicitar"):
                if nome_cad and email_cad and senha_cad:
                    try:
                        # Criando o dicionário de dados
                        novo_usuario = {
                            'nome': nome_cad,
                            'email': email_cad,
                            'senha': senha_cad,
                            'status': 'pendente',
                            'data_solicitacao': str(datetime.date.today())
                        }
                        # Salvando no Firebase
                        db.reference('usuarios_pendentes').push(novo_usuario)
                        st.success("✅ Solicitação enviada! O administrador revisará seu acesso.")
                        st.info("Você já pode clicar em VOLTAR e aguardar a aprovação.")
                    except Exception as e:
                        st.error(f"❌ Erro ao salvar no banco: {e}")
                else:
                    st.warning("⚠️ Por favor, preencha todos os campos antes de enviar.")

        with col_cad2:
            if st.button("VOLTAR", key="btn_voltar_cad"):
                mudar_pagina("login")

    st.markdown("""
        <hr>
        <p style='text-align: center; font-size: 14px; color: #666;'>
        Após enviar, o administrador (admin@teste.com) precisará aprovar seu login no Painel Principal.
        </p>
    """, unsafe_allow_html=True)
