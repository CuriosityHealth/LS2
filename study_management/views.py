from django.conf import settings
from django.shortcuts import render
from .models import Researcher, Participant
# from django.contrib.auth.decorators import login_required
from .decorators import researcher_login_required, researcher_changed_password
from django.contrib.auth.views import LoginView, PasswordResetView
from .forms import ResearcherAuthenticationForm, ParticipantCreationForm
from .utils import should_warn_about_password_age
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse

from health_check.views import MainView

import logging

# Get an instance of a logger
logger = logging.getLogger(__name__)

# Create your views here.

class ResearcherLoginView(LoginView):
    authentication_form = ResearcherAuthenticationForm

class HealthCheckCustomView(MainView):
    template_name = 'study_management/health_check.html'
    pass

class LS2PasswordResetView(PasswordResetView):
    html_email_template_name = 'registration/html_password_reset_email.html'
    pass

@researcher_login_required
def first_login(request):

    return render(request, 'study_management/first_login.html', {})

@researcher_login_required
@researcher_changed_password
def home(request):

    logger.info('We\'re home!!')

    researcher = request.user.researcher
    context = {'researcher': researcher}

    if should_warn_about_password_age(request.user):
        messages.warning(request, 'Your password will expire soon.')

    return render(request, 'study_management/researcher_home.html', context)

@researcher_login_required
@researcher_changed_password
def study_detail(request, study_uuid):

    researcher = request.user.researcher
    ##This ensures that researcher has access to this study
    try:
        study = researcher.studies.get(uuid=study_uuid)
    except Study.DoesNotExist:
        return render(request, '404.html')

    context = {
        'study': study,
        'data_download_default': settings.DATA_DOWNLOAD_DEFAULT,
        'data_export_enabled': settings.DATA_EXPORT_ENABLED,
    }
    
    return render(request, 'study_management/study_detail.html', context)

@researcher_login_required
@researcher_changed_password
def add_participants(request, study_uuid):

    researcher = request.user.researcher

    ##This ensures that researcher has access to this study
    ##Test this for both non-existent studies as well as studies
    ##This researcher does not have access to
    try:
        study = researcher.studies.get(uuid=study_uuid)
    except Study.DoesNotExist:
        return render(request, '404.html')

    context = {'study': study}

    if request.method == "POST":
        form = ParticipantCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            participant = Participant(label=form.cleaned_data['participant_label'], user=user, study=study)

            try:
                participant.full_clean()
                participant.save()
            except ValidationError as e:
                user.delete()
                # Do something based on the errors contained in e.message_dict.
                # Display them to a user, or handle them programmatically.
                for k,el in e.message_dict.items():
                    for err in el:
                        form.add_error(k, err)
                context['form'] = form
                return render(request, 'study_management/add_participants.html', context=context, status=400)

            context['form'] = form
            return render(request, 'study_management/add_participants.html', context=context, status=201)

        else:
            context['form'] = form
            return render(request, 'study_management/add_participants.html', context=context, status=400)

    else:
        context['form'] = ParticipantCreationForm()
        return render(request, 'study_management/add_participants.html', context=context, status=200)
