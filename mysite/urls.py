from django.urls import path

from .views import index,history,cari_data,topic_modeling,view_history
urlpatterns = [
    path("",index, name="home"),
    path("history",history, name="history"),
    path("proses",cari_data, name ="proses"),
    path("process_lda",topic_modeling, name ="proseslda"),
    path("lihat-history",view_history,name ="lihat_history")
]