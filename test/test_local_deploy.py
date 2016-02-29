# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import unittest
import shutil
import os
import tempfile
import dashboards_bundlers.local_deploy as converter
from os.path import join as pjoin
from os.path import isdir, isfile, exists
from jupyter_core.paths import jupyter_data_dir

# Mock existence of declarative widgets
DECL_WIDGETS_DIR = pjoin(jupyter_data_dir(), 'nbextensions/urth_widgets/')
DECL_WIDGETS_JS_DIR = pjoin(DECL_WIDGETS_DIR, 'js')
DECL_VIZ_DIR = pjoin(DECL_WIDGETS_DIR, 'components/urth-viz')
DECL_CORE_DIR = pjoin(DECL_WIDGETS_DIR, 'components/urth-core')
BOWER_COMPONENT_DIR = pjoin(jupyter_data_dir(), 'nbextensions/urth_widgets/urth_components/component-a')

class MockHandler(object):
    def __init__(self, notebook_dir):
        self.notebook_dir = notebook_dir
        self.settings = {
            'base_url' : '/'
        }
        self.last_redirect = None
        self.tools = None

    def redirect(self, location):
        self.last_redirect = location

class TestLocalDeploy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.makedirs(DECL_WIDGETS_JS_DIR)
        os.makedirs(DECL_CORE_DIR)
        os.makedirs(DECL_VIZ_DIR)
        os.makedirs(BOWER_COMPONENT_DIR)

    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_bundle(self):
        '''Should bundle and redirect to the application output dzirectory.'''
        handler = MockHandler(self.tmp)
        converter.bundle(handler, 'test/resources/no_imports.ipynb')

        output_dir = pjoin(self.tmp, 'local_dashboards', 'no_imports')
        self.assertTrue(isdir(output_dir), 'app directory should exist')
        self.assertEqual(handler.last_redirect, '/files/local_dashboards/no_imports/index.html',
            'redirect to application url')

    def test_bundle_index(self):
        '''Should write a valid index.html.'''
        converter.bundle_index(self.tmp, 'test/resources/no_imports.ipynb')
        self.assertTrue(isfile(pjoin(self.tmp, 'index.html')), 'index.html should exist')
        with open(pjoin(self.tmp, 'index.html')) as f:
            contents = f.read()
            self.assertIn('DOCTYPE', contents, 'should declare a DOCTYPE')
            self.assertIn('data-main="./static/main.js', contents, 'should load main.js script')
            self.assertIn("origin = window.location.origin", contents, 'should use local notebook server for kernels')
            self.assertIn("tmpnb_mode = false", contents, 'should not use tmpnb spawn API')
            self.assertIn("kernel_name = 'python3'", contents, 'should use correct kernel')

    def test_bundle_web_static(self):
        '''Should write a static directory.'''
        converter.bundle_web_static(self.tmp)
        # Check path from converter
        self.assertTrue(isdir(pjoin(self.tmp, 'static', 'bower_components')), 'bower_components should exist')
        # Check file from converter
        self.assertTrue(isfile(pjoin(self.tmp, 'static', 'main.js')), 'main.js should exist')
        # Check path from extension source
        self.assertTrue(isdir(pjoin(self.tmp, 'static', 'dashboard-common')), 'dashboard-common should exist')

    def test_bundle_declarative_widgets(self):
        '''Should write declarative widgets to output.'''
        converter.bundle_declarative_widgets(self.tmp, 'test/resources/env.ipynb')
        self.assertTrue(exists(pjoin(self.tmp, 'static/urth_widgets')), 'urth_widgets should exist')
        self.assertTrue(exists(pjoin(self.tmp, 'static/urth_components')), 'urth_components should exist')

    def test_skip_declarative_widgets(self):
        '''Should not write declarative widgets to output.'''
        # Testing to make sure we do not add bower components if we do not need to
        converter.bundle_declarative_widgets(self.tmp, 'test/resources/no_imports.ipynb')
        self.assertFalse(exists(pjoin(self.tmp, 'static/urth_widgets')), 'urth_widgets should not exist')
        self.assertFalse(exists(pjoin(self.tmp, 'static/urth_components')), 'urth_components should not exist')
