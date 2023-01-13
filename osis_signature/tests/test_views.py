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
from django.test import TestCase, override_settings, RequestFactory
from django.urls import reverse
from django.views import generic

from base.tests.factories.person import PersonFactory
from base.tests.factories.user import UserFactory
from osis_signature.contrib.mixins import ActorFormsetMixin
from osis_signature.models import Process, Actor
from osis_signature.tests.test_signature.models import DoubleModel, SimpleModel


@override_settings(ROOT_URLCONF='osis_signature.urls')
class ViewsTestCase(TestCase):
    def test_person_autocomplete(self):
        PersonFactory()
        response = self.client.get(reverse("person-autocomplete"))
        self.assertEqual(response.status_code, 403)

        self.client.force_login(UserFactory())
        response = self.client.get(reverse("person-autocomplete"))
        self.assertEqual(len(response.json()['results']), 1)


@override_settings(ROOT_URLCONF='osis_signature.tests.test_signature.urls')
class MixinTestCase(TestCase):
    def test_simple_mixin(self):
        person = PersonFactory()

        response = self.client.get(reverse("simple-create"))
        self.assertEqual(response.status_code, 200)
        self.assertIn('actors_formset', response.context)

        response = self.client.post(reverse("simple-create"))
        self.assertEqual(response.status_code, 200)
        self.assertIn('actors_formset', response.context)
        self.assertFalse(Process.objects.exists())
        self.assertFalse(Actor.objects.exists())

        response = self.client.post(reverse("simple-create"), {
            'title': 'Foo',
            'actors-INITIAL_FORMS': 0,
            'actors-TOTAL_FORMS': 1,
            'actors-0-person': person.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Process.objects.exists())
        self.assertTrue(Actor.objects.exists())

        pk = SimpleModel.objects.first().pk
        response = self.client.post(reverse("simple-update", kwargs={'pk': pk}), {
            'title': 'Foo',
            'actors-INITIAL_FORMS': 1,
            'actors-TOTAL_FORMS': 2,
            'actors-0-id': Actor.objects.first().pk,
            'actors-0-person': person.pk,
            'actors-1-person': PersonFactory().pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Process.objects.count(), 1)
        self.assertEqual(Actor.objects.count(), 2)

    def test_double_mixin(self):
        class DoubleCreateView(ActorFormsetMixin, generic.CreateView):
            model = DoubleModel
            fields = '__all__'

        with self.assertRaises(ImproperlyConfigured):
            DoubleCreateView.as_view()(RequestFactory().get('/'))

        class DoubleCreateView(ActorFormsetMixin, generic.CreateView):
            model = DoubleModel
            fields = '__all__'
            process_fk_name = 'special_jury'

        response = DoubleCreateView.as_view()(RequestFactory().get('/'))
        self.assertEqual(response.status_code, 200)
