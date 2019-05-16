"Test the DbShare API view endpoint."

import http.client

import dbshare.schema.db
import dbshare.schema.view
import dbshare.schema.rows

from dbshare.test.base import *


class View(Base):
    "Test the DbShare API view endpoint."

    def test_db_upload(self):
        "Create a database with view by file upload, check the view JSON."
        response = self.upload_file(view=True)
        self.assertEqual(response.status_code, http.client.OK)
        # Check that API db JSON is valid.
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.db.schema)
        # Check that API view JSON is valid.
        view_url = f"{CONFIG['root_url']}/view/{CONFIG['dbname']}/{CONFIG['viewname']}"
        response = self.session.get(view_url)
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.view.schema)
        # Check that API view rows JSON is valid.
        rows_url = f"{CONFIG['base_url']}/view/{CONFIG['dbname']}/{CONFIG['viewname']}.json"
        response = self.session.get(rows_url)
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.rows.schema)


if __name__ == '__main__':
    unittest.main()