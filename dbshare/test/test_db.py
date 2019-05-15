"Test the DbShare API db endpoint."

import http.client
import os
import sqlite3

import dbshare.schema.db

from dbshare.test.base import *

DBNAME = 'test'
TABLENAME = 't1'
FILENAME = '/tmp/test.sqlite3'

class Db(Base):
    "Test the DbShare API db endpoint."

    def test_create_scratch(self):
        "Test creation of a database from scratch, schema, and deletion."
        url = f"{CONFIG['root']}/db/{DBNAME}"
        # Ensure that no such database exists.
        self.session.delete(url)
        response = self.session.put(url)
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.db.schema)
        response = self.session.delete(url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

    def test_create_file(self):
        "Test creation of a database from file content, schema, and deletion."
        try:                    # Ensure that no such file exists.
            os.remove(FILENAME)
        except OSError:
            pass
        cnx = sqlite3.connect(FILENAME)
        cnx.execute(f"CREATE TABLE {TABLENAME} (i INT PRIMARY KEY)")
        cnx.execute(f"INSERT INTO {TABLENAME} (i) VALUES (?)", (1,))
        cnx.execute(f"INSERT INTO {TABLENAME} (i) VALUES (?)", (2,))
        cnx.close()
        url = f"{CONFIG['root']}/db/{DBNAME}"
        # Ensure that no such database exists.
        self.session.delete(url)
        with open(FILENAME, 'rb') as infile:
            response = self.session.put(url, data=infile)
        self.assertEqual(response.status_code, http.client.OK)
        jsonschema.validate(instance=response.json(),
                            schema=dbshare.schema.db.schema)
        response = self.session.delete(url)
        self.assertEqual(response.status_code, http.client.NO_CONTENT)
        os.remove(FILENAME)


if __name__ == '__main__':
    unittest.main()