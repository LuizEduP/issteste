import requests
import time
import os

def verificar_prefeitura(nome_cidade, url):
    headers = {'User-Agent': 'MonitorNFSe/1.0', 'Accept': 'text/xml, text/html'}
    url_teste = f"{url}?wsdl" if not url.endswith("?wsdl") else url
    inicio = time.time()
    
    try:
        resposta = requests.get(url_teste, headers=headers, timeout=12, verify=True)
        tempo_resposta = round(time.time() - inicio, 2)
        if resposta.status_code == 200:
            print(f"✅ ONLINE | {nome_cidade} respondeu em {tempo_resposta}s.")
        else:
            print(f"⚠️ INSTÁVEL | {nome_cidade} retornou HTTP {resposta.status_code} em {tempo_resposta}s.")
    except requests.exceptions.Timeout:
        print(f"❌ FORA DO AR (TIMEOUT) | O servidor de {nome_cidade} travou.")
    except Exception as e:
        print(f"❌ ERRO | Falha ao conectar em {nome_cidade}. Detalhe: {e}")

if __name__ == "__main__":
    endpoints = {
        "Brasília - DF (ISSNet Produção)": "https://df.issnetonline.com.br/webservicenfse204/nfse.asmx",
        "Brasília - DF (ISSNet Homologação)": "https://www.issnetonline.com.br/homologaabrasf/webservicenfse204/nfse.asmx"
    }
    print("=== INICIANDO VERIFICAÇÃO DE INSTABILIDADE ===")
    for cidade, url in endpoints.items():
        verificar_prefeitura(cidade, url)