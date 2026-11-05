import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, ArrowUpRight, Network, Search, SearchX, Plus, Pencil, Trash2 } from 'lucide-react';
import { domains, entities, type Entity } from '../data/ontology';
import { DomainIcon } from '../components/Icons';
import { isClinicalDomain, useClinicalCollection, useClinicalResource } from '../hooks/useClinicalRecords';
import ClinicalSource from '../components/ClinicalSource';
import EntityCard from '../components/EntityCard';
import PharmacologyCollection from './PharmacologyCollection';
import SafetyCollection from './SafetyCollection';
import { useMoleculeCollection } from '../hooks/useMoleculeRecords';
import DiseaseCollection from './DiseaseCollection';
import ResearchCollection from './ResearchCollection';
import ClinicalEditor from '../components/ClinicalEditor';
import { apiWrite } from '../lib/api';

export default function Collection() {
  const {slug} = useParams();
  return slug === 'medications' ? <PharmacologyCollection/> : slug === 'studies' || slug === 'results' ? <ResearchCollection key={slug}/> : slug === 'diseases' || slug === 'symptoms' ? <DiseaseCollection key={slug}/> : slug === 'side-effects' || slug === 'contraindications' ? <SafetyCollection key={slug}/> : <OntologyCollection key={slug}/>;
}

