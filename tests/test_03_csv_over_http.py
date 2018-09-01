from __future__ import absolute_import
from . import ProgressiveTest
from progressivis.io import CSVLoader
from progressivis.table.constant import Constant
from progressivis.table.table import Table
from progressivis.datasets import get_dataset, DATA_DIR
from progressivis.core.utils import RandomBytesIO
#import logging, sys
from multiprocessing import Process
import time, os
import requests
from requests.packages.urllib3.exceptions import ReadTimeoutError
from requests.exceptions import ConnectionError


from RangeHTTPServer import RangeRequestHandler

import six
import shutil

if six.PY3:
    import http.server as http_srv
else:
    import SimpleHTTPServer as http_srv
        
class ThrottledReqHandler(RangeRequestHandler):
    threshold = 10**6
    sleep_times = 3
    def copyfile(self, src, dest):
        buffer_size = 1024*16
        sleep_times = ThrottledReqHandler.sleep_times
        if not self.range:
            cnt = 0
            while True:
                data = src.read(buffer_size)
                if not data:
                    break
                cnt += len(data)
                if sleep_times and cnt > ThrottledReqHandler.threshold:
                    time.sleep(1)
                    sleep_times -= 1
                dest.write(data)
        else:
            RangeRequestHandler.copyfile(self, src, dest)


def run_throttled_server(port=8000, threshold=10**6):
    _ = get_dataset('smallfile')
    _ = get_dataset('bigfile')
    os.chdir(DATA_DIR)
    ThrottledReqHandler.threshold = threshold
    if six.PY2:
        import sys
        sys.argv[1] = 8000
        http_srv.test(HandlerClass=ThrottledReqHandler)
    else:
        http_srv.test(HandlerClass=ThrottledReqHandler, port=port)

PORT = 8000
HOST = 'localhost'

def make_url(name):
    return 'http://{host}:{port}/{name}.csv'.format(host=HOST,
                                                        port=PORT,
                                                        name=name)

def run_simple_server():
    _ = get_dataset('smallfile')
    _ = get_dataset('bigfile')
    os.chdir(DATA_DIR)
    if six.PY2:
        import SimpleHTTPServer
        import RangeHTTPServer
        from RangeHTTPServer import RangeRequestHandler
        import sys
        sys.argv[1] = 8000
        SimpleHTTPServer.test(HandlerClass=RangeRequestHandler)
    else:
        import RangeHTTPServer.__main__
        
class TestProgressiveLoadCSVOverHTTP(ProgressiveTest):
    def setUp(self):
        super(TestProgressiveLoadCSVOverHTTP, self).setUp()        
        self._http_proc = None

    def tearDown(self):
        if self._http_proc is not None:
            try:
                self._http_proc.terminate()
                time.sleep(1)
            except:
                pass

    def test_01_read_http_csv_ok(self):
        p = Process(target=run_simple_server, args=())
        p.start()
        self._http_proc = p
        time.sleep(1)
        s=self.scheduler()
        module=CSVLoader(make_url('bigfile'), index_col=False, header=None, scheduler=s)
        self.assertTrue(module.table() is None)
        s.start()
        s.join()
        self.assertEqual(len(module.table()), 1000000)


    def test_02_read_http_csv_with_recovery(self):
        p = Process(target=run_throttled_server, args=(8000, 10**7))
        p.start()
        self._http_proc = p        
        time.sleep(1)        
        s=self.scheduler()
        module=CSVLoader(make_url('bigfile'), index_col=False, header=None, scheduler=s, timeout=0.01)
        self.assertTrue(module.table() is None)
        s.start()
        s.join()
        self.assertGreater(module.parser._recovery_cnt, 0)
        self.assertEqual(len(module.table()), 1000000)
        
    def test_03_read_multiple_csv(self):
        p = Process(target=run_throttled_server, args=(8000, 10**6))
        p.start()
        self._http_proc = p
        time.sleep(1) 
        s=self.scheduler()
        filenames = Table(name='file_names',
                          dshape='{filename: string}',
                          data={'filename': [make_url('smallfile'), make_url('smallfile')]})
        cst = Constant(table=filenames, scheduler=s)
        csv = CSVLoader(index_col=False, header=None, scheduler=s, timeout=0.01)
        csv.input.filenames = cst.output.table
        csv.start()
        s.join()
        self.assertEqual(len(csv.table()), 60000)

if __name__ == '__main__':
    ProgressiveTest.main()
