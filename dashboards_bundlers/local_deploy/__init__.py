# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import os
import shutil
import subprocess
import time
import re
import errno
import fnmatch
import glob
import nbformat
from os.path import join as pjoin
from tempfile import mkdtemp
from jupyter_core.paths import jupyter_data_dir
from notebook.utils import url_path_join
from tornado import escape

# Location of this file
HERE = os.path.abspath(os.path.dirname(__file__))
# Absolute path to nbconvert templates
TEMPLATES_PATH = pjoin(HERE, 'jinja_templates')
# Absolute path for dashboard static resources
STATICS_PATH = pjoin(HERE, 'static')

def bundle(handler, abs_nb_path):
    '''
    Bundles a notebook as a static web application on this Jupyter Notebook
    server and redirects the requestor there.
    '''
    # Get name of notebook from filename
    notebook_basename = os.path.basename(abs_nb_path)
    notebook_name = os.path.splitext(notebook_basename)[0]

    # Always put the app in a local_dashboards directory
    output_dir = pjoin(handler.notebook_dir, 'local_dashboards', notebook_name)

    # Clean up bundle dir if it exists
    shutil.rmtree(output_dir, True)
    os.makedirs(output_dir)

    # Bundle it
    bundle_app(abs_nb_path, output_dir, tools=handler.tools)

    # Redirect the user to the new local app
    bundle_url_path = url_path_join(handler.settings['base_url'],
        'files',
        'local_dashboards',
        escape.url_escape(notebook_name, False),
        'index.html'
    )
    handler.redirect(bundle_url_path)

def bundle_app(notebook_fn, output_path, template_fn=None, tools=None):
    '''
    Converts a notebook into a static web application that uses Thebe to request
    a kernel from the local Jupyter Notebook server where the notebook 
    originated. Deposits the application in the output path.

    :param notebook_fn: Notebook file path
    :param app_location: Output directory
    :param template_fn: Template file name
    :param tools: BundlerTools reference from jupyter_cms, if available
    :returns:
    '''
    # Invoke nbconvert to get the HTML
    full_output = create_index_html(notebook_fn, {}, 'html', os.getcwd(), template_fn)

    # Include frontend files referenced via the jupyter_cms bundle mechanism
    if tools is not None:
        referenced_files = tools.get_file_references(notebook_fn, 4)
        tools.copy_filelist(os.path.dirname(notebook_fn), output_path, referenced_files)

    # Write out the index file
    with open(pjoin(output_path, 'index.html'), 'wb') as f:
        f.write(full_output)

    # Copy static assets for Thebe
    shutil.copytree(STATICS_PATH, pjoin(output_path, 'static'))

    # Select specific files from bower_components, not whole git clones
    components = [
        'bower_components/gridstack/dist/gridstack.min.css',
        'bower_components/gridstack/dist/gridstack.min.js',
        'bower_components/gridstack/dist/gridstack.min.map',
        'bower_components/jquery/dist/jquery.min.js',
        'bower_components/jquery/dist/jquery.min.map',
        'bower_components/jquery-ui/themes/smoothness/jquery-ui.min.css',
        'bower_components/lodash/lodash.min.js',
        'bower_components/requirejs/require.js'
    ]
    # Select only dashboard common files
    component_dirs = [
        'dashboard-common',
        'bower_components/jquery-ui/themes/smoothness/images'
    ]

    # Paths for dashboard extension source and destination in local app folder
    src_components = pjoin(jupyter_data_dir(), 'nbextensions/urth_dash_js/notebook')
    dest_components = pjoin(output_path, 'static')

    # Copy individual files, making directories as we go
    for component in components:
        dest_file = pjoin(dest_components, component)
        dest_dir = os.path.dirname(dest_file)
        if not os.path.exists(dest_dir):
            os.makedirs(dest_dir)
        shutil.copy(pjoin(src_components, component), dest_file)
    
    # Copy entire directories
    for comp_dir in component_dirs:
        shutil.copytree(pjoin(src_components, comp_dir), pjoin(dest_components, comp_dir))

    # Copy declarative widgets if they were used
    bundle_declarative_widgets(output_path, notebook_fn)

    return output_path

def bundle_declarative_widgets(output_path, notebook_file):
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
    '''
    widgets_dir = pjoin(jupyter_data_dir(), 'nbextensions/urth_widgets')
    if not os.path.isdir(widgets_dir):
        return

    # Check if any of the cells contain widgets, if not we do not to copy the bower_components
    notebook = nbformat.read(notebook_file, 4)
    # Using find instead of a regex to help future-proof changes that might be
    # to how user's will use urth-core-import
    # (i.e. <link is=urth-core-import> vs. <urth-core-import>)
    any_cells_with_widgets = any(cell.get('source').find('urth-core-import') != -1 for cell in notebook.cells)
    if not any_cells_with_widgets:
        return

    # Directory of declarative widgets extension
    widgets_dir = pjoin(jupyter_data_dir(), 'nbextensions/urth_widgets')
    # Root of declarative widgets within a dashboard app
    output_widgets_dir = pjoin(output_path, 'static/urth_widgets/')
    # JavaScript entry point for widgets in dashboard app
    output_js_dir = pjoin(output_widgets_dir, 'js')
    # Web referenceable path from which all urth widget components will be served
    output_components_dir = pjoin(output_path, 'static/urth_components/')

    # Copy declarative widgets js and installed bower components into the app 
    # under output directory
    widgets_js_dir = pjoin(widgets_dir, 'js')
    shutil.copytree(widgets_js_dir, output_js_dir)

    # Install the bower components into the output components directory
    shutil.copytree(pjoin(widgets_dir, 'bower_components'), output_components_dir)

def create_index_html(path, env_vars, fmt, cwd, template_fn):
    '''
    Converts a notebook at path with env vars and current working directory set.
    If the conversion subprocess emits anything on its stderr, raises
    RuntimeError. Otherwise, returns the notebook in the requested format:
    html or notebook (JSON).
    '''
    if env_vars is None:
        env_vars = {}
    env_vars['PATH'] = os.environ['PATH']

    proc = subprocess.Popen([
        'ipython',
        'nbconvert',
        '--log-level',
        'ERROR',
        '--stdout',
        '--TemplateExporter.template_path=["{}"]'.format(TEMPLATES_PATH),
        '--template',
        template_fn if template_fn is not None and os.path.isfile(pjoin(TEMPLATES_PATH, template_fn)) else 'thebe.tpl',
        '--to',
        fmt,
        path
    ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        env=env_vars
    )
    stdout, stderr = proc.communicate()
    if stderr:
        raise RuntimeError('nbconvert wrote to stderr: {}'.format(stderr))
    return stdout
