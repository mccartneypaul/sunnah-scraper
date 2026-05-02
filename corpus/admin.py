from django.contrib import admin
from .models import Collection, Hadith, Language, Snapshot

admin.site.register(Hadith)
admin.site.register(Collection)
admin.site.register(Language)
admin.site.register(Snapshot)
