# Generated by Django 2.2.13 on 2021-07-08 16:44

from django.db import migrations, models
import django.db.models.deletion
import osis_signature.contrib.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('osis_signature', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SpecialActor',
            fields=[
                ('actor_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='osis_signature.Actor')),
                ('civility', models.CharField(choices=[('mr', 'M.'), ('mme', 'Mme')], max_length=30)),
            ],
            bases=('osis_signature.actor',),
        ),
        migrations.CreateModel(
            name='SimpleModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('jury', osis_signature.contrib.fields.SignatureProcessField(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='osis_signature.Process')),
            ],
        ),
        migrations.CreateModel(
            name='DoubleModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('jury', osis_signature.contrib.fields.SignatureProcessField(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='osis_signature.Process')),
                ('special_jury', osis_signature.contrib.fields.SignatureProcessField(editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='osis_signature.Process')),
            ],
        ),
    ]
