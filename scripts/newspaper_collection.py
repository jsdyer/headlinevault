import json

def manifest(captures):
    papers={};dates=[]
    for c in captures['captures'].values():
        dates.append(c['capturedAt'])
        for row in c['records']:
            if row.get('lccn'):papers[row['lccn']]={k:row.get(k,'') for k in ['lccn','newspaper','city','state']}
    return {'schema':'coolcode.newspaper-collection.v1','source':'Library of Congress · Chronicling America','geography':'Selected digitized U.S. newspapers; may report on Canada','configUrl':'https://coolcode.ca/headlinevault/config.json','capturesUrl':'https://coolcode.ca/headlinevault/data/captures.json','capturedAt':max(dates) if dates else None,'papers':list(papers.values()),'reuse':'Retain each capture date and query; page citations must link to the original loc.gov record.'}
