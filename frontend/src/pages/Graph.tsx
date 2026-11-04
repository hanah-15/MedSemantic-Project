import { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ArrowUpRight, CircleDot, Info, Network, Waypoints } from 'lucide-react';
import { domains, links, type DomainSlug } from '../data/ontology';
import { DomainIcon } from '../components/Icons';

const coords:Record<DomainSlug,[number,number]>={medications:[440,265],molecules:[680,125],diseases:[240,120],symptoms:[110,320],'side-effects':[790,315],contraindications:[670,460],patients:[235,460],conditions:[440,510],studies:[455,82],results:[805,120]};

export default function Graph() {
  const [selected,setSelected]=useState<DomainSlug>('medications');
  const domain=domains.find(d=>d.slug===selected)!;
  const related=links.filter(([a,b])=>a===selected||b===selected);
  return <div className="page-flow inner-page">
    <div className="page-topline"><span className="eyebrow"><span className="eyebrow-indicator"/> KNOWLEDGE EXPLORER</span><span className="topline-right">ONTOLOGY / GRAPH</span></div>
    <div className="inner-page-title"><div><span className="eyebrow">BEYOND INDIVIDUAL FACTS</span><h1>See how it <em>connects.</em></h1><p>Every class is part of a living network of concepts. Select a node to uncover its relationships and explore further.</p></div><div className="page-title-icon"><Network size={60} strokeWidth={1.2}/></div></div>
    <div className="graph-layout"><section className="graph-panel"><div className="graph-panel-top"><span><Waypoints size={21}/> Medical ontology map</span><span><CircleDot size={15}/> Select any concept</span></div><div className="graph-canvas"><svg className="graph-svg" viewBox="0 0 910 580" role="img" aria-label="Interactive ontology class relationship map"><defs><marker id="g-arrow" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="#89b5bd"/></marker><filter id="glow"><feGaussianBlur stdDeviation="4"/></filter></defs>
      {links.map(([from,to],i)=>{const a=coords[from],b=coords[to],angle=Math.atan2(b[1]-a[1],b[0]-a[0]),active=from===selected||to===selected;return <line key={i} x1={a[0]+Math.cos(angle)*43} y1={a[1]+Math.sin(angle)*43} x2={b[0]-Math.cos(angle)*46} y2={b[1]-Math.sin(angle)*46} stroke={active?'#087f8c':'#b5cfd4'} strokeWidth={active?2.8:1.35} opacity={active?1:.64} markerEnd="url(#g-arrow)"/>;})}
      {domains.map(item=>{const [x,y]=coords[item.slug];return <g key={item.slug} role="button" tabIndex={0} aria-label={'Select '+item.title} className={'graph-node '+(selected===item.slug?'selected':'')} transform={`translate(${x} ${y})`} onClick={()=>setSelected(item.slug)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();setSelected(item.slug);}}}><circle className="node-halo" r="44"/><circle className="node-core" r="31"/><text className="node-initial" dy="5" textAnchor="middle">{item.owl.slice(0,2)}</text><text className="node-label" y="57" textAnchor="middle">{item.title}</text></g>})}
    </svg></div><div className="graph-panel-foot"><Info size={17}/> Class relationships defined in the ontology specification. Inference and live SPARQL exploration will be connected through FastAPI.</div></section>
    <aside className="graph-inspector"><span className="eyebrow">FOCUSED CONCEPT</span><span className={'collection-icon tone-'+domain.group.toLowerCase()}><DomainIcon name={domain.icon} size={35}/></span><h2>{domain.title}</h2><code>{domain.owl}</code><p>{domain.description}</p><div className="inspector-separator"/><div className="inspector-heading"><strong>Connected properties</strong><span>{related.length}</span></div><div className="inspector-links">{related.map(([a,b,predicate],i)=>{const other=domains.find(item=>item.slug===(a===selected?b:a))!;return <button key={i} onClick={()=>setSelected(other.slug)}><span className="inspector-predicate">{predicate}<small>{a===selected?'Outgoing':'Incoming'}</small></span><span className="inspector-target">{other.title}<ArrowUpRight size={17}/></span></button>;})}</div><Link className="button-primary inspector-button" to={'/catalog/'+selected}>Explore {domain.title}<ArrowRight size={18}/></Link></aside></div>
  </div>;
}
