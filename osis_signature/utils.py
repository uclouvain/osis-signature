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
from datetime import datetime

from django.core import signing

from osis_signature.models import Actor


def get_signing_token(actor: Actor):
    latest_state = actor.states.last()
    if not latest_state:
        raise ValueError("Can't generate token: no state recorded for this actor yet")
    return signing.dumps({
        'date': latest_state.created_at.isoformat(),
        'pk': actor.pk,
    })


def get_actor_from_token(token):
    try:
        payload = signing.loads(token)
    except signing.BadSignature:
        return None
    actor = Actor.objects.get(pk=payload['pk'])
    date = datetime.fromisoformat(payload['date'])
    if actor.states.latest('created_at').created_at == date:
        return actor
