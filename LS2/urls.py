"""LS2 URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
# from django.contrib import admin
from .admin import admin_site
from django.urls import path, re_path, include
from django.contrib.auth import views as auth_views

from rest_framework.urlpatterns import format_suffix_patterns

from study_management import views as study_management_views
from study_management import rest_views



from . import settings

# check to see if we should enable the admin portal
if settings.ADMIN_PORTAL_ENABLE:
    admin_patterns = [
        path(settings.ADMIN_PORTAL_ROOT, admin_site.urls),
    ]
else:
    admin_patterns = []

researcher_account_patterns = [
    #researcher account urls
    path('management/login/', study_management_views.ResearcherLoginView.as_view(), name='researcher_login'),
    path('management/logout/', auth_views.logout, name='researcher_logout'),

    path('management/password_change/', auth_views.password_change, name='password_change'),
    path('management/password_change/done/', auth_views.password_change_done, name='password_change_done'),

    path('management/password_reset/', study_management_views.LS2PasswordResetView.as_view(), name='password_reset'),
    path('management/password_reset/done/', auth_views.password_reset_done, name='password_reset_done'),
    re_path(r'^management/reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        auth_views.password_reset_confirm, name='password_reset_confirm'),
    path('management/reset/done/', auth_views.password_reset_complete, name='password_reset_complete'),
]

researcher_study_patterns = [
    #study management urls
    path('management/', study_management_views.home, name='researcher_home'),
    path('management/first_login', study_management_views.first_login, name='researcher_first_login'),
    path('management/studies/<uuid:study_uuid>/add_participants', study_management_views.add_participants, name='add_participants'),
    path('management/studies/<uuid:study_uuid>/', study_management_views.study_detail, name='study_detail'),
]

rest_patterns = [
    path('management/studies/<uuid:study_uuid>/study_data', rest_views.DatapointListView.as_view(), name='all_study_data'),
    path('management/studies/<uuid:study_uuid>/study_data/<uuid:participant_uuid>', rest_views.DatapointListView.as_view(), name='study_data_for_participant'),
]

rest_patterns = format_suffix_patterns(rest_patterns)

participant_patterns = [
    path('dsu/auth/token', rest_views.ObtainAuthToken.as_view(), name='participant_auth'),
    path('dsu/auth/token/check', rest_views.ParticipantTokenCheck.as_view(), name='participant_token_check'),
    path('dsu/auth/logout', rest_views.ParticipantLogOutView.as_view(), name='participant_logout'),
    path('dsu/dataPoints', rest_views.DatapointCreateView.as_view(), name='dataPoints'),
    path('dsu/study/configuration', rest_views.StudyConfigurationView.as_view(), name='study_configuration'),
    path('dsu/public_keys/<uuid:public_key_uuid>', rest_views.PublicKeyView.as_view(), name='public_keys'),
]

health_check_patterns = [
    # re_path(r'ht/', include('health_check.urls')),
    re_path(r'ht/', study_management_views.HealthCheckCustomView.as_view(), name='health_check_custom'),
]

security_patterns = [
    # session_security support
    # Session security forces log out after n seconds of inactivity
    re_path(r'session_security/', include('session_security.urls')),
]


urlpatterns = admin_patterns + researcher_account_patterns + researcher_study_patterns + rest_patterns + participant_patterns + health_check_patterns + security_patterns
