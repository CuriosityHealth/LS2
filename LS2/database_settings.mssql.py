
def get_databases(environ):
    databases = {
        'default': {
            'ENGINE': 'sql_server.pyodbc',
            'NAME': environ.get('DATABASE_NAME', ''),
            'USER': environ.get('DATABASE_USER', ''),
            'PASSWORD': environ.get('DATABASE_PASSWORD', ''),
            'HOST': environ.get('DATABASE_HOST', ''),
            'PORT': environ.get('DATABASE_PORT', ''),
            'OPTIONS': {
                'driver': 'ODBC Driver 13 for SQL Server',
            },
        }
    }

    return databases
