from study_management.models import Datapoint

datapoint_encrypted_fields = ['body', 'metadata']
def rotate_fernet_key():
    for datapoint in Datapoint.objects.all():
        datapoint.save(update_fields=datapoint_encrypted_fields, force_update=True)
