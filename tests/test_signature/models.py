# ##############################################################################
#
#    OSIS stands for Open Student Information System. It's an application
#    designed to manage the core business of higher education institutions,
#    such as universities, faculties, institutes and professional schools.
#    The core business involves the administration of students, teachers,
#    courses, programs and so on.
#
#    Copyright (C) 2015-2021 Université catholique de Louvain (http://www.uclouvain.be)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of this license - GNU General Public License - is available
#    at the root of the source code of this program.  If not,
#    see http://www.gnu.org/licenses/.
#
# ##############################################################################

from django.db import models
from django.shortcuts import resolve_url

from osis_signature.models import Actor
from osis_signature.contrib.fields import SignatureProcessField


class SimpleModel(models.Model):
    title = models.CharField(max_length=200)
    jury = SignatureProcessField(related_name='+')

    def get_absolute_url(self):
        return resolve_url('simple-detail', pk=self.pk)


class DoubleModel(models.Model):
    title = models.CharField(max_length=200)
    jury = SignatureProcessField(related_name='+')
    special_jury = SignatureProcessField(related_name='+')


class SpecialActor(Actor):
    civility = models.CharField(
        max_length=30,
        choices=(
            ('mr', 'M.'),
            ('mme', 'Mme'),
        )
    )
