import { useEffect, useState } from 'react';
import { Link, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, ArrowUpRight, BookOpenText, GitBranch, Info, Layers3, Link2, Network } from 'lucide-react';
import { entities, getEntity, getDomain, type Entity } from '../data/ontology';
import { DomainIcon } from '../components/Icons';
import { getClinicalRecord, listDiseasesForSymptom, toClinicalEntity, type ClinicalDomain } from '../lib/ontologyApi';

export default function Detail() {
  const {id} = useParams();
  const [searchParams] = useSearchParams();
  const requestedDomain = searchParams.get('domain');
  const sampleEntity = getEntity(id ?? '');
  const inferredDomain = sampleEntity?.domain === 'diseases' || sampleEntity?.domain === 'symptoms'
    ? sampleEntity.domain
    : null;
  const liveDomain: ClinicalDomain | null = requestedDomain === 'diseases' || requestedDomain === 'symptoms'
    ? requestedDomain
    : inferredDomain;
  const [liveEntity, setLiveEntity] = useState<Entity | null>(null);
  const [incomingEntities, setIncomingEntities] = useState<Entity[] | null>(null);
  const [loading, setLoading] = useState(requestedDomain === 'diseases' || requestedDomain === 'symptoms');
  const [error, setError] = useState<string | null>(null);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    if (!liveDomain || !id) {
      setLoading(false);
      setError(null);
      setLiveEntity(null);
      setIncomingEntities(null);
      return;
    }
    const controller = new AbortController();
    setLoading(true);
    setError(null);
    setLiveEntity(null);
    setIncomingEntities(null);

    const loadEntity = getClinicalRecord(liveDomain, id, controller.signal);
    const loadIncoming = liveDomain === 'symptoms'
      ? listDiseasesForSymptom(id, controller.signal)
      : Promise.resolve([]);

    Promise.all([loadEntity, loadIncoming])
      .then(([record, incoming]) => {
        setLiveEntity(toClinicalEntity(record, liveDomain));
        setIncomingEntities(incoming.map(item => toClinicalEntity(item, 'diseases')));
      })
      .catch(reason => {
        if (!controller.signal.aborted) {
          setError(reason instanceof Error ? reason.message : 'Could not load this ontology record.');
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [id, liveDomain, reload]);

  if (liveDomain && (loading || liveEntity?.id !== id) && !error) return <div className="empty-state" role="status"><p>Loading ontology record…</p></div>;
  if (error) return <div className="empty-state api-error-state" role="alert"><h2>Could not load this record</h2><p>{error}</p><button className="button-primary" onClick={()=>setReload(value=>value+1)}>Try again <ArrowRight size={17}/></button><Link to="/search">Back to search</Link></div>;
  const entity = liveDomain ? liveEntity : getEntity(id ?? '');
  if (!entity) return <div className="empty-state"><h2>We couldn't find that concept.</h2><Link className="button-primary" to="/search">Explore the library <ArrowRight size={17}/></Link></div>;
  const domain = getDomain(entity.domain)!;
  const incoming = (incomingEntities ?? entities)
    .flatMap(other => (other.relations ?? []).filter(rel => rel.target === entity.id).map(rel => ({...rel,source:other})));
  const properties = Object.entries({Identifier: entity.id, 'Ontology class': domain.owl, Category: entity.type, ...entity.properties});
  const detailHref = (target: Entity | undefined, targetId: string, predicate: string) => {
    const targetDomain = target?.domain ?? (entity.domain === 'diseases' && predicate === 'presenteSymptome' ? 'symptoms' : undefined);
    const path = '/entity/' + encodeURIComponent(targetId);
    return targetDomain === 'diseases' || targetDomain === 'symptoms'
      ? `${path}?domain=${targetDomain}`
      : path;
  };

  return <div className="page-flow inner-page">
    <div className="page-topline"><span className="eyebrow"><span className="eyebrow-indicator"/> KNOWLEDGE PROFILE</span><span className="topline-right">ONTOLOGY / {domain.owl.toUpperCase()}</span></div>
    <Link className="back-link" to={'/catalog/'+entity.domain}><ArrowLeft size={17}/> Back to {domain.title}</Link>
    <section className="profile-heading"><div className={'collection-icon tone-'+domain.group.toLowerCase()}><DomainIcon name={domain.icon} size={35}/></div><div><span className="eyebrow">{domain.owl} / {entity.type}</span><h1>{entity.name.replaceAll('_',' ')}<span className="heading-dot">.</span></h1><p>{entity.description}</p></div><Link className="button-outline" to="/graph"><Network size={18}/> Knowledge graph <ArrowUpRight size={16}/></Link></section>
    <div className="section-intro profile-section-title"><div><span className="eyebrow">SEMANTIC CONTEXT</span><h2>Connected knowledge<span className="heading-dot">.</span></h2><p>Trace how this concept relates to the rest of the medical ontology.</p></div></div>
    <div className="detail-layout">
      <div className="detail-main">
        <section className="detail-panel"><header><span className="detail-heading-icon"><GitBranch size={22}/></span><div><h3>Outgoing relationships</h3><p>Connections originating from this concept</p></div><span className="detail-count">{entity.relations?.length ?? 0}</span></header>
          {entity.relations?.length ? <div className="relationship-list">{entity.relations.map((rel,i) => {
            const target = getEntity(rel.target);
            return <div className="relationship-row" key={i}><span className="relationship-predicate">{rel.predicate}</span><span className="relationship-direction"><ArrowRight size={19}/></span><Link to={detailHref(target, rel.target, rel.predicate)}><span>{target?.name.replaceAll('_',' ') ?? rel.target.replaceAll('_',' ')}</span><ArrowUpRight size={17}/></Link></div>;
          })}</div> : <div className="relationship-empty">No outgoing relationships are recorded for this concept.</div>}
        </section>
        <section className="detail-panel"><header><span className="detail-heading-icon"><Link2 size={21}/></span><div><h3>Incoming relationships</h3><p>Other concepts linking to this one</p></div><span className="detail-count">{incoming.length}</span></header>
          {incoming.length ? <div className="relationship-list">{incoming.map((rel,i)=><div className="relationship-row" key={i}><Link to={detailHref(rel.source, rel.source.id, rel.predicate)}><span>{rel.source.name.replaceAll('_',' ')}</span><ArrowUpRight size={17}/></Link><span className="relationship-direction"><ArrowRight size={19}/></span><span className="relationship-predicate">{rel.predicate}</span></div>)}</div> : <div className="relationship-empty">{liveDomain === 'diseases' ? 'Incoming links from other ontology modules are not included in this API yet.' : 'No incoming relationships are recorded for this concept.'}</div>}
        </section>
      </div>
      <aside className="detail-side"><section className="detail-panel"><header><span className="detail-heading-icon"><Layers3 size={21}/></span><div><h3>Properties</h3><p>Ontology attributes</p></div></header><dl className="profile-properties">{properties.map(([key,value])=><div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl></section>
      <div className="profile-note"><Info size={20}/><p>Records shown here illustrate ontology structure. They are not verified clinical guidance or individual treatment advice.</p></div>
      <Link to="/search" className="profile-side-link"><BookOpenText size={18}/> Browse related concepts <ArrowUpRight size={18}/></Link></aside>
    </div>
  </div>;
}
