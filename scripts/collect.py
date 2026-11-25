#!/usr/bin/env python3
"""Refresh configurable saved searches. Write only after all requested searches succeed."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import time
from urllib.parse import urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
ROOT=Path(__file__).resolve().parents[1]
BASE='https://www.loc.gov/collections/chronicling-america/'

def safe_url(value):
    if not isinstance(value,str): return ''
    p=urlsplit(value)
    if p.scheme not in ('http','https') or not (p.hostname=='loc.gov' or (p.hostname or '').endswith('.loc.gov')) or p.username or p.password:return ''
    return urlunsplit(('https',p.netloc,p.path,p.query,p.fragment))

def query_url(query,size):
    if not query.get('query','').strip() and not any(query.get(k) for k in ['start','end','state','city','title','lccn']):raise ValueError('Each collection needs search words or a date/place/newspaper filter')
    if query.get('operation','AND') not in ('AND','OR','PHRASE','~5','~10'):raise ValueError('Unknown search operation')
    p={'dl':'page','searchType':'advanced','qs':query['query'],'ops':query.get('operation','AND'),'c':size,'sp':1,'fo':'json'}
    for key,param in {'start':'start_date','end':'end_date','state':'location_state','city':'location_city','title':'partof_title'}.items():
        if query.get(key):p[param]=query[key]
    if query.get('lccn'):p['fa']='number_lccn:'+query['lccn']
    if query.get('sort') not in (None,'relevance'):p['sb']=query['sort']
    return BASE+'?'+urlencode(p)

def first(v):return str(v[0]) if isinstance(v,list) and v else v if isinstance(v,str) else ''

def normalize(payload,query,captured,url,raw):
    if not isinstance(payload.get('results'),list) or not isinstance(payload.get('pagination'),dict):raise ValueError('Not an archive search response')
    records=[];seen=set()
    for r in payload['results']:
        source=safe_url(r.get('url') or r.get('id'));identity=safe_url(r.get('id')) or source
        if not source or not r.get('title') or r.get('access_restricted') is True or identity in seen:continue
        seen.add(identity)
        images=[safe_url(x) for x in r.get('image_url',[]) if '.jpg' in x or '.png' in x]
        records.append({'id':identity,'url':source,'title':r['title'],'date':r.get('date',''),'newspaper':first(r.get('partof_title')),'state':first(r.get('location_state')),'city':first(r.get('location_city')),'lccn':first(r.get('number_lccn')),'page':first(r.get('number_page')).lstrip('0'),'image':images[-1] if images else '', 'excerpt':first(r.get('description'))[:320],'language':first(r.get('language')),'contributor':first(r.get('contributor'))})
    total=payload['pagination'].get('of')
    if not isinstance(total,int) or total<0:total=None
    return {'schemaVersion':1,'source':'Library of Congress · Chronicling America','capturedAt':captured,'query':query,'page':1,'pageSize':payload['pagination'].get('perpage',len(records)),'total':total,'hasNext':bool(payload['pagination'].get('next')),'records':records,'provenance':{'url':url,'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}}

def collect(root=ROOT,only=None):
    config=json.loads((root/'web/config.json').read_text());collections=config['collections'];size=config['pageSize'];delay=max(3.5,config['minimumRequestIntervalMs']/1000)
    if not 1<=size<=100:raise ValueError('pageSize must be 1 to 100')
    ids=[x['id'] for x in collections]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate collection IDs')
    if only and only not in ids:raise ValueError('Unknown collection ID')
    output=root/'web/data/captures.json';result=json.loads(output.read_text()) if output.exists() else {'schemaVersion':1,'captures':{}}
    if not only:result={'schemaVersion':1,'captures':{}}
    chosen=[c for c in collections if not only or c['id']==only]
    for n,item in enumerate(chosen):
        if n:time.sleep(delay)
        q={k:v for k,v in {**config['defaults'],**item}.items() if k in ('query','operation','start','end','state','city','title','lccn','sort')};url=query_url(q,size)
        request=Request(url,headers={'User-Agent':'CoolCode HeadlineVault contact jeffdyer@gmail.com','Accept':'application/json'})
        with urlopen(request,timeout=config['requestTimeoutMs']/1000) as response:
            raw=response.read(20_000_001)
        if len(raw)>20_000_000:raise ValueError('Source response too large')
        captured=datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
        result['captures'][item['id']]=normalize(json.loads(raw),q,captured,url,raw)
        print(item['id'],len(result['captures'][item['id']]['records']),'pages',flush=True)
    output.parent.mkdir(parents=True,exist_ok=True);temporary=output.with_suffix('.tmp');temporary.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');temporary.replace(output)

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--collection');args=parser.parse_args();collect(only=args.collection)
