# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import nbformat
import requests
import shutil
import tempfile
from jupyter_core.paths import jupyter_path
from notebook.utils import url_path_join
from os.path import join as pjoin
from tornado import escape, web
from tornado.log import access_log, app_log

UPLOAD_ENDPOINT = '/_api/notebooks/'
VIEW_ENDPOINT = '/dashboards/'


def skip_ssl_verification():
    return os.getenv('DASHBOARD_SERVER_NO_SSL_VERIFY', '').lower() in ['yes', 'true']


# Log a warning if SSL verification is off at the outset
if skip_ssl_verification():
    app_log.warn('Dashboard server SSL verification disabled')


def bundle(handler, model):
    '''
    Uploads a notebook to a Jupyter Dashboard Server, either by itself, or
    within a zip file with associated data and widget files
    '''
    # Noteook implementation passes ContentManager models. This
    # bundler only works with local files anyway.
    abs_nb_path = os.path.join(
        handler.settings['contents_manager'].root_dir,
        model['path']
    )

    # Get name of notebook from filename
    notebook_basename = os.path.basename(abs_nb_path)
    notebook_name = os.path.splitext(notebook_basename)[0]

    # Python 2/3 compatible try/finally to cleanup a temp working directory
    tmp_dir = tempfile.mkdtemp()
    try:
        output_dir = os.path.join(tmp_dir, notebook_name)
        bundled = make_upload_bundle(abs_nb_path, output_dir, handler.tools)
        send_file(bundled, notebook_name, handler)
    finally:
        shutil.rmtree(tmp_dir, True)


def get_extension_path(*parts):
    '''
    Searches all known jupyter extension paths for the referenced directory.
    Returns the first hit or None if not found.
    '''
    ext_path = pjoin(*parts)
    for root_path in jupyter_path():
        full_path = pjoin(root_path, 'nbextensions', ext_path)
        if os.path.exists(full_path):
            return full_path


def bundle_file_references(output_path, notebook_fn, tools):
    '''
    Looks for files references in the notebook in the manner supported by
    notebook.bundler.tools. Adds those files to the output path if found.

    :param output_path: The output path of the dashboard being assembled
    :param notebook_fn: The absolute path to the notebook file being packaged
    '''
    if tools is not None:
        referenced_files = tools.get_file_references(notebook_fn, 4)
        tools.copy_filelist(os.path.dirname(notebook_fn), output_path,
                            referenced_files)


def bundle_declarative_widgets(output_path, notebook_file, widget_folder='static'):
    '''
    Adds frontend bower components dependencies into the bundle for the dashboard
    application. Creates the following directories under output_path:

    static/urth_widgets: Stores the js for urth_widgets which will be loaded in
                         the frontend of the dashboard
    static/urth_components: The directory for all of the bower components of the
                            dashboard.

    NOTE: This function is too specific to urth widgets. In the
        future we should investigate ways to make this more generic.

    :param output_path: The output path of the dashboard being assembled
    :param notebook_file: The absolute path to the notebook file being packaged
    :param widget_folder: Subfolder name in which the widgets should be contained.
    '''
    # Check if any of the cells contain widgets, if not we do not to copy the
    # bower_components
    notebook = nbformat.read(notebook_file, 4)
    # Using find instead of a regex to help future-proof changes that might be
    # to how user's will use urth-core-import
    # (i.e. <link is=urth-core-import> vs. <urth-core-import>)
    any_cells_with_widgets = any(cell.get('source').find('urth-core-') != -1
                                 for cell in notebook.cells)
    if not any_cells_with_widgets:
        return

    # Directory of declarative widgets extension
    widgets_dir = get_extension_path('declarativewidgets') or get_extension_path('urth_widgets')
    if widgets_dir is None:
        raise web.HTTPError(500, 'Missing jupyter_declarativewidgets extension')

    # Root of declarative widgets within a dashboard app
    output_widgets_dir = pjoin(output_path, widget_folder, 'urth_widgets/') if widget_folder is not None else pjoin(output_path, 'urth_widgets/')
    # JavaScript entry point for widgets in dashboard app
    output_js_dir = pjoin(output_widgets_dir, 'js')
    # Web referenceable path from which all urth widget components will be served
    output_components_dir = pjoin(output_path, widget_folder, 'urth_components/') if widget_folder is not None else pjoin(output_path, 'urth_components/')

    # Copy declarative widgets js and installed bower components into the app
    # under output directory
    widgets_js_dir = pjoin(widgets_dir, 'js')
    shutil.copytree(widgets_js_dir, output_js_dir)

    # Widgets bower components could be under 'urth_components' or
    # 'bower_components' depending on the version of widgets being used.
    widgets_components_dir = pjoin(widgets_dir, 'urth_components')
    if not os.path.isdir(widgets_components_dir):
        widgets_components_dir = pjoin(widgets_dir, 'bower_components')

    # Install the widget components into the output components directory
    shutil.copytree(widgets_components_dir, output_components_dir)


