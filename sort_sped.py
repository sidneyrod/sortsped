import streamlit as st
from decimal import Decimal, ROUND_HALF_UP
from tempfile import NamedTemporaryFile

st.set_page_config(page_title="Reestruturador Bloco C - EFD", layout="centered")
st.title("📄 Reestruturador do Bloco C - EFD Contribuições")

# Tema escuro estilizado
st.markdown("""
    <style>
    html, body, [class*="css"]  {
        background-color: #1e1e1e;
        color: #f5f5f5;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #0a84ff;
        color: white;
        font-weight: bold;
        border: none;
        border-radius: 6px;
        padding: 0.5em 1em;
    }
    .stTextInput>div>div>input, .stFileUploader>div>div {
        background-color: #2b2b2b;
        color: white;
    }
    .stRadio>div>div>label, .stMarkdown h1, h2, h3 {
        color: white;
    }
    </style>
""", unsafe_allow_html=True)

def decimal_br(valor):
    return Decimal(valor.replace(",", ".")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def processar_efd_contribuicoes(conteudo):
    linhas = conteudo.splitlines()
    novas_linhas = []
    i = 0
    total = len(linhas)
    progress = st.progress(0.0)

    while i < total:
        linha = linhas[i]

        if linha.startswith("|C100|"):
            grupo_c100 = [linha]
            i += 1

            grupo_c170 = []
            grupo_c180 = []
            registros_auxiliares = []
            outros = []

            # Coletar registros até o próximo C100
            while i < total and not linhas[i].startswith("|C100|"):
                atual = linhas[i]
                if atual.startswith("|C170|"):
                    grupo_c170.append(atual)
                elif atual.startswith("|C180|"):
                    grupo_c180.append(atual)
                elif atual.startswith(("|C190|", "|C195|", "|C197|")):
                    registros_auxiliares.append(atual)
                else:
                    outros.append(atual)
                i += 1

            # Relacionar corretamente C180 com C170
            estrutura = []
            usados_c180 = set()
            for c170 in grupo_c170:
                estrutura.append(c170)
                campos_c170 = c170.split("|")
                try:
                    valor_c170 = decimal_br(campos_c170[7])
                except:
                    continue

                for idx, c180 in enumerate(grupo_c180):
                    if idx in usados_c180:
                        continue
                    campos_c180 = c180.split("|")
                    try:
                        qtd = decimal_br(campos_c180[3])
                        v_unit = decimal_br(campos_c180[5])
                        valor_total = qtd * v_unit
                        if abs(valor_total - valor_c170) <= Decimal("0.01"):
                            estrutura.append(c180)
                            usados_c180.add(idx)
                            break
                    except:
                        continue

            # C180s restantes sem correspondência
            c180_sobras = [grupo_c180[idx] for idx in range(len(grupo_c180)) if idx not in usados_c180]

            # Montar bloco completo na ordem correta
            grupo_c100.extend(estrutura)
            grupo_c100.extend(c180_sobras)
            grupo_c100.extend(outros)
            grupo_c100.extend(registros_auxiliares)
            novas_linhas.extend(grupo_c100)

        else:
            novas_linhas.append(linha)
            i += 1

        progress.progress(min(i / total, 1.0))

    return "\n".join(novas_linhas)

# Upload do arquivo .txt
uploaded_file = st.file_uploader("📤 Envie o arquivo da EFD Contribuições", type=["txt"])

if uploaded_file:
    conteudo = uploaded_file.read().decode("latin1")

    if st.button("🚀 Processar Arquivo"):
        resultado = processar_efd_contribuicoes(conteudo)

        st.success("✅ Processamento concluído!")

        with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="latin1") as f:
            f.write(resultado)
            output_path = f.name

        with open(output_path, "rb") as f:
            st.download_button("📥 Baixar Arquivo Reestruturado", f, file_name="efd_reestruturado.txt")
else:
    st.markdown("ℹ️ Envie o arquivo `.txt` gerado para processamento e reestruturar o Bloco C automaticamente.")

