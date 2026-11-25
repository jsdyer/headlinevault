export const BASE = 'https://www.loc.gov/collections/chronicling-america/';
const OPS = new Set(['AND','OR','PHRASE','~5','~10']);
const SORTS = new Set(['relevance','date','date_desc']);
const text = v => typeof v === 'string' ? v.trim() : '';
const first = v => Array.isArray(v) ? text(v[0]) : text(v);
export function safeLocUrl(value, image = false) {
  try { const u = new URL(value); if (!['http:','https:'].includes(u.protocol) || u.username || u.password || !(u.hostname === 'loc.gov' || u.hostname.endsWith('.loc.gov'))) return ''; u.protocol='https:'; if(image && !/\.(jpg|jpeg|png|gif|webp)(#|$)/i.test(u.href)) return ''; return u.href; } catch { return ''; }
}
function date(value) { if(!value) return ''; if(!/^\d{4}-\d{2}-\d{2}$/.test(value) || Number.isNaN(Date.parse(value)) || new Date(value).toISOString().slice(0,10)!==value) throw new Error('Use valid calendar dates.'); return value; }
export function validateQuery(raw) {
  const q={query:text(raw.query),operation:text(raw.operation)||'AND',start:date(text(raw.start)),end:date(text(raw.end)),state:text(raw.state),city:text(raw.city),title:text(raw.title),lccn:text(raw.lccn),sort:text(raw.sort)||'relevance'};
  if(q.query.length>300 || (!q.query&&!q.start&&!q.end&&!q.state&&!q.city&&!q.title&&!q.lccn)) throw new Error('Enter search words, a date, a town or a newspaper (up to 300 search characters).');
  if(!OPS.has(q.operation)||!SORTS.has(q.sort)) throw new Error('Choose a supported search operation and order.');
  if(q.start && q.end && q.start>q.end) throw new Error('The start date must not follow the end date.');
  if(q.lccn && !/^[a-zA-Z0-9-]{4,30}$/.test(q.lccn)) throw new Error('Use the newspaper LCCN, such as sn83045462.');
  for(const key of ['state','city','title']) if(q[key].length>200) throw new Error('The place or title filter is too long.');
  return q;
}
export function searchUrl(raw, page=1, pageSize=12, api=true) {
  const q=validateQuery(raw); if(!Number.isInteger(page)||page<1||!Number.isInteger(pageSize)||pageSize<1||pageSize>100) throw new Error('Invalid result page size.');
  if((page-1)*pageSize>=100000) throw new Error('Narrow the dates or newspaper before searching deeper.');
  const u=new URL(BASE); u.searchParams.set('dl','page');u.searchParams.set('searchType','advanced');u.searchParams.set('qs',q.query);u.searchParams.set('ops',q.operation);u.searchParams.set('c',pageSize);u.searchParams.set('sp',page);
  for(const [key,param] of Object.entries({start:'start_date',end:'end_date',state:'location_state',city:'location_city',title:'partof_title'})) if(q[key])u.searchParams.set(param,q[key]);
  if(q.lccn)u.searchParams.set('fa',`number_lccn:${q.lccn}`);
  if(q.sort!=='relevance')u.searchParams.set('sb',q.sort);
  if(api){u.searchParams.set('fo','json');u.searchParams.set('at','results,pagination');} return u.href;
}
export function validateConfig(c) {
  if(c?.schemaVersion!==1 || !Number.isInteger(c.pageSize)||c.pageSize<1||c.pageSize>100 || !Number.isInteger(c.requestTimeoutMs)||c.requestTimeoutMs<1000||c.requestTimeoutMs>120000||!Number.isInteger(c.minimumRequestIntervalMs)||c.minimumRequestIntervalMs<3000)throw new Error('Invalid search configuration.');
  validateQuery(c.defaults); if(!Array.isArray(c.collections))throw new Error('Collections must be a list.'); const ids=new Set();
  for(const item of c.collections) { if(!/^[a-z0-9-]+$/.test(item.id)||ids.has(item.id)||!text(item.label))throw new Error('Collection IDs must be unique with labels.');ids.add(item.id);validateQuery({...c.defaults,...item}); }return c;
}
export function normalizeResult(r) {
  const url=safeLocUrl(r.url || r.id || r.resources?.[0]?.url); const title=text(r.title);if(!url||!title||r.access_restricted===true)return null;
  const images=Array.isArray(r.image_url)?r.image_url:[];
  return {id:safeLocUrl(r.id)||url,url,title,date:text(r.date),newspaper:first(r.partof_title),state:first(r.location_state),city:first(r.location_city),lccn:first(r.number_lccn),page:first(r.number_page).replace(/^0+/, '')||'',image:images.map(x=>safeLocUrl(x,true)).filter(Boolean).slice(-1)[0]||'',excerpt:first(r.description).slice(0,320),language:first(r.language),contributor:first(r.contributor)};
}
export function normalizeResponse(payload, query, capturedAt=new Date().toISOString(), page=1, pageSize=12) {
  if(!payload || !Array.isArray(payload.results) || typeof payload.pagination!=='object')throw new Error('The archive did not return a valid results page. Your earlier results are still available.');
  const records=payload.results.map(normalizeResult).filter(Boolean);const unique=[...new Map(records.map(r=>[r.id,r])).values()]; const total=Number(payload.pagination.of);
  return {schemaVersion:1,source:'Library of Congress · Chronicling America',capturedAt,query:validateQuery(query),page,pageSize,total:Number.isFinite(total)&&total>=0?total:null,hasNext:Boolean(payload.pagination.next),records:unique};
}
export function validateReceipt(receipt) {
  if(receipt?.schemaVersion!==1||!Array.isArray(receipt.records)||receipt.records.length>10000||!(Number.isFinite(Date.parse(receipt.capturedAt))||(receipt.capturedAt===null&&receipt.timestampKind==='imported'&&Number.isFinite(Date.parse(receipt.importedAt)))))throw new Error('This is not a supported Headline Vault receipt.');
  const query=validateQuery(receipt.query);const ids=new Set();const records=receipt.records.map(r=>{if(!r||typeof r.title!=='string'||!safeLocUrl(r.url)||!safeLocUrl(r.id)||ids.has(r.id))throw new Error('Receipt contains an invalid or duplicate newspaper reference.');ids.add(r.id);return {...r,url:safeLocUrl(r.url),id:safeLocUrl(r.id),image:safeLocUrl(r.image,true),excerpt:text(r.excerpt).slice(0,320)};});return {...receipt,query,records};
}
export function csv(records) {
  const keys=['title','date','newspaper','city','state','lccn','page','url'];const cell=v=>{let s=String(v??'');if(/^[=+@\-\t\r]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};return [keys,...records.map(r=>keys.map(k=>r[k]))].map(row=>row.map(cell).join(',')).join('\r\n');
}
export function decadeCounts(records) {const m=new Map();for(const r of records){const y=Number(r.date?.slice(0,4));if(y>0){const d=Math.floor(y/10)*10;m.set(d,(m.get(d)||0)+1);}}return [...m].sort((a,b)=>a[0]-b[0]);}

// Only the newspaper search shape generated by this app is accepted as import context.
export function parseSourceSearchUrl(value) {
  let u;try{u=new URL(value);}catch{throw new Error('Paste the complete Library of Congress JSON search URL.');}
  if(u.protocol!=='https:'||u.hostname!=='www.loc.gov'||u.port||u.username||u.password||u.hash||u.pathname!=='/collections/chronicling-america/')throw new Error('Use the HTTPS Chronicling America JSON search URL from this tool.');
  const allowed=new Set(['dl','searchType','qs','ops','c','sp','start_date','end_date','location_state','location_city','partof_title','fa','sb','fo','at','st']);
  for(const key of u.searchParams.keys())if(!allowed.has(key)||u.searchParams.getAll(key).length!==1)throw new Error('The source URL has unsupported or repeated search parameters. Use Open source JSON for this search.');
  const p=u.searchParams;
  if(!p.has('qs')||!OPS.has(p.get('ops'))||p.get('fo')!=='json'||p.get('dl')!=='page'||p.get('searchType')!=='advanced'||(p.has('st')&&p.get('st')!=='gallery')||(p.has('at')&&p.get('at')!=='results,pagination'))throw new Error('Use the original JSON page-search URL generated by this tool.');
  if(!/^[1-9]\d*$/.test(p.get('sp')||'')||! /^[1-9]\d*$/.test(p.get('c')||''))throw new Error('The source URL must include its exact result page and page size.');
  let lccn='';if(p.has('fa')){const match=/^number_lccn:([a-zA-Z0-9-]{4,30})$/.exec(p.get('fa'));if(!match)throw new Error('Only a newspaper LCCN facet is supported for this import.');lccn=match[1];}
  const query=validateQuery({query:p.get('qs'),operation:p.get('ops'),start:p.get('start_date'),end:p.get('end_date'),state:p.get('location_state'),city:p.get('location_city'),title:p.get('partof_title'),lccn,sort:p.get('sb')});
  const page=Number(p.get('sp')),pageSize=Number(p.get('c'));
  searchUrl(query,page,pageSize); // Validate bounds without silently changing the supplied context.
  return {query,page,pageSize,sourceUrl:u.href};
}
export function importSourceResponse(payload,sourceUrl,importedAt=new Date().toISOString()) {
  const context=parseSourceSearchUrl(sourceUrl);
  if(!Number.isFinite(Date.parse(importedAt)))throw new Error('The import time is invalid.');
  if(!payload||!Array.isArray(payload.results)||!payload.pagination||!Number.isInteger(payload.pagination.current)||!Number.isInteger(payload.pagination.perpage))throw new Error('This file is not a Library of Congress JSON search response with page information.');
  if(payload.pagination.current!==context.page||payload.pagination.perpage!==context.pageSize)throw new Error('The JSON page or page size does not match the supplied source URL. Paste the URL for this exact response.');
  const result=normalizeResponse(payload,context.query,null,context.page,context.pageSize);
  return {...result,sourceUrl:context.sourceUrl,timestampKind:'imported',importedAt};
}
export function archiveResponseProblem(status,contentType='',challenge=false) {
  if(challenge)return 'The Library of Congress returned a browser verification page instead of search data. Open the same search on its website; this app will not retry the verification.';
  if(status===429)return 'The Library of Congress is limiting requests (HTTP 429). Pause requests before trying again; the Library documents blocks of up to an hour.';
  if(status===403)return 'The Library of Congress declined this request (HTTP 403). Open the same search on its website to see its explanation. This response alone does not identify the cause.';
  if(status<200||status>=300)return `The Library of Congress returned HTTP ${status}. Your browser reached the service, but it did not provide a successful search response.`;
  if(!contentType.toLowerCase().includes('json'))return 'The Library of Congress returned a web page or another format instead of JSON search data. Open the same search on its website to check the response.';
  return '';
}
export function archiveFetchError(error) {
  if(error?.name==='AbortError'||error?.name==='TimeoutError')return 'The archive did not finish within the request time limit. Try a narrower date range, or open the exact search on the Library of Congress website.';
  if(error instanceof SyntaxError)return 'The Library of Congress response was not valid JSON search data. Open the exact source search to check what the service returned.';
  if(error instanceof TypeError)return 'This browser could not read the Library of Congress response. A network interruption, cross-site access restriction or source verification page can cause this; the browser does not reveal which. Open the exact search on the Library website, or import its JSON results below.';
  return error?.message||'The archive response could not be read.';
}

export function centuryDate(value){date(value);if(!value)throw Error('Choose a reference date.');const [year,month,day]=value.split('-').map(Number);if(year<=100)throw Error('Choose a reference year after 100.');const target=year-100;const last=new Date(Date.UTC(target,month,0)).getUTCDate();return `${String(target).padStart(4,'0')}-${String(month).padStart(2,'0')}-${String(Math.min(day,last)).padStart(2,'0')}`;}
export function pageCitation(record){const url=safeLocUrl(record.url);if(!url)throw Error('Invalid source page.');return [record.newspaper||record.title,[record.city,record.state].filter(Boolean).join(', '),record.date||'Date not stated',record.page?'page '+record.page:'page number not supplied','Library of Congress, Chronicling America',url].filter(Boolean).join('. ');}
export function queryPermalink(raw,base){const q=validateQuery(raw);const u=new URL(base);u.search='';u.hash='search';for(const [k,v] of Object.entries(q))if(v)u.searchParams.set(k,v);return u.href;}
export function paperDirectory(captures){const map=new Map();for(const c of Object.values(captures))for(const r of c.records||[])if(r.lccn&&!map.has(r.lccn))map.set(r.lccn,{lccn:r.lccn,title:r.newspaper||r.title,city:r.city||'',state:r.state||''});return [...map.values()].sort((a,b)=>a.title.localeCompare(b.title));}
