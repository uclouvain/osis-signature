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

from django.test import TestCase

from base.tests.factories.person import PersonFactory
from osis_signature.enums import SignatureState
from osis_signature.models import Actor
from osis_signature.tests.factories import ProcessFactory, ActorFactory


class ModelsTestCase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.process = ProcessFactory()
        cls.person = PersonFactory()

    def test_actor_can_be_created_with_person(self):
        Actor.objects.create(process=self.process, person=self.person)

    def test_actor_default_state(self):
        actor = ActorFactory()
        with self.assertNumQueries(1):
            self.assertEqual(actor.state, SignatureState.NOT_INVITED.name)
        first_actor = Actor.objects.first()
        with self.assertNumQueries(0):
            self.assertEqual(first_actor.state, SignatureState.NOT_INVITED.name)

    def test_actor_current_state(self):
        actor = ActorFactory()
        actor.switch_state(SignatureState.INVITED)
        with self.assertNumQueries(1):
            self.assertEqual(actor.state, SignatureState.INVITED.name)
        first_actor = Actor.objects.first()
        with self.assertNumQueries(0):
            self.assertEqual(first_actor.state, SignatureState.INVITED.name)

    def test_string(self):
        self.assertEqual(str(Actor()), "Actor object (None)")
        self.assertEqual(str(ActorFactory(
            person__first_name='John',
            person__last_name='Doe',
        )), 'Actor (from person: DOE, John)')
        person = PersonFactory()
        self.assertIn(str(person), str(ActorFactory(person=person)))
