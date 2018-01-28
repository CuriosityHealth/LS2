from health_check.backends import BaseHealthCheckBackend
from health_check.exceptions import HealthCheckException

from django.core.files import File
import sys
from datetime import datetime, timedelta
from django.utils import timezone
from . import settings
import arrow

from django.utils.translation import ugettext_lazy as _

class TooOldException(HealthCheckException):
    message_type = "Too Old"

class DateUnknownException(HealthCheckException):
    message_type = "Date Unknown"

class BackupHealthCheckBackend(BaseHealthCheckBackend):

    def last_backup_date(self):
        try:
            with open('/backup-status/latest_backup_date', 'r') as f:
                date_string = f.readline()
                date_format = '%Y-%m-%dT%H:%M:%S%z\n'
                date = datetime.strptime(date_string, date_format)
                return date
        except:
            return None

    def check_status(self):
        # The test code goes here.
        # You can use `self.add_error` or
        # raise a `HealthCheckException`,
        # similar to Django's form validation.
        last_backup_date = self.last_backup_date()
        if not last_backup_date:
            self.add_error(DateUnknownException("Status File Not Found"))

        else:
            age_max = timedelta(minutes=settings.BACKUP_AGE_MINS_MAX)
            age = timezone.now() - last_backup_date
            if age > age_max:
                human_date = arrow.get(last_backup_date).humanize()
                self.add_error(TooOldException(f'Last Backup {human_date}'))

    def pretty_status(self):
        if self.errors:
            return "\n".join(str(e) for e in self.errors)

        last_backup_date = self.last_backup_date()
        if not last_backup_date:
            return _('working')
        else:
            human_date = arrow.get(last_backup_date).humanize()
            return f'Working: Last Backup {human_date}'

    def identifier(self):
        return "Periodic Backup"  # Display name on the endpoint.
