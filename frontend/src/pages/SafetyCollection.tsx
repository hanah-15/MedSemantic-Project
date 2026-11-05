import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, Search, SearchX } from 'lucide-react';
import { domains } from '../data/ontology';
import { DomainIcon } from '../components/Icons';
import EntityCard from '../components/EntityCard';
import ClinicalSource from '../components/ClinicalSource';
import { useSafetyCollection } from '../hooks/useSafetyRecords';

export default function SafetyCollection() {
  const {slug} = useParams();
  const domain = domains.find(item=>item.slug === slug)!;
  const effects = slug === 'side-effects';
  const [query,setQuery] = useState('');
  const [type,setType] = useState('');
  const [severity,setSeverity] = useState('');
  const [frequency,setFrequency] = useState('');
  const [medication,setMedication] = useState('');
  const filters:Record<string,string> = effects ? {type_effet:type,gravite:severity,frequence:frequency,medicament:medication} : {type_ci:type,medicament:medication};
  const records = useSafetyCollection(slug,filters);
  const choices = useSafetyCollection(slug);
  const types = [...new Set((choices.data ?? []).map(item=>item.type))].sort();
  const values = (property:string)=>[...new Set((choices.data ?? []).map(item=>item.properties?.[property]).filter((value):value is string=>!!value))].sort();
  const meds = [...new Set((choices.data ?? []).flatMap(item=>(item.incomingRelations ?? []).map(link=>link.source)))].sort();
  const items = (records.data ?? []).filter(item=>[item.id,item.name,item.type,...Object.values(item.properties ?? {})].join(' ').toLowerCase().includes(query.toLowerCase().trim()));
  const reset = ()=>{setQuery('');setType('');setSeverity('');setFrequency('');setMedication('');};
  return <div className="page-flow inner-page">
    <Link className="back-link" to="/"><ArrowLeft size={17}/>Back to overview</Link>
    <section className="collection-hero collection-safety"><div className="collection-icon tone-safety"><DomainIcon name={domain.icon} size={36}/></div><div className="collection-heading"><span className="eyebrow">{domain.owl}</span><h1>{domain.title}<span className="heading-dot">.</span></h1><p>{domain.description}</p></div><div className="collection-stat"><strong>{items.length.toString().padStart(2,'0')}</strong><span>RECORDS</span></div></section>
    <div className="section-intro collection-intro"><div><h2>The collection<span className="heading-dot">.</span></h2><p>Explore the recorded properties and relationships.</p></div><label className="collection-search"><Search size={20}/><input aria-label={'Filter '+domain.title} placeholder="Search records..." value={query} onChange={event=>setQuery(event.target.value)}/></label></div>
    <div className="clinical-filters"><label>Type<select value={type} onChange={event=>setType(event.target.value)}><option value="">All types</option>{types.map(value=><option key={value}>{value}</option>)}</select></label>
      {effects && <><label>Severity<select value={severity} onChange={event=>setSeverity(event.target.value)}><option value="">All severities</option>{values('gravite').map(value=><option key={value}>{value}</option>)}</select></label><label>Frequency<select value={frequency} onChange={event=>setFrequency(event.target.value)}><option value="">All frequencies</option>{values('frequenceEffet').map(value=><option key={value}>{value}</option>)}</select></label></>}
      <label>Medication<select value={medication} onChange={event=>setMedication(event.target.value)}><option value="">All medications</option>{meds.map(value=><option key={value}>{value}</option>)}</select></label><button className="button-outline" onClick={reset}>Clear filters</button>
    </div>
    <ClinicalSource status={records.status} retry={records.retry}/>
    {['error','unavailable'].includes(choices.status) && <ClinicalSource status={choices.status} retry={choices.retry}/>}
    {records.status === 'connected' && (items.length ? <div className="entity-grid">{items.map(item=><EntityCard key={item.id} item={item}/>)}</div> : <div className="empty-state"><SearchX size={32}/><h3>No records found</h3><p>Try another search or clear your filters.</p></div>)}
  </div>;
}
