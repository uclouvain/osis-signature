# Generated by Django 2.2.13 on 2021-06-16 16:32

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
                ('first_name', models.CharField(blank=True, db_index=True, max_length=50, null=True, verbose_name='First name')),
                ('last_name', models.CharField(blank=True, max_length=50, null=True, verbose_name='Last name')),
                ('email', models.EmailField(max_length=255, null=True, verbose_name='E-mail')),
                ('language', models.CharField(choices=[('fr-be', 'French'), ('en', 'English')], default='fr-be', max_length=30, null=True, verbose_name='Language')),
                ('birth_date', models.DateField(blank=True, null=True, verbose_name='Birth date')),
                ('pdf_file', osis_document.contrib.fields.FileField(base_field=models.UUIDField(), default=list, size=1, verbose_name='PDF file')),
                ('state', models.CharField(choices=[('NOT_INVITED', 'Not yet invited'), ('INVITED', 'Invited to signed'), ('APPROVED', 'Approved'), ('DECLINED', 'Declined')], default='NOT_INVITED', max_length=30, verbose_name='State')),
                ('comment', models.TextField(default='', verbose_name='Comment')),
                ('person', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='base.Person', verbose_name='Person')),
            ],
            options={
                'verbose_name': 'Actor',
            },
        ),
        migrations.CreateModel(
            name='Process',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('field_ref', models.CharField(editable=False, max_length=150, verbose_name='Field reference')),
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
                ('state', models.CharField(choices=[('NOT_INVITED', 'Not yet invited'), ('INVITED', 'Invited to signed'), ('APPROVED', 'Approved'), ('DECLINED', 'Declined')], default='NOT_INVITED', max_length=30, verbose_name='State')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Date')),
                ('actor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='osis_signature.Actor', verbose_name='Actor')),
            ],
            options={
                'verbose_name': 'State history entry',
                'verbose_name_plural': 'State history entries',
            },
        ),
        migrations.AddField(
            model_name='actor',
            name='process',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='osis_signature.Process', verbose_name='Signature process'),
        ),
        migrations.AddConstraint(
            model_name='actor',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('email__isnull', True), ('person__isnull', True), _connector='OR'), models.Q(('email__isnull', True), ('person__isnull', True), _negated=True)), name='email_xor_person'),
        ),
    ]
