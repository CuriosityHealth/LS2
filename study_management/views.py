from . import settings
from django.shortcuts import render, redirect
from .models import Researcher, Participant, Study, TokenBasedParticipantAccountGenerator, ParticipantAccountToken
# from django.contrib.auth.decorators import login_required
from .decorators import researcher_login_required, researcher_changed_password
from django.contrib.auth.views import LoginView, PasswordResetView
from .forms import ResearcherAuthenticationForm, ParticipantCreationForm
from django.urls import reverse
from django.contrib import messages
from django.http import HttpResponse
from django.http import JsonResponse

from health_check.views import MainView
from datetime import datetime
from django.utils import timezone

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

    if researcher.should_warn_about_password_age():
        messages.warning(request, 'Your password will expire soon.')

    return render(request, 'study_management/researcher_home.html', context)


def last_upload_date_for_sort(participant):
    last_upload_date = participant.last_datapoint_submission_date()
    if last_upload_date == None:
        return datetime.min
    else:
        return timezone.make_naive(last_upload_date)

def sort_participants(participants, sort):
    if sort == None:
        return participants

    if sort == 'username':
        key = lambda x: x.user.username
        return sorted(participants, key=key)

    if sort == '-username':
        key = lambda x: x.user.username
        return sorted(participants, key=key, reverse=True)

    if sort == 'participant_label':
        key = lambda x: x.label
        return sorted(participants, key=key)

    if sort == '-participant_label':
        key = lambda x: x.label
        return sorted(participants, key=key, reverse=True)

    if sort == 'participant_id':
        key = lambda x: x.uuid
        return sorted(participants, key=key)

    if sort == '-participant_id':
        key = lambda x: x.uuid
        return sorted(participants, key=key, reverse=True)

    if sort == 'date_joined':
        key = lambda x: x.user.date_joined
        return sorted(participants, key=key)

    if sort == '-date_joined':
        key = lambda x: x.user.date_joined
        return sorted(participants, key=key, reverse=True)

    if sort == 'last_upload':
        return sorted(participants, key=last_upload_date_for_sort)

    if sort == '-last_upload':
        return sorted(participants, key=last_upload_date_for_sort, reverse=True)

    return participants

@researcher_login_required
@researcher_changed_password
def study_detail(request, study_uuid):

    researcher = request.user.researcher
    ##This ensures that researcher has access to this study
    try:
        study = researcher.studies.get(uuid=study_uuid)
    except Study.DoesNotExist:
        return render(request, '404.html')

    sort = request.GET.get('sort')
    sorted_particpiants = sort_participants(study.participant_set.all(), request.GET.get('sort'))

    context = {
        'study': study,
        'participants': sorted_particpiants,
        'sort': sort,
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

    sort = request.GET.get('sort')
    sorted_particpiants = sort_participants(study.participant_set.all(), request.GET.get('sort'))

    context = {
        'study': study,
        'participants': sorted_particpiants,
        'sort': sort,
    }

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

@researcher_login_required
@researcher_changed_password
def token_based_participant_account_generator(request, study_uuid, generator_uuid):

    researcher = request.user.researcher

    ##This ensures that researcher has access to this study
    ##Test this for both non-existent studies as well as studies
    ##This researcher does not have access to
    try:
        study = researcher.studies.get(uuid=study_uuid)
    except Study.DoesNotExist:
        return render(request, '404.html')

    try:
        generator = study.tokenbasedparticipantaccountgenerator_set.get(uuid=generator_uuid)
    except TokenBasedParticipantAccountGenerator.DoesNotExist:
        return render(request, '404.html')

    context = {
        'study': study, 
        'generator': generator
    }

    if request.method == "POST":

        if generator.can_generate_token() == False:
            messages.error(request, 'The token generator is disabled. Please contact the administrator.')
            return render(request, 'study_management/token_based_participant_account_generator_detail.html', context=context, status=403)

        view_token = generator.generate_token()
        if view_token != None:

            context['obfuscate_token'] = False
            context['view_token'] = view_token

            return render(request, 'study_management/token_based_participant_account_generator_detail.html', context=context, status=201)

            # logger.debug(request.path)
            # redirect_path = f'{request.path}?token_id={new_token}'
            # logger.debug(redirect_path)
            # return redirect(redirect_path)
         
        else:
            messages.error(request, 'Could not generate a unique token. Please try again later.')
            return render(request, 'study_management/token_based_participant_account_generator_detail.html', context=context, status=409)
        
    else:

        token_id = request.GET.get('token_id', None)
        context['obfuscate_token'] = settings.PARTICIPANT_ACCOUNT_GENERATOR_OBFUSCATE_TOKENS
        logger.debug(token_id)
        if token_id != None:
            view_token = ParticipantAccountToken.getTokenByUUID(
                token_id=token_id,
                generator_id=generator_uuid
            )

            if view_token != None:
                logger.debug(view_token)
                
                context['view_token'] = view_token

        return render(request, 'study_management/token_based_participant_account_generator_detail.html', context=context, status=200)