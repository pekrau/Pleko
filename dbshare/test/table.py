"Test the table API endpoint."

import csv
import io
import http.client

import dbshare.schema.db
import dbshare.schema.table
import dbshare.schema.rows

from dbshare import constants
from dbshare.test.base import *


class Table(Base):
    "Test the table API endpoint."

    table_spec = {'name': 't1',
                  'title': 'Test table',
                  'columns': [
                      {'name': 'i',
                       'type': 'INTEGER',
                       'primarykey': True},
                      {'name': 't',
                       'type': 'TEXT',
                       'notnull': False},
                      {'name': 'r',
                       'type': 'REAL',
                       'notnull': True}
                  ]
    }

    def get_csvfile_data(self, rows):
        csvfile = io.StringIO()
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow([c['name'] for c in self.table_spec['columns']])
        writer.writerows(rows)
        return csvfile.getvalue()
        

    def get_url(self, *segments):
        return URL('table', CONFIG['dbname'], self.table_spec['name'],*segments)

    def test_db_upload(self):
        "Create a database with table by file upload, check the table JSON."

        # Upload a file containing a plain Sqlite3 database.
        response = self.upload_file()
        self.assertEqual(response.status_code, http.client.OK)
        json_validate(response.json(), dbshare.schema.db.schema)

        # The table API JSON is valid.
        response = self.session.get(self.get_url())
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        json_validate(result, dbshare.schema.table.schema)
        rows_url = result['rows']['href']

        # The table rows JSON is valid.
        response = self.session.get(rows_url)
        self.assertEqual(response.status_code, http.client.OK)
        json_validate(response.json(), dbshare.schema.rows.schema)

        # Content negotiation for rows using URL without '.json' extension.
        response = self.session.get(rows_url.rstrip('.json'),
                                    headers={'Accept': constants.JSON_MIMETYPE})
        self.assertEqual(response.status_code, http.client.OK)
        json_validate(response.json(), dbshare.schema.rows.schema)

    def test_create(self):
        "Create a database and a table in it. Check the table definition."

        # Create an empty database.
        response = self.create_database()
        self.assertEqual(response.status_code, http.client.OK)

        # Create a table in the database.
        response = self.session.put(self.get_url(), json=self.table_spec)
        self.assertEqual(response.status_code, http.client.OK)

        # Check the created table.
        result = response.json()
        json_validate(result, dbshare.schema.table.schema)
        self.assertEqual(len(result['columns']),
                         len(self.table_spec['columns']))
        self.assertEqual(result['title'], self.table_spec['title'])
        lookup = dict([(c['name'], c) for c in self.table_spec['columns']])
        for column in result['columns']:
            self.assertTrue(column['name'] in lookup)
            self.assertEqual(column['type'], lookup[column['name']]['type'])

        # PRIMAY KEY implies NOT NULL.
        lookup = dict([(c['name'], c) for c in result['columns']])
        self.assertTrue(lookup['i']['primarykey'])
        self.assertTrue(lookup['i']['notnull'])

        # Delete the table.
        response = self.session.delete(self.get_url())
        self.assertEqual(response.status_code, http.client.NO_CONTENT)

        # Check no tables in the database.
        response = self.session.get(self.db_url)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(len(result['tables']), 0)

    def test_insert(self):
        "Create database and table; insert data."

        # Create an empty database.
        response = self.create_database()
        self.assertEqual(response.status_code, http.client.OK)

        # Create a table in the database.
        response = self.session.put(self.get_url(), json=self.table_spec)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 0)

        # Insert data.
        data = {'data': [{'i': 1, 't': 'stuff', 'r': 1.2345}] }
        response = self.session.post(self.get_url('insert'), json=data)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 1)

        data = {'data': [{'i': 2, 't': 'another', 'r': 3}] }
        response = self.session.post(self.get_url('insert'), json=data)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 2)

        data = {'data': [{'i': 3, 'r': -0.45}] }
        response = self.session.post(self.get_url('insert'), json=data)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 3)

        row_3 = {'i': 4, 't': 'multirow', 'r': -0.45}
        data = {'data': [row_3,
                         {'i': 5, 't': 'multirow 2', 'r': 1.2e4}] }
        response = self.session.post(self.get_url('insert'), json=data)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 5)

        # Try to insert invalid data of different kinds.
        data = {'data': [{'i': 3, 't': 'primary key clash', 'r': -0.1}] }
        response = self.session.post(self.get_url('insert'), json=data)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

        data = {'data': [{'i': 8, 't': 'missing value'}] }
        response = self.session.post(self.get_url('insert'), json=data)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

        data = {'data': [{'i': 9, 't': 'wrong type', 'r': 'string!'}] }
        response = self.session.post(self.get_url('insert'), json=data)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

        response = self.session.get(self.get_url())
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 5)

        # Get the rows and compare one of them
        response = self.session.get(result['rows']['href'])
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 5)
        self.assertEqual(len(result['data']), result['nrows'])
        self.assertEqual(result['data'][3], row_3)

        # Empty the table.
        response = self.session.post(self.get_url('empty'))
        self.assertEqual(response.status_code, http.client.OK)
        response = self.session.get(self.get_url())
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 0)

    def test_csv(self):
        "Create database and table; insert CSV operations."

        # Create an empty database.
        response = self.create_database()
        self.assertEqual(response.status_code, http.client.OK)

        # Create a table in the database.
        response = self.session.put(self.get_url(), json=self.table_spec)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 0)

        headers = {'Content-Type': 'text/csv'}

        # Insert CSV data.
        data = self.get_csvfile_data([(1, 'test', 0.2),
                                      (2, 'another test', 4.123e5),
                                      (3, 'third', -13)])
        response = self.session.post(self.get_url('insert'),
                                     data=data,headers=headers)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 3)

        # Row with None for a pkey item.
        data = self.get_csvfile_data([(None, 'missing pkey', 0.2)])
        response = self.session.post(self.get_url('insert'),
                                     data=data,headers=headers)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

        # Row with too many items.
        data = self.get_csvfile_data([(1, 'test', 2.1, 'superfluous')])
        response = self.session.post(self.get_url('insert'),
                                     data=data,headers=headers)
        self.assertEqual(response.status_code, http.client.BAD_REQUEST)

    def test_update(self):
        "Create database and table; insert and update using CSV."

        # Create an empty database.
        response = self.create_database()
        self.assertEqual(response.status_code, http.client.OK)

        # Create a table in the database.
        response = self.session.put(self.get_url(), json=self.table_spec)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 0)

        headers = {'Content-Type': 'text/csv'}

        # Insert CSV data.
        data = self.get_csvfile_data([(1, 'test', 0.2),
                                      (2, 'another test', 4.123e5),
                                      (3, 'third', -13)])
        response = self.session.post(self.get_url('insert'),
                                     data=data,headers=headers)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 3)

        # Update CSV data; check that it actually changed anything.
        data = self.get_csvfile_data([(1, 'changed', -1.0)])
        response = self.session.post(self.get_url('update'),
                                     data=data,headers=headers)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 3)

        response = self.session.get(result['rows']['href'])
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        rows = result['data']
        self.assertEqual(rows[0]['i'], 1)
        self.assertEqual(rows[0]['t'], 'changed')
        self.assertEqual(rows[2]['i'], 3)
        self.assertEqual(rows[2]['t'], 'third')

        # Update non-existent row; should not change anything.
        data = self.get_csvfile_data([(4, 'this row does not exist', 1.0)])
        response = self.session.post(self.get_url('update'),
                                     data=data,headers=headers)
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(result['nrows'], 3)
        response = self.session.get(result['rows']['href'])
        self.assertEqual(response.status_code, http.client.OK)
        result = response.json()
        self.assertEqual(rows, result['data'])


if __name__ == '__main__':
    run()
