"Database lists API endpoints."

import http.client

import flask

import dbshare.dbs
import dbshare.user

import dbshare.api.db
import dbshare.api.user

from dbshare import utils


blueprint = flask.Blueprint('api_dbs', __name__)

@blueprint.route('/public')
def public():
    "Return the list of public databases."
    return flask.jsonify(
        utils.get_api(title='Public databases',
                      databases=get_api(dbshare.dbs.get_dbs(public=True))))

@blueprint.route('/all')
@dbshare.user.admin_required
def all():
    "Return the list of all databases."
    dbs = dbshare.dbs.get_dbs()
    return flask.jsonify(
        utils.get_api(title='All databases',
                      total_size=sum([db['size'] for db in dbs]),
                      databases=get_api(dbs)))

@blueprint.route('/owner/<name:username>')
@dbshare.user.login_required
def owner(username):
    "Return the list of databases owned by the given user."
    if not dbshare.dbs.has_access(username):
        return flask.abort(http.client.UNAUTHORIZED)
    dbs = dbshare.dbs.get_dbs(owner=username)
    return flask.jsonify(
        utils.get_api(title=f"Databases owned by {username}",
                      user=dbshare.api.user.get_api(username),
                      total_size=sum([db['size'] for db in dbs]),
                      databases=get_api(dbs)))

def get_api(dbs):
    "Return API JSON for the databases."
    result = []
    for db in dbs:
        data = dbshare.api.db.get_api(db)
        data['href'] = utils.url_for('api_db.database', dbname=db['name'])
        result.append(data)
    return result