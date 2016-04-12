# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import unittest
import shutil
import os
import tempfile
import dashboards_bundlers.server_download as converter
import jupyter_cms
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
        self.tools = jupyter_cms.bundler.BundlerTools()

    def set_header(self, name, value):
        self.headers[name] = value

    def write(self, *args):
        self.written = True

    def finish(self):
        self.finished = True

class TestServerDownload(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        
    def test_bundle_ipynb(self):
        '''Should initialize an ipynb file download.'''
        handler = MockHandler(self.tmp)
        converter.bundle(handler, 'test/resources/no_imports.ipynb')
        
        output_dir = pjoin(self.tmp, 'no_imports')
        self.assertFalse(isdir(output_dir), 'app directory should no longer exist')
        self.assertTrue(handler.written, 'data should be written')
        self.assertTrue(handler.finished, 'response should be finished')
        self.assertIn('application/json', handler.headers['Content-Type'], 
            'headers should set json content type')
        self.assertIn('no_imports.ipynb', handler.headers['Content-Disposition'], 
            'headers should name the ipynb file')
        
    def test_bundle_zip(self):
        '''Should bundle and initiate a zip file download.'''
        handler = MockHandler(self.tmp)
        converter.bundle(handler, 'test/resources/some.ipynb')
    
        output_dir = pjoin(self.tmp, 'some')
        self.assertFalse(isdir(output_dir), 'app directory should no longer exist')
        self.assertTrue(handler.written, 'data should be written')
        self.assertTrue(handler.finished, 'response should be finished')
        self.assertIn('application/zip', handler.headers['Content-Type'], 
            'headers should set zip content type')
        self.assertIn('some.zip', handler.headers['Content-Disposition'], 
            'headers should name the zip file')