def make_upload_bundle(abs_nb_path, staging_dir, tools):
    '''
    Assembles the notebook and resources it needs, returning the path to a
    zip file bundling the notebook and its requirements if there are any,
    the notebook's path otherwise.
    :param abs_nb_path: The path to the notebook
    :param staging_dir: Temporary work directory, created and removed by the
        caller
    '''
    # Clean up bundle dir if it exists
    shutil.rmtree(staging_dir, True)
    os.makedirs(staging_dir)

    # Include the notebook as index.ipynb to make the final URL cleaner
    # and for consistency
    shutil.copy2(abs_nb_path, os.path.join(staging_dir, 'index.ipynb'))
    # Include frontend files referenced via the jupyter_cms bundle mechanism
    bundle_file_references(staging_dir, abs_nb_path, tools)
    bundle_declarative_widgets(staging_dir, abs_nb_path, widget_folder=None)

    # if nothing else was required, indicate to upload the notebook itself
    if len(os.listdir(staging_dir)) == 1:
        return abs_nb_path

    zip_file = shutil.make_archive(staging_dir, format='zip',
                                   root_dir=staging_dir, base_dir='.')
    return zip_file


def send_file(file_path, dashboard_name, handler):
    '''
    Posts a file to the Jupyter Dashboards Server to be served as a dashboard
    :param file_path: The path of the file to send
    :param dashboard_name: The dashboard name under which it should be made
        available
    '''
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
                                                   hostname=hostname,
                                                   port=port)
        upload_url = url_path_join(dashboard_server, UPLOAD_ENDPOINT,
                                   escape.url_escape(dashboard_name, False))
        with open(file_path, 'rb') as file_content:
            headers = {}
            token = os.getenv('DASHBOARD_SERVER_AUTH_TOKEN')
            if token:
                headers['Authorization'] = 'token {}'.format(token)
            result = requests.post(upload_url, files={'file': file_content},
                                   headers=headers, timeout=60, verify=not
                                   skip_ssl_verification())
            if result.status_code >= 400:
                raise web.HTTPError(result.status_code)

        # Redirect to link specified in response body
        res_body = result.json()
        if 'link' in res_body:
            redirect_link = res_body['link']
        else:
            # Compute redirect link using environment variables
            # First try redirect URL as it might be different from
            # internal upload URL
            redirect_server = os.getenv('DASHBOARD_REDIRECT_URL')
            if redirect_server:
                redirect_root = redirect_server.format(hostname=hostname,
                                                       port=port,
                                                       protocol=protocol)
            else:
                redirect_root = dashboard_server

            redirect_link = url_path_join(redirect_root, VIEW_ENDPOINT,
                                          escape.url_escape(dashboard_name,
                                                            False))
        handler.redirect(redirect_link)
    else:
        access_log.debug('Can not deploy, DASHBOARD_SERVER_URL not set')
        raise web.HTTPError(500, log_message='No dashboard server configured')