function OntologyCollection() {
  const {slug} = useParams();
  const domain = domains.find(d => d.slug === slug);
  const [query,setQuery] = useState('');
  const [category,setCategory] = useState('all');
  const [minAge,setMinAge] = useState('');
  const [maxAge,setMaxAge] = useState('');
  const [sex,setSex] = useState('');
  const [severity,setSeverity] = useState('');
  const [editing,setEditing] = useState<Entity|null|undefined>(undefined);
  const [feedback,setFeedback] = useState('');
  const [mutationError,setMutationError] = useState('');
  const [deleting,setDeleting] = useState('');
  const filters:Record<string,string> = slug === 'patients'
    ? {q:query,age_category:category === 'all' ? '' : category,min_age:minAge,max_age:maxAge,sexe:sex}
    : {q:query,category:category === 'all' ? '' : category,severity};
  const { data: liveItems, status, retry } = useClinicalCollection(slug,filters);
  const clinical = isClinicalDomain(slug);
  const molecules = useMoleculeCollection(slug === 'molecules');
  const filterOptions = useClinicalResource<{sexes?:string[];severities?:string[]}>(clinical ? slug+'/filter-options' : '',clinical ? '/api/'+slug+'/filter-options' : null);
  const filterValue = slug === 'patients' ? sex : severity;
  const filterValues = [...new Set([...(filterOptions.data?.[slug === 'patients' ? 'sexes' : 'severities'] ?? []),...(filterValue ? [filterValue] : [])])].sort();
  const hasFilters = !!(query.trim() || category !== 'all' || minAge || maxAge || sex || severity);
  const domainItems = slug === 'molecules' ? molecules.data ?? [] : clinical && status !== 'unavailable' ? liveItems ?? [] : entities.filter(entity => entity.domain === slug);
  if (!domain) return <div className="empty-state"><SearchX size={32}/><h2>Collection not found</h2><Link className="button-primary" to="/">Back to overview <ArrowRight size={17}/></Link></div>;
  const categoryKey = slug === 'patients' ? 'ageCategory' : 'category';
  const categories = slug === 'patients' ? ['Enfant','Adulte','PersonneAgee'] : ['EtatPhysiologique','EtatPathologique'];
  const items = domainItems.filter(entity => [entity.name,entity.type,entity.id,...Object.values(entity.properties ?? {})].join(' ').toLowerCase().includes(query.trim().toLowerCase()) && (category === 'all' || !categories.includes(category) || entity.properties?.[categoryKey] === category));
  async function remove(record:Entity) {
    if (!window.confirm(`Delete ${record.name}? This also removes links to this record.`)) return;
    setDeleting(record.id);setMutationError('');setFeedback('');
    try {await apiWrite('/api/'+slug+'/'+encodeURIComponent(record.id),'DELETE');setFeedback('Record deleted.');retry();filterOptions.retry();}
    catch(error) {setMutationError(error instanceof Error ? error.message : 'Unable to delete this record.');}
    finally {setDeleting('');}
  }
  return <div className="page-flow inner-page">
    <div className="page-topline"><span className="eyebrow"><span className="eyebrow-indicator"/> THE MEDICAL ATLAS</span><span className="topline-right">ONTOLOGY / {domain.owl.toUpperCase()}</span></div>
    <Link className="back-link" to="/"><ArrowLeft size={17}/> Back to overview</Link>
    <section className={'collection-hero collection-'+domain.group.toLowerCase()}>
      <div className={'collection-icon tone-'+domain.group.toLowerCase()}><DomainIcon name={domain.icon} size={36}/></div>
      <div className="collection-heading"><span className="eyebrow">ONTOLOGY CLASS / {domain.owl}</span><h1>{domain.title}<span className="heading-dot">.</span></h1><p>{domain.description} — explore its records and discover their connections.</p></div>
      <div className="collection-stat"><strong>{domainItems.length.toString().padStart(2,'0')}</strong><span>CONNECTED ENTRIES</span></div>
    </section>
    <div className="section-intro collection-intro"><div><span className="eyebrow">BROWSE & DISCOVER</span><h2>The collection<span className="heading-dot">.</span></h2><p>Explore the available records and their defined relationships.</p></div><label className="collection-search"><Search size={20}/><input aria-label={'Filter '+domain.title} placeholder={'Search '+domain.title.toLowerCase()+'...'} value={query} onChange={e=>setQuery(e.target.value)}/></label></div>
    {clinical && <div className="clinical-toolbar"><ClinicalSource status={status} retry={()=>{retry();filterOptions.retry();}} preview/><button className="button-primary" disabled={status !== 'connected'} onClick={()=>{setEditing(null);setFeedback('');}}><Plus size={18}/>Add {slug === 'patients' ? 'patient' : 'condition'}</button></div>}
    {clinical && status === 'connected' && ['unavailable','error','not-found'].includes(filterOptions.status) && <div className="source-status" role="status">Filter choices could not be loaded.<button onClick={filterOptions.retry}>Try again</button></div>}
    {slug === 'molecules' && <ClinicalSource status={molecules.status} retry={molecules.retry}/>}
    {feedback && <p role="status" className="clinical-success">{feedback}</p>}
    {mutationError && <p role="alert" className="clinical-error">{mutationError}</p>}
    {clinical && <div className="clinical-filters">{slug === 'patients' ? <><label>Minimum age<input type="number" min="0" value={minAge} onChange={event=>setMinAge(event.target.value)}/></label><label>Maximum age<input type="number" min="0" value={maxAge} onChange={event=>setMaxAge(event.target.value)}/></label><label>Sex<select value={sex} onChange={event=>setSex(event.target.value)}><option value="">All</option>{filterValues.map(value=><option key={value} value={value}>{value === 'F' ? 'Female (F)' : value === 'M' ? 'Male (M)' : value}</option>)}</select></label></> : <label>Severity<select value={severity} onChange={event=>setSeverity(event.target.value)}><option value="">All severities</option>{filterValues.map(value=><option key={value} value={value}>{value}</option>)}</select></label>}</div>}
    {clinical && categories.length > 0 && <div className="clinical-filters"><label>{slug === 'patients' ? 'Age category' : 'Condition category'}<select aria-label={slug === 'patients' ? 'Age category' : 'Condition category'} value={categories.includes(category) ? category : 'all'} onChange={event=>setCategory(event.target.value)}><option value="all">All categories</option>{categories.map(value=><option key={value} value={value}>{value}</option>)}</select></label><span>{items.length} of {domainItems.length} records</span></div>}
    {clinical && status === 'loading' ? <div className="empty-state" role="status"><h3>Loading records…</h3></div> : items.length ? <div className="entity-grid">{items.map(item=><div className="clinical-card" key={item.id}><EntityCard item={item}/>{clinical && status === 'connected' && <div className="clinical-card-actions"><button className="button-outline" aria-label={'Edit '+item.name} onClick={()=>setEditing(item)} disabled={!!deleting}><Pencil size={16}/>Edit</button><button className="button-outline" aria-label={'Delete '+item.name} onClick={()=>remove(item)} disabled={!!deleting}><Trash2 size={16}/>{deleting === item.id ? 'Deleting…' : 'Delete'}</button></div>}</div>)}</div> : <div className="empty-state"><SearchX size={35}/><h3>{status === 'error' ? 'Records could not be loaded' : 'No records found'}</h3><p>{domainItems.length || hasFilters ? 'Try another keyword or clear your filters.' : 'There are no records to display.'}</p>{(domainItems.length > 0 || hasFilters) && <button className="button-primary" onClick={()=>{setQuery('');setCategory('all');setMinAge('');setMaxAge('');setSex('');setSeverity('');}}>Show all entries <ArrowRight size={17}/></button>}</div>}
    {clinical && editing !== undefined && <ClinicalEditor domain={slug === 'patients' ? 'patients' : 'conditions'} record={editing} onClose={()=>setEditing(undefined)} onSaved={()=>{setEditing(undefined);setFeedback('Record saved.');retry();filterOptions.retry();}}/>}
    <div className="related-banner"><span><Network size={26}/></span><div><strong>There’s more to the story.</strong><p>Every concept is part of a larger system of relationships.</p></div><Link to="/graph">Explore the knowledge graph <ArrowUpRight size={18}/></Link></div>
  </div>;
}
