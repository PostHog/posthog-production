# Generated by Django 3.0.7 on 2020-08-30 21:45

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='UserMessagingRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('campaign', models.CharField(max_length=64)),
                ('sent_at', models.DateTimeField(choices=[('no_event_ingestion_follow_up', 'No Event Ingestion Follow-Up')], default=None, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='messaging_records', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('user', 'campaign')},
            },
        ),
    ]
