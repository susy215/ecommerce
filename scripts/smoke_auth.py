import os, sys, pathlib
BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
# Allow test client host
os.environ.setdefault('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,testserver')

import django
django.setup()

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()

username = 'cliente1'
email = 'cliente1@example.com'
password = 'Passw0rd!123'

u, created = User.objects.get_or_create(username=username, defaults={'email': email, 'rol': 'cliente'})
if created:
    u.set_password(password)
    u.save()

client = APIClient()
url = '/api/usuarios/token/'
print('Posting JSON username...')
res = client.post(url, {'username': username, 'password': password}, format='json')
print('status:', res.status_code, 'body:', res.content)

print('Posting email...')
res2 = client.post(url, {'email': email, 'password': password}, format='json')
print('status:', res2.status_code, 'body:', res2.content)
