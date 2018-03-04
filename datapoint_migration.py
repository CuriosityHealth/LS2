from study_management.models import Datapoint
import json

def migrate_datapoints():
    for datapoint in Datapoint.objects.all():
        datapoint.encrypted_body = json.dumps(datapoint.body)
        datapoint.save()
