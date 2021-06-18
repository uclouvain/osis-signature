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

from django.conf import settings
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
    field_ref = models.CharField(
        editable=False,
        max_length=150,
        verbose_name=_("Field reference"),
    )

    class Meta:
        verbose_name = _("Process")
        verbose_name_plural = _("Processes")


class ActorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().annotate(
            last_state=Coalesce(
                models.Subquery(StateHistory.objects.filter(
                    actor=models.OuterRef('pk'),
                ).values('state')[:1]),
                models.Value(SignatureState.NOT_INVITED.name),
            ),
        )


class Actor(models.Model):
    process = models.ForeignKey(
        'osis_signature.Process',
        on_delete=models.CASCADE,
        verbose_name=_("Signature process"),
    )
    person = models.ForeignKey(
        'base.Person',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        verbose_name=_("Person"),
    )
    first_name = models.CharField(
        max_length=50,
        blank=True,
        default='',
        db_index=True,
        verbose_name=_("First name"),
    )
    last_name = models.CharField(
        max_length=50,
        blank=True,
        default='',
        verbose_name=_("Last name"),
    )
    email = models.EmailField(
        max_length=255,
        blank=True,
        default='',
        verbose_name=_("E-mail"),
    )
    language = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        choices=settings.LANGUAGES,
        verbose_name=_("Language"),
    )
    birth_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_("Birth date"),
    )
    pdf_file = FileField(
        limit=1,
        mimetypes=['application/pdf'],
        verbose_name=_("PDF file"),
    )
    comment = models.TextField(
        default='',
        verbose_name=_("Comment"),
    )

    objects = ActorManager()

    @property
    def state(self):
        if hasattr(self, 'last_state'):
            return self.last_state
        last_state = self.states.last()
        if last_state:
            return last_state.state
        return SignatureState.NOT_INVITED.name

    class Meta:
        verbose_name = _("Actor")
        constraints = [
            models.CheckConstraint(
                # @formatter:off
                check=(
                        (  # Either external data is empty
                                models.Q(
                                    first_name='',
                                    last_name='',
                                    email='',
                                    language__isnull=True,
                                    birth_date__isnull=True,
                                )
                                # Or person is empty
                                | models.Q(person__isnull=True)
                        )
                        # But not all can be empty
                        & ~models.Q(
                            person__isnull=True,
                            first_name='',
                            last_name='',
                            email='',
                            language__isnull=True,
                            birth_date__isnull=True,
                        )
                ),
                # @formatter:on
                name='external_xor_person',
            )
        ]


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
