from django.core.serializers.json import DjangoJSONEncoder
from django.core import serializers

def excluded_field_names_for_instance(instance):
    if instance._meta.label == 'auth.User':
        return ['password']
    if instance._meta.label == 'study_management.ParticipantAccountToken':
        return ['token']
    return []

def custom_easy_audit_serializer(instance):
    excluded_fields = excluded_field_names_for_instance(instance)
    field_names = [field.name for field in instance._meta.fields if field.name not in excluded_fields]
    return serializers.serialize("json", [instance], fields=field_names)

def easy_audit_model_delta_callback(old_instance, new_instance, delta):
    excluded_fields = excluded_field_names_for_instance(new_instance)
    for field_name in excluded_fields:
        if field_name in delta:
            delta[field_name] = ['excluded', 'excluded']
    return delta

