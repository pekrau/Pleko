"Test the db API endpoint."

import http.client
import sqlite3

import dbshare.schema.db

from dbshare.test.base import *


class Db(Base):
    "Test the db API endpoint."

    def setUp(self):
        super().setUp()
        self.db_url = f"{CONFIG['root_url']}/db/{CONFIG['dbname']}"

    def test_create(self):
        "Create an empty database, check its JSON, and delete it."

        # Create an empty database.
        response = self.session.put(self.db_url)
        self.assertEqual(response.status_code, http.client.OK)

        # Valid API db JSON.
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.db.schema)

        # Delete the database.
        response = self.session.delete(self.db_url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

    def test_upload(self):
        "Create a database by file upload, check its JSON."
        response = self.upload_file()

        # Valid API db JSON.
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.db.schema)

    def test_edit(self):
        "Create an empty database, edit it, check its JSON."

        # Create an empty database.
        response = self.session.put(self.db_url)
        self.assertEqual(response.status_code, http.client.OK)

        # Valid API db JSON.
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.db.schema)

        # Edit the title.
        title = 'New title'
        response = self.session.post(self.db_url, json={'title': title})
        self.assertEqual(response.status_code, http.client.OK)
        data = response.json()
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.db.schema)
        self.assertEqual(data.get('title'), title)

        # Edit the description.
        description = 'A description'
        response = self.session.post(self.db_url,
                                     json={'description': description})
        self.assertEqual(response.status_code, http.client.OK)
        data = response.json()
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.db.schema)
        self.assertEqual(data.get('description'), description)
        # Same title as before.
        self.assertEqual(data.get('title'), title)

        # Rename the database; record its new url.
        name = 'test2'
        response = self.session.post(self.db_url, json={'name': name})
        self.assertEqual(response.status_code, http.client.OK)
        data = response.json()
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.db.schema)
        self.assertTrue(data['$id'].endswith(name))
        # So that the database is deleted at cleanup.
        self.db_url = data['$id']
        self.addCleanup(self.delete_db)


if __name__ == '__main__':
    unittest.main()
