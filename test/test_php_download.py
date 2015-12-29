# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import unittest
import shutil
import os
import tempfile
import dashboards_bundlers.php_download as converter
from os.path import join as pjoin
from os.path import isdir, isfile, exists

class MockHandler(object):
    def __init__(self, notebook_dir):
        self.settings = {
            'base_url' : '/'
        }
        self.headers = {}
        self.request = type('HTTPRequest', (object,), {
            'protocol': 'http',
            'host': 'fake-host:5555'
        })
        self.written = False
        self.finished = False
        self.tools = None

    def set_header(self, name, value):
        self.headers[name] = value

    def write(self, *args):
        self.written = True

    def finish(self):
        self.finished = True

class TestPHPDownload(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_bundle(self):
        '''Should bundle and initiate a zip file download.'''
        handler = MockHandler(self.tmp)
        converter.bundle(handler, 'test/resources/no_imports.ipynb')

        output_dir = pjoin(self.tmp, 'no_imports')
        self.assertFalse(isdir(output_dir), 'app directory should no longer exist')
        self.assertTrue(handler.written, 'data should be written')
        self.assertTrue(handler.finished, 'response should be finished')
        self.assertIn('application/zip', handler.headers['Content-Type'], 
            'headers shuold set zip content type')
        self.assertIn('no_imports.zip', handler.headers['Content-Disposition'], 
            'headers should name the zip file')

    def test_bundle_index(self):
        '''Should write a valid index.php.'''
        converter.bundle_index(self.tmp, 'test/resources/no_imports.ipynb', 
            converter.DEFAULT_TEMPLATE_PATH, 'index.php')
        self.assertTrue(isfile(pjoin(self.tmp, 'index.php')), 'index.php should exist')
        with open(pjoin(self.tmp, 'index.php')) as f:
            contents = f.read()
            self.assertIn("thebe_url = '<?php echo $_ENV[\"KERNEL_SERVICE_URL\"] ?>'", contents, 
                'should read KERNEL_SERVICE_URL env var')
            self.assertIn("tmpnb_mode = ('<?php echo $_ENV[\"TMPNB_MODE\"] ?>'", contents, 
                'should read TMPNB_MODE env var')

    def test_bundle_meta(self):
        '''Should write preconfigured Dockerfile, manifest.yml, README.'''
        handler = MockHandler(self.tmp)
        converter.bundle_meta(self.tmp, 'fake-notebook', handler)
        self.assertTrue(isfile(pjoin(self.tmp, 'README.md')))
        
        self.assertTrue(isfile(pjoin(self.tmp, 'Dockerfile')))
        with open(pjoin(self.tmp, 'Dockerfile')) as f:
            contents = f.read()
        self.assertIn('ENV KERNEL_SERVICE_URL http://fake-host:5555/', contents)
        self.assertIn('ENV TMPNB_MODE false', contents)

        self.assertTrue(isfile(pjoin(self.tmp, 'manifest.yml')))
        with open(pjoin(self.tmp, 'manifest.yml')) as f:
            contents = f.read()
        self.assertIn('KERNEL_SERVICE_URL: http://fake-host:5555/', contents)
        # YAML requires quoting here else it gets cast as a bool which CF
        # does not like
        self.assertIn('TMPNB_MODE: "false"', contents)

class TestPHPDownloadWithEnviron(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        os.environ['TMPNB_MODE'] = 'true'
        os.environ['KERNEL_SERVICE_URL'] = 'http://another-fake:8888/'

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        del os.environ['TMPNB_MODE']
        del os.environ['KERNEL_SERVICE_URL']

    def test_bundle_meta(self):
        '''Should respect notebook env vars in Dockerfile, manifest.yml.'''
        handler = MockHandler(self.tmp)
        converter.bundle_meta(self.tmp, 'fake-notebook', handler)
        self.assertTrue(isfile(pjoin(self.tmp, 'README.md')))
        
        self.assertTrue(isfile(pjoin(self.tmp, 'Dockerfile')))
        with open(pjoin(self.tmp, 'Dockerfile')) as f:
            contents = f.read()
        self.assertIn('ENV KERNEL_SERVICE_URL http://another-fake:8888/', contents)
        self.assertIn('ENV TMPNB_MODE true', contents)

        self.assertTrue(isfile(pjoin(self.tmp, 'manifest.yml')))
        with open(pjoin(self.tmp, 'manifest.yml')) as f:
            contents = f.read()
        self.assertIn('KERNEL_SERVICE_URL: http://another-fake:8888/', contents)
        # YAML requires quoting here else it gets cast as a bool which CF
        # does not like
        self.assertIn('TMPNB_MODE: "true"', contents)
