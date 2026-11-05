import { Link, useParams, useSearchParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, ArrowUpRight, BookOpenText, FlaskConical, GitBranch, Info, Layers3, Link2, Network } from 'lucide-react';
import { entities, getEntity, getDomain, type DomainSlug } from '../data/ontology';
import { DomainIcon } from '../components/Icons';
import { isClinicalDomain, useClinicalCollection, useClinicalEntity } from '../hooks/useClinicalRecords';
import ClinicalSource from '../components/ClinicalSource';
import { isResearchDomain, useResearchRecord } from '../hooks/useResearchRecords';
import { useMedicationRecord } from '../hooks/useMedicationRecord';

const targetDomains: Record<string, DomainSlug> = {aPourMaladie:'diseases', aPourCondition:'conditions', ressentSymptome:'symptoms', prend:'medications', contientPrincipeActif:'molecules', contientExcipient:'molecules', testeMedicament:'medications', porteSurMaladie:'diseases', aPourResultat:'results'};
const propertyLabels: Record<string, string> = {age:'Age', sexe:'Sex', ageCategory:'Age category', category:'Condition category', severite:'Recorded severity',phaseEssai:'Trial phase',nombreParticipants:'Participants',anneePublication:'Publication year',estComparative:'Comparative study',valeurMesuree:'Measured value',uniteMesure:'Measurement unit'};
const entityLink = (id: string, domain: string) => '/entity/' + encodeURIComponent(id) + '?domain=' + domain;

