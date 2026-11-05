import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, ArrowUpRight, Network, Search, SearchX } from 'lucide-react';
import { domains, entities } from '../data/ontology';
import { DomainIcon } from '../components/Icons';
import EntityCard from '../components/EntityCard';
import { listClinicalRecords, toClinicalEntity, type ClinicalDomain } from '../lib/ontologyApi';

export default function Collection() {
  const {slug} = useParams();
  const domain = domains.find(d => d.slug === slug);
  const [query,setQuery] = useState('');
  const [clinicalItems, setClinicalItems] = useState<typeof entities>([]);
  const [loadedDomain, setLoadedDomain] = useState<ClinicalDomain | null>(null);
  const [loading, setLoading] = useState(slug === 'diseases' || slug === 'symptoms');
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);
  const apiDomain: ClinicalDomain | null = slug === 'diseases' || slug === 'symptoms' ? slug : null;

  useEffect(() => {
    if (!apiDomain) return;
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    listClinicalRecords(apiDomain, controller.signal)
      .then(records => {
        setClinicalItems(records.map(record => toClinicalEntity(record, apiDomain)));
        setLoadedDomain(apiDomain);
      })
      .catch(reason => {
        if (!controller.signal.aborted) {
          setLoadedDomain(apiDomain);
          setError(reason instanceof Error ? reason.message : 'Could not load this collection.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [apiDomain, reload]);

  if (!domain) return <div className="empty-state"><SearchX size={32}/><h2>Collection not found</h2><Link className="button-primary" to="/">Back to overview <ArrowRight size={17}/></Link></div>;
  const collectionItems = apiDomain
    ? clinicalItems
    : entities.filter(entity => entity.domain === slug);
  const items = collectionItems.filter(entity => [
    entity.name,
    entity.type,
    entity.id,
    entity.description,
    ...Object.values(entity.properties ?? {}),
  ].join(' ').toLowerCase().includes(query.trim().toLowerCase()));
  return <div className="page-flow inner-page">
    <div className="page-topline"><span className="eyebrow"><span className="eyebrow-indicator"/> THE MEDICAL ATLAS</span><span className="topline-right">ONTOLOGY / {domain.owl.toUpperCase()}</span></div>
    <Link className="back-link" to="/"><ArrowLeft size={17}/> Back to overview</Link>
    <section className={'collection-hero collection-'+domain.group.toLowerCase()}>
      <div className={'collection-icon tone-'+domain.group.toLowerCase()}><DomainIcon name={domain.icon} size={36}/></div>
      <div className="collection-heading"><span className="eyebrow">ONTOLOGY CLASS / {domain.owl}</span><h1>{domain.title}<span className="heading-dot">.</span></h1><p>{domain.description} — explore its records and discover their connections.</p></div>
      <div className="collection-stat"><strong>{(apiDomain ? clinicalItems.length : collectionItems.length).toString().padStart(2,'0')}</strong><span>CONNECTED ENTRIES</span></div>
    </section>
    <div className="section-intro collection-intro"><div><span className="eyebrow">BROWSE & DISCOVER</span><h2>The collection<span className="heading-dot">.</span></h2><p>{apiDomain ? 'Live records loaded from the MedSemantic ontology.' : 'Explore the available records and their defined relationships.'}</p></div><label className="collection-search"><Search size={20}/><input aria-label={'Filter '+domain.title} placeholder={'Search '+domain.title.toLowerCase()+'...'} value={query} onChange={e=>setQuery(e.target.value)}/></label></div>
    {apiDomain && (loading || loadedDomain !== apiDomain) ? <div className="empty-state" role="status"><p>Loading ontology records…</p></div>
      : error ? <div className="empty-state api-error-state" role="alert"><h3>Could not load {domain.title.toLowerCase()}</h3><p>{error}</p><button className="button-primary" onClick={()=>setReload(value=>value+1)}>Try again <ArrowRight size={17}/></button></div>
      : items.length ? <div className="entity-grid">{items.map(item=><EntityCard key={item.id} item={item}/>)}</div>
      : <div className="empty-state"><SearchX size={35}/><h3>No records found</h3><p>{query ? 'Try another keyword or clear your search.' : 'No instances of this class are currently in the ontology.'}</p>{query && <button className="button-primary" onClick={()=>setQuery('')}>Show all entries <ArrowRight size={17}/></button>}</div>}
    <div className="related-banner"><span><Network size={26}/></span><div><strong>There’s more to the story.</strong><p>Every concept is part of a larger system of relationships.</p></div><Link to="/graph">Explore the knowledge graph <ArrowUpRight size={18}/></Link></div>
  </div>;
}
