from django.shortcuts import render, redirect
from django_pandas.io import read_frame
from django.conf import settings
from .models import History, HasilLDA, DataBerita
import requests
import numpy as np
import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from gensim import corpora
from gensim.models.ldamodel import LdaModel
from gensim.models.coherencemodel import CoherenceModel
from django.http import JsonResponse
import google.generativeai as genai
import os
import markdown

# Create your views here.
def index(request):
    if request.user.is_authenticated:
        return render(request, "home.html")
    else:
        return redirect("/login")

def history(request):
    # Mengambil semua History untuk user yang sedang login
    histories = History.objects.filter(username=request.user.username).prefetch_related('hasillda_set')
    # Menyiapkan data untuk dikirim ke template
    history_data = []
    for history in histories:
        hasil_lda = history.hasillda_set.first()
        history_data.append({
            'id': history.id,
            'katakunci': history.katakunci,
            'created_at': history.created_at,
            'num_topics': hasil_lda.num_topics if hasil_lda else None,
            'coherence_score': hasil_lda.coherence_score if hasil_lda else None,
        })
    
    context = {
        'history_data': history_data,
    }
    
    return render(request, "history.html", context)

def cari_data(request):
    if request.method == 'POST':
        katakunci = request.POST.get('katakunci')
        history = History(username=request.user.username, katakunci=katakunci)
        history.save()
        databerita = ambil_data(history,katakunci)
        context = {
            'katakunci': katakunci,
            'history_id':history.id,
            'databerita': databerita,
        }
        return render(request, "praprosesing.html", context)
    else:
        return redirect("/")

def ambil_data(history, katakunci):
    # Set the base URL and parameters
    base_url = 'https://api.thenewsapi.com/v1/news/all'
    api_token = settings.THENEWSAPI_TOKEN
    language = 'id'
    search = katakunci
    # Inisialisasi DataFrame untuk menyimpan data
    df = pd.DataFrame()
    # Loop untuk mengambil data sebanyak 100 kali
    for page in range(1, 101):
        # Define the parameters for the request
        params = {
            'api_token': api_token,
            'language': language,
            'search': search,
            'page': page,
        }
        # Kirimkan permintaan dan dapatkan respon
        response = requests.get(base_url, params=params)
        # Konversi respon ke DataFrame pandas dan tambah ke DataFrame utama
        data = response.json()
        df = pd.concat([df, pd.DataFrame(data['data'])], ignore_index=True)
    # Simpan data ke basis data
    data_berita = []
    for index, row in df.iterrows():
        data_berita.append(DataBerita.objects.create(
            id_history=history,
            judul=row['title'],
            url=row['url'],
        ))
    return data_berita

def topic_modeling(request):
    if request.method == 'POST':
        id_history = request.POST.get('id_history')
        keyword = request.POST.get('keyword')
        # Ambil data berita berdasarkan id_history
        data_berita = DataBerita.objects.filter(id_history=id_history)
        # Preprocess the titles
        processed_titles = [preprocess(berita.judul) for berita in data_berita]
        
        # Create dictionary and corpus
        dictionary = corpora.Dictionary(processed_titles)
        corpus = [dictionary.doc2bow(text) for text in processed_titles]
        # Try different number of topics and find the one with the highest coherence score
        max_topics = 10  # Maximum number of topics to try
        best_coherence = float('-inf')
        best_num_topics = 1
        results = {}  # Dictionary to store the results
        for num_topics in range(1, max_topics + 1):
            alpha = 50 / num_topics
            lda_model = LdaModel(corpus, num_topics=num_topics, id2word=dictionary, passes=30, alpha = alpha, eta = 0.01,random_state=42)
            coherence_model_lda = CoherenceModel(model=lda_model, texts=processed_titles, dictionary=dictionary, coherence='c_v')
            coherence_lda = coherence_model_lda.get_coherence()

            # Store the results
            results[num_topics] = {
                'coherence_score': coherence_lda,
                'model': lda_model
            }
            if coherence_lda > best_coherence:
                best_coherence = coherence_lda
                best_num_topics = num_topics

        # Access the LDA model with the best parameters
        best_lda_model = results[best_num_topics]['model']
        best_coherence_model_lda = CoherenceModel(model=best_lda_model, texts=processed_titles, dictionary=dictionary, coherence='c_v')
        best_coherence_lda = best_coherence_model_lda.get_coherence()

        # Print the topics from the best LDA model
        best_topics = best_lda_model.print_topics(num_words=5)

        # Menghitung log perplexity
        log_perplexity = best_lda_model.log_perplexity(corpus)
        # Menghitung eksponensial dari log perplexity
        perplexity_exp = np.exp(-log_perplexity)

        genai.configure(api_key= settings.GENAI_API_KEY )
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Tolong analisis secara jelas hasil LDA ini menggunakan bahasa indonesia :" + str(best_topics) + "Hasil dari pencarian berita dengan kata kunci"+str(keyword)+ "menunjukkan nilai c_v Coherence Score sebesar"+str(best_coherence_lda)+"Berikan kesimpulannya.")
        # Simpan ke model HasilLDA dengan format yang diinginkan
        history_instance = History.objects.get(id=id_history)
        hasil_lda = HasilLDA.objects.create(
            id_history=history_instance,
            num_topics=best_num_topics,
            coherence_score = best_coherence_lda,
            perplexity = perplexity_exp,
            hasil="\n".join([f"Topic {i+1}: {topic}" for i, topic in enumerate(best_topics)]),
            analisis=markdown.markdown(response.text)
        )
        context = {
            'keyword': keyword,
            'data_berita': data_berita,
            'hasil_lda': hasil_lda,
        }
        return render(request, "hasil.html", context)
    
# Preprocess the titles
factory = StemmerFactory()
stop_words = set(stopwords.words('indonesian'))
stemmer = factory.create_stemmer()

def preprocess(title):
    tokens = word_tokenize(title.lower())
    tokens = [word for word in tokens if word.isalnum()]  # Remove punctuation
    tokens = [word for word in tokens if word not in stop_words]  # Remove stopwords
    tokens = [stemmer.stem(word) for word in tokens]  # Stem
    return tokens

def view_history(request):
    id_history = request.POST.get('history_id')
    history = History.objects.get(id=id_history)
    data_berita = DataBerita.objects.filter(id_history=id_history)
    hasil_lda = HasilLDA.objects.get(id_history=id_history)
    katakunci = history.katakunci
    context = {
        'keyword': katakunci,
        'data_berita': data_berita,
        'hasil_lda': hasil_lda,
    }
    return render(request, "hasil.html", context)
