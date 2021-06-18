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

from osis_signature.enums import SignatureState
from osis_signature.tests.factories import ExternalActorFactory
from osis_signature.utils import get_signing_token, get_actor_from_token


class UtilsTestCase(TestCase):
    def test_get_token(self):
        actor = ExternalActorFactory()
        with self.assertRaises(ValueError):
            get_signing_token(actor)

        actor.switch_state(SignatureState.INVITED)
        self.assertIsNotNone(get_signing_token(actor))

    def test_get_actor(self):
        actor = ExternalActorFactory()
        actor.switch_state(SignatureState.INVITED)

        old_token = get_signing_token(actor)

        actor.switch_state(SignatureState.INVITED)
        good_token = get_signing_token(actor)

        self.assertIsNone(get_actor_from_token(old_token))
        self.assertEqual(get_actor_from_token(good_token), actor)
