# Generated by Django 5.0.6 on 2024-06-27 04:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mysite', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='databerita',
            old_name='role',
            new_name='judul',
        ),
        migrations.RenameField(
            model_name='databerita',
            old_name='username',
            new_name='url',
        ),
    ]
