import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, ArrowUpRight, BookOpenText, GitBranch, Info, Layers3, Link2, Network } from 'lucide-react';
import { entities, getEntity, getDomain, type Entity } from '../data/ontology';
import { apiGet } from '../lib/api';
import { DomainIcon } from '../components/Icons';

type EtudeDetailApi = {
  id: string;
  iri: string;
  type_etude?: string | null;
  medicament_id?: string | null;
  maladie_id?: string | null;
  phase?: number | null;
  annee?: number | null;
  participants?: number | null;
  comparative?: boolean | null;
  resultats?: {
    id: string;
    iri: string;
    type_resultat?: string | null;
    valeur?: number | null;
    unite?: string | null;
  }[];
};

type ResultatDetailApi = {
  id: string;
  iri: string;
  type_resultat?: string | null;
  valeur?: number | null;
  unite?: string | null;
  etude_id?: string | null;
  type_etude?: string | null;
  medicament_id?: string | null;
};

export default function Detail() {
  const {id} = useParams();
  const staticEntity = getEntity(id ?? '');
  const [liveEntity, setLiveEntity] = useState<Entity | null>(null);

  useEffect(() => {
    setLiveEntity(null);
    if (!id) return;
    const isStudy = staticEntity?.domain === 'studies' || id.startsWith('Essai_') || id.startsWith('Etude_');
    const isResult = staticEntity?.domain === 'results' || id.startsWith('Res_');
    if (!isStudy && !isResult) return;

    const controller = new AbortController();
    if (isStudy) {
      apiGet<EtudeDetailApi>(`/etudes/${encodeURIComponent(id)}`, controller.signal)
        .then(d => {
          const props: Record<string, string> = { IRI: d.iri };
          if (d.phase != null) props.phaseEssai = String(d.phase);
          if (d.participants != null) props.nombreParticipants = String(d.participants);
          if (d.annee != null) props.anneePublication = String(d.annee);
          if (d.comparative != null) props.estComparative = String(d.comparative);
          const rels: {predicate: string; target: string}[] = [];
          if (d.medicament_id) rels.push({predicate: 'testeMedicament', target: d.medicament_id});
          if (d.maladie_id) rels.push({predicate: 'porteSurMaladie', target: d.maladie_id});
          for (const r of d.resultats ?? []) {
            rels.push({predicate: 'aPourResultat', target: r.id});
          }
          setLiveEntity({
            id: d.id,
            name: d.id.replaceAll('_', ' '),
            domain: 'studies',
            type: d.type_etude ?? 'EtudeClinique',
            description: `${d.type_etude ?? 'Étude clinique'} (${d.annee ?? 'N/A'}) — ${d.participants ?? 0} participants`,
            properties: props,
            relations: rels,
          });
        })
        .catch(() => setLiveEntity(null));
    } else if (isResult) {
      apiGet<ResultatDetailApi>(`/resultats/${encodeURIComponent(id)}`, controller.signal)
        .then(r => {
          const props: Record<string, string> = { IRI: r.iri };
          if (r.valeur != null) props.valeurMesuree = String(r.valeur);
          if (r.unite) props.uniteMesure = r.unite;
          if (r.type_etude) props.typeEtudeAssociee = r.type_etude;
          const rels: {predicate: string; target: string}[] = [];
          if (r.etude_id) rels.push({predicate: 'aPourResultat (étude)', target: r.etude_id});
          if (r.medicament_id) rels.push({predicate: 'testeMedicament', target: r.medicament_id});
          setLiveEntity({
            id: r.id,
            name: r.id.replaceAll('_', ' '),
            domain: 'results',
            type: r.type_resultat ?? 'ResultatClinique',
            description: r.valeur != null && r.unite ? `Résultat mesuré : ${r.valeur} ${r.unite}` : 'Résultat clinique',
            properties: props,
            relations: rels,
          });
        })
        .catch(() => setLiveEntity(null));
    }
    return () => controller.abort();
  }, [id, staticEntity?.domain]);

  const entity = liveEntity ?? staticEntity;
  if (!entity) return <div className="empty-state"><h2>We couldn't find that concept.</h2><Link className="button-primary" to="/search">Explore the library <ArrowRight size={17}/></Link></div>;
  const domain = getDomain(entity.domain)!;
  const incoming = entities.flatMap(other => (other.relations ?? []).filter(rel => rel.target === entity.id).map(rel => ({...rel,source:other})));
  const properties = Object.entries({Identifier: entity.id, 'Ontology class': domain.owl, Category: entity.type, ...entity.properties});

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