export default function Detail() {
  const {id} = useParams();
  const [searchParams] = useSearchParams();
  const previewEntity = getEntity(id ?? '');
  const clinicalDomain = searchParams.get('domain') ?? previewEntity?.domain ?? (id?.startsWith('Patient_') ? 'patients' : undefined);
  const clinical = isClinicalDomain(clinicalDomain);
  const clinicalRecord = useClinicalEntity(clinicalDomain, id);
  const pharmacology = clinicalDomain === 'medications';
  const medicationRecord = useMedicationRecord(pharmacology,id);
  const medicationPatients = useClinicalCollection(pharmacology ? 'patients' : undefined);
  const research = isResearchDomain(clinicalDomain);
  const researchRecord = useResearchRecord(clinicalDomain,id);
  const managed = clinical || pharmacology || research;
  const {status,retry} = research ? researchRecord : pharmacology ? medicationRecord : clinicalRecord;
  const entity = research ? researchRecord.entity : pharmacology ? medicationRecord.entity : clinical ? clinicalRecord.data ?? (status === 'unavailable' && previewEntity?.domain === clinicalDomain ? previewEntity : undefined) : previewEntity;
  if ((managed) && status === 'loading') return <div className="empty-state" role="status"><h2>Loading record…</h2></div>;
  if (!entity) return <div className="empty-state">{(managed) && <ClinicalSource status={status} retry={retry}/>}<h2>{status === 'unavailable' || status === 'error' ? 'This record could not be loaded.' : "We couldn't find that concept."}</h2><Link className="button-primary" to="/search">Explore the library <ArrowRight size={17}/></Link></div>;
  const domain = getDomain(entity.domain)!;
  const incoming = pharmacology
    ? (medicationPatients.data ?? []).flatMap(patient=>(patient.relations ?? []).filter(link=>link.target === entity.id && link.predicate === 'prend').map(link=>({predicate:link.predicate,source:patient})))
    : (clinical || research) && status === 'connected'
    ? (entity.incomingRelations ?? []).map(rel => ({predicate:rel.predicate, source:{id:rel.source, domain:rel.sourceDomain, name:rel.source.replaceAll('_',' ')}}))
    : entities.flatMap(other => (other.relations ?? []).filter(rel => rel.target === entity.id).map(rel => ({...rel,source:other})));
  const properties = Object.entries({Identifier: entity.id, 'Ontology class': domain.owl, Category: entity.type, ...entity.properties}).map(([key,value])=>[propertyLabels[key] ?? key,value]);

  return <div className="page-flow inner-page">
    <div className="page-topline"><span className="eyebrow"><span className="eyebrow-indicator"/> KNOWLEDGE PROFILE</span><span className="topline-right">ONTOLOGY / {domain.owl.toUpperCase()}</span></div>
    <Link className="back-link" to={'/catalog/'+entity.domain}><ArrowLeft size={17}/> Back to {domain.title}</Link>
    {managed ? <ClinicalSource status={status} retry={retry} preview={clinical}/> : <div className="source-status">Sample record</div>}
    <section className="profile-heading"><div className={'collection-icon tone-'+domain.group.toLowerCase()}><DomainIcon name={domain.icon} size={35}/></div><div><span className="eyebrow">{domain.owl} / {entity.type}</span><h1>{entity.name.replaceAll('_',' ')}<span className="heading-dot">.</span></h1><p>{entity.description}</p></div><Link className="button-outline" to={clinical ? '/graph?domain='+entity.domain+'&id='+encodeURIComponent(entity.id) : '/graph'}><Network size={18}/> Knowledge graph <ArrowUpRight size={16}/></Link></section>
    {clinical && entity.domain === 'conditions' && <div className="condition-path" aria-label="Condition hierarchy"><span>ConditionMedicale</span><ArrowRight size={16}/>{entity.properties?.category && <><span>{entity.properties.category}</span><ArrowRight size={16}/></>}<strong>{entity.type}</strong></div>}
    {medicationRecord.medication?.molecules && medicationRecord.medication.molecules.length > 0 && <section className="detail-panel"><header><FlaskConical size={22}/><div><h3>Composition chimique</h3><p>Principes actifs et excipients</p></div></header><div className="entity-grid">{medicationRecord.medication.molecules.map(molecule=><div key={molecule.type_molecule+molecule.nom}><h3>{molecule.nom}</h3><p>{molecule.type_molecule}</p>{molecule.formule_chimique && <code>{molecule.formule_chimique}</code>}</div>)}</div></section>}
    <div className="section-intro profile-section-title"><div><span className="eyebrow">SEMANTIC CONTEXT</span><h2>Connected knowledge<span className="heading-dot">.</span></h2><p>Trace how this concept relates to the rest of the medical ontology.</p></div></div>
    <div className="detail-layout">
      <div className="detail-main">
        <section className="detail-panel"><header><span className="detail-heading-icon"><GitBranch size={22}/></span><div><h3>Outgoing relationships</h3><p>Connections originating from this concept</p></div><span className="detail-count">{entity.relations?.length ?? 0}</span></header>
          {entity.relations?.length ? <div className="relationship-list">{entity.relations.map((rel,i) => {
            const target = getEntity(rel.target);
            const targetDomain = targetDomains[rel.predicate] ?? target?.domain;
            return <div className="relationship-row" key={i}><span className="relationship-predicate">{rel.predicate}</span><span className="relationship-direction"><ArrowRight size={19}/></span>{targetDomain ? <Link to={entityLink(rel.target,targetDomain)}><span>{rel.target.replaceAll('_',' ')}{(managed) && !isClinicalDomain(targetDomain) && targetDomain !== 'medications' && !isResearchDomain(targetDomain) && <small className="relationship-source"> Sample profile</small>}</span><ArrowUpRight size={17}/></Link> : <span>{rel.target}</span>}</div>;
          })}</div> : <div className="relationship-empty">No outgoing relationships are recorded for this concept.</div>}
        </section>
        {(!clinical || entity.domain === 'conditions') && (!pharmacology || medicationPatients.status === 'connected') && <section className="detail-panel"><header><span className="detail-heading-icon"><Link2 size={21}/></span><div><h3>{pharmacology ? 'Patients taking this medication' : 'Incoming relationships'}</h3><p>Other concepts linking to this one</p></div><span className="detail-count">{incoming.length}</span></header>
          {incoming.length ? <div className="relationship-list">{incoming.map((rel,i)=><div className="relationship-row" key={i}><Link to={entityLink(rel.source.id,rel.source.domain)}><span>{rel.source.name.replaceAll('_',' ')}{clinical && !isClinicalDomain(rel.source.domain) && <small className="relationship-source"> Sample profile</small>}</span><ArrowUpRight size={17}/></Link><span className="relationship-direction"><ArrowRight size={19}/></span><span className="relationship-predicate">{rel.predicate}</span></div>)}</div> : <div className="relationship-empty">No incoming relationships are recorded for this concept.</div>}
        </section>}
      </div>
      <aside className="detail-side"><section className="detail-panel"><header><span className="detail-heading-icon"><Layers3 size={21}/></span><div><h3>Properties</h3><p>Ontology attributes</p></div></header><dl className="profile-properties">{properties.map(([key,value])=><div key={key}><dt>{key}</dt><dd>{value}</dd></div>)}</dl></section>
      <div className="profile-note"><Info size={20}/><p>For educational use. Not medical advice.</p></div>
      <Link to="/search" className="profile-side-link"><BookOpenText size={18}/> Browse related concepts <ArrowUpRight size={18}/></Link></aside>
    </div>
  </div>;
}
