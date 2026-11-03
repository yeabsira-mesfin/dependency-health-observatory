import unittest,json
from tempfile import TemporaryDirectory
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request
from research.common import JsonClient,CollectionError,SafeRedirect,csv_cell

class Response:
    status=200
    headers={}
    def __init__(self,data): self.raw=json.dumps(data).encode()
    def read(self,n): return self.raw[:n]
    def __enter__(self): return self
    def __exit__(self,*args): pass

class TransportTests(unittest.TestCase):
    def test_cache_preserves_observation_time_and_hash(self):
        with TemporaryDirectory() as t:
            client=JsonClient(t)
            with patch.object(client.opener,'open',return_value=Response({'a':1})) as call:
                self.assertEqual(client.get('https://api.github.com/repos/a/b'),{'a':1})
                first=client.sources[-1]
                self.assertEqual(client.get('https://api.github.com/repos/a/b'),{'a':1})
                self.assertEqual(call.call_count,1)
                self.assertEqual(first['observed_at'],client.sources[-1]['observed_at'])
                self.assertEqual(first['sha256'],client.sources[-1]['sha256'])
    def test_refuse_unsafe_hosts_and_credentials(self):
        with TemporaryDirectory() as t:
            client=JsonClient(t)
            for url in ['http://api.github.com/x','https://localhost/x','https://api.github.com.evil.test/x','https://u:p@api.github.com/x','https://api.github.com:444/x']:
                with self.assertRaises(CollectionError):client.get(url)
    def test_cross_host_redirect_refused(self):
        with self.assertRaises(CollectionError):
            SafeRedirect().redirect_request(Request('https://api.github.com/x'),None,302,'',{},'https://example.com')
    def test_pagination_reports_truncation(self):
        with TemporaryDirectory() as t:
            client=JsonClient(t)
            with patch.object(client,'get',side_effect=[[1,2],[3,4]]):
                rows,complete=client.pages('https://api.github.com/x',2,2)
                self.assertEqual(rows,[1,2,3,4]);self.assertFalse(complete)
            with patch.object(client,'get',side_effect=[[1,2],[]]):
                self.assertTrue(client.pages('https://api.github.com/x',2,2)[1])
    def test_rate_limit_long_wait_is_not_bypassed(self):
        with TemporaryDirectory() as t:
            client=JsonClient(t)
            with patch.object(client.opener,'open',side_effect=HTTPError('https://api.github.com/x',429,'rate limit',{'Retry-After':'100'},None)):
                with self.assertRaisesRegex(CollectionError,'later retry'):client.get('https://api.github.com/x')
    def test_bounded_retry_and_request_budget(self):
        with TemporaryDirectory() as t:
            client=JsonClient(t,max_requests=1)
            with patch.object(client.opener,'open',side_effect=HTTPError('https://api.github.com/x',503,'unavailable',{},None)),patch('research.common.time.sleep'):
                with self.assertRaisesRegex(CollectionError,'budget'):client.get('https://api.github.com/x')
    def test_offline_miss_is_explicit(self):
        with TemporaryDirectory() as t:
            with self.assertRaisesRegex(CollectionError,'Offline cache miss'):JsonClient(t,offline=True).get('https://api.github.com/x')
    def test_csv_formula_escaping(self):
        for value in ['=1+1',' +cmd','@SUM(A1)']:
            self.assertTrue(csv_cell(value).startswith("'"))
        self.assertEqual(csv_cell('safe'),'safe')

if __name__=='__main__':unittest.main()
