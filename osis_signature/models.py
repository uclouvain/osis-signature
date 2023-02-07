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
import operator
import uuid
from functools import reduce

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.functions import Coalesce
from django.utils.translation import gettext_lazy as _

from osis_signature.enums import SignatureState

NOT_MAPPED = ''
PERSON_FIELD_MAPPING = {
    'first_name': 'first_name',
    'last_name': 'last_name',
    'email': 'email',
    'institute': NOT_MAPPED,
    'city': NOT_MAPPED,
    'country': 'country_of_citizenship',
    'language': 'language',
}
EXTERNAL_PERSON_FIELDS = list(PERSON_FIELD_MAPPING.keys())
TEXT_FIELDS = sorted(set(EXTERNAL_PERSON_FIELDS) - {'country'})


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
        return (
            super()
            .get_queryset()
            .select_related('person')
            .annotate(
                last_state=Coalesce(
                    models.Subquery(
                        StateHistory.objects.filter(actor=models.OuterRef('pk'))
                        .order_by('-created_at')
                        .values('state')[:1]
                    ),
                    models.Value(SignatureState.NOT_INVITED.name),
                ),
                last_state_date=models.Subquery(
                    StateHistory.objects.filter(actor=models.OuterRef('pk'))
                    .order_by('-created_at')
                    .values('created_at')[:1]
                ),
            )
        )

    def all_signed(self):
        return not self.get_queryset().exclude(last_state=SignatureState.APPROVED.name).exists()


class Actor(models.Model):
    """
    A model that handle an actor of the process, it can be internal (referenced by person, or external).
    Attributes (either actor is external or not) can be accessed the same way, meaning first_name will point to
    person.first_name if person is not empty
    """

    uuid = models.UUIDField(
        default=uuid.uuid4,
        db_index=True,
    )

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
    institute = models.CharField(
        verbose_name=_("Institution"),
        max_length=255,
        blank=True,
        default='',
    )
    city = models.CharField(
        verbose_name=_("City"),
        max_length=255,
        blank=True,
        default='',
    )
    country = models.ForeignKey(
        'reference.Country',
        verbose_name=_("Country"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    language = models.CharField(
        max_length=30,
        blank=True,
        default='',
        choices=settings.LANGUAGES,
        verbose_name=_("Language"),
    )
    comment = models.TextField(
        default='',
        verbose_name=_("Comment"),
        blank=True,
    )

    @property
    def is_external(self):
        return self.person_id is None

    objects = ActorManager()

    class Meta:
        verbose_name = _("Actor")
        constraints = [
            models.CheckConstraint(
                check=(
                    (
                        # Either external data is empty
                        (
                            reduce(
                                operator.and_,
                                [models.Q(**{field: ''}) for field in TEXT_FIELDS]
                                + [models.Q(country_id__isnull=True)],
                            )
                        )
                        # Or person is empty
                        | models.Q(person__isnull=True)
                    )
                    # But not all can be empty
                    & ~(
                        models.Q(person__isnull=True)
                        & (
                            reduce(
                                operator.or_,
                                [models.Q(**{field: ''}) for field in TEXT_FIELDS]
                                + [models.Q(country_id__isnull=True)],
                            )
                        )
                    )
                ),
                name='external_xor_person',
            )
        ]
        base_manager_name = 'objects'

    def __str__(self):
        if self.person_id:
            return "Actor (from person: {})".format(self.person)
        external_fields_str = ' '.join(str(getattr(self, field)) for field in EXTERNAL_PERSON_FIELDS)
        return "Actor ({})".format(external_fields_str.strip())

    def __getattribute__(self, name: str):
        """When we have a person related, get data from person"""
        if name in EXTERNAL_PERSON_FIELDS and self.person_id and not hasattr(self, '_disable_proxy'):
            return getattr(self.person, PERSON_FIELD_MAPPING[name], '')
        return super().__getattribute__(name)

    def clean_fields(self, exclude=None):
        self._disable_proxy = True
        super().clean_fields(exclude)
        delattr(self, '_disable_proxy')

    def save(self, *args, **kwargs):
        self._disable_proxy = True
        super().save(*args, **kwargs)
        delattr(self, '_disable_proxy')

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

    @property
    def external_data_is_valid(self):
        return all(getattr(self, field) for field in EXTERNAL_PERSON_FIELDS)

    default_error_messages = {
        'actor_data_required': _("Actor must have external data or person set"),
    }

    def clean(self):
        if not self.person_id and not self.external_data_is_valid:
            raise ValidationError(self.default_error_messages['actor_data_required'], code='actor_data_required')

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
