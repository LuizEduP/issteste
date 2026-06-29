import streamlit as st
import pandas as pd
import requests
import time

# Configuração da página da Web
st.set_page_config(page_title="Monitor de Instabilidade NFSe", page_icon="📊", layout="centered")

st.title("📊 Monitor de Instabilidade NFSe")

col_main, col_help = st.columns([3, 1])
with col_main:
    st.markdown("Selecione o estado e a cidade para testar a comunicação com o WebService da prefeitura em tempo real.")

with col_help:
    if "ajudou_count" not in st.session_state:
        st.session_state.ajudou_count = 0

    st.markdown("### Me ajudou")
    if st.button("Me ajudou"):
        st.session_state.ajudou_count += 1
    st.metric("Pessoas ajudadas", st.session_state.ajudou_count)

# Função de teste de conexão
def testar_endpoint(url):
    if pd.isna(url) or not str(url).strip().startswith("http"):
        return "erro", "Link inválido ou em branco na planilha."
        
    url_final = str(url).strip()
    if "?wsdl" not in url_final.lower():
        url_final = f"{url_final}?wsdl"
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'text/xml, text/html'
    }
    
    inicio = time.time()
    try:
        resposta = requests.get(url_final, headers=headers, timeout=10, verify=True)
        tempo = round(time.time() - inicio, 2)
        
        if resposta.status_code == 200:
            return "online", f"✅ ONLINE | Servidor respondeu com sucesso em {tempo}s (Status 200 OK)."
        else:
            return "instavel", f"⚠️ INSTÁVEL | O servidor respondeu, mas retornou Erro HTTP {resposta.status_code} em {tempo}s."
            
    except requests.exceptions.Timeout:
        return "caido", "❌ FORA DO AR | Erro: TIMEOUT (O servidor demorou mais de 10 segundos para responder)."
    except requests.exceptions.ConnectionError:
        return "caido", "❌ FORA DO AR | Erro: FALHA DE CONEXÃO (Não foi possível estabelecer contato com o servidor)."
    except Exception as e:
        return "erro", f"❌ ERRO DESCONHECIDO | Detalhes: {e}"

# Carregar a planilha
nome_arquivo = "prefeituras.xlsx"
try:
    df = pd.read_excel(nome_arquivo)
    df.columns = [c.strip() for c in df.columns]
    df['UF'] = df['UF'].astype(str).str.strip().str.upper()
    df['Cidade'] = df['Cidade'].astype(str).str.strip()

    # --- INTERFACE DO USUÁRIO ---
    
    # 1. Seleção de UF
    ufs_disponiveis = sorted(df['UF'].unique())
    uf_escolhida = st.selectbox("1. Selecione a UF:", ufs_disponiveis)

    # Filtrar cidades pela UF escolhida
    df_filtrado = df[df['UF'] == uf_escolhida]
    cidades_disponiveis = sorted(df_filtrado['Cidade'].unique())
    
    # 2. Seleção de Cidade
    cidade_escolhida = st.selectbox("2. Selecione a Cidade:", cidades_disponiveis)

    # Buscar dados da cidade selecionada
    linha_cidade = df_filtrado[df_filtrado['Cidade'] == cidade_escolhida].iloc[0]
    
    # Mostrar informações do provedor na tela
    st.info(f"**Provedor:** {linha_cidade['Provedor']} | **Integração:** {linha_cidade['Integração']}")

    # 3. Botão de Testar
    if st.button("🚀 Testar Conexão Agora", use_container_width=True):
        with st.spinner("Conectando ao WebService da prefeitura... Aguarde."):
            status, mensagem = testar_endpoint(linha_cidade['URL Produção'])
            
            # Exibir alertas baseados no resultado técnico
            if status == "online":
                st.success(mensagem)
            elif status == "instavel":
                st.warning(mensagem)
            else:
                st.error(mensagem)

except FileNotFoundError:
    st.error(f"Erro: O arquivo '{nome_arquivo}' não foi encontrado. Certifique-se de que ele foi enviado ao repositório.")
except Exception as e:
    st.error(f"Erro ao processar os dados: {e}")