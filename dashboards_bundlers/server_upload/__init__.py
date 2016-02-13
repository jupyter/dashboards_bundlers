# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import requests
from notebook.utils import url_path_join
from tornado import escape, web
from tornado.log import access_log, app_log

UPLOAD_ENDPOINT = '/_api/notebooks/'
VIEW_ENDPOINT = '/dashboards/'

def bundle(handler, abs_nb_path):
    '''
    Uploads a notebook to a Jupyter Dashboard Server
    '''
    # Get name of notebook from filename
    notebook_basename = os.path.basename(abs_nb_path)
    notebook_name = os.path.splitext(notebook_basename)[0]

    # Make information about the request Host header available for use in
    # constructing the urls
    segs = handler.request.host.split(':')
    hostname = segs[0]
    if len(segs) > 1:
        port = segs[1]
    else:
        port = ''
    protocol = handler.request.protocol

    # Treat empty as undefined
    dashboard_server = os.getenv('DASHBOARD_SERVER_URL')
    if dashboard_server:
        dashboard_server = dashboard_server.format(protocol=protocol,
            hostname=hostname, port=port)
        upload_url = url_path_join(dashboard_server, UPLOAD_ENDPOINT,
            escape.url_escape(notebook_name, False))
        with open(abs_nb_path, 'rb') as notebook:
            headers = {}
            token = os.getenv('DASHBOARD_SERVER_AUTH_TOKEN')
            if token:
                # TODO: server side should expect Authorization: token <value>
                headers['Authorization'] = token
            result = requests.post(upload_url, files={'file': notebook},
                headers=headers, timeout=60)
            if result.status_code >= 400:
                raise web.HTTPError(result.status_code)

        # Redirect for client might be different from internal upload URL
        redirect_server = os.getenv('DASHBOARD_REDIRECT_URL')
        if redirect_server:
            redirect_root = redirect_server.format(hostname=hostname,
                port=port, protocol=protocol)
        else:
            redirect_root = dashboard_server
        handler.redirect(url_path_join(redirect_root, VIEW_ENDPOINT, escape.url_escape(notebook_name, False)))
    else:
        access_log.debug('Can not deploy, DASHBOARD_SERVER_URL not set')
        raise web.HTTPError(500, log_message='No dashboard server configured')
