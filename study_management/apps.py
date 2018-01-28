from django.apps import AppConfig
from health_check.plugins import plugin_dir

class StudyManagementConfig(AppConfig):
    name = 'study_management'

    def ready(self):
        import study_management.signals

        from .backup_health_check import BackupHealthCheckBackend
        plugin_dir.register(BackupHealthCheckBackend)
