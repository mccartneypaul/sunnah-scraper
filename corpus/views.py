import logging

from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.

# Set up logging for the corpus app
logger = logging.getLogger('corpus.views.index')

logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(name)s at %(asctime)s (%(levelname)s) :: %(message)s')

# used to direct all logs to the standard error.
sh = logging.StreamHandler()
sh.setFormatter(formatter)

logger.addHandler(sh)

def index(request):
    return HttpResponse("Hello, world. You're at the corpus index.")
