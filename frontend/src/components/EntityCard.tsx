import { ArrowUpRight, GitBranch, Layers3 } from 'lucide-react';
import { Link } from 'react-router-dom';
import { getDomain, type Entity } from '../data/ontology';
import { DomainIcon } from './Icons';

export default function EntityCard({ item }: { item: Entity }) {
  const domain = getDomain(item.domain)!;
  return <Link className="entity-card" to={'/entity/' + encodeURIComponent(item.id)}>
    <div className="entity-card-head">
      <span className={'domain-icon tone-' + domain.group.toLowerCase()}><DomainIcon size={23} name={domain.icon}/></span>
      <span className="card-action"><ArrowUpRight size={19}/></span>
    </div>
    <div className="entity-type"><Layers3 size={13}/>{item.type}</div>
    <h3>{item.name.replaceAll('_',' ')}</h3>
    <p>{item.description}</p>
    <div className="entity-card-footer"><span><GitBranch size={16}/>{item.relations?.length ?? 0} connections</span><span>Explore <ArrowUpRight size={15}/></span></div>
  </Link>;
}
