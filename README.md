# OSIS Signature

`OSIS Signature` is a Django application to ease signature workflows OSIS plateform.

# Requirements

`OSIS Signature` requires

- Django 2.2+

# Installation

## Configuring Django

Add `osis_signature` to `INSTALLED_APPS`:

```python
INSTALLED_APPS = (
    ...
    'osis_signature',
    ...
)
```

Add `osis_signature` urls to your patterns (useful for autocompletion):

```python
from django.urls import path, include

urlpatterns = [
    ...
    path('osis_signature/', include('osis_signature.urls')),
]
```

# Using OSIS Signature

`osis_signature` is used to manage signature states for a workflow implementing approval.

## Attach to a model

Attach a process by using a ForeignKey to the `Process` model to enable adding actors for signing.

```python
from django.db import models


class YourModel(models.Model):
    ...
    jury = models.ForeignKey(
        'osis_signature.Process',
        on_delete=models.CASCADE,
        editable=False,
        null=True,
    )
```

## Exposing actors in a form

To add or edit actors of your model, you can use the `ActorFormsetMixin` mixin which adds a formset to your view.

As a reminder, you can configure the formset as per
[formset documentation](https://docs.djangoproject.com/en/3.2/topics/forms/modelforms/#model-formsets), override the
`actors_formset_factory_kwargs` attribute to set the factory kwargs, for example:

- force having at least a number of actors with the `min_num` option (default: 1)
- restrict adding too many actors with the `max_num` and `validate_max` options
- override `form` (defaults to `ActorForm`) to
    - handle more precisely field widgets
    - only allow adding external actors using `ExternalActorForm`
    - only allow adding internal actors using `InternalActorForm`

## Attaching extra data to actors

If you need extra data attached to actors, subclass the model, and use it in the mixin, e.g.:

```python
# models.py
from django.db import models

from osis_signature.models import Actor


class YourModel(models.Model):
    title = models.CharField(max_length=200)
    jury = models.ForeignKey(
        'osis_signature.Process',
        on_delete=models.CASCADE,
        editable=False,
        null=True,
    )


class SpecialActor(Actor):
    civility = models.CharField(
        max_length=30,
        choices=(
            ('mr', 'M.'),
            ('mme', 'Mme'),
        )
    )

    external_fields = ['civility'] + Actor.external_fields


# forms.py
from osis_signature.contrib.forms import ActorForm
from osis_signature.models import Actor


class SpecialActorForm(ActorForm):
    class Meta(ActorForm.Meta):
        model = SpecialActor
        fields = ['civility'] + Actor.widget_fields


# views.py
from osis_signature.contrib.mixins import ActorFormsetMixin
from django.views import generic


class SimpleCreateView(ActorFormsetMixin, generic.CreateView):
    model = YourModel
    fields = '__all__'
    actors_formset_factory_kwargs = {
        'model': SpecialActor,
        'form': SpecialActorForm,
    }
```

## Display actors

When displaying a process' value, you can use the following template tag:

```html
{% load osis_signature %}

{% signature_table instance.jury %}
```

This will display a bootstrap-themed table of actors with their corresponding state for the process, and the button to
send an e-mail and or sign by PDF. You can pass `allow_pdf=False` or `allow_sending=False` to prevent showing these
buttons.

If you need more granular control over the rendering of this table, the output is similar to:

```html
{% load i18n %}
<table class="table table-striped">
  <thead>
  <tr>
    <th>#</th>
    <th>{% trans "First name" %}</th>
    <th>{% trans "Last name" %}</th>
    <th>{% trans "E-mail" %}</th>
    <th>{% trans "Status" %}</th>
  </tr>
  </thead>
  <tbody>
  {% for actor in actors %}
  <tr>
    <th scope="row">{{ forloop.counter }}</th>
    <td>{{ actor.computed.first_name }}</td>
    <td>{{ actor.computed.last_name }}</td>
    <td>{{ actor.computed.email }}</td>
    <td>{{ actor.get_state_display }}</td>
  </tr>
  {% endfor %}
  </tbody>
</table>
```

## Implement the signing workflow

To fully implement a signing workflow, you will need to implement these views:

1. a _send invite_ view (requiring at least an actor to send the invite to as a parameter)
1. a _signing_ view (requiring at least a token to identify the signing actor as a parameter)

Here's an example url configuration:

```python
from django.urls import path
from yourapp import views

app_name = 'yourapp'
urlpatterns = [
    path('send-invite/<int:actor_pk>', views.send_invite, name="send-invite"),
    path('sign/<path:token>', views.signing_view, name="sign"),
]
```

You can of course add as much as parameters as needed to give more context to your views.

### Send an invitation

To send an e-mail when the user clicks on a _"Send invitation"_ button, you must implement a view. It is advised to use
other modules such as
[osis-mail-template](https://github.com/uclouvain/osis-mail-template),
[osis-notification](https://github.com/uclouvain/osis-notification) and
[osis-history](https://github.com/uclouvain/osis-history):

```python
from django.forms import Form
from django.shortcuts import render, get_object_or_404, redirect, resolve_url
from osis_history.utilities import add_history_entry
from osis_signature.utils import get_signing_token
from osis_mail_template import generate_email
from osis_notification.contrib.handlers import EmailNotificationHandler
from osis_signature.models import Actor, SignatureState
from yourapp.mail_templates import YOUR_TEMPLATE_MAIL_ID


def send_invite(request, actor_pk):
    actor = get_object_or_404(Actor, pk=actor_pk)
    form = Form(request.POST or None)
    if form.is_valid():
        actor.switch_state(SignatureState.INVITED)
        tokens = {
            "first_name": actor.computed.first_name,
            "last_name": actor.computed.last_name,
            "signing_link": resolve_url('yourapp:sign', token=get_signing_token(actor)),
        }
        email_message = generate_email(
          YOUR_TEMPLATE_MAIL_ID, 
          actor.computed.language, 
          tokens, 
          recipients=[actor.computed.email],
        )
        EmailNotificationHandler.create(email_message)
        add_history_entry(
            actor.process_id,
            '{} notifié par e-mail'.format(actor.computed.email),
            '{} notified by mail'.format(actor.computed.email),
            request.user.person.username,
        )
        return redirect('home')
    return render(request, "send_invite.html", {'form': form, 'actor': actor})
```

In case a signal did not respond for the model, a `MissingSendInviteSignal` exception will be thrown.

### Implement signing view

When a user clicks either on a "Sign uploading PDF" button, or an actor on a signing link in a received e-mail, they
will be redirected to the `signing_url` set in the `SignatureProcessField`. You must implement this view using
the `SignView` generic view:

In your urls:

```python
from django.urls import path
from yourapp.views import JurySignView

app_name = 'yourapp'
urlpatterns = [
    ...
    path('signing/<path:token>', JurySigningView.as_view(), name='yourapp')
]
```

In your views:

```python
from django.shortcuts import get_object_or_404
from osis_signature import SignView
from yourapp.models import YourModel


class JurySigningView(SignView):
    template_name = 'yourapp/jury_signing.html'

    def get_related_object(self, related_uuid):
        return get_object_or_404(YourModel, uuid=related_uuid)
```

You must provide:

- a `get_related_object()` method that may be useful for explaining the context of signature
- the template which must contains a form that may look like this:

```html
{% extends "layout.html" %}
{% load i18n bootstrap3 %}

{% block content %}
<div class="page-header">
  <h1>{% blocktrans %}Sign for {{ related_object }}{% endblocktrans %}</h1>
</div>

<form action="" method="post">
    {% crsf_token %}
    {% if form %}
        {% blocktrans %}
        Upload the PDF document on behalf of {{ actor.get_first_name }} {{ actor.get_last_name }}.
        {% endblocktrans %}
        {% bootstrap_form form %}
        <button type="submit" class="btn btn-primary">
            {% trans "Upload" %}
        </button>
        <a href="{{ related_object.get_absolute_url }}" class="text-danger">
            {% trans "Cancel" %}
        </a>
    {% else %}
        {% blocktrans %}
        Hello {{ actor.get_first_name }} {{ actor.get_last_name }}, indicate here if you
        approve or decline {{ related_object }}.
        {% endblocktrans %}
        {% bootstrap_form form %}
        <button type="submit" class="btn btn-primary" value="decline">
            {% trans "Approve" %}
        </button>
        <button type="submit" class="btn btn-primary" value="approve">
            {% trans "Decline" %}
        </button>
    {% endif %}
</form>
{% endblock %}
```

You may notice that this view is used both for signing by PDF (on behalf of an actor) or as result of clicking an e-mail
link.

## Checking if all actors have signed

You may check within a queryset if all actors have signed by using the `all_signed` lookup or by checking the property
onto the field:

```python
from yourapp.models import YourModel

YourModel.objects.filter(jury__all_signed=True)
assert YourModel.objects.first().jury.all_signed
```

# Utilities

By default, the related object author is responsible for sending invites to actors (by clicking on the links). If
needed, it is possible to implement a sequential order by programmatically sending invites:

```python
from yourapp.models import YourModel

instance = YourModel.objects.first()
for actor in instance.jury.actors:
    actor.send_invite()
```

You may follow-up on the process by listening to other signals sent by `osis_signature`:

```python
from django.dispatch import receiver
from osis_history.utilities import add_history_entry
from osis_signature import Actor
from osis_signature.signals import approved, declined, signed
from yourapp.models import YourModel


@receiver(signed, sender=YourModel)
def signed(sender: YourModel, actor: Actor, action=None, pdf=False, comment='', **kwargs):
    name = '{actor.get_first_name} {actor.get_last_name}'.format(actor=actor)
    add_history_entry(
        sender.uuid,
        '{} a {} par e-mail'.format(name, "approuvé" if action == 'approved' else 'décliné'),
        '{} {} by mail'.format(name, "approved" if action == 'approved' else 'declined'),
        name,
    )


@receiver(signed, sender=YourModel)
def approved(sender: YourModel, actor: Actor, comment='', **kwargs):
    pass


@receiver(signed, sender=YourModel)
def declined(sender: YourModel, actor: Actor, comment='', **kwargs):
    pass
```
