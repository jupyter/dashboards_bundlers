# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import requests
from notebook.utils import url_path_join
from tornado import escape, web
from tornado.log import access_log

UPLOAD_ENDPOINT = '/_api/notebooks/'
VIEW_ENDPOINT = '/dashboards/'

def bundle(handler, abs_nb_path):
    '''
    Uploads a notebook to a Jupyter Dashboard Server
    '''
    # Get name of notebook from filename
    notebook_basename = os.path.basename(abs_nb_path)
    notebook_name = os.path.splitext(notebook_basename)[0]
    if 'DASHBOARD_SERVER_URL' in os.environ:
        dashboard_url = url_path_join(os.getenv('DASHBOARD_SERVER_URL'), UPLOAD_ENDPOINT, escape.url_escape(notebook_name, False))
        with open(abs_nb_path, 'rb') as notebook:
            headers = {}
            if 'DASHBOARD_SERVER_AUTH_TOKEN' in os.environ:
                headers['Authorization'] = os.getenv('DASHBOARD_SERVER_AUTH_TOKEN')
            result = requests.post(dashboard_url, files={'file': notebook}, headers=headers, timeout=60)
            result.raise_for_status()
            handler.redirect(url_path_join(os.getenv('DASHBOARD_SERVER_URL'), VIEW_ENDPOINT, escape.url_escape(notebook_name, False)))
    else:
        access_log.debug('Can not deploy, DASHBOARD_SERVER_URL not set')
        raise web.HTTPError(500, log_message='No dashboard server configured')
