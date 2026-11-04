import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { ArrowRight, Filter, Search, SearchX, SlidersHorizontal } from 'lucide-react';
import { domains, entities } from '../data/ontology';
import EntityCard from '../components/EntityCard';
import { useClinicalCollection } from '../hooks/useClinicalRecords';

export default function SearchPage() {
  const [params,setParams] = useSearchParams();
  const query = params.get('q') ?? '';
  const [filter,setFilter] = useState('all');
  const { data: livePatients } = useClinicalCollection('patients');
  const { data: liveConditions } = useClinicalCollection('conditions');
  const searchable = useMemo(() => [
    ...entities.filter(item => !(item.domain === 'patients' && livePatients) && !(item.domain === 'conditions' && liveConditions)),
    ...(livePatients ?? []),
    ...(liveConditions ?? []),
  ], [livePatients, liveConditions]);
  const matches = useMemo(() => searchable.filter(entity => {
    const text = [entity.id,entity.name,entity.type,entity.description,...Object.values(entity.properties ?? {})].join(' ').toLowerCase();
    return (filter === 'all' || entity.domain === filter) && text.includes(query.trim().toLowerCase());
  }),[filter,query,searchable]);

  return <div className="page-flow inner-page">
    <div className="page-topline"><span className="eyebrow"><span className="eyebrow-indicator"/> DISCOVERY ENGINE</span><span className="topline-right">EXPLORE / SEARCH</span></div>
    <div className="inner-page-title"><div><span className="eyebrow">FIND MEANING IN MEDICAL DATA</span><h1>Explore the <em>knowledge.</em></h1><p>One search, ten interconnected areas of medical knowledge. Find what matters and follow the relationships.</p></div><div className="page-title-icon"><Search size={55} strokeWidth={1.3}/></div></div>
    <section className="search-studio"><label className="studio-search"><Search size={24}/><input autoFocus value={query} placeholder="Search a drug, condition, patient or study..." aria-label="Search knowledge" onChange={e=>setParams(e.target.value ? {q:e.target.value} : {},{replace:true})}/><span><ArrowRight size={20}/></span></label>
      <div className="studio-filters"><span className="filters-label"><SlidersHorizontal size={18}/> Narrow your search</span><div className="filters-wrap"><button className={filter==='all'?'filter-chip active':'filter-chip'} onClick={()=>setFilter('all')}>Everything</button>{domains.map(d=><button className={filter===d.slug?'filter-chip active':'filter-chip'} key={d.slug} onClick={()=>setFilter(d.slug)}>{d.title}</button>)}</div></div>
    </section>
    <div className="section-intro result-intro"><div><span className="eyebrow">KNOWLEDGE LIBRARY</span><h2>{matches.length} {matches.length===1?'result':'results'} found<span className="heading-dot">.</span></h2><p>{query ? `Showing concepts related to “${query}”` : 'Browse the concepts that make up the medical atlas.'}</p></div><span className="result-sort"><Filter size={17}/> All results</span></div>
    {matches.length ? <div className="entity-grid">{matches.map(entity=><EntityCard key={entity.id} item={entity}/>)}</div> : <div className="empty-state"><span><SearchX size={38}/></span><h3>No matching concepts</h3><p>Try a broader term or remove a filter to explore more of the knowledge base.</p><button className="button-primary" onClick={()=>{setParams({});setFilter('all');}}>Clear search <ArrowRight size={17}/></button></div>}
  </div>;
}
