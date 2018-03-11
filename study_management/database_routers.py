import logging

logger = logging.getLogger(__name__)

class DatapointRouter:

    def db_for_read(self, model, **hints):
        # logger.debug('db_for_read')
        # logger.debug(model)
        # logger.debug(model._meta.label)
        if model._meta.label == "study_management.Datapoint":
            logger.debug("returning datapoints db")
            return "datapoints"
        return None

    def db_for_write(self, model, **hints):
        if model._meta.label == "study_management.Datapoint":
            logger.debug("returning datapoints db")
            return "datapoints"
        return None

    def allow_relation(self, obj1, obj2, **hints):
        if obj1._meta.label == "study_management.Datapoint" or \
            obj2._meta.label == "study_management.Datapoint":
            return False
        else:
            return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if db == "datapoints":
            return app_label == "study_management" and model_name == "datapoint"
        else:
            return None
