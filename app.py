# --- MÓDULO RELATÓRIOS (AJUSTE DE LAYOUT E QUEBRA DE TEXTO) ---
elif st.session_state.page == "relatorios":
    st.title("📊 Relatórios")
    col_rel_l, col_rel_r = st.columns([1, 1])
    with col_rel_l:
        d_ini = st.date_input("Período Inicial", format="DD/MM/YYYY", value=datetime.date.today() - datetime.timedelta(days=30))
        d_fim = st.date_input("Período Final", format="DD/MM/YYYY")
        opcao = st.selectbox("Tipo de Relatório", ["CONSOLIDADO", "MEDICAMENTOS", "CONSULTAS", "EXAMES"])
    with col_rel_r:
        st.write("##")
        gerar = st.button("GERAR RELATÓRIO PDF", use_container_width=True)
        if st.button("VOLTAR", use_container_width=True): mudar_pagina("dashboard")

    if gerar:
        try:
            # Configuração: A4 (210mm x 297mm), margens de 10mm
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.set_margins(left=10, top=10, right=10)
            pdf.add_page()
            
            # Cabeçalho
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, "Relatorio de Saude e Cuidados", 0, 1, "C")
            pdf.set_font("Arial", "", 10)
            pdf.cell(0, 10, f"Periodo: {d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}", 0, 1, "C")
            
            def add_sec(title, path, fields):
                res = db.reference(path).get()
                if res:
                    pdf.ln(5)
                    pdf.set_fill_color(240, 240, 240) # Fundo cinza claro para o título
                    pdf.set_font("Arial", "B", 11)
                    pdf.cell(0, 8, title, 1, 1, "L", fill=True)
                    pdf.set_font("Arial", "", 9)
                    
                    for k, v in res.items():
                        v_d = v.get('data') or v.get('data_cadastro')
                        if v_d:
                            v_date_obj = datetime.datetime.strptime(v_d, '%Y-%m-%d').date()
                            if d_ini <= v_date_obj <= d_fim:
                                # Monta o texto com quebra de linha automática (multi_cell)
                                dt_br = v_date_obj.strftime('%d/%m/%Y')
                                info = " | ".join([f"{f}: {v.get(f.lower(), 'N/A')}" for f in fields])
                                # O parâmetro 0 na largura faz ocupar até a margem direita
                                pdf.multi_cell(0, 6, f"[{dt_br}] {info}", border='B', align="L")
                                pdf.ln(1) # Pequeno respiro entre itens

            if opcao in ["CONSOLIDADO", "MEDICAMENTOS"]: 
                add_sec("MEDICAMENTOS", 'medicamentos', ["Nome", "mg", "Turno", "Medico"])
            if opcao in ["CONSOLIDADO", "CONSULTAS"]: 
                add_sec("CONSULTAS", 'consultas', ["Especialidade", "Medico", "Local"])
            if opcao in ["CONSOLIDADO", "EXAMES"]: 
                add_sec("EXAMES", 'exames', ["Nome", "Medico", "Local", "Preparo"])

            pdf_out = pdf.output() 
            st.download_button(
                label="📥 Baixar Relatório Ajustado", 
                data=bytes(pdf_out), 
                file_name=f"Relatorio_{opcao}.pdf", 
                mime="application/pdf"
            )
            st.success("Relatório gerado com margens corrigidas!")
        except Exception as e:
            st.error(f"Erro ao formatar PDF: {e}")
