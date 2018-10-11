from django.contrib import admin
from django import forms
from django.conf import settings
from . import settings as app_settings
from datetime import datetime, timedelta
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponseRedirect

from django.urls import reverse

from django.contrib.auth import get_user_model

from easyaudit.admin import CRUDEventAdmin, LoginEventAdmin, RequestEventAdmin
from easyaudit.models import CRUDEvent, LoginEvent, RequestEvent

from .models import (
    Study, Researcher, Participant, LDAPUserToResearcherConverter,
    Datapoint, PasswordChangeEvent, LoginTimeout,
    ParticipantAccountGenerator,
    ParticipantAccountGenerationRequestEvent,
    ParticipantAccountGenerationTimeout,
    TokenBasedParticipantAccountGenerator,
    ParticipantAccountToken,
    ParticipantAuthToken
)
# Register your models here.
from django.utils.safestring import mark_safe
from .serializers import DatapointSerializer
from rest_framework.renderers import JSONRenderer

from .forms import ParticipantAccountGeneratorCreationForm, ParticipantAccountGeneratorChangeForm

import logging

logger = logging.getLogger(__name__)

UserModel = get_user_model()

admin.site.register(Study)

class ResearcherForm(forms.ModelForm):

    def get_user_queryset():
        return UserModel.objects.filter(participant__isnull=True)

    user = forms.ModelChoiceField(queryset=get_user_queryset())

    class Meta:
        model = Researcher
        exclude = ['uuid']
        widgets = {
            'studies': forms.widgets.CheckboxSelectMultiple(),
        }

class ResearcherAdmin(admin.ModelAdmin):

    form = ResearcherForm


admin.site.register(Researcher, ResearcherAdmin)

class LDAPUserToResearcherConverterForm(forms.ModelForm):

    class Meta:
        model = LDAPUserToResearcherConverter
        exclude = []
        widgets = {
            'studies': forms.widgets.CheckboxSelectMultiple(),
        }

class LDAPUserToResearcherConverterAdmin(admin.ModelAdmin):

    form = LDAPUserToResearcherConverterForm

admin.site.register(LDAPUserToResearcherConverter, LDAPUserToResearcherConverterAdmin)

class PasswordChangeEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'username', 'created_date')
    readonly_fields = ('user', 'username', 'created_date')
    fields = ('user', 'username', 'created_date')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return True

admin.site.register(PasswordChangeEvent, PasswordChangeEventAdmin)

class LoginTimeoutAdmin(admin.ModelAdmin):
    list_display = ('username', 'remote_ip','created_date', 'disable_until')
    readonly_fields = ('username', 'remote_ip','created_date', 'disable_until')
    fields = ('username', 'remote_ip','created_date', 'disable_until')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return True

admin.site.register(LoginTimeout, LoginTimeoutAdmin)

class ParticipantAdmin(admin.ModelAdmin):

    # fieldsets = [
    #     (None,               {'fields': ['question_text']}),
    #     ('Date information', {'fields': ['pub_date'], 'classes': ['collapse']}),
    # ]
    # inlines = [ChoiceInline]
    # list_display = ('question_text', 'pub_date', 'was_published_recently')
    # fields = ('label', 'user', 'study')
    list_display = ('__str__', 'study')
    list_filter = ['study__name']
    # search_fields = ['question_text']
    pass

admin.site.register(Participant, ParticipantAdmin)
class ParticipantAuthTokenAdmin(admin.ModelAdmin):

    list_display = ('key', 'user', 'created', 'last_used')
    fields = ('user',)
    readonly_fields = ('user',)
    ordering = ('-created',)
    pass

admin.site.register(ParticipantAuthToken, ParticipantAuthTokenAdmin)

