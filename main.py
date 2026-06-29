import os
import time
import requests
import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

PAGE_CSS = """
<style>
:root {
    color-scheme: dark;
}
body {
    background-color: #11131a;
}
section.main {
    background-color: #11131a !important;
}
#MainMenu, footer, header {
    visibility: hidden !important;
    height: 0px !important;
}
.block-container {
    padding-top: 2.5rem;
    padding-left: 2.5rem;
    padding-right: 2.5rem;
    background-color: #11131a;
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
}
.stButton>button {
    width: 100%;
    border-radius: 14px;
    background: linear-gradient(135deg, #8c6d52 0%, #b39f84 100%);
    color: #faf8f2;
    font-size: 1rem;
    font-weight: 700;
    padding: 0.95rem 1rem;
    box-shadow: 0 12px 28px rgba(0, 0, 0, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.08);
}
.stButton>button:hover {
    transform: translateY(-1px);
}
.title-gradient {
    font-size: 2.4rem;
    font-weight: 800;
    background: linear-gradient(90deg, #e7d4b1 0%, #d8c2a2 55%, #f4eccf 100%);
    -webkit-background-clip: text;
    color: transparent;
    margin-bottom: 0.2rem;
}
.subtitle {
    color: #c7c1b0;
    margin-top: 0.35rem;
    line-height: 1.6;
}
.badge-card, .metadata-card {
    border: 1px solid rgba(240, 232, 218, 0.08);
    background: rgba(22, 23, 31, 0.9);
    border-radius: 24px;
    padding: 1.5rem;
    box-shadow: 0 16px 32px rgba(0,0,0,0.16);
}
.badge-card {
    text-align: center;
}
.badge-card .label {
    color: #dac7aa;
    text-transform: uppercase;
    letter-spacing: 0.14em;
    font-size: 0.75rem;
    margin-bottom: 0.7rem;
}
.badge-card .value {
    font-size: 2.2rem;
    font-weight: 800;
    color: #f8f4ec;
}
.metadata-card {
    display: flex;
    gap: 1rem;
    margin-top: 1.4rem;
    flex-wrap: wrap;
}
.metadata-item {
    flex: 1;
    min-width: 200px;
    border-radius: 24px;
    background: rgba(35, 34, 41, 0.92);
    padding: 1.2rem;
}
.metadata-label {
    color: #d8c7ad;
    font-size: 0.8rem;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.55rem;
}
.metadata-value {
    color: #f8f4ec;
    font-size: 1.05rem;
    font-weight: 700;
}
.metadata-value.monospace {
    font-family: 'Courier New', Courier, monospace;
}
.stSelectbox>div>div>div>div {
    border-radius: 22px;
    background: rgba(26, 27, 33, 0.95);
}
.stSelectbox>div>div>div>div>div {
    background: rgba(255, 255, 255, 0.04) !important;
    color: #f8f4ec !important;
}
.stSelectbox>label {
    color: #c7c1b0;
}
.stSelectbox span,
.stSelectbox div {
    color: #f8f4ec !important;
}
.css-1cpxqw2 {
    background: rgba(255,255,255,0.03) !important;
}
.css-cio0dv {
    background: rgba(255,255,255,0.03) !important;
}
</style>
"""

st.set_page_config(
    page_title="Monitor de Instabilidade NFSe",
    page_icon="📊",
    layout="wide"
)
st.markdown(PAGE_CSS, unsafe_allow_html=True)

EXPECTED_COLUMNS = [
    "UF",
    "Cidade",
    "Provedor",
    "Integração",
    "URL Produção",
    "URL Homologação"
]

