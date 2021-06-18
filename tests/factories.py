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

import factory
from django.conf import settings

from osis_signature.enums import SignatureState
from osis_signature.models import Process, Actor, StateHistory


class ProcessFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Process


class InternalActorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Actor

    process = factory.SubFactory(ProcessFactory)
    person = factory.SubFactory('base.tests.factories.person.PersonFactory')


class ExternalActorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Actor

    process = factory.SubFactory(ProcessFactory)
    email = factory.Faker('email')
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    language = settings.LANGUAGE_CODE_EN
    birth_date = factory.Faker('date_of_birth')
