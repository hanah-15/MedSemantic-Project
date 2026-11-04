import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, ArrowUpRight, Network, Search, SearchX, SlidersHorizontal } from 'lucide-react';
import { domains, entities, type Entity } from '../data/ontology';
import { apiGet } from '../lib/api';
import { DomainIcon } from '../components/Icons';
import EntityCard from '../components/EntityCard';

type EtudeApi = {
  id: string;
  iri: string;
  type_etude?: string | null;
  medicament_id?: string | null;
  maladie_id?: string | null;
  phase?: number | null;
  annee?: number | null;
  participants?: number | null;
  comparative?: boolean | null;
};

type ResultatApi = {
  id: string;
  iri: string;
  type_resultat?: string | null;
  valeur?: number | null;
  unite?: string | null;
  etude_id?: string | null;
  medicament_id?: string | null;
};

type StatEtudeApi = {
  type_etude: string;
  nombre_etudes: number;
  moyenne_participants?: number | null;
};

type StatResultatApi = {
  type_resultat: string;
  nombre_resultats: number;
};

const STUDY_FILTERS = [
  { key: 'all', label: 'Toutes (/etudes/)', endpoint: '/etudes/' },
  { key: 'essai', label: 'EssaiClinique', endpoint: '/etudes/type/EssaiClinique' },
  { key: 'obs', label: 'EtudeObservationnelle', endpoint: '/etudes/type/EtudeObservationnelle' },
  { key: 'phase3', label: 'Phase 3 (/phase/3)', endpoint: '/etudes/phase/3' },
  { key: 'sans-res', label: 'Sans résultat (/sans-resultat)', endpoint: '/etudes/sans-resultat' },
  { key: 'comp', label: 'Comparatives', endpoint: '/etudes/comparatives/liste' },
  { key: 'glucophage', label: 'Médicament : Glucophage', endpoint: '/etudes/medicament/Glucophage' },
  { key: 'diabete', label: 'Maladie : DiabeteType2', endpoint: '/etudes/maladie/DiabeteType2' },
] as const;

const RESULT_FILTERS = [
  { key: 'all', label: 'Tous (/resultats/)', endpoint: '/resultats/' },
  { key: 'efficacite', label: 'Efficacité (/type/efficacite)', endpoint: '/resultats/type/efficacite' },
  { key: 'securite', label: 'Sécurité ⊇ Tolérance (/type/securite)', endpoint: '/resultats/type/securite' },
  { key: 'tolerance', label: 'Tolérance (/type/tolerance)', endpoint: '/resultats/type/tolerance' },
  { key: 'glucophage', label: 'Médicament : Glucophage', endpoint: '/resultats/medicament/Glucophage' },
] as const;

function mapEtudeToEntity(e: EtudeApi): Entity {
  const props: Record<string, string> = {};
  if (e.phase != null) props.phaseEssai = String(e.phase);
  if (e.participants != null) props.nombreParticipants = String(e.participants);
  if (e.annee != null) props.anneePublication = String(e.annee);
  if (e.comparative != null) props.estComparative = String(e.comparative);
  const rels: {predicate: string; target: string}[] = [];
  if (e.medicament_id) rels.push({predicate: 'testeMedicament', target: e.medicament_id});
  if (e.maladie_id) rels.push({predicate: 'porteSurMaladie', target: e.maladie_id});
  return {
    id: e.id,
    name: e.id.replaceAll('_', ' '),
    domain: 'studies',
    type: e.type_etude ?? 'EtudeClinique',
    description: `${e.type_etude ?? 'Étude clinique'}${e.medicament_id ? ` portant sur ${e.medicament_id}` : ''}${e.annee ? ` (${e.annee})` : ''}`,
    properties: props,
    relations: rels,
  };
}

function mapResultatToEntity(r: ResultatApi): Entity {
  const props: Record<string, string> = {};
  if (r.valeur != null) props.valeurMesuree = String(r.valeur);
  if (r.unite) props.uniteMesure = r.unite;
  const rels: {predicate: string; target: string}[] = [];
  if (r.etude_id) rels.push({predicate: 'aPourResultat (depuis)', target: r.etude_id});
  if (r.medicament_id) rels.push({predicate: 'testeMedicament', target: r.medicament_id});
  return {
    id: r.id,
    name: r.id.replaceAll('_', ' '),
    domain: 'results',
    type: r.type_resultat ?? 'ResultatClinique',
    description: r.valeur != null && r.unite ? `Mesure clinique : ${r.valeur} ${r.unite}` : 'Résultat clinique issu de Fuseki',
    properties: props,
    relations: rels,
  };
}

