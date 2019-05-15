"DbShare API table schema."

from . import definitions

schema = {
    '$id': 'https://dbshare.scilifelab.se/api/schema/table',
    '$schema': 'http://json-schema.org/draft-07/schema#',
    'title': __doc__,
    'definitions': definitions.schema,
}
