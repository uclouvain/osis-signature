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
from django.core.exceptions import ValidationError
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

    external_fields = [
        'first_name',
        'last_name',
        'email',
        'language',
        'birth_date',
    ]

    widget_fields = [
        'person',
        *external_fields,
    ]

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
        base_manager_name = 'objects'

    def __str__(self):
        if not self.has_external_data() and not self.person:
            return super().__str__()
        elif not self.has_external_data():
            return "Actor (from person: {})".format(self.person)
        return "Actor ({})".format(
            ' '.join(str(getattr(self, field)) for field in self.external_fields)
        )

    @property
    def computed(self):
        # Return either external fields or filled from the person
        if self.person_id:
            return self.person
        from base.models.person import Person
        return Person(**{field: getattr(self, field) for field in self.external_fields})

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

    def has_external_data(self):
        return any(getattr(self, field) for field in self.external_fields)

    def valid_external_data(self):
        return all(getattr(self, field) for field in self.external_fields)

    default_error_messages = {
        'actor_internal_with_data': _("Actor can't be a person and have external data"),
        'actor_all_external_data': _("Actor must provide all external data"),
        'actor_data_required': _("Actor must have external data or person set"),
    }

    def clean(self):
        if not self.has_external_data() and not self.person:
            raise ValidationError(
                self.default_error_messages['actor_data_required'], code='actor_data_required'
            )
        if self.has_external_data() and self.person:
            raise ValidationError(
                self.default_error_messages['actor_internal_with_data'], code='actor_internal_with_data'
            )
        if self.has_external_data() and not self.valid_external_data():
            raise ValidationError(
                self.default_error_messages['actor_all_external_data'], code='actor_all_external_data'
            )

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
