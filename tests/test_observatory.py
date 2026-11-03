import unittest
from research.observatory import signals,valid_package,downstream_change,github_repository

META={'name':'example','dist-tags':{'latest':'1.1.0'},'versions':{'1.0.0':{},'1.1.0':{}},'time':{'created':'2019-01-01T00:00:00Z','1.0.0':'2020-01-01T00:00:00Z','1.1.0':'2020-02-01T00:00:00Z'}}

class SignalTests(unittest.TestCase):
    def test_old_package_is_not_declared_abandoned(self):
        row=signals(META,'2026-01-01T00:00:00Z')
        self.assertEqual(row['maintenance_signal'],'possibly inactive')
        self.assertEqual(row['median_release_gap_days'],31)
        self.assertIsNone(row['archived']);self.assertIsNone(row['advisories_for_latest'])
    def test_explicit_deprecation_and_archival_separate(self):
        meta={**META,'versions':{'1.0.0':{},'1.1.0':{'deprecated':'Use another package instead'}}}
        row=signals(meta,'2026-01-01T00:00:00Z',True,0)
        self.assertEqual(row['maintenance_signal'],'explicitly deprecated')
        self.assertTrue(row['archived']);self.assertEqual(row['advisories_for_latest'],0)
        self.assertIsNotNone(row['replacement_recommendation'])
    def test_missing_is_not_removal(self):
        old={'dependencies':{'example':'^1'}}
        self.assertEqual(downstream_change(old,None,'example')['outcome'],'unknown')
        self.assertEqual(downstream_change(old,{},'example')['outcome'],'removed')
    def test_declared_range_not_resolved_version(self):
        old={'dependencies':{'example':'^1'}};new={'dependencies':{'example':'^2'}}
        row=downstream_change(old,new,'example')
        self.assertEqual(row['outcome'],'range updated');self.assertIsNone(row['resolved_version'])
        self.assertIsNone(row['response_days_upper_bound'])
    def test_right_censoring_and_upper_bound(self):
        old={'dependencies':{'example':'^1'}}
        self.assertTrue(downstream_change(old,old,'example')['right_censored'])
        row=downstream_change(old,{},'example','2020-02-01T00:00:00Z','2020-03-01T00:00:00Z','2020-01-01T00:00:00Z')
        self.assertEqual(row['response_days_upper_bound'],60)
    def test_bad_metadata_and_names(self):
        with self.assertRaises(ValueError):signals({},'2026-01-01T00:00:00Z')
        for name in ['../foo','https://evil.example','a?x=1','UPPER']:
            with self.assertRaises(ValueError): valid_package(name)
        self.assertEqual(valid_package('@scope/name'),'@scope/name')
    def test_repository_normalization(self):
        self.assertEqual(github_repository({'url':'git+https://github.com/facebook/react.git'}),'facebook/react')
        self.assertIsNone(github_repository('https://example.org/test'))

if __name__=='__main__':unittest.main()