export default function Collection() {
  const {slug} = useParams();
  const domain = domains.find(d => d.slug === slug);
  const [query,setQuery] = useState('');
  const [activeFilter, setActiveFilter] = useState('all');
  const [liveItems, setLiveItems] = useState<Entity[] | null>(null);
  const [studyStats, setStudyStats] = useState<StatEtudeApi[] | null>(null);
  const [resultStats, setResultStats] = useState<StatResultatApi[] | null>(null);

  useEffect(() => {
    setActiveFilter('all');
    setLiveItems(null);
    setStudyStats(null);
    setResultStats(null);
  }, [slug]);

  useEffect(() => {
    if (slug !== 'studies' && slug !== 'results') return;
    const controller = new AbortController();
    if (slug === 'studies') {
      const f = STUDY_FILTERS.find(x => x.key === activeFilter) ?? STUDY_FILTERS[0];
      apiGet<EtudeApi[]>(f.endpoint, controller.signal)
        .then(data => setLiveItems(data.map(mapEtudeToEntity)))
        .catch(() => setLiveItems(null));
      apiGet<StatEtudeApi[]>('/etudes/stats', controller.signal)
        .then(setStudyStats)
        .catch(() => setStudyStats(null));
    } else if (slug === 'results') {
      const f = RESULT_FILTERS.find(x => x.key === activeFilter) ?? RESULT_FILTERS[0];
      apiGet<ResultatApi[]>(f.endpoint, controller.signal)
        .then(data => setLiveItems(data.map(mapResultatToEntity)))
        .catch(() => setLiveItems(null));
      apiGet<StatResultatApi[]>('/resultats/stats', controller.signal)
        .then(setResultStats)
        .catch(() => setResultStats(null));
    }
    return () => controller.abort();
  }, [slug, activeFilter]);

  if (!domain) return <div className="empty-state"><SearchX size={32}/><h2>Collection not found</h2><Link className="button-primary" to="/">Back to overview <ArrowRight size={17}/></Link></div>;

  const fallbackEntities = entities.filter(entity => {
    if (entity.domain !== slug) return false;
    if (slug === 'studies') {
      if (activeFilter === 'essai') return entity.type === 'EssaiClinique';
      if (activeFilter === 'obs') return entity.type === 'EtudeObservationnelle';
      if (activeFilter === 'phase3') return entity.properties?.phaseEssai === '3';
      if (activeFilter === 'sans-res') return !(entity.relations ?? []).some(r => r.predicate === 'aPourResultat');
      if (activeFilter === 'comp') return entity.properties?.estComparative === 'true';
      if (activeFilter === 'glucophage') return (entity.relations ?? []).some(r => r.target === 'Glucophage');
      if (activeFilter === 'diabete') return (entity.relations ?? []).some(r => r.target === 'DiabeteType2');
    } else if (slug === 'results') {
      if (activeFilter === 'efficacite') return entity.type === 'Efficacite';
      if (activeFilter === 'securite') return entity.type === 'Securite' || entity.type === 'Tolerance';
      if (activeFilter === 'tolerance') return entity.type === 'Tolerance';
      if (activeFilter === 'glucophage') return entity.id.includes('Glucophage');
    }
    return true;
  });

  const baseEntities = liveItems ?? fallbackEntities;
  const items = baseEntities.filter(entity => [entity.name,entity.type,entity.id].join(' ').toLowerCase().includes(query.trim().toLowerCase()));

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
          <span className="filters-label"><SlidersHorizontal size={18}/> Filtres SPARQL (Aymen)</span>
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
                <strong>{s.type_etude}</strong> : {s.nombre_etudes} étude(s) · moy. {s.moyenne_participants ?? 0} participants
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
    {items.length ? <div className="entity-grid">{items.map(item=><EntityCard key={item.id} item={item}/>)}</div> : <div className="empty-state"><SearchX size={35}/><h3>No records found</h3><p>Try another keyword or clear your search.</p><button className="button-primary" onClick={()=>{setQuery('');setActiveFilter('all');}}>Show all entries <ArrowRight size={17}/></button></div>}
    <div className="related-banner"><span><Network size={26}/></span><div><strong>There’s more to the story.</strong><p>Every concept is part of a larger system of relationships.</p></div><Link to="/graph">Explore the knowledge graph <ArrowUpRight size={18}/></Link></div>
  </div>;
}
