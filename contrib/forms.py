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
from dal import autocomplete
from django import forms
from django.core.exceptions import ImproperlyConfigured

from osis_signature.enums import SignatureState
from osis_signature.models import Actor


class EmptyPermittedForm:
    def __init__(self, *args, **kwargs):
        kwargs['empty_permitted'] = True
        super().__init__(*args, **kwargs)


class ActorForm(EmptyPermittedForm, forms.ModelForm):
    class Meta:
        model = Actor
        fields = Actor.widget_fields
        widgets = {
            'person': autocomplete.ModelSelect2(url="osis_signature:person-autocomplete"),
        }


class InternalActorForm(EmptyPermittedForm, forms.ModelForm):
    class Meta:
        model = Actor
        fields = ['person']
        widgets = {
            'person': autocomplete.ModelSelect2(url="osis_signature:person-autocomplete"),
        }


class ExternalActorForm(EmptyPermittedForm, forms.ModelForm):
    class Meta:
        model = Actor
        fields = Actor.external_fields


class SigningForm(forms.ModelForm):
    def clean(self):
        if 'submitted' not in self.data:
            raise ImproperlyConfigured(
                "Please set up the signing form so that it contains 2 submit buttons with the name "
                "'submitted' and the 'approved' and 'declined' values."
            )
        self.cleaned_data['approved'] = 'declined' not in self.data.get('submitted')
        return self.cleaned_data

    def save(self, commit=True):
        # Upon saving this form, we need to add a new state to this actor depending on the button clicked
        self.instance.switch_state(
            SignatureState.APPROVED if self.cleaned_data['approved'] else SignatureState.DECLINED
        )
        return super().save(commit)


class CommentSigningForm(SigningForm):
    class Meta:
        model = Actor
        fields = ['comment']


class PdfSigningForm(forms.ModelForm):
    class Meta:
        model = Actor
        fields = ['pdf_file', 'comment']