DB_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS contador_ajuda (
    id INT PRIMARY KEY,
    total INT NOT NULL DEFAULT 0
);
"""


def get_db_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise EnvironmentError("A variável DATABASE_URL não está configurada no ambiente Railway.")

    try:
        connection = psycopg2.connect(database_url, sslmode="require", cursor_factory=RealDictCursor)
        return connection
    except Exception as exc:
        raise ConnectionError(f"Falha ao conectar ao PostgreSQL: {exc}") from exc


def ensure_counter_table():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(DB_TABLE_SQL)
            cursor.execute(
                "INSERT INTO contador_ajuda (id, total) VALUES (1, 0) ON CONFLICT (id) DO NOTHING;"
            )
            conn.commit()


def get_help_count():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT total FROM contador_ajuda WHERE id = 1;")
            row = cursor.fetchone()
            return row["total"] if row else 0


def increment_help_count():
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE contador_ajuda SET total = total + 1 WHERE id = 1;")
            conn.commit()


def testar_endpoint(url):
    if pd.isna(url) or not str(url).strip().startswith("http"):
        return "erro", "Link inválido ou em branco na planilha."

    url_final = str(url).strip()
    if "?wsdl" not in url_final.lower():
        url_final = f"{url_final}?wsdl"

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Accept": "text/xml, text/html"
    }

    inicio = time.time()
    try:
        resposta = requests.get(url_final, headers=headers, timeout=10, verify=True)
        tempo = round(time.time() - inicio, 2)

        if resposta.status_code == 200:
            return "online", f"✅ ONLINE | Servidor respondeu com sucesso em {tempo}s (Status 200 OK)."
        return "instavel", f"⚠️ INSTÁVEL | O servidor respondeu, mas retornou Erro HTTP {resposta.status_code} em {tempo}s."

    except requests.exceptions.Timeout:
        return "caido", "❌ FORA DO AR | Erro: TIMEOUT (O servidor demorou mais de 10 segundos para responder)."
    except requests.exceptions.ConnectionError:
        return "caido", "❌ FORA DO AR | Erro: FALHA DE CONEXÃO (Não foi possível estabelecer contato com o servidor)."
    except Exception as exc:
        return "erro", f"❌ ERRO DESCONHECIDO | Detalhes: {exc}"


def load_prefeitura_data(nome_arquivo):
    if not os.path.exists(nome_arquivo):
        raise FileNotFoundError(f"O arquivo '{nome_arquivo}' não foi encontrado no diretório atual.")

    df = pd.read_excel(nome_arquivo, engine="openpyxl")
    df.columns = [c.strip() for c in df.columns]

    missing_columns = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing_columns:
        raise ValueError(
            f"A planilha precisa conter as colunas exatas: {', '.join(EXPECTED_COLUMNS)}. Colunas ausentes: {', '.join(missing_columns)}"
        )

    df = df[EXPECTED_COLUMNS].copy()
    df["UF"] = df["UF"].astype(str).str.strip().str.upper()
    df["Cidade"] = df["Cidade"].astype(str).str.strip()
    return df


def render_header(contador_global):
    col_title, col_badge = st.columns([3, 1], gap="large")

    with col_title:
        st.markdown("<div class='title-gradient'>Monitor de Instabilidade NFSe</div>", unsafe_allow_html=True)
        st.markdown("<div class='subtitle'>Este código é um monitor web que testa se o sistema de Nota Fiscal (NFSe) de uma cidade está online, fazendo um teste rápido de conexão (ping) na URL do servidor.

O detalhe importante: A resposta do teste nem sempre reflete a realidade do sistema como um todo. Se o teste der erro, pode ser apenas uma instabilidade momentânea na rota da internet ou um bloqueio de segurança no servidor, e não necessariamente significa que a emissão de notas está completamente fora do ar para todo mundo. O monitor serve como um indicativo rápido, mas não é uma verdade absoluta.</div>", unsafe_allow_html=True)

    with col_badge:
        if st.button("Me ajudou 👍", key="me_ajudou"):
            try:
                increment_help_count()
            except Exception as exc:
                st.error(f"Não foi possível atualizar o contador: {exc}")

        st.markdown(
            "<div class='badge-card'>"
            "<div class='label'>Contador</div>"
            f"<div class='value'>{get_help_count()}</div>"
            "<div class='label' style='margin-top: 0.8rem;'>De quantas pessoas foram ajudadas</div>"
            "</div>",
            unsafe_allow_html=True,
        )


def render_metadata_card(linha):
    st.markdown(
        "<div class='metadata-card'>"
        "<div class='metadata-item'>"
        "<div class='metadata-label'>Provedor de Tecnologia</div>"
        f"<div class='metadata-value'>{linha['Provedor']}</div>"
        "</div>"
        "<div class='metadata-item'>"
        "<div class='metadata-label'>Modelo de Integração</div>"
        f"<div class='metadata-value monospace'>{linha['Integração']}</div>"
        "</div>"
        "<div class='metadata-item'>"
        "<div class='metadata-label'>Região Fiscal</div>"
        f"<div class='metadata-value'>{linha['UF']}</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def main():
    try:
        ensure_counter_table()
        contador_global = get_help_count()
    except Exception as exc:
        st.error(f"Erro de persistência no banco de dados: {exc}")
        return

    st.sidebar.markdown("<div style='padding: 1rem; color: #9aa7d1;'>Railway PostgreSQL conectado via DATABASE_URL</div>", unsafe_allow_html=True)

    df = load_prefeitura_data("prefeituras.xlsx")

    render_header(contador_global)

    st.markdown("---")

    uf_col, cidade_col = st.columns(2, gap="large")
    with uf_col:
        uf_escolhida = st.selectbox("Selecione a UF", sorted(df["UF"].unique()))

    with cidade_col:
        cidades_disponiveis = sorted(df[df["UF"] == uf_escolhida]["Cidade"].unique())
        cidade_escolhida = st.selectbox("Selecione a Cidade", cidades_disponiveis)

    linha_cidade = df[(df["UF"] == uf_escolhida) & (df["Cidade"] == cidade_escolhida)].iloc[0]

    render_metadata_card(linha_cidade)

    st.markdown("---")

    if st.button("🚀 Executar Teste de Conectividade", key="run_connectivity_test"):
        with st.spinner("Executando verificação de conectividade no WebService..."):
            status, mensagem = testar_endpoint(linha_cidade["URL Produção"])
            if status == "online":
                st.success(mensagem)
            elif status == "instavel":
                st.warning(mensagem)
            else:
                st.error(mensagem)


if __name__ == "__main__":
    main()
