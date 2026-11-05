import { useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, ArrowUpRight, Network, Search, SearchX, SlidersHorizontal } from 'lucide-react';
import { domains } from '../data/ontology';
import { DomainIcon } from '../components/Icons';
import EntityCard from '../components/EntityCard';
import ClinicalSource from '../components/ClinicalSource';
import { useClinicalResource } from '../hooks/useClinicalRecords';
import { mapEtudeToEntity, mapResultatToEntity, type EtudeApi, type ResultatApi, type StatEtudeApi, type StatResultatApi } from '../hooks/useResearchRecords';

const STUDY_FILTERS = [
  { key: 'all', label: 'All studies', endpoint: '/etudes/' },
  { key: 'essai', label: 'Clinical trials', endpoint: '/etudes/type/EssaiClinique' },
  { key: 'obs', label: 'Observational studies', endpoint: '/etudes/type/EtudeObservationnelle' },
  { key: 'phase3', label: 'Phase 3', endpoint: '/etudes/phase/3' },
  { key: 'sans-res', label: 'Without results', endpoint: '/etudes/sans-resultat' },
  { key: 'comp', label: 'Comparative studies', endpoint: '/etudes/comparatives/liste' },
  { key: 'glucophage', label: 'Medication: Glucophage', endpoint: '/etudes/medicament/Glucophage' },
  { key: 'diabete', label: 'Disease: Type 2 diabetes', endpoint: '/etudes/maladie/DiabeteType2' },
] as const;

const RESULT_FILTERS = [
  { key: 'all', label: 'All results', endpoint: '/resultats/' },
  { key: 'efficacite', label: 'Efficacy', endpoint: '/resultats/type/efficacite' },
  { key: 'securite', label: 'Safety (including tolerance)', endpoint: '/resultats/type/securite' },
  { key: 'tolerance', label: 'Tolerance', endpoint: '/resultats/type/tolerance' },
  { key: 'glucophage', label: 'Medication: Glucophage', endpoint: '/resultats/medicament/Glucophage' },
] as const;

export default function ResearchCollection() {
  const {slug} = useParams();
  const domain = domains.find(d => d.slug === slug)!;
  const [query,setQuery] = useState('');
  const [activeFilter,setActiveFilter] = useState('all');
  const filters = slug === 'studies' ? STUDY_FILTERS : RESULT_FILTERS;
  const path = (filters.find(f=>f.key === activeFilter) ?? filters[0]).endpoint;
  const records = useClinicalResource<(EtudeApi|ResultatApi)[]>(path,path);
  const statsPath = slug === 'studies' ? '/etudes/stats' : '/resultats/stats';
  const stats = useClinicalResource<(StatEtudeApi|StatResultatApi)[]>(statsPath,statsPath);
  const baseEntities = (records.data ?? []).map(record=>slug === 'studies' ? mapEtudeToEntity(record as EtudeApi) : mapResultatToEntity(record as ResultatApi));
  const studyStats = slug === 'studies' ? stats.data as StatEtudeApi[]|null : null;
  const resultStats = slug === 'results' ? stats.data as StatResultatApi[]|null : null;
  const items = baseEntities.filter(entity=>[entity.id,entity.name,entity.type,...Object.values(entity.properties ?? {})].join(' ').toLowerCase().includes(query.trim().toLowerCase()));
  return <div className="page-flow inner-page">
    <div className="page-topline"><span className="eyebrow"><span className="eyebrow-indicator"/> THE MEDICAL ATLAS</span><span className="topline-right">ONTOLOGY / {domain.owl.toUpperCase()}</span></div>
    <Link className="back-link" to="/"><ArrowLeft size={17}/> Back to overview</Link>
    <section className={'collection-hero collection-'+domain.group.toLowerCase()}>
      <div className={'collection-icon tone-'+domain.group.toLowerCase()}><DomainIcon name={domain.icon} size={36}/></div>
      <div className="collection-heading"><span className="eyebrow">ONTOLOGY CLASS / {domain.owl}</span><h1>{domain.title}<span className="heading-dot">.</span></h1><p>{domain.description} — explore its records and discover their connections.</p></div>
      <div className="collection-stat"><strong>{baseEntities.length.toString().padStart(2,'0')}</strong><span>CONNECTED ENTRIES</span></div>
    </section>

    {(slug === 'studies' || slug === 'results') && (
      <section className="search-studio">
        <div className="studio-filters" style={{marginTop: 0}}>
          <span className="filters-label"><SlidersHorizontal size={18}/> Filters</span>
          <div className="filters-wrap">
            {(slug === 'studies' ? STUDY_FILTERS : RESULT_FILTERS).map(f => (
              <button
                key={f.key}
                className={activeFilter === f.key ? 'filter-chip active' : 'filter-chip'}
                onClick={() => setActiveFilter(f.key)}
              >
                {f.label}
              </button>
            ))}
          </div>
        </div>
        {slug === 'studies' && studyStats && studyStats.length > 0 && (
          <div className="filters-wrap" style={{marginTop: '14px'}}>
            {studyStats.map(s => (
              <span key={s.type_etude} className="result-sort">
                <strong>{s.type_etude}</strong> : {s.nombre_etudes} étude(s) · average {s.moyenne_participants ?? '—'} participants
              </span>
            ))}
          </div>
        )}
        {slug === 'results' && resultStats && resultStats.length > 0 && (
          <div className="filters-wrap" style={{marginTop: '14px'}}>
            {resultStats.map(s => (
              <span key={s.type_resultat} className="result-sort">
                <strong>{s.type_resultat}</strong> : {s.nombre_resultats} résultat(s)
              </span>
            ))}
          </div>
        )}
      </section>
    )}

    <div className="section-intro collection-intro"><div><span className="eyebrow">BROWSE & DISCOVER</span><h2>The collection<span className="heading-dot">.</span></h2><p>Explore the available records and their defined relationships.</p></div><label className="collection-search"><Search size={20}/><input aria-label={'Filter '+domain.title} placeholder={'Search '+domain.title.toLowerCase()+'...'} value={query} onChange={e=>setQuery(e.target.value)}/></label></div>
    <ClinicalSource status={records.status} retry={()=>{records.retry();stats.retry();}}/>
    {stats.status === 'error' && <ClinicalSource status={stats.status} retry={stats.retry}/>}
    {records.status === 'loading' ? <div className="empty-state" role="status"><h3>Loading records…</h3></div> : items.length ? <div className="entity-grid">{items.map(item=><EntityCard key={item.id} item={item}/>)}</div> : <div className="empty-state"><SearchX size={35}/><h3>No records found</h3><p>Try another keyword or clear your search.</p><button className="button-primary" onClick={()=>{setQuery('');setActiveFilter('all');}}>Show all entries <ArrowRight size={17}/></button></div>}
    <div className="related-banner"><span><Network size={26}/></span><div><strong>There’s more to the story.</strong><p>Every concept is part of a larger system of relationships.</p></div><Link to="/graph">Explore the knowledge graph <ArrowUpRight size={18}/></Link></div>
  </div>;
}
