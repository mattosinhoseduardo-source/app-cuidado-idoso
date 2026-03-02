# --- MÓDULO RELATÓRIOS (CORREÇÃO DE DOWNLOAD PDF) ---
elif st.session_state.page == "relatorios":
    st.title("📊 Relatórios")
    
    col_rel_l, col_rel_r = st.columns([1, 1])
    
    with col_rel_l:
        d_ini = st.date_input("Período Inicial", format="DD/MM/YYYY", value=datetime.date.today() - datetime.timedelta(days=30))
        d_fim = st.date_input("Período Final", format="DD/MM/YYYY")
        opcao = st.selectbox("Tipo de Relatório", ["CONSOLIDADO", "MEDICAMENTOS", "CONSULTAS", "EXAMES"])

    with col_rel_r:
        st.write("##") # Espaçador
        gerar = st.button("GERAR RELATÓRIO PDF", use_container_width=True)
        if st.button("VOLTAR", use_container_width=True): mudar_pagina("dashboard")

    if gerar:
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(190, 10, "Relatorio de Saude", 0, 1, "C")
            pdf.set_font("Arial", "", 10)
            pdf.cell(190, 10, f"Periodo: {d_ini.strftime('%d/%m/%Y')} a {d_final.strftime('%d/%m/%Y')}", 0, 1, "C")
            
            def add_sec(title, path, fields):
                res = db.reference(path).get()
                if res:
                    pdf.ln(5)
                    pdf.set_font("Arial", "B", 12)
                    pdf.cell(190, 10, title, 1, 1, "L")
                    pdf.set_font("Arial", "", 9)
                    for k, v in res.items():
                        v_d = v.get('data') or v.get('data_cadastro')
                        if v_d:
                            # Converte string para objeto date para comparar
                            v_date_obj = datetime.datetime.strptime(v_d, '%Y-%m-%d').date()
                            if d_ini <= v_date_obj <= d_fim:
                                info = " | ".join([f"{f}: {v.get(f.lower(), 'N/A')}" for f in fields])
                                pdf.multi_cell(190, 7, f"[{v_date_obj.strftime('%d/%m/%Y')}] {info}", 0, "L")

            if opcao in ["CONSOLIDADO", "MEDICAMENTOS"]: add_sec("MEDICAMENTOS", 'medicamentos', ["Nome", "mg", "Turno", "Medico"])
            if opcao in ["CONSOLIDADO", "CONSULTAS"]: add_sec("CONSULTAS", 'consultas', ["Especialidade", "Medico", "Local"])
            if opcao in ["CONSOLIDADO", "EXAMES"]: add_sec("EXAMES", 'exames', ["Nome", "Medico", "Local", "Preparo"])

            # CORREÇÃO AQUI: fpdf2 já retorna bytes, não precisa de .encode()
            pdf_out = pdf.output() 
            
            st.download_button(
                label="📥 Baixar Relatório PDF",
                data=bytes(pdf_out), # Garante o formato correto para o Streamlit
                file_name=f"Relatorio_{opcao}_{datetime.date.today().strftime('%d_%m_%Y')}.pdf",
                mime="application/pdf"
            )
            st.success("Relatório preparado para download!")
            
        except Exception as e:
            st.error(f"Erro ao processar PDF: {e}")
