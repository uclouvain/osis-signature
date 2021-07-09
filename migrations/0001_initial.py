# Generated by Django 2.2.13 on 2021-06-18 12:09

from django.db import migrations, models
import django.db.models.deletion
import osis_document.contrib.fields
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('base', '0587_auto_20210603_1411'),
    ]

    operations = [
        migrations.CreateModel(
            name='Actor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(blank=True, db_index=True, default='', max_length=50, verbose_name='First name')),
                ('last_name', models.CharField(blank=True, default='', max_length=50, verbose_name='Last name')),
                ('email', models.EmailField(blank=True, default='', max_length=255, verbose_name='E-mail')),
                ('language', models.CharField(blank=True, choices=[('fr-be', 'French'), ('en', 'English')], max_length=30, null=True, verbose_name='Language')),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name='Birth date')),
                ('pdf_file', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=1, verbose_name='PDF file')),
                ('comment', models.TextField(blank=True, default='', verbose_name='Comment')),
                ('person', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='base.Person', verbose_name='Person')),
            ],
            options={
                'verbose_name': 'Actor',
            },
        ),
        migrations.CreateModel(
            name='Process',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
            ],
            options={
                'verbose_name': 'Process',
                'verbose_name_plural': 'Processes',
            },
        ),
        migrations.CreateModel(
            name='StateHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state', models.CharField(choices=[('NOT_INVITED', 'Not yet invited'), ('INVITED', 'Invited to signed'), ('APPROVED', 'Approved'), ('DECLINED', 'Declined')], max_length=30, verbose_name='State')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date')),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='states', to='osis_signature.Actor', verbose_name='Actor')),
            ],
            options={
                'verbose_name': 'State history entry',
                'verbose_name_plural': 'State history entries',
                'ordering': ('created_at',),
            },
        ),
        migrations.AddField(
            model_name='actor',
            name='process',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='osis_signature.Process', verbose_name='Signature process', related_name='actors'),
        ),
        migrations.AddConstraint(
            model_name='actor',
            constraint=models.CheckConstraint(check=models.Q(models.Q(models.Q(('birth_date__isnull', True), ('email', ''), ('first_name', ''), ('language__isnull', True), ('last_name', '')), ('person__isnull', True), _connector='OR'), models.Q(('birth_date__isnull', True), ('email', ''), ('first_name', ''), ('language__isnull', True), ('last_name', ''), ('person__isnull', True), _negated=True)), name='external_xor_person'),
        ),
    ]
