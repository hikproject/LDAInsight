from django.shortcuts import render, redirect
from django_pandas.io import read_frame
from .models import History, HasilLDA, DataBerita
import requests
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
    histories = History.objects.filter(user_id=request.user.id)
    context = {'histories': histories}
    return render(request, "history.html", context)

def proses(request):
    if request.method == 'POST':
        katakunci = request.POST.get('katakunci')
        history = History(user_id=request.user.id, katakunci=katakunci)
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
    api_token = 'AOFwVOaQHYhU0tf3RhAIyD8JYt4N3YohhCox5Ytm'
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
        stop_words = set(stopwords.words('indonesian'))
        factory = StemmerFactory()
        stemmer = factory.create_stemmer()
        processed_titles = [preprocess(berita.judul) for berita in data_berita]
        
        # Create dictionary and corpus
        dictionary = corpora.Dictionary(processed_titles)
        corpus = [dictionary.doc2bow(text) for text in processed_titles]
        # Try different number of topics and find the one with the highest coherence score
        max_topics = 20  # Maximum number of topics to try
        best_coherence = -1
        best_num_topics = 1

        for num_topics in range(1, max_topics + 1):
            lda_model = LdaModel(corpus, num_topics=num_topics, id2word=dictionary, passes=10)
            coherence_model_lda = CoherenceModel(model=lda_model, texts=processed_titles, dictionary=dictionary, coherence='c_v')
            coherence_lda = coherence_model_lda.get_coherence()

            if coherence_lda > best_coherence:
                best_coherence = coherence_lda
                best_num_topics = num_topics

        # Train LDA model with the best number of topics
        lda_model = LdaModel(corpus, num_topics=best_num_topics, id2word=dictionary, passes=10)

        # Return the topics and coherence score via AJAX
        topics = lda_model.print_topics(num_words=5)
        genai.configure(api_key="AIzaSyAW7cMj9RA0jWDq1oS1bkfrkLtV0Ltc2S8")
        model = genai.GenerativeModel('gemini-1.5-flash')
        response = model.generate_content("Tolong analisis secara jelas hasil lda ini menggunakan bahasa indonesia" + str(topics) + "yang dimana hasil dari pencarian berita dengan kata kunci"+str(keyword)+ "dengan Coherence Score sebesar"+str(best_coherence)+"dan beri saya kesimpulannya")
        # Simpan ke model HasilLDA dengan format yang diinginkan
        history_instance = History.objects.get(id=id_history)
        hasil_lda = HasilLDA.objects.create(
            id_history=history_instance,
            num_topics=best_num_topics,
            coherence_score = best_coherence,
            hasil="\n".join([f"Topic {i+1}: {topic}" for i, topic in enumerate(topics)]),
            analisis=markdown.markdown(response.text)
        )
        context = {
            'keyword': keyword,
            'data_berita': data_berita,
            'hasil_lda': hasil_lda,
        }
        return render(request, "hasil.html", context)
    
def preprocess(title):
    # Preprocess the titles
    factory = StemmerFactory()
    stop_words = set(stopwords.words('indonesian'))
    stemmer = factory.create_stemmer()
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
