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
from django.urls import path, include
from django.views.generic import DetailView

from osis_signature.tests.test_signature import views
from osis_signature.tests.test_signature.models import SimpleModel

urlpatterns = [
    path('simple-create', views.SimpleCreateView.as_view(), name='simple-create'),
    path('double-create', views.DoubleCreateView.as_view(), name='double-create'),
    path('edit/<int:pk>', views.SimpleUpdateView.as_view(), name='simple-update'),
    path('<int:pk>', DetailView.as_view(model=SimpleModel), name='simple-detail'),
    path('send-invite/<int:actor_pk>', views.send_invite, name="send-invite"),
    path('sign/<path:token>', views.signing_view, name="sign"),
    path('signature/', include('osis_signature.urls', namespace='test_signature')),
]
