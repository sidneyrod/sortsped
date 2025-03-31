import pandas as pd
import streamlit as st
import io

st.set_page_config(page_title="Reestruturador Bloco C - EFD 2020", layout="centered")
st.title("📄 Reestruturador do Bloco C (EFD Contribuições - Leiaute 2020)")
st.markdown("Reestrutura os registros C170, C180, C185 conforme o tipo de nota fiscal (entrada ou saída).")

uploaded_file = st.file_uploader("📤 Envie seu arquivo BLOCO C (.csv ou .txt)", type=["csv", "txt"])
formato_saida = st.radio("📦 Formato de saída desejado:", ["CSV", "TXT"])

if uploaded_file:
    progress = st.progress(0, text="🔄 Carregando dados...")

    if uploaded_file.name.endswith(".txt"):
        df_raw = pd.read_csv(uploaded_file, header=None, dtype=str, sep="\n", engine="python")
        df_raw.columns = ['Conteudo']
        df_raw['Registro'] = df_raw['Conteudo'].str.extract(r'\|(C\d{3})\|')
        df_raw['Nota'] = df_raw['Conteudo'].str.extract(r'\|C100\|(\d+)')
        df_raw['Nota'] = df_raw['Nota'].fillna(method='ffill')
        df = df_raw[['Nota', 'Registro', 'Conteudo']].copy()
    else:
        df = pd.read_csv(uploaded_file, header=None, dtype=str, low_memory=False)
        df = df[[0, 14, 13]]
        df.columns = ['Nota', 'Registro', 'Conteudo']

    df['Nota'] = pd.to_numeric(df['Nota'], errors='coerce')
    df = df.dropna(subset=['Nota']).reset_index(drop=True)

    progress.progress(0.1, text="🔍 Identificando tipo de operação por nota...")

    df_c100 = df[df['Registro'] == 'C100'].copy()
    df_c100['Tipo_Operacao'] = df_c100['Conteudo'].str.split('|').str[2]
    mapa_operacao = df_c100.set_index('Nota')['Tipo_Operacao'].to_dict()

    progress.progress(0.2, text="🔧 Reestruturando registros...")

    saida_final = []
    nota_atual = None
    buffer = {
        'C100': [],
        'C170': [],
        'C180': [],
        'C185': [],
        'C190': [],
        'C195': [],
        'C197': []
    }

    def descarregar_bloco_formatado(saida_final, buffer, tipo_op):
        saida_final.extend(buffer['C100'])
        for i, c170 in enumerate(buffer['C170']):
            saida_final.append(c170)
            if tipo_op == '0' and i < len(buffer['C180']):
                saida_final.append(buffer['C180'][i])
            elif tipo_op == '1' and i < len(buffer['C185']):
                saida_final.append(buffer['C185'][i])
        saida_final.extend(buffer['C190'])
        saida_final.extend(buffer['C195'])
        saida_final.extend(buffer['C197'])

    total_linhas = len(df)

    for idx, row in df.iterrows():
        nota = int(row['Nota'])
        reg = row['Registro']
        conteudo = row['Conteudo']

        if reg == 'C100':
            if buffer['C100']:
                tipo_op = mapa_operacao.get(nota_atual, '0')
                descarregar_bloco_formatado(saida_final, buffer, tipo_op)
                buffer = {k: [] for k in buffer}
            nota_atual = nota
            buffer['C100'].append(conteudo)

        elif reg in buffer:
            buffer[reg].append(conteudo)

        if idx % 500 == 0:
            progress.progress(min((idx + 1) / total_linhas, 1.0), text=f"⏳ Processando linha {idx + 1} de {total_linhas}")

    if buffer['C100']:
        tipo_op = mapa_operacao.get(nota_atual, '0')
        descarregar_bloco_formatado(saida_final, buffer, tipo_op)

    progress.progress(1.0, text="✅ Reestruturação concluída!")

    if formato_saida == "CSV":
        csv_str = pd.DataFrame({'Conteudo': saida_final}).to_csv(index=False, header=False)
        csv_bytes = io.BytesIO(csv_str.encode("utf-8"))
        st.download_button(
            label="📥 Baixar arquivo reestruturado (.csv)",
            data=csv_bytes,
            file_name="BLOCO_C_REESTRUTURADO.csv",
            mime="text/csv"
        )

    elif formato_saida == "TXT":
        txt_str = "\n".join(saida_final)
        txt_bytes = io.BytesIO(txt_str.encode("utf-8"))
        st.download_button(
            label="📥 Baixar arquivo reestruturado (.txt)",
            data=txt_bytes,
            file_name="BLOCO_C_REESTRUTURADO.txt",
            mime="text/plain"
        )
