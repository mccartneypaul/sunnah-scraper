from django.db import models

class Collection(models.Model):
    """Represents a collection of hadith (e.g., Sahih Bukhari, Muslim, etc.)."""
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

class Language(models.Model):
    """Represents a language taken from ISO 639-1 standard."""
    id = models.AutoField(primary_key=True)
    name = models.TextField()
    iso_two_code = models.CharField(max_length=2)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return self.name

class Snapshot(models.Model):
    """Represents a point-in-time snapshot from when the hadith data was archived."""
    id = models.AutoField(primary_key=True)
    taken_on = models.DateTimeField()
    source = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"Snapshot taken on {self.taken_on} from {self.source}"
    
class Hadith(models.Model):
    """Represents a single hadith (Islamic tradition/narration) with its metadata."""
    id = models.AutoField(primary_key=True)
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    language = models.ForeignKey(Language, on_delete=models.CASCADE)
    snapshot = models.ForeignKey(Snapshot, on_delete=models.CASCADE)
    reference_number = models.IntegerField()
    in_book_reference = models.TextField()
    narrator = models.TextField()
    text = models.TextField()
    grade = models.TextField()
    link = models.TextField()
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self):
        return f"{self.collection.name} - Hadith {self.reference_number} - Snapshot {self.snapshot.source} {self.snapshot.taken_on.date().isoformat()}"
    class Meta:
        unique_together = ('collection', 'reference_number', 'snapshot', 'language')
