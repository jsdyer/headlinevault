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
  if(!q.query || q.query.length>300) throw new Error('Enter search words or a phrase (up to 300 characters).');
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
  if(api)u.searchParams.set('fo','json'); return u.href;
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
  if(receipt?.schemaVersion!==1||!Array.isArray(receipt.records)||receipt.records.length>10000||!Number.isFinite(Date.parse(receipt.capturedAt)))throw new Error('This is not a supported Headline Vault receipt.');
  const query=validateQuery(receipt.query);const ids=new Set();const records=receipt.records.map(r=>{if(!r||typeof r.title!=='string'||!safeLocUrl(r.url)||!safeLocUrl(r.id)||ids.has(r.id))throw new Error('Receipt contains an invalid or duplicate newspaper reference.');ids.add(r.id);return {...r,url:safeLocUrl(r.url),id:safeLocUrl(r.id),image:safeLocUrl(r.image,true),excerpt:text(r.excerpt).slice(0,320)};});return {...receipt,query,records};
}
export function csv(records) {
  const keys=['title','date','newspaper','city','state','lccn','page','url'];const cell=v=>{let s=String(v??'');if(/^[=+@\-\t\r]/.test(s))s="'"+s;return '"'+s.replaceAll('"','""')+'"';};return [keys,...records.map(r=>keys.map(k=>r[k]))].map(row=>row.map(cell).join(',')).join('\r\n');
}
export function decadeCounts(records) {const m=new Map();for(const r of records){const y=Number(r.date?.slice(0,4));if(y>0){const d=Math.floor(y/10)*10;m.set(d,(m.get(d)||0)+1);}}return [...m].sort((a,b)=>a[0]-b[0]);}
