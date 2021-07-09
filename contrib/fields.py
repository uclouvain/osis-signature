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

from django.db import models
from django.db.models.fields.related_lookups import RelatedLookupMixin
from django.utils.translation import gettext_lazy as _

from osis_signature.enums import SignatureState
from osis_signature.models import Actor


class SignatureProcessField(models.ForeignKey):
    description = _("A process for signing an object")

    def __init__(self, *args, **kwargs):
        kwargs.setdefault('to', 'osis_signature.Process')
        # The process should be deleted by default, but allow to override if needed
        kwargs.setdefault('on_delete', models.CASCADE)
        kwargs.setdefault('editable', False)
        kwargs.setdefault('null', True)
        super().__init__(*args, **kwargs)


@SignatureProcessField.register_lookup
class AllSignedLookup(RelatedLookupMixin, models.Lookup):
    lookup_name = 'all_signed'
    prepare_rhs = False

    def as_sql(self, compiler, connection):
        sql, params = compiler.compile(
            Actor.objects.filter(
                process_id=self.lhs,
            ).exclude(
                last_state=SignatureState.APPROVED.name,
            ).values('pk').query
        )
        if self.rhs:
            return "NOT EXISTS(%s)" % sql, params
        else:
            return "EXISTS(%s)" % sql, params
