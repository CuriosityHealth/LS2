from django.contrib import admin
from django.conf import settings

from easyaudit.admin import CRUDEventAdmin, LoginEventAdmin, RequestEventAdmin
from easyaudit.models import CRUDEvent, LoginEvent, RequestEvent

from .models import Study, Researcher, Participant, Datapoint, PasswordChangeEvent, LoginTimeout
# Register your models here.
from django.utils.safestring import mark_safe
from .serializers import DatapointSerializer
from rest_framework.renderers import JSONRenderer

admin.site.register(Study)
admin.site.register(Researcher)

class PasswordChangeEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_date')
    readonly_fields = ('user', 'created_date')
    fields = ('user', 'created_date')

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

class DatapointAdmin(admin.ModelAdmin):

    list_display = ['uuid', 'study', 'schema_string', 'participant', 'created_date_time']
    date_hierarchy = 'created_date_time'
    list_filter = ['study', 'participant', 'created_date_time', ]

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

class LS2CRUDEventAdmin(CRUDEventAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return True

admin.site.register(CRUDEvent, LS2CRUDEventAdmin)

class LS2LoginEventAdmin(LoginEventAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return True

admin.site.register(LoginEvent, LS2LoginEventAdmin)

class LS2RequestEventAdmin(RequestEventAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return False

    def has_module_permission(self, request):
        return True

admin.site.register(RequestEvent, LS2RequestEventAdmin)
