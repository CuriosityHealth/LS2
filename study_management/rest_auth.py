from rest_framework.authentication import SessionAuthentication, TokenAuthentication
from .utils import is_researcher, is_participant

class ResearcherSessionAuthentication(SessionAuthentication):

    def authenticate(self, request):

        user_tuple = super().authenticate(request)
        if user_tuple != None and is_researcher(user_tuple[0]):
            return user_tuple
        else:
            return None

class ParticipantTokenAuthentication(TokenAuthentication):

    def authenticate(self, request):

        user_tuple = super().authenticate(request)
        if user_tuple != None and is_participant(user_tuple[0]):
            return user_tuple

        else:
            return None
