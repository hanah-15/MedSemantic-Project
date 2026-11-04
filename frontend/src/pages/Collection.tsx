import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, ArrowUpRight, Network, Search, SearchX } from 'lucide-react';
import { domains, entities } from '../data/ontology';
import { DomainIcon } from '../components/Icons';
import { isClinicalDomain, useClinicalCollection } from '../hooks/useClinicalRecords';
import ClinicalSource from '../components/ClinicalSource';
import EntityCard from '../components/EntityCard';
import PharmacologyCollection from './PharmacologyCollection';

export default function Collection() {
  const {slug} = useParams();
  return slug === 'medications' ? <PharmacologyCollection/> : <OntologyCollection/>;
}

function OntologyCollection() {
  const {slug} = useParams();
  const domain = domains.find(d => d.slug === slug);
  const [query,setQuery] = useState('');
  const [category,setCategory] = useState('all');
  const { data: liveItems, status, retry } = useClinicalCollection(slug);
  const clinical = isClinicalDomain(slug);
  const domainItems = clinical && status !== 'unavailable' ? liveItems ?? [] : entities.filter(entity => entity.domain === slug);
  if (!domain) return <div className="empty-state"><SearchX size={32}/><h2>Collection not found</h2><Link className="button-primary" to="/">Back to overview <ArrowRight size={17}/></Link></div>;
  const categoryKey = slug === 'patients' ? 'ageCategory' : 'category';
  const categories = [...new Set(domainItems.map(item => item.properties?.[categoryKey]).filter((value): value is string => !!value))].sort();
  const items = domainItems.filter(entity => [entity.name,entity.type,entity.id,...Object.values(entity.properties ?? {})].join(' ').toLowerCase().includes(query.trim().toLowerCase()) && (category === 'all' || !categories.includes(category) || entity.properties?.[categoryKey] === category));
  return <div className="page-flow inner-page">
    <div className="page-topline"><span className="eyebrow"><span className="eyebrow-indicator"/> THE MEDICAL ATLAS</span><span className="topline-right">ONTOLOGY / {domain.owl.toUpperCase()}</span></div>
    <Link className="back-link" to="/"><ArrowLeft size={17}/> Back to overview</Link>
    <section className={'collection-hero collection-'+domain.group.toLowerCase()}>
      <div className={'collection-icon tone-'+domain.group.toLowerCase()}><DomainIcon name={domain.icon} size={36}/></div>
      <div className="collection-heading"><span className="eyebrow">ONTOLOGY CLASS / {domain.owl}</span><h1>{domain.title}<span className="heading-dot">.</span></h1><p>{domain.description} — explore its records and discover their connections.</p></div>
      <div className="collection-stat"><strong>{domainItems.length.toString().padStart(2,'0')}</strong><span>CONNECTED ENTRIES</span></div>
    </section>
    <div className="section-intro collection-intro"><div><span className="eyebrow">BROWSE & DISCOVER</span><h2>The collection<span className="heading-dot">.</span></h2><p>Explore the available records and their defined relationships.</p></div><label className="collection-search"><Search size={20}/><input aria-label={'Filter '+domain.title} placeholder={'Search '+domain.title.toLowerCase()+'...'} value={query} onChange={e=>setQuery(e.target.value)}/></label></div>
    {clinical && <ClinicalSource status={status} retry={retry} preview/>}
    {clinical && categories.length > 0 && <div className="clinical-filters"><label>{slug === 'patients' ? 'Age category' : 'Condition category'}<select aria-label={slug === 'patients' ? 'Age category' : 'Condition category'} value={categories.includes(category) ? category : 'all'} onChange={event=>setCategory(event.target.value)}><option value="all">All categories</option>{categories.map(value=><option key={value} value={value}>{value}</option>)}</select></label><span>{items.length} of {domainItems.length} records</span></div>}
    {clinical && status === 'loading' ? <div className="empty-state" role="status"><h3>Loading records…</h3></div> : items.length ? <div className="entity-grid">{items.map(item=><EntityCard key={item.id} item={item}/>)}</div> : <div className="empty-state"><SearchX size={35}/><h3>{status === 'error' ? 'Records could not be loaded' : 'No records found'}</h3><p>{domainItems.length ? 'Try another keyword or clear your filters.' : 'There are no records to display.'}</p>{domainItems.length > 0 && <button className="button-primary" onClick={()=>{setQuery('');setCategory('all');}}>Show all entries <ArrowRight size={17}/></button>}</div>}
    <div className="related-banner"><span><Network size={26}/></span><div><strong>There’s more to the story.</strong><p>Every concept is part of a larger system of relationships.</p></div><Link to="/graph">Explore the knowledge graph <ArrowUpRight size={18}/></Link></div>
  </div>;
}
