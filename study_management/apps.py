from django.apps import AppConfig
from .settings import BACKUP_HEALTH_CHECK_ENABLED
from health_check.plugins import plugin_dir

class StudyManagementConfig(AppConfig):
    name = 'study_management'

    def ready(self):
        import study_management.signals

        if BACKUP_HEALTH_CHECK_ENABLED:
            from .backup_health_check import BackupHealthCheckBackend
            plugin_dir.register(BackupHealthCheckBackend)
