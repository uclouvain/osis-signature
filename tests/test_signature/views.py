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
from django.contrib import messages
from django.forms import Form
from django.http import Http404
from django.shortcuts import render, get_object_or_404, redirect, resolve_url
from django.views import generic

from osis_signature.contrib.forms import CommentSigningForm
from osis_signature.contrib.mixins import ActorFormsetMixin
from osis_signature.enums import SignatureState
from osis_signature.models import Actor
from osis_signature.tests.test_signature.forms import SpecialActorForm
from osis_signature.tests.test_signature.models import SimpleModel, SpecialActor, DoubleModel
from osis_signature.utils import get_signing_token, get_actor_from_token


class SimpleCreateView(ActorFormsetMixin, generic.CreateView):
    model = SimpleModel
    fields = '__all__'


class SimpleUpdateView(ActorFormsetMixin, generic.UpdateView):
    model = SimpleModel
    fields = '__all__'


class DoubleCreateView(ActorFormsetMixin, generic.CreateView):
    model = DoubleModel
    fields = '__all__'
    process_fk_name = 'special_jury'
    actors_formset_factory_kwargs = {
        'model': SpecialActor,
        'form': SpecialActorForm,
    }


def send_invite(request, actor_pk):
    actor = get_object_or_404(Actor, pk=actor_pk)
    form = Form(request.POST or None)
    if form.is_valid():
        actor.switch_state(SignatureState.INVITED)
        url = resolve_url('sign', token=get_signing_token(actor))
        messages.success(request, url)
        return redirect('home')
    return render(request, "test_signature/send_invite.html", {'form': form, 'actor': actor})


def signing_view(request, token):
    actor = get_actor_from_token(token)
    if not actor:
        raise Http404
    form = CommentSigningForm(request.POST or None, instance=actor)
    if form.is_valid():
        form.save()
        return redirect('home')
    return render(request, "test_signature/sign.html", {'form': form, 'actor': actor})
