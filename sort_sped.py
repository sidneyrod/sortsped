import streamlit as st
import pandas as pd
import io

st.set_page_config(
    page_title="Reestruturador Bloco C - EFD",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# 🌒 Dark theme estilizado (moderno)
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        background-color: #1e1e1e;
        color: #f5f5f5;
    }
    .stButton>button {
        background-color: #0a84ff;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 6px;
        padding: 0.5em 1em;
    }
    .stDownloadButton>button {
        background-color: #0a84ff;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 6px;
        padding: 0.5em 1em;
    }
    .stTextInput>div>div>input {
        background-color: #2b2b2b;
        color: white;
    }
    .stRadio>div>div>label {
        color: #ccc;
    }
    .stFileUploader>div>div {
        background-color: #2b2b2b;
        color: white;
    }
    .stMarkdown h1, h2, h3 {
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛠️ Reestruturador do Bloco C - EFD Contribuições")
st.markdown("Ajusta a estrutura do Bloco C conforme o leiaute oficial validado no PVA.")

uploaded_file = st.file_uploader("📤 Envie o arquivo .txt da EFD:", type=["txt"])

if uploaded_file:
    progress = st.progress(0, text="🔄 Carregando arquivo...")

    content = uploaded_file.read().decode("ISO-8859-1")
    linhas = content.splitlines(keepends=True)

    df_txt = pd.DataFrame(linhas, columns=["Conteudo"])
    df_txt['Registro'] = df_txt['Conteudo'].str.extract(r'\|(C\d{3})\|')

    # Mapeia o tipo da operação para cada C100
    tipo_op_map = {}
    for i, row in df_txt.iterrows():
        if row['Registro'] == 'C100':
            campos = row['Conteudo'].split('|')
            if len(campos) > 2:
                tipo_op_map[i] = campos[2]

    saida_final = []
    buffer = {k: [] for k in ['C100', 'C170', 'C180', 'C185', 'C190', 'C195', 'C197']}
    c100_idx = None
    total = len(df_txt)

    progress.progress(0.1, text="🔧 Reestruturando Bloco C...")

    for idx, row in df_txt.iterrows():
        reg = row['Registro']
        conteudo = row['Conteudo']

        if reg == 'C100':
            if buffer['C100']:
                tipo_op = tipo_op_map.get(c100_idx, '0')
                saida_final.extend(buffer['C100'])

                if tipo_op == '1':  # SAÍDA
                    saida_final.extend(buffer['C185'])
                    saida_final.extend(buffer['C190'])
                else:  # ENTRADA
                    for j, c170 in enumerate(buffer['C170']):
                        saida_final.append(c170)
                        if j < len(buffer['C180']):
                            saida_final.append(buffer['C180'][j])
                    saida_final.extend(buffer['C190'])

                saida_final.extend(buffer['C195'])
                saida_final.extend(buffer['C197'])
                buffer = {k: [] for k in buffer}
            c100_idx = idx
            buffer['C100'].append(conteudo)

        elif reg in buffer:
            buffer[reg].append(conteudo)

        elif reg == 'C990':
            if buffer['C100']:
                tipo_op = tipo_op_map.get(c100_idx, '0')
                saida_final.extend(buffer['C100'])

                if tipo_op == '1':
                    saida_final.extend(buffer['C185'])
                    saida_final.extend(buffer['C190'])
                else:
                    for j, c170 in enumerate(buffer['C170']):
                        saida_final.append(c170)
                        if j < len(buffer['C180']):
                            saida_final.append(buffer['C180'][j])
                    saida_final.extend(buffer['C190'])

                saida_final.extend(buffer['C195'])
                saida_final.extend(buffer['C197'])
                buffer = {k: [] for k in buffer}
            saida_final.append(conteudo)

        elif isinstance(reg, str) and reg.startswith("C"):
            saida_final.append(conteudo)
        else:
            saida_final.append(conteudo)

        if idx % 500 == 0:
            progress.progress((idx + 1) / total, text=f"⏳ Processando linha {idx + 1} de {total}")

    progress.progress(1.0, text="✅ Reestruturação concluída!")

    # Geração do arquivo final
    txt_output = io.BytesIO("".join(saida_final).encode("ISO-8859-1"))
    st.download_button(
        label="📥 Baixar arquivo reestruturado (.txt)",
        data=txt_output,
        file_name="BLOCO_C_REESTRUTURADO.txt",
        mime="text/plain"
    )
