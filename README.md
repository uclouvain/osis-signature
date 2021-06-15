# OSIS Signature

`OSIS Signature` is a Django application to ease signature workflows OSIS plateform.

# Requirements

`OSIS Signature` requires

- Django 2.2+
- Django REST Framework 3.12+


# How to install ?

## Configuring Django

Add `osis_signature` to `INSTALLED_APPS`:

```python
import os

INSTALLED_APPS = (
    ...
    'osis_signature',
    ...
)
```

# Using OSIS Signature

`osis_signature` is used to manage signature states for a workflow implementing approval.


## Attach to a model

Declare a `SignatureProcessField` on your model to enable adding actor for signing.


```python
from django.db import models
from django.urls import reverse
from osis_signature.contrib.fields import SignatureProcessField 

class YourModel(models.Model)
    ...
    jury = SignatureProcessField(
        signing_url=reverse('yourapp:sign'),
    )
```

The `signing_url` parameter is mandatory and must match to an existing view implementing 
[the generic `SignView`](#implement-signing-view). 

Then display this field in any form to enable the model creator to add actors. If needed, you can
 - force having at least a number of actors with the `minimum` option
 - restrict adding too many actors with the `maximum` option
 - prevent adding external actors passing `allow_external=False`
 - prevent adding internal actors passing `allow_internal=False`
 - prevent signing by uploading a PDF file using `allow_pdf=False`
 - prevent signing by sending a mail file using `allow_sending=False`


## Display actors

When displaying the `SignatureProcessField` values, it is advised to use the following template tag:

```html+django
{% load osis_signature %}

{% signature_table instance.jury %}
```

This will display a bootstrap-themed table of actors with their corresponding state for the process, and the button to
send an e-mail and or sign by PDF. You can pass `allow_pdf=False` or `allow_sending=False` to prevent showing these buttons.

If you need more granular control over the rendering of this table, the output is similar to:

```html+django
<table class"table">
```

[comment]: <> (TODO)

## Implement signals

An e-mail is sent when the user clicks on a "Send invitation" button, but it is the implementing module's duty to
actually send this invitation. A signal must be implemented, allowing you to use other modules such as 
[osis-mail-template](https://github.com/uclouvain/osis-mail-template),
[osis-notification](https://github.com/uclouvain/osis-notification) and
[osis-history](https://github.com/uclouvain/osis-history):

```python
from django.dispatch import receiver
from osis_history.utilities import add_history_entry
from osis_signature import Actor, get_signing_link
from osis_signature.signals import send_invite
from osis_mail_template import generate_email
from osis_notification.contrib.handlers import EmailNotificationHandler
from yourapp.models import YourModel
from yourapp.mail_templates import YOUR_TEMPLATE_MAIL_ID


@receiver(send_mail, sender=YourModel)
def send_invite(sender: YourModel, actor: Actor, user=None, **kwargs):
    language = actor.get_language
    tokens = {
        "first_name": actor.get_first_name, 
        "last_name": actor.get_first_name,
        "signing_link": get_signing_link(actor),
    }
    email_message = generate_email(YOUR_TEMPLATE_MAIL_ID, language, tokens, recipients=[actor.get_email])
    EmailNotificationHandler.create(email_message)
    add_history_entry(
        sender.uuid, 
        '{} notifié par e-mail'.format(actor.get_email),
        '{} notified by mail'.format(actor.get_email),
        user.person.username if user else "system",
    )
```

In case a signal did not respond for the model, a `MissingSendInviteSignal` exception will be thrown.

## Implement signing view

When a user clicks either on a "Sign uploading PDF" button, or an actor on a signing link in a received e-mail, 
they will be redirected to the `signing_url` set in the `SignatureProcessField`. You must implement this view using
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
from osis_signature import SignView

class JurySigningView(SignView):
    template_name = 'yourapp/jury_signing.html'

    def get_related_object(self, ):
```

You must provide:
 - a `get_related_object()` method that may be useful for explaining the context of signature
 - the template which must contains a form that may look like this:

```html+django
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
        <button type="submit" class="btn btn-primary"">
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

You may notice that this view is used both for signing by PDF (on behalf of an actor) or as result of clicking 
an e-mail link.

## Checking if all actors have signed

You may check within a queryset if all actors have signed by using the `all_signed` lookup or by checking the property 
onto the field:

```python
from yourapp.models import YourModel

YourModel.objects.filter(jury__all_signed=True)
assert YourModel.objects.first().jury.all_signed
```

# Utilities

By default, the related object author is responsible for sending invites to actors (by clicking on the links).
If needed, it is possible to implement a sequential order by programmatically sending invites:

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
