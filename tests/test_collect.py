import json
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from collect import normalize,query_url,safe_url,collect
ROOT=Path(__file__).resolve().parents[1]
class CollectionTests(unittest.TestCase):
 def test_normalizes_counts_and_safe_urls(self):
  payload={'results':[{'id':'http://www.loc.gov/resource/test/','url':'https://www.loc.gov/resource/test/','title':'Title','date':'1900-01-01','number_page':['0003'],'description':['Excerpt'],'image_url':['https://tile.loc.gov/a.jpg']},{'url':'javascript:bad()','title':'Bad'}],'pagination':{'of':59,'total':10,'next':'yes'}}
  d=normalize(payload,{'query':'test'},'2026-11-23T00:00:00Z','https://www.loc.gov/',b'{}');self.assertEqual(len(d['records']),1);self.assertEqual(d['records'][0]['page'],'3');self.assertEqual(d['total'],59);self.assertEqual(len(d['provenance']['sha256']),64)
 def test_custom_query_and_lccn(self):
  url=query_url({'query':'Halifax & explosion','lccn':'sn83045462'},20);self.assertIn('qs=Halifax+%26+explosion',url);self.assertIn('number_lccn%3Asn83045462',url)
 def test_saved_data_has_valid_provenance(self):
  bundle=json.loads((ROOT/'web/data/captures.json').read_text());self.assertTrue(bundle['captures'])
  for cap in bundle['captures'].values():
   self.assertTrue(cap['records']);self.assertTrue(cap['capturedAt']);self.assertEqual(len(cap['provenance']['sha256']),64)
   for r in cap['records']:self.assertTrue(safe_url(r['url']))
 def test_failed_refresh_preserves_last_good_file(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'web/data').mkdir(parents=True);(root/'web/config.json').write_text((ROOT/'web/config.json').read_text());out=root/'web/data/captures.json';out.write_text('{"schemaVersion":1,"captures":{}}');before=out.read_bytes()
   with patch('collect.read_loc',side_effect=RuntimeError('LOC request failed')):
    with self.assertRaises(RuntimeError):collect(root)
   self.assertEqual(before,out.read_bytes())
 def test_empty_query_rejected(self):
  with self.assertRaises(ValueError):query_url({'query':''},12)
if __name__=='__main__':unittest.main()
