import requests
from bs4 import BeautifulSoup
import spacy
from facebook import GraphAPI
from googletrans import Translator
from datetime import datetime
import logging
import time

# Configurações
FACEBOOK_ACCESS_TOKEN = 'YOUR_FACEBOOK_ACCESS_TOKEN'  # Coloque seu token de acesso seguro aqui
SEARCH_QUERIES = [
    'https://news.google.com/rss/search?q=tijolo+ecológico',
    'https://news.google.com/rss/search?q=construção+sustentável'
]
POST_LIMIT = 3
START_HOUR = 9  # Horário de início da automação
END_HOUR = 18   # Horário de fim da automação

# Configuração de logging
logging.basicConfig(level=logging.INFO)

# Função para buscar notícias
def buscar_noticias():
    noticias = []
    for url in SEARCH_QUERIES:
        try:
            response = requests.get(url)
            response.raise_for_status()  # Garante que um erro HTTP seja gerado em caso de falha
            soup = BeautifulSoup(response.content, 'lxml-xml')
            items = soup.find_all('item')
            for item in items:
                noticia = {
                    'title': item.title.text,
                    'url': item.link.text
                }
                noticias.append(noticia)
        except requests.RequestException as e:
            logging.error(f"Erro ao buscar notícias: {e}")
    return noticias

# Função para resumir texto
def resumir_texto(texto, num_sentences=5):
    nlp = spacy.load('pt_core_news_sm')
    doc = nlp(texto)
    resumo = ' '.join([sent.text for sent in doc.sents][:num_sentences])  # Limita o resumo a 5 frases
    return resumo

# Função para traduzir texto
def traduzir_texto(texto, destino='pt'):
    try:
        translator = Translator()
        traducao = translator.translate(texto, dest=destino)
        return traducao.text
    except Exception as e:
        logging.error(f"Erro ao traduzir texto: {e}")
        return texto  # Retorna o texto original em caso de erro

# Função para postar no Facebook
def postar_no_facebook(mensagem):
    try:
        graph = GraphAPI(access_token=FACEBOOK_ACCESS_TOKEN)
        graph.put_object(parent_object='me', connection_name='feed', message=mensagem)
        logging.info("Postagem realizada com sucesso!")
    except Exception as e:
        logging.error(f"Erro ao postar no Facebook: {e}")

# Automação
def automacao():
    logging.info("Buscando notícias...")
    noticias = buscar_noticias()
    logging.info(f"Encontradas {len(noticias)} notícias.")
    post_count = 0
    for noticia in noticias:
        if post_count >= POST_LIMIT:
            break
        titulo = noticia['title']
        url = noticia['url']
        logging.info(f"Processando notícia: {titulo}")
        
        # Obtendo o conteúdo da notícia
        try:
            conteudo = requests.get(url).text
            soup = BeautifulSoup(conteudo, 'html.parser')
            texto = soup.get_text()
            resumo = resumir_texto(texto)
            
            # Traduzindo o resumo, se necessário
            if not texto.startswith('pt'):
                resumo = traduzir_texto(resumo)
            
            # Criando a mensagem para postagem
            mensagem = f'{titulo}\n\n{resumo}\n\nLeia mais: {url}'
            logging.info(f"Postando no Facebook: {mensagem}")
            postar_no_facebook(mensagem)
            post_count += 1
        except Exception as e:
            logging.error(f"Erro ao processar a notícia {titulo}: {e}")

    logging.info("Automação concluída.")

# Verifica se está no horário comercial (9h às 18h)
current_hour = datetime.now().hour
if START_HOUR <= current_hour < END_HOUR:
    automacao()
else:
    logging.info("Fora do horário comercial. A automação não será executada.")
