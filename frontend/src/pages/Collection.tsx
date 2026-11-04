import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, ArrowUpRight, Network, Search, SearchX } from 'lucide-react';
import { domains, entities } from '../data/ontology';
import { DomainIcon } from '../components/Icons';
import { useClinicalCollection } from '../hooks/useClinicalRecords';
import EntityCard from '../components/EntityCard';

export default function Collection() {
  const {slug} = useParams();
  const domain = domains.find(d => d.slug === slug);
  const [query,setQuery] = useState('');
  const { data: liveItems, status } = useClinicalCollection(slug);
  const domainItems = liveItems ?? entities.filter(entity => entity.domain === slug);
  if (!domain) return <div className="empty-state"><SearchX size={32}/><h2>Collection not found</h2><Link className="button-primary" to="/">Back to overview <ArrowRight size={17}/></Link></div>;
  const items = domainItems.filter(entity => [entity.name,entity.type,entity.id].join(' ').toLowerCase().includes(query.trim().toLowerCase()));
  return <div className="page-flow inner-page">
    <div className="page-topline"><span className="eyebrow"><span className="eyebrow-indicator"/> THE MEDICAL ATLAS</span><span className="topline-right">ONTOLOGY / {domain.owl.toUpperCase()}</span></div>
    <Link className="back-link" to="/"><ArrowLeft size={17}/> Back to overview</Link>
    <section className={'collection-hero collection-'+domain.group.toLowerCase()}>
      <div className={'collection-icon tone-'+domain.group.toLowerCase()}><DomainIcon name={domain.icon} size={36}/></div>
      <div className="collection-heading"><span className="eyebrow">ONTOLOGY CLASS / {domain.owl}</span><h1>{domain.title}<span className="heading-dot">.</span></h1><p>{domain.description} — explore its records and discover their connections.</p></div>
      <div className="collection-stat"><strong>{domainItems.length.toString().padStart(2,'0')}</strong><span>CONNECTED ENTRIES</span></div>
    </section>
    <div className="section-intro collection-intro"><div><span className="eyebrow">BROWSE & DISCOVER</span><h2>The collection<span className="heading-dot">.</span></h2><p>Explore the available records and their defined relationships.</p></div><label className="collection-search"><Search size={20}/><input aria-label={'Filter '+domain.title} placeholder={'Search '+domain.title.toLowerCase()+'...'} value={query} onChange={e=>setQuery(e.target.value)}/></label></div>
    {(slug === 'patients' || slug === 'conditions') && <div className={'source-status source-' + status} role="status">{status === 'connected' ? 'Connected to Fuseki through FastAPI' : status === 'loading' ? 'Loading ontology records...' : 'Preview records · Start FastAPI and Fuseki for live results'}</div>}
    {items.length ? <div className="entity-grid">{items.map(item=><EntityCard key={item.id} item={item}/>)}</div> : <div className="empty-state"><SearchX size={35}/><h3>No records found</h3><p>Try another keyword or clear your search.</p><button className="button-primary" onClick={()=>setQuery('')}>Show all entries <ArrowRight size={17}/></button></div>}
    <div className="related-banner"><span><Network size={26}/></span><div><strong>There’s more to the story.</strong><p>Every concept is part of a larger system of relationships.</p></div><Link to="/graph">Explore the knowledge graph <ArrowUpRight size={18}/></Link></div>
  </div>;
}
