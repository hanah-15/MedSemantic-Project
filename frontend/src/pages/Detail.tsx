import { Link, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, ArrowUpRight, BookOpenText, GitBranch, Info, Layers3, Link2, Network } from 'lucide-react';
import { entities, getEntity, getDomain } from '../data/ontology';
import { DomainIcon } from '../components/Icons';
import { useClinicalEntity } from '../hooks/useClinicalRecords';

export default function Detail() {
  const {id} = useParams();
  const [searchParams] = useSearchParams();
  const previewEntity = getEntity(id ?? '');
  const clinicalDomain = searchParams.get('domain') ?? previewEntity?.domain ?? (id?.startsWith('Patient_') ? 'patients' : undefined);
  const { data: liveEntity, status } = useClinicalEntity(clinicalDomain, id);
  const entity = liveEntity ?? previewEntity;
  if (!entity && status === 'loading') return <div className="empty-state"><h2>Loading knowledge record...</h2></div>;
  if (!entity) return <div className="empty-state"><h2>We couldn't find that concept.</h2><Link className="button-primary" to="/search">Explore the library <ArrowRight size={17}/></Link></div>;
  const domain = getDomain(entity.domain)!;
  const incoming = entities.flatMap(other => (other.relations ?? []).filter(rel => rel.target === entity.id).map(rel => ({...rel,source:other})));
  const properties = Object.entries({Identifier: entity.id, 'Ontology class': domain.owl, Category: entity.type, ...entity.properties});

  return <div className="page-flow inner-page">
    <div className="page-topline"><span className="eyebrow"><span className="eyebrow-indicator"/> KNOWLEDGE PROFILE</span><span className="topline-right">ONTOLOGY / {domain.owl.toUpperCase()}</span></div>
    <Link className="back-link" to={'/catalog/'+entity.domain}><ArrowLeft size={17}/> Back to {domain.title}</Link>
    {(clinicalDomain === 'patients' || clinicalDomain === 'conditions') && <div className={'source-status source-' + status} role="status">{status === 'connected' ? 'Live ontology record' : status === 'loading' ? 'Loading live ontology record...' : 'Preview record · FastAPI or Fuseki is unavailable'}</div>}
    <section className="profile-heading"><div className={'collection-icon tone-'+domain.group.toLowerCase()}><DomainIcon name={domain.icon} size={35}/></div><div><span className="eyebrow">{domain.owl} / {entity.type}</span><h1>{entity.name.replaceAll('_',' ')}<span className="heading-dot">.</span></h1><p>{entity.description}</p></div><Link className="button-outline" to="/graph"><Network size={18}/> Knowledge graph <ArrowUpRight size={16}/></Link></section>
    <div className="section-intro profile-section-title"><div><span className="eyebrow">SEMANTIC CONTEXT</span><h2>Connected knowledge<span className="heading-dot">.</span></h2><p>Trace how this concept relates to the rest of the medical ontology.</p></div></div>
    <div className="detail-layout">
      <div className="detail-main">
        <section className="detail-panel"><header><span className="detail-heading-icon"><GitBranch size={22}/></span><div><h3>Outgoing relationships</h3><p>Connections originating from this concept</p></div><span className="detail-count">{entity.relations?.length ?? 0}</span></header>
          {entity.relations?.length ? <div className="relationship-list">{entity.relations.map((rel,i) => {
            const target = getEntity(rel.target);
            return <div className="relationship-row" key={i}><span className="relationship-predicate">{rel.predicate}</span><span className="relationship-direction"><ArrowRight size={19}/></span>{target ? <Link to={'/entity/'+encodeURIComponent(target.id)}><span>{target.name.replaceAll('_',' ')}</span><ArrowUpRight size={17}/></Link> : <span>{rel.target}</span>}</div>;
          })}</div> : <div className="relationship-empty">No outgoing relationships are recorded for this concept.</div>}
        </section>
        <section className="detail-panel"><header><span className="detail-heading-icon"><Link2 size={21}/></span><div><h3>Incoming relationships</h3><p>Other concepts linking to this one</p></div><span className="detail-count">{incoming.length}</span></header>
          {incoming.length ? <div className="relationship-list">{incoming.map((rel,i)=><div className="relationship-row" key={i}><Link to={'/entity/'+encodeURIComponent(rel.source.id)}><span>{rel.source.name.replaceAll('_',' ')}</span><ArrowUpRight size={17}/></Link><span className="relationship-direction"><ArrowRight size={19}/></span><span className="relationship-predicate">{rel.predicate}</span></div>)}</div> : <div className="relationship-empty">No incoming relationships are recorded for this concept.</div>}
        </section>
      </div>
      <aside className="detail-side"><section className="detail-panel"><header><span className="detail-heading-icon"><Layers3 size={21}/></span><div><h3>Properties</h3><p>Ontology attributes</p></div></header><dl className="profile-properties">{properties.map(([key,value])=><div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl></section>
      <div className="profile-note"><Info size={20}/><p>Records shown here illustrate ontology structure. They are not verified clinical guidance or individual treatment advice.</p></div>
      <Link to="/search" className="profile-side-link"><BookOpenText size={18}/> Browse related concepts <ArrowUpRight size={18}/></Link></aside>
    </div>
  </div>;
}
