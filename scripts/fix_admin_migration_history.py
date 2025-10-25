import os
import sys
import pathlib
import django

BASE_DIR = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.db import connection

with connection.cursor() as cursor:
    cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app = %s", ['admin'])
    (count_before,) = cursor.fetchone()
    cursor.execute("DELETE FROM django_migrations WHERE app = %s", ['admin'])
    connection.commit()
    cursor.execute("SELECT COUNT(*) FROM django_migrations WHERE app = %s", ['admin'])
    (count_after,) = cursor.fetchone()

print(f"Deleted {count_before - count_after} admin migration records (before={count_before}, after={count_after}).")
