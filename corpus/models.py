from django.db import models

# Create your models here.
class Hadith(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

