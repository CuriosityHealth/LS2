* 1.10.17
    * Updated dependencies
* 1.10.16
    * Updated dependencies
* 1.10.15
    * Updated dependencies
* 1.10.14
    * Updated dependencies
* 1.10.13
    * Updated dependencies
* 1.10.12
    * Updated dependencies, changed django-pyodbc-azure -> django-mssql-backend to support Django 2.2
* 1.10.11
    * Updated dependencies
* 1.10.10
    * Updated dependencies
* 1.10.9
    * Updated dependencies
* 1.10.8
    * Updated dependencies
* 1.10.7
    * Updated easy audit and added support for filtering of fields in CRUD audit events
* 1.10.6
    * Updated dependencies
* 1.10.5
    * Updated dependencies
* 1.10.4
    * Added support for displaying version number on study management portal
    * Added new command to generate a new random fernet key
    * Updated dependencies
* 1.10.3
    * Added commands
* 1.10.2
    * Updated dependencies* 
1.10.1
    * Updated dependencies
* 1.10.0
    * Added Description field to account generators
    * Added sorting capability to participant table
    * Updated dependencies
* 1.9.0
    * Improved audit event admin by adding support for purging events older than configured retention window
    * Added setting to obfuscate participant account generation tokens after creation
    * Added error codes to token based participant account generation authentication to support client error handling
    * Removed password change link in the case that the user authenticated via LDAP
    * Updated Django dependency
* 1.8.0
    * Added token-based participant account generation
    * Added support for multiple tokens per participant
    * Added support for downloading participant mapping 
    * Improved admin for Researcher and LDAP to Researcher converter
    * Fixed some issues with development logging
* 1.7.3
    * Fixed issues where crashes would sometimes occur in Admin portal during password change & logout
    * Updated default values for participant account generation throttling
    * Added warning logs when a failure occurs during participant account generation
* 1.7.2
    * Updated dependencies, mainly Django 2.1. Needed to update URLS to change to class based views due to removal of function based views from Django contrib auth views.
* 1.7.1
    * Fixed bug where admin logout did not take into account the admin root setting
* 1.7.0
    * Refactored settings to make it easier to activate admin, study management, and participant api independently of one another. Also migrated to JSON based configuration.
    * Added LDAP Auth URL blacklist to prevent participant API auth from going through the LDAP pathway. Note that this can be used as an alternative to operating a separate participant API container
    * Added LDAP to reseracher converter. This allows the admin to create a proxy object (specifying LDAP username & studies) that will be converted over to a researcher object once the researcher authenticates with their LDAP account for the first time.
* 1.6.0
    * Added LDAP support
    * Added Participant Account Generator functionality