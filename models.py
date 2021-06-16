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
        verbose_name=_("Person"),
    )
    first_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        db_index=True,
        verbose_name=_("First name"),
    )
    last_name = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        verbose_name=_("Last name"),
    )
    email = models.EmailField(
        max_length=255,
        null=True,
        verbose_name=_("E-mail"),
    )
    language = models.CharField(
        max_length=30,
        null=True,
        choices=settings.LANGUAGES,
        default=settings.LANGUAGE_CODE,
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
    state = models.CharField(
        choices=SignatureState.choices(),
        default=SignatureState.NOT_INVITED.name,
        verbose_name=_("State"),
        max_length=30,
    )
    comment = models.TextField(
        default='',
        verbose_name=_("Comment"),
    )

    class Meta:
        verbose_name = _("Actor")
        constraints = [
            models.CheckConstraint(
                check=(
                        (models.Q(email__isnull=True) | models.Q(person__isnull=True))
                        & ~models.Q(email__isnull=True, person__isnull=True)
                ),
                name='email_xor_person',
            )
        ]


class StateHistory(models.Model):
    actor = models.ForeignKey(
        'osis_signature.Actor',
        on_delete=models.CASCADE,
        verbose_name=_("Actor"),
    )
    state = models.CharField(
        choices=SignatureState.choices(),
        default=SignatureState.NOT_INVITED.name,
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
