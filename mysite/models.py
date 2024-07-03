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
    username = models.CharField(max_length=255,default='default_username')
    katakunci = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
<<<<<<< HEAD
        return f"{self.user_id} - {self.katakunci}"
=======
        return f"{self.username} - {self.katakunci}"
>>>>>>> dev
    
class HasilLDA(models.Model):
    id = models.AutoField(primary_key=True)
    id_history = models.ForeignKey('History', on_delete=models.CASCADE)
    num_topics = models.IntegerField()
    coherence_score = models.DecimalField(max_digits=10, decimal_places=2)
    hasil = models.TextField()
    analisis = models.TextField()
    
    def __str__(self):
        return f"Hasil LDA untuk {self.id_history.katakunci}"