class DatapointAdmin(admin.ModelAdmin):

    list_display = ['uuid', 'study_uuid', 'schema_string', 'participant_uuid', 'created_date_time']
    date_hierarchy = 'created_date_time'
    list_filter = ['study_uuid', 'participant_uuid', 'created_date_time', ]

    readonly_fields = ['datapoint_prettified', ]
    exclude = ['schema_namespace', 'schema_name', 'schema_version_major',
        'schema_version_minor', 'schema_version_patch', 'participant', 'study',
        'ap_source_name', 'ap_source_creation_date_time', 'ap_source_modality',
        'body']

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return True

    def datapoint_prettified(self, obj):
        serializer = DatapointSerializer(obj)
        json = JSONRenderer().render(serializer.data, renderer_context={'indent': 4})
        html = '<pre>' + json.decode("utf-8", "strict") + '</pre>'
        # return mark_safe(html)
        return json.decode("utf-8", "strict")

    datapoint_prettified.short_description = 'Datapoint'

if settings.DEBUG:
    admin.site.register(Datapoint, DatapointAdmin)

class LS2AuditEventAdminHelper():

    @staticmethod
    def audit_log_retention_days():
        return getattr(app_settings, 'AUDIT_LOG_RETENTION_DAYS', 90)

    @staticmethod
    def objects_to_purge(model, retention_time):
            return model.objects.filter(datetime__lt=timezone.now() - retention_time)

    @staticmethod
    def truncate_table(model, retention_time):
        results = LS2AuditEventAdminHelper.objects_to_purge(model, retention_time)
        results.delete()

    # Helper view to remove all rows in a table
    @staticmethod
    def purge_objects(request, modeladmin):
        """
        Removes all objects in this table.
        This action first displays a confirmation page;
        next, it deletes all objects and redirects back to the change list.
        """

        audit_log_retention_days = LS2AuditEventAdminHelper.audit_log_retention_days()
        audit_log_retention_time = timedelta(days=audit_log_retention_days)

        # modeladmin = self
        opts = modeladmin.model._meta

        # Check that the user has delete permission for the actual model
        if not request.user.is_superuser:
           raise PermissionDenied
        if not modeladmin.has_delete_permission(request):
            raise PermissionDenied

        # If the user has already confirmed or cancelled the deletion,
        # (eventually) do the deletion and return to the change list view again.
        if request.method == 'POST':
            if 'btn-confirm' in request.POST:
                try:
                    n = LS2AuditEventAdminHelper.objects_to_purge(modeladmin.model, audit_log_retention_time).count()
                    LS2AuditEventAdminHelper.truncate_table(modeladmin.model, audit_log_retention_time)
                    modeladmin.message_user(request, _("Successfully removed %d rows" % n), messages.SUCCESS);
                except Exception as e:
                    modeladmin.message_user(request, _(u'ERROR') + ': %r' % e, messages.ERROR)
            else:
                modeladmin.message_user(request, _("Action cancelled by user"), messages.SUCCESS);
            return HttpResponseRedirect(reverse('admin:%s_%s_changelist' % (opts.app_label, opts.model_name)))

        context = {
            "title": _("Purge all %s older than %d days... are you sure?") % (opts.verbose_name_plural, audit_log_retention_days),
            "opts": opts,
            "app_label": opts.app_label,
            "retention_days": audit_log_retention_days,
        }

        # Display the confirmation page
        return render(
            request,
            'admin/study_management/purge_confirmation.html',
            context
        )

