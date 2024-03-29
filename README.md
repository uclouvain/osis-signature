# OSIS Signature

`OSIS Signature` is a Django application to ease signature workflows OSIS platform.

# Requirements

`OSIS Signature` requires

- Django 2.2+

# Installation

## For production

```bash
# From your osis install, with python environment activated
pip install git+https://github.com/uclouvain/osis-signature.git@dev#egg=osis_signature
```

## For development

```bash
# From your osis install, with python environment activated
git clone git@github.com:uclouvain/osis-signature.git
pip install -e ./osis-signature
```


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

Attach a process by declaring a `SignatureProcessField` to enable adding actors for signing.

```python
from django.db import models
from osis_signature.contrib.fields import SignatureProcessField


class YourModel(models.Model):
    ...
    jury = SignatureProcessField()
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

Here is a code example for displaying the formset in a template:

```html
<form action="" method="post">
  {% csrf_token %}
  {% bootstrap_form form %}
  <div id="actors-formset">
    {% bootstrap_formset_errors actors_formset %}
    {% for form in actors_formset.forms %}
    <div class="form-row">
      {% bootstrap_form form layout='horizontal' exclude='DELETE' %}
      {% bootstrap_field form.DELETE show_label=False %}
    </div>
    {% endfor %}
    {{ actors_formset.management_form }}
  </div>
  <input type="submit" value="Envoyer" class="btn btn-primary">
</form>
<script src="{% statici18n LANGUAGE_CODE %}"></script>
<script src="{% static 'js/jquery.formset.js' %}"></script>
<script>
  $('#actors-formset > .form-row').formset({
    addText: gettext('Add another'),
    deleteText: gettext('Remove'),
    addCssClass: 'btn btn-info btn-sm',
    deleteCssClass: 'btn btn-warning btn-sm',
    prefix: 'actors',
    added: function(row) {
      $('select', row).val('').trigger('change')
    }
  });
</script>
{{ form.media }}
{{ actors_formset.media }}
```

## Attaching extra data to actors

If you need extra data attached to actors, subclass the model, and use it in the mixin, e.g.:

```python
# models.py
from django.db import models

from osis_signature.models import Actor
from osis_signature.contrib.fields import SignatureProcessField


class YourModel(models.Model):
    title = models.CharField(max_length=200)
    jury = SignatureProcessField()


class SpecialActor(Actor):
    civility = models.CharField(
        max_length=30,
        choices=(
            ('mr', 'M.'),
            ('mme', 'Mme'),
        ),
        blank=True,  # must be not required
    )


# forms.py
from osis_signature.contrib.forms import ActorForm
from osis_signature.models import EXTERNAL_PERSON_FIELDS


class SpecialActorForm(ActorForm):
    class Meta(ActorForm.Meta):
        model = SpecialActor
        fields = ['civility'] + EXTERNAL_PERSON_FIELDS


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
send an e-mail. You can pass `allow_sending=False` to prevent showing these
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
    <td>{{ actor.first_name }}</td>
    <td>{{ actor.last_name }}</td>
    <td>{{ actor.email }}</td>
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
    path('send-invite/<int:pk>', views.SendInviteView.as_view(), name="send-invite"),
    path('sign/<path:token>', views.SigningView.as_view(), name="sign"),
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
from urllib.parse import quote
from django.forms import Form
from django.shortcuts import redirect, resolve_url
from django.views import generic
from django.views.generic.detail import SingleObjectMixin
from osis_history.utilities import add_history_entry
from osis_signature.utils import get_signing_token
from osis_mail_template import generate_email
from osis_notification.contrib.handlers import EmailNotificationHandler
from osis_signature.models import Actor, SignatureState
from yourapp.mail_templates import YOUR_TEMPLATE_MAIL_ID


class SendInviteView(SingleObjectMixin, generic.FormView):
    form_class = Form
    model = Actor
    template_name = "send_invite.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        actor = self.object
        actor.switch_state(SignatureState.INVITED)
        sign_url = quote(resolve_url('demo:sign', token=get_signing_token(actor)))
        tokens = {
            "first_name": actor.first_name,
            "last_name": actor.last_name,
            "sign_url": self.request.build_absolute_uri(sign_url),
        }
        email_message = generate_email(
            YOUR_TEMPLATE_MAIL_ID,
            actor.language,
            tokens,
            recipients=[actor.email],
        )
        EmailNotificationHandler.create(email_message)
        add_history_entry(
            actor.process_id,
            '{} notifié par e-mail'.format(actor.email),
            '{} notified by mail'.format(actor.email),
            self.request.user.person.username,
        )
        return redirect('home')
```

### Implement signing view

To implement the logic behind an actor clicking on a signing link in a received e-mail. You must implement a view and
may use `CommentSigningForm` :

```python

from django.http import Http404
from django.urls import reverse_lazy
from django.views import generic

from osis_signature.contrib.forms import CommentSigningForm
from osis_signature.models import Actor
from osis_signature.utils import get_actor_from_token


class SigningView(generic.UpdateView):
    form_class = CommentSigningForm
    model = Actor
    template_name = "sign.html"
    success_url = reverse_lazy('home')

    def get_object(self, queryset=None):
        actor = get_actor_from_token(self.kwargs['token'])
        if not actor:
            raise Http404
        return actor
```

And for the template `sign.html`:

```html
{% extends "layout.html" %}
{% load i18n bootstrap3 %}

{% block content %}
<div class="page-header">
  <h1>{% blocktrans %}Sign for {{ related_object }}{% endblocktrans %}</h1>
</div>

<form action="" method="post" enctype="multipart/form-data">
  {% csrf_token %}
  {% blocktrans trimmed %}
  Hello {{ actor.first_name }} {{ actor.last_name }}, indicate here if you
  approve or decline.
  {% endblocktrans %}
  {% bootstrap_form form %}
  <button type="submit" name="submitted" value="approved" class="btn btn-primary">Approve</button>
  <button type="submit" name="submitted" value="declined" class="btn btn-danger">Decline</button>
  {% endif %}
</form>
{% endblock %}
```

NB: it is very important to provide two buttons with the `submitted` name, so that the system know if the signature is
approved or declined.

## Checking if all actors have signed

You may check within a queryset if all actors have signed by using the `all_signed` lookup or by checking the manager
method on the field:

```python
from yourapp.models import YourModel

YourModel.objects.filter(jury__all_signed=True)
assert YourModel.objects.first().jury.all_signed()
```
