import copy
import datetime as dt
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET

spec=importlib.util.spec_from_file_location('rhythm',Path(__file__).parents[1]/'scripts/generate_contribution_rhythm.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def fixture(start='2026-09-13', n=8, counts=None):
    a=dt.date.fromisoformat(start);counts=counts or [0,1,3,5,0,8,12,2][:n]
    rows=[dict(date=(a+dt.timedelta(days=i)).isoformat(),count=c,level=0 if c==0 else 1 if c<4 else 2 if c<9 else 3) for i,c in enumerate(counts)]
    return dict(schemaVersion=1,username='takagibit18',status='ready',period={'from':start,'to':rows[-1]['date']},fetchedAt='2026-09-20T04:00:00Z',timezone='UTC',totalContributions=sum(counts),days=rows,source={'kind':'test-fixture'})

class CalendarTests(unittest.TestCase):
    def test_sunday_not_moved_into_following_week(self):
        self.assertEqual(m.grid_position('2026-09-13','2026-09-13'),(0,6))
        self.assertEqual(m.grid_position('2026-09-14','2026-09-13'),(1,0))
    def test_year_boundary(self):
        self.assertEqual(m.grid_position('2027-01-01','2026-12-28'),(0,4))
    def test_leap_day(self):
        d=fixture('2024-02-27',counts=[0,1,2,3]);self.assertEqual(d['days'][2]['date'],'2024-02-29');m.validate(d)
    def test_counts_reconcile(self):m.validate(fixture())
    def test_missing_day_rejected(self):
        d=fixture();d['days'].pop(2)
        with self.assertRaises(ValueError):m.validate(d)
    def test_duplicate_day_rejected(self):
        d=fixture();d['days'][1]['date']=d['days'][0]['date']
        with self.assertRaises(ValueError):m.validate(d)
    def test_negative_count_rejected(self):
        d=fixture();d['days'][1]['count']=-1
        with self.assertRaises(ValueError):m.validate(d)
    def test_false_is_not_a_number(self):
        d=fixture();d['days'][0]['count']=False
        with self.assertRaises(ValueError):m.validate(d)
    def test_aggregate_mismatch_rejected(self):
        d=fixture();d['totalContributions']+=1
        with self.assertRaises(ValueError):m.validate(d)
    def test_zero_level_consistency(self):
        d=fixture();d['days'][0]['level']=3
        with self.assertRaises(ValueError):m.validate(d)
    def test_demo_never_published(self):
        d=fixture();d['status']='demo'
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):m.publish(d,Path(tmp))
            self.assertEqual(list(Path(tmp).iterdir()),[])
    def test_unavailable_is_not_zero(self):
        d=fixture();d.update(status='unavailable',days=[],totalContributions=None);m.validate(d)
        self.assertIn('No contribution counts loaded',m.svg(d,'dark'))
        d['totalContributions']=0
        with self.assertRaises(ValueError):m.validate(d)
    def test_all_zero_has_no_latest_pulse(self):
        d=fixture(counts=[0]*8);m.validate(d);s=m.svg(d,'dark');self.assertNotIn('class="fx pulse"',s)
    def test_svg_xml_and_date_uniqueness(self):
        for theme in ('light','dark'):
            for mobile in (False,True):
                d=fixture();root=ET.fromstring(m.svg(d,theme,mobile));dates=[e.attrib['data-date'] for e in root.iter() if 'data-date' in e.attrib];self.assertEqual(dates,[r['date'] for r in d['days']])
    def test_mobile_full_year(self):
        d=fixture('2025-09-17',counts=[1]*365);root=ET.fromstring(m.svg(d,'dark',True));dates=[e.attrib['data-date'] for e in root.iter() if 'data-date' in e.attrib];self.assertEqual(len(dates),365);self.assertEqual(len(set(dates)),365)
    def test_generated_data_js_agrees(self):
        d=fixture()
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);m.publish(d,p);data=json.loads((p/'docs/contributions.json').read_text());self.assertEqual(data,d);js=(p/'docs/data.js').read_text();self.assertEqual(json.loads(js.split(' = ',1)[1].rstrip(';\n')),d)
    def test_normalize_flattens_and_sorts(self):
        d=fixture();rows=[{'date':r['date'],'contributionCount':r['count'],'contributionLevel':list(m.LEVELS)[r['level']]} for r in reversed(d['days'])]
        p={'data':{'user':{'contributionsCollection':{'contributionCalendar':{'totalContributions':d['totalContributions'],'weeks':[{'contributionDays':rows}]}}}}}
        got=m.normalize(p,'takagibit18',m.day(d['period']['from']),m.day(d['period']['to']),d['fetchedAt']);self.assertEqual(got['days'],d['days'])
    def test_graphql_errors_do_not_overwrite(self):
        with self.assertRaises(ValueError):m.normalize({'errors':[{'message':'secret details not printed'}]},'takagibit18',dt.date(2026,1,1),dt.date(2026,1,2),'2026-01-02T00:00:00Z')
    def test_script_string_escapes_html(self):
        d=fixture();d['source']['note']='</script><img src=x>';self.assertNotIn('</script>',m.safe_js(d))

if __name__=='__main__':unittest.main()
