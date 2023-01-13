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
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase

from osis_signature.contrib.forms import CommentSigningForm
from osis_signature.tests.factories import ActorFactory


class FormsTestCase(TestCase):
    def test_signing_form(self):
        actor = ActorFactory(external=True)
        form = CommentSigningForm({}, instance=actor)
        with self.assertRaises(ImproperlyConfigured):
            form.is_valid()

        form = CommentSigningForm({'submitted': ['declined']}, instance=actor)
        self.assertTrue(form.is_valid())
        self.assertFalse(form.cleaned_data['approved'])

        form = CommentSigningForm({'submitted': ['approved']}, instance=actor)
        self.assertTrue(form.is_valid())
        self.assertTrue(form.cleaned_data['approved'])

        self.assertFalse(actor.states.exists())
        form.save()
        self.assertTrue(actor.states.exists())
