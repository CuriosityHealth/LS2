

## Maybe this module only handles encoding / decoding, key mgmt, and lifetimes?

## ID Token simply states who you are
## Access token permits you to do certain things
## For example, as a participant, I can create datapoints
## about myself in the context of a particular study

## generate ID token
## takes in user
## creates JWT w/ type ID token and 1 week lifetime
## signed with latest JWT key

## decode ID token
## takes in JWT, verifies it against list of JWT keys
## Verifies that it has not expired
## returns participant_uuid and study_uuid

## generate Access Token
## takes in ID token and requested access policy
## decodes ID token and verifies that user can assume requested access policy
## maybe this happens at a higher level?
## generates the Access Token
## The Access Token in this case would include:
## - my ID (who I am)
## - role ( {"type": "participant", "participant_id": participant_uuid, "study_id": study_uuid})
## From this, we can validate, verify permissions, audit, and perform action

## decode Acccess Token
## verify lifetime
## possibly perform permission check
