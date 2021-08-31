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
import uuid

from django.db import models
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

from osis_document.contrib import FileField
from osis_signature.enums import SignatureState


class Process(models.Model):
    uuid = models.UUIDField(
        default=uuid.uuid4,
        primary_key=True,
    )

    class Meta:
        verbose_name = _("Process")
        verbose_name_plural = _("Processes")


class ActorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related('person').annotate(
            last_state=Coalesce(
                models.Subquery(StateHistory.objects.filter(
                    actor=models.OuterRef('pk'),
                ).order_by('-created_at').values('state')[:1]),
                models.Value(SignatureState.NOT_INVITED.name),
            ),
            last_state_date=models.Subquery(StateHistory.objects.filter(
                actor=models.OuterRef('pk'),
            ).order_by('-created_at').values('created_at')[:1]),
        )

    def all_signed(self):
        return not self.get_queryset().exclude(
            last_state=SignatureState.APPROVED.name,
        ).exists()


class Actor(models.Model):
    process = models.ForeignKey(
        'osis_signature.Process',
        on_delete=models.CASCADE,
        verbose_name=_("Signature process"),
        related_name='actors',
    )
    person = models.ForeignKey(
        'base.Person',
        on_delete=models.PROTECT,
        verbose_name=_("Person"),
    )
    pdf_file = FileField(
        min_files=1,
        max_files=1,
        mimetypes=['application/pdf'],
        verbose_name=_("PDF file"),
    )
    comment = models.TextField(
        default='',
        verbose_name=_("Comment"),
        blank=True,
    )

    objects = ActorManager()

    class Meta:
        verbose_name = _("Actor")
        base_manager_name = 'objects'

    def __str__(self):
        if self.person_id:
            return "Actor (from person: {})".format(self.person)
        return "Actor object (None)"

    @property
    def state(self):
        if hasattr(self, 'last_state'):
            return self.last_state
        last_state = self.states.last()
        if last_state:
            return last_state.state
        return SignatureState.NOT_INVITED.name

    def get_state_display(self):
        return SignatureState.get_value(self.state)

    def switch_state(self, state: SignatureState):
        StateHistory.objects.create(actor=self, state=state.name)


class StateHistory(models.Model):
    actor = models.ForeignKey(
        'osis_signature.Actor',
        on_delete=models.CASCADE,
        verbose_name=_("Actor"),
        related_name='states',
    )
    state = models.CharField(
        choices=SignatureState.choices(),
        verbose_name=_("State"),
        max_length=30,
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Date"),
    )

    class Meta:
        verbose_name = _("State history entry")
        verbose_name_plural = _("State history entries")
        ordering = ('created_at',)
