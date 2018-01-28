from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import REDIRECT_FIELD_NAME
from .models import Researcher
from .utils import is_researcher
from django.shortcuts import redirect, resolve_url

from functools import wraps


def is_authenticated_researcher(user):
    if not user.is_authenticated:
        return False

    return is_researcher(user)

def researcher_login_required(function=None, redirect_field_name=REDIRECT_FIELD_NAME, login_url=None):
    """
    Decorator for views that checks that the user is logged in and the user is a researcher,
    redirecting to the log-in page if necessary.
    """
    actual_decorator = user_passes_test(
        lambda u: is_authenticated_researcher(u),
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator


def researcher_passes_test(test_func, redirect_url):
    """
    Decorator for views that checks that the user passes the given test,
    redirecting to the log-in page if necessary. The test should be a callable
    that takes the user object and returns True if the user passes.
    """

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if test_func(request.user.researcher):
                return view_func(request, *args, **kwargs)
            path = request.build_absolute_uri()
            resolved_redirect_url = resolve_url(redirect_url)
            return redirect(resolved_redirect_url)
        return _wrapped_view
    return decorator

# assume that the researcher is logged in at thisn point
def researcher_changed_password(function):

    actual_decorator = researcher_passes_test(
        lambda r: not r.must_change_password(),
        redirect_url='researcher_first_login'
    )
    return actual_decorator(function)
