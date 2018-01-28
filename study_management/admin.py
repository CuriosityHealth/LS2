from django.contrib import admin

from .models import Study, Researcher, Participant, Datapoint, PasswordChangeEvent, LoginTimeout
# Register your models here.

admin.site.register(Study)
admin.site.register(Researcher)

class PasswordChangeEventAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_date')
    readonly_fields = ('user', 'created_date')
    fields = ('user', 'created_date')
admin.site.register(PasswordChangeEvent, PasswordChangeEventAdmin)

class LoginTimeoutAdmin(admin.ModelAdmin):
    list_display = ('username', 'remote_ip','created_date', 'disable_until')
    readonly_fields = ('username', 'remote_ip','created_date', 'disable_until')
    fields = ('username', 'remote_ip','created_date', 'disable_until')
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
admin.site.register(Datapoint)
