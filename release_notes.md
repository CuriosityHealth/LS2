* 1.7.1
    * Fixed bug where admin logout did not take into account the admin root setting
* 1.7.0
    * Refactored settings to make it easier to activate admin, study management, and participant api independently of one another. Also migrated to JSON based configuration.
    * Added LDAP Auth URL blacklist to prevent participant API auth from going through the LDAP pathway. Note that this can be used as an alternative to operating a separate participant API container
    * Added LDAP to reseracher converter. This allows the admin to create a proxy object (specifying LDAP username & studies) that will be converted over to a researcher object once the researcher authenticates with their LDAP account for the first time.
* 1.6.0
    * Added LDAP support
    * Added Participant Account Generator functionality