
def get_databases(environ):
    databases = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': environ.get('DATABASE_NAME', ''),
            'USER': environ.get('DATABASE_USER', ''),
            'PASSWORD': environ.get('DATABASE_PASSWORD', ''),
            'HOST': environ.get('DATABASE_HOST', ''),
            'PORT': environ.get('DATABASE_PORT', ''),
        }
    }

    return databases
