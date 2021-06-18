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

from django import forms
from django.core.exceptions import ImproperlyConfigured
from django.forms.models import _get_foreign_key
from django.views.generic.edit import BaseCreateView

from osis_signature.contrib.forms import ActorForm
from osis_signature.models import Process, Actor


class ActorFormsetMixin:
    process_fk_name = None
    actors_formset_context_object_name = 'actors_formset'
    actors_formset_factory_kwargs = {}
    actors_formset_prefix = 'actors'

    def get_context_data(self, **kwargs):
        """Add formset to context data (if not already set by validation)"""
        context = super().get_context_data(**kwargs)
        if self.actors_formset_context_object_name not in context:
            context[self.actors_formset_context_object_name] = self.get_actor_formset()
        return context

    def get_process_field(self):
        """Get the process field name from the foreign key"""
        try:
            return _get_foreign_key(Process, self.model, fk_name=self.process_fk_name).name
        except ValueError as e:
            raise ImproperlyConfigured(
                "{} Check or set the 'process_fk_name' attribute.".format(e)
            )

    def get_formset_class(self):
        """Get the formset class for actors"""
        factory_kwargs = {
            'form': ActorForm,
            'validate_min': True,
            # 'can_order': True,
            'extra': 0,
            'min_num': 1,
            'model': Actor,
            **self.actors_formset_factory_kwargs,
        }
        return forms.inlineformset_factory(Process, **factory_kwargs)

    def get_actor_formset(self):
        """Initialize the formset from request data"""
        return self.get_formset_class()(
            data=self.request.POST or None,
            files=self.request.FILES or None,
            instance=getattr(self.object, self.get_process_field(), None),
            prefix=self.actors_formset_prefix,
        )

    def process_invalid(self, form, formset):
        """If the form or the formset is invalid, render both."""
        context = {'form': form, self.actors_formset_context_object_name: formset}
        return self.render_to_response(self.get_context_data(**context))

    def post(self, request, *args, **kwargs):
        """Validate both form and formset, and attach process with actors if valid"""
        if isinstance(self, BaseCreateView):
            self.object = None
        else:
            self.object = self.get_object()
        form = self.get_form()
        formset = self.get_actor_formset()
        if form.is_valid() and formset.is_valid():
            if self.object is None:
                # Create process
                process = Process.objects.create()
                setattr(form.instance, self.get_process_field(), process)
            else:
                process = getattr(self.object, self.get_process_field())
            response = super().form_valid(form)

            # Save actors
            formset.instance = process
            formset.save()

            return response
        return self.process_invalid(form, formset)