class LS2CRUDEventAdmin(CRUDEventAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return True

    change_list_template = "admin/study_management/audit_event_change_list.html"
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['retention_days'] = LS2AuditEventAdminHelper.audit_log_retention_days()
        return super().changelist_view(request, extra_context=extra_context)

    def purge_objects(self, request):
        return LS2AuditEventAdminHelper.purge_objects(request, self)

admin.site.register(CRUDEvent, LS2CRUDEventAdmin)

class LS2LoginEventAdmin(LoginEventAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return True

    change_list_template = "admin/study_management/audit_event_change_list.html"
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['retention_days'] = LS2AuditEventAdminHelper.audit_log_retention_days()
        return super().changelist_view(request, extra_context=extra_context)

    def purge_objects(self, request):
        return LS2AuditEventAdminHelper.purge_objects(request, self)

admin.site.register(LoginEvent, LS2LoginEventAdmin)

class LS2RequestEventAdmin(RequestEventAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_module_permission(self, request):
        return True

    change_list_template = "admin/study_management/audit_event_change_list.html"
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['retention_days'] = LS2AuditEventAdminHelper.audit_log_retention_days()
        return super().changelist_view(request, extra_context=extra_context)
        
    def purge_objects(self, request):
        return LS2AuditEventAdminHelper.purge_objects(request, self)

admin.site.register(RequestEvent, LS2RequestEventAdmin)

class ParticipantAccountGeneratorAdmin(admin.ModelAdmin):

    # fieldsets = (
    #     (None, {'fields': ('study', 'password')}),
    #     (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
    #     (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
    #                                    'groups', 'user_permissions')}),
    #     (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    # )
    # add_fieldsets = (
    #     (None, {
    #         'classes': ('wide',),
    #         'fields': ('username', 'password1', 'password2'),
    #     }),
    # )

    # def get_fieldsets(self, request, obj=None):
    #     if not obj:
    #         return self.add_fieldsets
    #     return super().get_fieldsets(request, obj)

    list_display = ('__str__', 'study', 'number_of_participants_created', 'max_participants_to_create')

    def get_readonly_fields(self, request, obj=None):
        if not obj:
            return ('uuid', 'number_of_participants_created')
        else:
            return ('uuid', 'number_of_participants_created', 'study')


    form = ParticipantAccountGeneratorChangeForm
    add_form = ParticipantAccountGeneratorCreationForm

    def get_form(self, request, obj=None, **kwargs):
        """
        Use special form during user creation
        """
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)
if app_settings.PARTICIPANT_ACCOUNT_GENERATION_ENABLED:
    admin.site.register(ParticipantAccountGenerator, ParticipantAccountGeneratorAdmin)

class ParticipantAccountGenerationTimeoutAdmin(admin.ModelAdmin):
    list_display = ('remote_ip', 'generator_id', 'created_date', 'disable_until')
    readonly_fields = ('remote_ip', 'generator_id', 'created_date', 'disable_until')
    list_filter = ('generator_id', 'remote_ip')


if app_settings.PARTICIPANT_ACCOUNT_GENERATION_ENABLED:
    admin.site.register(ParticipantAccountGenerationTimeout, ParticipantAccountGenerationTimeoutAdmin)

class ParticipantAccountGenerationRequestEventAdmin(admin.ModelAdmin):
    list_display = ('generator_id', 'remote_ip', 'created_date', )
    readonly_fields = ('remote_ip', 'generator_id', 'created_date', )
    list_filter = ('generator_id', )
    # def has_add_permission(self, request):
    #     return False
    #
    # def has_change_permission(self, request, obj=None):
    #     return True
    #
    # def has_delete_permission(self, request, obj=None):
    #     return False
    #
    # def has_module_permission(self, request):
    #     return True

if app_settings.PARTICIPANT_ACCOUNT_GENERATION_ENABLED:
    admin.site.register(ParticipantAccountGenerationRequestEvent, ParticipantAccountGenerationRequestEventAdmin)

class TokenBasedParticipantAccountGeneratorAdmin(admin.ModelAdmin):
    # readonly_fields = ()
    pass

class ParticipantAccountTokenAdmin(admin.ModelAdmin):
    # readonly_fields = ()
    list_display = ('__str__', 'username', 'account_generator', 'created_date_time', 'expiration_date_time', 'used', 'disabled')
    list_filter = ['used', 'disabled', 'account_generator']
    pass

if app_settings.PARTICIPANT_ACCOUNT_GENERATION_ENABLED:
    admin.site.register(TokenBasedParticipantAccountGenerator, TokenBasedParticipantAccountGeneratorAdmin)
    admin.site.register(ParticipantAccountToken, ParticipantAccountTokenAdmin)
