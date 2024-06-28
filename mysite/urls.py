from django.urls import path

from .views import index,history,proses,topic_modeling,view_history
urlpatterns = [
    path("",index, name="home"),
    path("history",history, name="history"),
    path("proses",proses, name ="proses"),
    path("process_lda",topic_modeling, name ="proseslda"),
    path("lihat-history",view_history,name ="lihat_history")
]