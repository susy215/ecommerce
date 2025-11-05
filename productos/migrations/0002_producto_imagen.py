# Generated manually for adding imagen field to Producto

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('productos', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='producto',
            name='imagen',
            field=models.ImageField(blank=True, help_text='Imagen del producto (se optimizará automáticamente)', null=True, upload_to='productos/'),
        ),
    ]

