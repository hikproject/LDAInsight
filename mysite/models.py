from django.db import models

# Create your models here.
class DataBerita(models.Model):
    id = models.AutoField(primary_key=True)
    id_history = models.ForeignKey('History', on_delete=models.CASCADE)
    judul = models.CharField(max_length=255)
    url = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.judul

class History(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    katakunci = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.id} - {self.katakunci}"
    
class HasilLDA(models.Model):
    id = models.AutoField(primary_key=True)
    id_history = models.ForeignKey('History', on_delete=models.CASCADE)
    num_topics = models.IntegerField()
    coherence_score = models.IntegerField()
    hasil = models.TextField()
    analisis = models.TextField()
    
    def __str__(self):
        return f"Hasil LDA untuk {self.id_history.katakunci}"
