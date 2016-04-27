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
from jupyter_core.paths import jupyter_path
from notebook.utils import url_path_join
from tornado import escape, web

# Location of this file
HERE = os.path.abspath(os.path.dirname(__file__))
# Absolute path to the default template
DEFAULT_TEMPLATE_PATH = pjoin(HERE, 'jinja_templates', 'index.html.tpl')
# Absolute path for dashboard static resources
STATICS_PATH = pjoin(HERE, 'static')

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

    # Generate the index.html file
    bundle_index(output_dir, abs_nb_path, DEFAULT_TEMPLATE_PATH)

    # Include frontend files referenced via the jupyter_cms bundle mechanism
    bundle_file_references(output_dir, abs_nb_path, handler.tools)

    # Include static web assets (e.g., Thebe)
    bundle_web_static(output_dir)

    # Copy declarative widgets if they were used
    bundle_declarative_widgets(output_dir, abs_nb_path)

    # Redirect the user to the new local app
    bundle_url_path = url_path_join(handler.settings['base_url'],
        'files',
        'local_dashboards',
        escape.url_escape(notebook_name, False),
        'index.html'
    )
    handler.redirect(bundle_url_path)

def bundle_index(output_path, notebook_fn, template_fn=DEFAULT_TEMPLATE_PATH, index_fn='index.html'):
    '''
    Runs nbconvert using the provided template and writes the HTML output as
    the given index filename under the output directory.

    :param output_path: The output path of the dashboard being assembled
    :param notebook_fn: The absolute path to the notebook file being packaged
    :param template_fn: The absolute path of the Jinja template for nbconvert
    :param index_fn: Basename of the file to write to the output_path
    '''
    # Invoke nbconvert to get the HTML
    full_output = create_index_html(notebook_fn, {}, 'html', os.getcwd(), template_fn)

    # Write out the index file
    with open(pjoin(output_path, index_fn), 'wb') as f:
        f.write(full_output)

def bundle_file_references(output_path, notebook_fn, tools):
    '''
    Looks for files references in the notebook in the manner supported by the
    jupyter_cms.BundlerTools. Adds those files to the output path if found.

    :param output_path: The output path of the dashboard being assembled
    :param notebook_fn: The absolute path to the notebook file being packaged
    '''
    if tools is not None:
        referenced_files = tools.get_file_references(notebook_fn, 4)
        tools.copy_filelist(os.path.dirname(notebook_fn), output_path, referenced_files)

def bundle_web_static(output_path):
    '''
    Copies all the static web assets needed for the dashboard to run stadalone
    to the static/ subdir of the output directory.

    :param output_path: The output path of the dashboard being assembled
    '''
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
        'bower_components/lodash/dist/lodash.min.js',
        'bower_components/requirejs/require.js'
    ]
    # Select only dashboard common files
    component_dirs = [
        'dashboard-common',
        'bower_components/jquery-ui/themes/smoothness/images'
    ]

    # Paths for dashboard extension source and destination in local app folder
    src_components = get_extension_path('jupyter_dashboards/notebook')
    if src_components is None:
        raise web.HTTPError(500, 'Missing jupyter_dashboards extension')
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
    # Check if any of the cells contain widgets, if not we do not to copy the bower_components
    notebook = nbformat.read(notebook_file, 4)
    # Using find instead of a regex to help future-proof changes that might be
    # to how user's will use urth-core-import
    # (i.e. <link is=urth-core-import> vs. <urth-core-import>)
    any_cells_with_widgets = any(cell.get('source').find('urth-core-') != -1 for cell in notebook.cells)
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

    # Always search for templates in the default template path as well as the
    # directory containing the provided template
    templates = '"{}","{}"'.format(
        os.path.dirname(template_fn),
        os.path.dirname(DEFAULT_TEMPLATE_PATH)
    )

    proc = subprocess.Popen([
        'jupyter',
        'nbconvert',
        '--log-level',
        'ERROR',
        '--stdout',
        '--TemplateExporter.template_path=[{}]'.format(templates),
        '--template',
        os.path.basename(template_fn),
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
