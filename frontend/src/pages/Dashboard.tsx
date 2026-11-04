import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Activity, ArrowRight, ArrowUpRight, Atom, ChevronRight, CircleDot,
  FlaskConical, GitBranch, Layers3, Network, Pill, Search,
  ShieldCheck, Sparkles, Stethoscope, UsersRound,
} from 'lucide-react';
import { domains, entities, getEntity, links } from '../data/ontology';
import { DomainIcon } from '../components/Icons';

const highlights = [
  { id: 'Glucophage', title: 'Glucophage', category: 'Medication', summary: 'Follow the link from a treatment to its molecule and medical context.', icon: Pill },
  { id: 'Patient_Karim', title: 'Patient Karim', category: 'Patient', summary: 'See how patient information connects to diseases and medications.', icon: UsersRound },
  { id: 'DiabeteType2', title: 'Type 2 diabetes', category: 'Disease', summary: 'Explore the disease and the treatments linked to it in the ontology.', icon: Activity },
];

const domainFeatures = ['medications','diseases','patients','contraindications','conditions','studies'];
const categoryLabels: Record<string,string> = {
  Pharmaceutical: 'PHARMACOLOGY', Clinical: 'CLINICAL', Safety: 'SAFETY', Research: 'EVIDENCE',
};

export default function Dashboard() {
  const [query,setQuery] = useState('');
  const [selected,setSelected] = useState('Glucophage');
  const navigate = useNavigate();
  const focused = getEntity(selected)!;
  const focusedDomain = domains.find(d => d.slug === focused.domain)!;
  const relationCount = entities.reduce((n,item) => n + (item.relations?.length ?? 0),0);
  const metrics = [
    { value: domains.length, label: 'Medical concepts', detail: 'Ontology classes', icon: Layers3, accent: 'mint' },
    { value: entities.length, label: 'Knowledge entries', detail: 'Connected records', icon: Atom, accent: 'blue' },
    { value: relationCount, label: 'Connections', detail: 'Mapped entity links', icon: GitBranch, accent: 'violet' },
    { value: new Set(links.map(l => l[2])).size, label: 'Relationship types', detail: 'Distinct predicates', icon: Network, accent: 'coral' },
  ];

  return <div className="dashboard page-flow">
    <div className="page-topline"><span className="eyebrow"><span className="eyebrow-indicator"/> RESEARCH WORKSPACE</span><span className="topline-right">MEDICAL ONTOLOGY <span>·</span> MEDSEMANTIC</span></div>
    <section className="hero">
      <div className="hero-content">
        <div className="hero-pill"><span className="pill-spark"><Sparkles size={15}/></span> Discover the knowledge behind medicine <ArrowUpRight size={15}/></div>
        <h1>Medicine is complex.<br/><span>Knowledge shouldn't be.</span></h1>
        <p>Understand the connections between medications, conditions, patients, and clinical evidence—all in one intelligent knowledge space.</p>
        <form className="hero-search" onSubmit={e => {e.preventDefault(); navigate('/search' + (query ? '?q='+encodeURIComponent(query) : ''));}}>
          <Search size={23}/><input aria-label="Search medical knowledge" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search medications, diseases, patients..."/>
          <button type="submit">Start exploring <ArrowRight size={18}/></button>
        </form>
        <div className="hero-examples"><span>POPULAR SEARCHES</span>{['Metformine','Hypertension','Patient Karim'].map(term => <button key={term} onClick={() => navigate('/search?q='+encodeURIComponent(term))}>{term}<ArrowUpRight size={13}/></button>)}</div>
      </div>
      <div className="hero-scene" aria-hidden="true">
        <div className="scene-halo halo-one"/><div className="scene-halo halo-two"/><div className="scene-halo halo-three"/>
        <span className="scene-line line-one"/><span className="scene-line line-two"/><span className="scene-line line-three"/><span className="scene-line line-four"/>
        <div className="scene-main"><span className="scene-main-ring"><Network size={43} strokeWidth={1.55}/></span><strong>Connected<br/>knowledge</strong><span className="scene-detail">MEDSEMANTIC ONTOLOGY</span></div>
        <div className="scene-float floating-med"><span><Pill size={24}/></span><div><b>Medication</b><small>Therapeutic insight</small></div></div>
        <div className="scene-float floating-patient"><span><UsersRound size={22}/></span><div><b>Patient</b><small>Clinical context</small></div></div>
        <div className="scene-float floating-study"><span><FlaskConical size={23}/></span><div><b>Clinical study</b><small>Research evidence</small></div></div>
        <div className="scene-cross cross-one">+</div><div className="scene-cross cross-two">+</div><div className="scene-cross cross-three">+</div>
      </div>
    </section>

    <section className="metric-section" aria-label="Knowledge overview">
      <div className="section-intro"><div><span className="eyebrow">THE KNOWLEDGE BASE</span><h2>Explore at a glance<span className="heading-dot">.</span></h2></div><Link className="text-action" to="/search">Browse all knowledge <ArrowUpRight size={17}/></Link></div>
      <div className="metric-grid">{metrics.map((metric,index) => <div className={'metric-card metric-'+metric.accent} key={metric.label}><div className="metric-top"><div className="metric-icon"><metric.icon size={24}/></div><span className="metric-index">0{index+1}</span></div><strong>{String(metric.value).padStart(2,'0')}</strong><h3>{metric.label}</h3><p>{metric.detail}</p><div className="metric-decoration"><span/><span/><span/></div></div>)}</div>
    </section>

    <section className="knowledge-section">
      <div className="section-intro"><div><span className="eyebrow">THE MEDICAL ATLAS</span><h2>Your gateway to discovery<span className="heading-dot">.</span></h2><p>Explore a field of knowledge and uncover how it connects to the rest.</p></div><Link className="text-action" to="/search">View all collections <ArrowRight size={17}/></Link></div>
      <div className="domain-grid">{domainFeatures.map((slug,index) => {
        const domain = domains.find(item => item.slug === slug)!;
        return <Link className={'domain-card domain-'+domain.group.toLowerCase()} to={'/catalog/'+domain.slug} key={slug}>
          <div className="domain-card-top"><span className={'domain-icon tone-'+domain.group.toLowerCase()}><DomainIcon name={domain.icon} size={26}/></span><span className="domain-numeric">0{index+1} / 06</span></div>
          <span className="domain-category">{categoryLabels[domain.group]}</span><h3>{domain.title}</h3><p>{domain.description}</p>
          <div className="domain-card-bottom"><span>{entities.filter(item => item.domain === slug).length} entries to explore</span><span className="card-arrow"><ArrowUpRight size={19}/></span></div>
        </Link>;
      })}</div>
    </section>

    <section className="discover-section">
      <div className="section-intro"><div><span className="eyebrow">CONNECTIONS IN CONTEXT</span><h2>See the bigger picture<span className="heading-dot">.</span></h2><p>The value of knowledge is in the relationships between the facts.</p></div></div>
      <div className="connection-layout">
        <div className="connection-selector"><div className="connection-heading"><span className="connection-glow"><CircleDot size={21}/></span><div><small>RELATIONSHIP EXPLORER</small><h3>Choose a starting point</h3></div></div>
          <div className="connection-options">{highlights.map(item => <button key={item.id} className={selected===item.id?'connection-option active':'connection-option'} onClick={() => setSelected(item.id)}><span className="connection-option-icon"><item.icon size={22}/></span><span><strong>{item.title}</strong><small>{item.category}</small></span><ChevronRight size={19}/></button>)}</div>
          <p className="connection-hint">Select a concept to reveal its linked knowledge.</p>
        </div>
        <div className="connection-preview"><div className="preview-top"><span><Network size={19}/> KNOWLEDGE CONNECTIONS</span><span className="preview-status"><i/> MAPPED</span></div><div className="preview-focus"><span className={'domain-icon tone-'+focusedDomain.group.toLowerCase()}><DomainIcon size={27} name={focusedDomain.icon}/></span><div><small>SELECTED CONCEPT</small><h3>{focused.name.replaceAll('_',' ')}</h3><p>{highlights.find(item=>item.id===selected)?.summary}</p></div></div>
          <div className="preview-links">{(focused.relations?.length ? focused.relations : [{predicate:'Classified as',target:focused.type}]).map((relation,i)=>{
            const connected = getEntity(relation.target);
            return <Link to={connected?'/entity/'+encodeURIComponent(connected.id):'/entity/'+encodeURIComponent(focused.id)} key={i} className="preview-relation"><span className="preview-relation-line"><span/></span><div><small>{relation.predicate}</small><strong>{(connected?.name ?? relation.target).replaceAll('_',' ')}</strong></div><ArrowUpRight size={18}/></Link>;
          })}</div>
          <Link className="preview-cta" to={'/entity/'+encodeURIComponent(focused.id)}>Open complete profile <ArrowRight size={17}/></Link>
        </div>
      </div>
    </section>

    <section className="bottom-banner"><span className="bottom-banner-icon"><Stethoscope size={29}/></span><div><span className="eyebrow">RESEARCH MORE INTELLIGENTLY</span><h2>Every relationship tells a story.</h2><p>Explore the ontology from a new perspective and navigate the web of medical knowledge.</p></div><Link to="/graph">Explore the knowledge graph <ArrowUpRight size={20}/></Link><span className="bottom-banner-art"><ShieldCheck size={170}/></span></section>
  </div>;
}
