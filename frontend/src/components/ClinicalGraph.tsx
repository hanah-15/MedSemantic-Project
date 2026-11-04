import { ArrowRight, Network } from 'lucide-react';
import { Link, useSearchParams } from 'react-router-dom';
import { useClinicalCollection } from '../hooks/useClinicalRecords';
import ClinicalSource from './ClinicalSource';

const targetDomains: Record<string, string> = {aPourMaladie:'diseases', aPourCondition:'conditions', ressentSymptome:'symptoms', prend:'medications'};

export default function ClinicalGraph() {
  const [params,setParams] = useSearchParams();
  const domain = params.get('domain') === 'conditions' ? 'conditions' : 'patients';
  const {data, status, retry} = useClinicalCollection(domain);
  const selectedId = params.get('id') ?? data?.[0]?.id ?? '';
  const record = data?.find(item=>item.id === selectedId);
  const edges = [
    ...(record?.relations ?? []).map(link=>({predicate:link.predicate, id:link.target, domain:targetDomains[link.predicate], incoming:false})),
    ...(record?.incomingRelations ?? []).map(link=>({predicate:link.predicate, id:link.source, domain:link.sourceDomain, incoming:true})),
  ];
  const height = Math.max(220, edges.length * 100 + 40);
  return <section className="detail-panel clinical-graph">
    <header><span className="detail-heading-icon"><Network size={22}/></span><div><h2>Recorded connections</h2><p>Explicit triples for patients and medical conditions</p></div></header>
    <div className="clinical-graph-body">
      <div className="clinical-filters"><label>Collection<select aria-label="Graph collection" value={domain} onChange={event=>setParams({domain:event.target.value})}><option value="patients">Patients</option><option value="conditions">Medical conditions</option></select></label>
        <label>Record<select aria-label="Graph record" value={selectedId} onChange={event=>setParams({domain,id:event.target.value})} disabled={!data?.length}>{params.has('id') && !record && <option value={selectedId}>{selectedId}</option>}{data?.map(item=><option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      </div>
      <ClinicalSource status={status} retry={retry}/>
      {record ? <>
        {edges.length ? <div className="record-graph-scroll"><svg className="record-graph" viewBox={`0 0 900 ${height}`} role="img" aria-label={'Explicit relationships for '+record.name}>
          <defs><marker id="record-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="#087f8c"/></marker></defs>
          <rect x="20" y={height/2-35} width="240" height="70" rx="15" fill="#e5f6ef" stroke="#88cbbb"/>
          <text x="140" y={height/2+5} textAnchor="middle" className="record-graph-label">{record.name}</text>
          {edges.map((edge,index)=>{const y=60+index*100; return <g key={edge.predicate+edge.id}>
            <path d={edge.incoming ? `M 610 ${y} L 270 ${height/2}` : `M 260 ${height/2} L 600 ${y}`} fill="none" stroke="#087f8c" strokeWidth="2" markerEnd="url(#record-arrow)"/>
            <rect x="315" y={(height/2+y)/2-14} width="245" height="28" rx="7" fill="white"/>
            <text x="437" y={(height/2+y)/2+5} textAnchor="middle" className="record-graph-predicate">{edge.predicate}</text>
            <rect x="610" y={y-32} width="275" height="64" rx="12" fill="#f1f8fa" stroke="#c2dce3"/>
            <text x="747" y={y+5} textAnchor="middle" className="record-graph-label">{edge.id.length > 29 ? edge.id.slice(0,26)+'…' : edge.id}</text>
            <title>{edge.incoming ? `${edge.id} → ${edge.predicate} → ${record.id}` : `${record.id} → ${edge.predicate} → ${edge.id}`}</title>
          </g>;})}
        </svg></div> : <p className="relationship-empty">No links are returned for this record. Missing assertions do not establish the absence of a medical condition.</p>}
        <div className="record-edge-links">{edges.map(edge=><div key={edge.predicate+edge.id}><code>{edge.predicate}</code><span>{edge.incoming ? 'Incoming from' : 'Outgoing to'}</span>{edge.domain ? <Link to={'/entity/'+encodeURIComponent(edge.id)+'?domain='+edge.domain}>{edge.id}<ArrowRight size={15}/></Link> : <span>{edge.id}</span>}</div>)}</div>
        <Link className="back-link" to={'/entity/'+encodeURIComponent(record.id)+'?domain='+domain}>Open {record.name} profile <ArrowRight size={17}/></Link>
      </> : status === 'connected' && <p>No matching record in this collection.</p>}
      <p className="graph-source-note">These edges come from Fuseki. Related profiles outside Patient and ConditionMedicale use preview data. No OWL reasoning is applied.</p>
    </div>
  </section>;
}
