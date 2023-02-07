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

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from base.tests.factories.person import PersonFactory
from osis_signature.enums import SignatureState
from osis_signature.models import Actor
from osis_signature.tests.factories import ActorFactory, ProcessFactory
from reference.tests.factories.country import CountryFactory


class ModelsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.process = ProcessFactory()
        cls.person = PersonFactory()
        cls.country = CountryFactory(name='CountryName')

    def test_actor_cant_be_created_without_person_or_external_data(self):
        with self.assertRaises(IntegrityError):
            Actor.objects.create(process=self.process)
        with self.assertRaises(ValidationError):
            Actor(process=self.process).clean()

    def test_actor_cant_have_partial_external_data(self):
        with self.assertRaises(ValidationError):
            Actor(process=self.process, email='foo@bar.com').clean()

    def test_actor_can_be_created_with_external_data(self):
        Actor.objects.create(
            process=self.process,
            email='foo@bar.com',
            first_name='John',
            last_name='Doe',
            institute='Institute',
            city='Somewhere',
            country_id=self.country.pk,
            language=settings.LANGUAGE_CODE_EN,
        )
        Actor(
            process=self.process,
            email='foo@bar.com',
            first_name='John',
            last_name='Doe',
            institute='Institute',
            city='Somewhere',
            country_id=self.country.pk,
            language=settings.LANGUAGE_CODE_EN,
        ).clean()

    def test_actor_can_be_created_with_person(self):
        Actor.objects.create(process=self.process, person=self.person)

    def test_actor_default_state(self):
        actor = ActorFactory(external=True)
        with self.assertNumQueries(1):
            self.assertEqual(actor.state, SignatureState.NOT_INVITED.name)
        first_actor = Actor.objects.first()
        with self.assertNumQueries(0):
            self.assertEqual(first_actor.state, SignatureState.NOT_INVITED.name)

    def test_actor_current_state(self):
        actor = ActorFactory(external=True)
        actor.switch_state(SignatureState.INVITED)
        with self.assertNumQueries(1):
            self.assertEqual(actor.state, SignatureState.INVITED.name)
        first_actor = Actor.objects.first()
        with self.assertNumQueries(0):
            self.assertEqual(first_actor.state, SignatureState.INVITED.name)

    def test_internal_actor_can_be_updated(self):
        actor = ActorFactory()
        actor.comment = 'Ok'
        actor.save()

    def test_computed(self):
        actor = ActorFactory(external=True, first_name='John')
        self.assertEqual(actor.first_name, 'John')
        self.assertEqual(actor.is_external, True)
        actor = ActorFactory()
        self.assertEqual(actor.first_name, actor.person.first_name)
        self.assertEqual(actor.institute, "")
        self.assertEqual(actor.is_external, False)

    def test_string(self):
        self.assertEqual(str(Actor()), "Actor (None)")
        self.assertEqual(str(ActorFactory(
            person=None,
            email='foo@example.com',
            first_name='John',
            last_name='Doe',
            institute='Institute',
            city='Somewhere',
            country_id=self.country.pk,
            language=settings.LANGUAGE_CODE_FR,
        )), 'Actor (John Doe foo@example.com Institute Somewhere CountryName fr-be)')
        person = PersonFactory()
        self.assertIn(str(person), str(ActorFactory(person=person)))
