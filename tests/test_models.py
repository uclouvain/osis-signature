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
import datetime
from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.test import TestCase

from base.tests.factories.person import PersonFactory
from osis_signature.enums import SignatureState
from osis_signature.models import Actor
from osis_signature.tests.factories import ProcessFactory, ExternalActorFactory, InternalActorFactory


class ModelsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.process = ProcessFactory()
        cls.person = PersonFactory()

    def test_actor_cant_be_created_without_person_or_external_data(self):
        with self.assertRaises(IntegrityError):
            Actor.objects.create(process=self.process)
        with self.assertRaises(ValidationError):
            Actor(process=self.process).clean()

    def test_actor_cant_be_created_with_person_and_external_data(self):
        with self.assertRaises(IntegrityError):
            Actor.objects.create(process=self.process, email='foo@bar.com', person=self.person)
        with self.assertRaises(ValidationError):
            Actor(process=self.process, email='foo@bar.com', person=self.person).clean()

    def test_actor_cant_have_partial_external_data(self):
        with self.assertRaises(ValidationError):
            Actor(process=self.process, email='foo@bar.com').clean()

    def test_actor_can_be_created_with_external_data(self):
        Actor.objects.create(
            process=self.process,
            email='foo@bar.com',
            first_name='John',
            last_name='Doe',
            language=settings.LANGUAGE_CODE_EN,
            birth_date=date(1980, 1, 1),
        )
        Actor(
            process=self.process,
            email='foo@bar.com',
            first_name='John',
            last_name='Doe',
            language=settings.LANGUAGE_CODE_EN,
            birth_date=date(1980, 1, 1),
        ).clean()

    def test_actor_can_be_created_with_person(self):
        Actor.objects.create(process=self.process, person=self.person)

    def test_actor_default_state(self):
        actor = ExternalActorFactory()
        with self.assertNumQueries(1):
            self.assertEqual(actor.state, SignatureState.NOT_INVITED.name)
        first_actor = Actor.objects.first()
        with self.assertNumQueries(0):
            self.assertEqual(first_actor.state, SignatureState.NOT_INVITED.name)

    def test_actor_current_state(self):
        actor = ExternalActorFactory()
        actor.switch_state(SignatureState.INVITED)
        with self.assertNumQueries(1):
            self.assertEqual(actor.state, SignatureState.INVITED.name)
        first_actor = Actor.objects.first()
        with self.assertNumQueries(0):
            self.assertEqual(first_actor.state, SignatureState.INVITED.name)

    def test_computed(self):
        actor = ExternalActorFactory()
        self.assertEqual(actor.computed.first_name, actor.first_name)
        actor = InternalActorFactory()
        self.assertEqual(actor.computed.first_name, actor.person.first_name)
        self.assertNotEqual(actor.first_name, actor.computed.first_name)

    def test_string(self):
        self.assertEqual(str(Actor()), "Actor object (None)")
        self.assertEqual(str(ExternalActorFactory(
            email='foo@example.com',
            first_name='John',
            last_name='Doe',
            language='fr',
            birth_date=datetime.date(1980, 1, 1),
        )), 'Actor (John Doe foo@example.com fr 1980-01-01)')
        person = PersonFactory()
        self.assertIn(str(person), str(InternalActorFactory(person=person)))
