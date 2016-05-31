# Copyright (c) Jupyter Development Team.
# Distributed under the terms of the Modified BSD License.

import unittest
import copy
import os
import zipfile
import dashboards_bundlers.server_upload as converter
import jupyter_cms
from tornado import web

dashboard_link = 'http://notebook-server:3000/dashboards/test'

class MockResult(object):
    def __init__(self, status_code, include_link=True):
        self.status_code = status_code
        if (include_link):
            self.json = lambda : { 'link': dashboard_link }
        else:
            self.json = lambda : {}

class MockPost(object):
    def __init__(self, status_code, include_result_link=True):
        self.args = None
        self.kwargs = None
        self.status_code = status_code
        self.include_result_link = include_result_link

    def __call__(self, *args, **kwargs):
        if self.args or self.kwargs:
            raise RuntimeError('MockPost already invoked')
        self.args = args
        self.kwargs = kwargs
        return MockResult(self.status_code, self.include_result_link)

class MockZipPost(object):
    '''
    Explicitly checks for a posted zip file
    '''
    def __init__(self, status_code):
        self.args = None
        self.kwargs = None
        self.status_code = status_code

    def __call__(self, *args, **kwargs):
        if self.args or self.kwargs:
            raise RuntimeError('MockZipPost already invoked')
        self.args = args
        self.kwargs = kwargs
        uploaded_zip = zipfile.ZipFile(kwargs['files']['file'], 'r')
        self.zipped_files = uploaded_zip.namelist()
        return MockResult(self.status_code)

class MockRequest(object):
    def __init__(self, host, protocol):
        self.host = host
        self.protocol = protocol

class MockHandler(object):
    def __init__(self, host='notebook-server:8888', protocol='http'):
        self.request = MockRequest(host, protocol)
        self.last_redirect = None
        self.tools = jupyter_cms.bundler.BundlerTools()

    def redirect(self, location):
        self.last_redirect = location

class TestServerUpload(unittest.TestCase):
    def setUp(self):
        self.origin_env = copy.deepcopy(os.environ)
        converter.requests.post = MockPost(200)

    def tearDown(self):
        os.environ = self.origin_env

    def test_no_server(self):
        '''Should error if no server URL is set.'''
        handler = MockHandler('fake-host:8000', 'http')
        self.assertRaises(web.HTTPError, converter.bundle,
            handler, 'test/resources/no_imports.ipynb')

    def test_upload_notebook(self):
        '''Should POST the notebook and redirect to the dashboard server.'''
        os.environ['DASHBOARD_SERVER_URL'] = 'http://dashboard-server'
        handler = MockHandler()
        converter.bundle(handler, 'test/resources/no_imports.ipynb')

        args = converter.requests.post.args
        kwargs = converter.requests.post.kwargs
        self.assertEqual(args[0], 'http://dashboard-server/_api/notebooks/no_imports')
        self.assertTrue(kwargs['files']['file'])
        self.assertEqual(kwargs['headers'], {})
        self.assertEqual(handler.last_redirect, dashboard_link)

    def test_upload_zip(self):
        '''
        Should POST the notebook in a zip with resources and redirect to
        the dashboard server.
        '''
        os.environ['DASHBOARD_SERVER_URL'] = 'http://dashboard-server'
        handler = MockHandler()
        converter.requests.post = MockZipPost(200)
        converter.bundle(handler, 'test/resources/some.ipynb')

        args = converter.requests.post.args
        kwargs = converter.requests.post.kwargs
        self.assertEqual(args[0], 'http://dashboard-server/_api/notebooks/some')
        self.assertTrue(kwargs['files']['file'])
        self.assertEqual(kwargs['headers'], {})
        self.assertEqual(handler.last_redirect, dashboard_link)
        self.assertTrue('index.ipynb' in converter.requests.post.zipped_files)
        self.assertTrue('some.csv' in converter.requests.post.zipped_files)

    def test_upload_token(self):
        '''Should include an auth token in the request.'''
        os.environ['DASHBOARD_SERVER_URL'] = 'http://dashboard-server'
        os.environ['DASHBOARD_SERVER_AUTH_TOKEN'] = 'fake-token'
        handler = MockHandler()
        converter.bundle(handler, 'test/resources/no_imports.ipynb')

        kwargs = converter.requests.post.kwargs
        self.assertEqual(kwargs['headers'],
            {'Authorization' : 'token fake-token'})

    def test_url_interpolation(self):
        '''Should build the server URL from the request Host header.'''
        os.environ['DASHBOARD_SERVER_URL'] = '{protocol}://{hostname}:8889'
        handler = MockHandler('notebook-server:8888', 'https')
        converter.bundle(handler, 'test/resources/no_imports.ipynb')

        args = converter.requests.post.args
        self.assertEqual(args[0], 'https://notebook-server:8889/_api/notebooks/no_imports')
        self.assertEqual(handler.last_redirect, dashboard_link)

    def test_redirect_fallback(self):
        '''Should redirect to the given URL'''
        converter.requests.post = MockPost(200, False)
        os.environ['DASHBOARD_SERVER_URL'] = '{protocol}://{hostname}:8889'
        os.environ['DASHBOARD_REDIRECT_URL'] = 'http://{hostname}:3000'
        handler = MockHandler('notebook-server:8888', 'https')
        converter.bundle(handler, 'test/resources/no_imports.ipynb')

        args = converter.requests.post.args
        self.assertEqual(args[0], 'https://notebook-server:8889/_api/notebooks/no_imports')
        self.assertEqual(handler.last_redirect,
            'http://notebook-server:3000/dashboards/no_imports')

    def test_ssl_verify(self):
        '''Should verify SSL certificate by default.'''
        handler = MockHandler()
        os.environ['DASHBOARD_SERVER_URL'] = '{protocol}://{hostname}:8889'
        converter.bundle(handler, 'test/resources/no_imports.ipynb')
        kwargs = converter.requests.post.kwargs
        self.assertEqual(kwargs['verify'], True)
        
    def test_no_ssl_verify(self):
        '''Should skip SSL certificate verification.'''
        os.environ['DASHBOARD_SERVER_NO_SSL_VERIFY'] = 'yes'
        os.environ['DASHBOARD_SERVER_URL'] = '{protocol}://{hostname}:8889'
        handler = MockHandler()
        converter.bundle(handler, 'test/resources/no_imports.ipynb')
        kwargs = converter.requests.post.kwargs
        self.assertEqual(kwargs['verify'], False)