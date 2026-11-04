import { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { ArrowLeft, ArrowRight, ArrowUpRight, BookOpenText, GitBranch, Info, Layers3, Link2, Network, FlaskConical } from 'lucide-react';
import { entities, getEntity, getDomain } from '../data/ontology';
import { DomainIcon } from '../components/Icons';
import { medicamentApi, type Molecule } from '../lib/medicamentApi';

export default function Detail() {
  const { id } = useParams();
  const entity = getEntity(id ?? '');
  const [liveMolecules, setLiveMolecules] = useState<Molecule[]>([]);

  useEffect(() => {
    if (!id) return;
    // Récupérer la composition chimique depuis Fuseki / FastAPI
    medicamentApi.getMolecules(id)
      .then(data => setLiveMolecules(data))
      .catch(err => console.warn('Composition API non disponible:', err));
  }, [id]);

  if (!entity) {
    return (
      <div className="empty-state">
        <h2>Concept introuvable.</h2>
        <Link className="button-primary" to="/search">Explorer le catalogue <ArrowRight size={17}/></Link>
      </div>
    );
  }

  const domain = getDomain(entity.domain)!;
  const incoming = entities.flatMap(other => (other.relations ?? []).filter(rel => rel.target === entity.id).map(rel => ({...rel, source: other})));
  const properties = Object.entries({Identifier: entity.id, 'Ontology class': domain.owl, Category: entity.type, ...entity.properties});

  return (
    <div className="page-flow inner-page">
      <div className="page-topline">
        <span className="eyebrow"><span className="eyebrow-indicator"/> KNOWLEDGE PROFILE</span>
        <span className="topline-right">ONTOLOGY / {domain.owl.toUpperCase()}</span>
      </div>
      <Link className="back-link" to={'/catalog/' + entity.domain}><ArrowLeft size={17}/> Retour à {domain.title}</Link>

      <section className="profile-heading">
        <div className={'collection-icon tone-' + domain.group.toLowerCase()}>
          <DomainIcon name={domain.icon} size={35}/>
        </div>
        <div>
          <span className="eyebrow">{domain.owl} / {entity.type}</span>
          <h1>{entity.name.replaceAll('_', ' ')}<span className="heading-dot">.</span></h1>
          <p>{entity.description}</p>
        </div>
        <Link className="button-outline" to="/graph">
          <Network size={18}/> Knowledge graph <ArrowUpRight size={16}/>
        </Link>
      </section>

      {/* Composition chimique dynamique depuis l'API Fuseki si disponible */}
      {liveMolecules.length > 0 && (
        <section style={{ background: '#f0fdfa', border: '1px solid #ccfbf1', borderRadius: '16px', padding: '20px', margin: '20px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
            <FlaskConical size={22} color="#0d9488" />
            <h3 style={{ margin: 0, color: '#134e4a', fontSize: '17px' }}>Composition chimique (Fuseki live)</h3>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '12px' }}>
            {liveMolecules.map((m, idx) => (
              <div key={idx} style={{ background: 'white', padding: '12px 16px', borderRadius: '10px', border: '1px solid #99f6e4' }}>
                <div style={{ fontWeight: 700, color: '#0f766e', fontSize: '15px' }}>{m.nom}</div>
                <div style={{ fontSize: '12px', color: '#64748b', marginTop: '2px' }}>
                  <span style={{ fontWeight: 600 }}>{m.type_molecule}</span>
                  {m.formule_chimique && <span> · Formule: <code>{m.formule_chimique}</code></span>}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="section-intro profile-section-title">
        <div>
          <span className="eyebrow">CONTEXTE SÉMANTIQUE</span>
          <h2>Relations ontologiques<span className="heading-dot">.</span></h2>
          <p>Visualisez les liens entre ce concept et le reste de la base de connaissances.</p>
        </div>
      </div>

      <div className="detail-layout">
        <div className="detail-main">
          <section className="detail-panel">
            <header>
              <span className="detail-heading-icon"><GitBranch size={22}/></span>
              <div>
                <h3>Outgoing relationships</h3>
                <p>Connexions partant de ce concept</p>
              </div>
              <span className="detail-count">{entity.relations?.length ?? 0}</span>
            </header>
            {entity.relations?.length ? (
              <div className="relationship-list">
                {entity.relations.map((rel, i) => {
                  const target = getEntity(rel.target);
                  return (
                    <div className="relationship-row" key={i}>
                      <span className="relationship-predicate">{rel.predicate}</span>
                      <span className="relationship-direction"><ArrowRight size={19}/></span>
                      {target ? (
                        <Link to={'/entity/' + encodeURIComponent(target.id)}>
                          <span>{target.name.replaceAll('_', ' ')}</span>
                          <ArrowUpRight size={17}/>
                        </Link>
                      ) : (
                        <span>{rel.target}</span>
                      )}
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="relationship-empty">Aucune relation sortante enregistrée.</div>
            )}
          </section>

          <section className="detail-panel">
            <header>
              <span className="detail-heading-icon"><Link2 size={21}/></span>
              <div>
                <h3>Incoming relationships</h3>
                <p>Autres concepts pointant vers celui-ci</p>
              </div>
              <span className="detail-count">{incoming.length}</span>
            </header>
            {incoming.length ? (
              <div className="relationship-list">
                {incoming.map((rel, i) => (
                  <div className="relationship-row" key={i}>
                    <Link to={'/entity/' + encodeURIComponent(rel.source.id)}>
                      <span>{rel.source.name.replaceAll('_', ' ')}</span>
                      <ArrowUpRight size={17}/>
                    </Link>
                    <span className="relationship-direction"><ArrowRight size={19}/></span>
                    <span className="relationship-predicate">{rel.predicate}</span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="relationship-empty">Aucune relation entrante enregistrée.</div>
            )}
          </section>
        </div>

        <aside className="detail-side">
          <section className="detail-panel">
            <header>
              <span className="detail-heading-icon"><Layers3 size={21}/></span>
              <div>
                <h3>Propriétés</h3>
                <p>Attributs ontologiques</p>
              </div>
            </header>
            <dl className="profile-properties">
              {properties.map(([key, value]) => (
                <div key={key}>
                  <dt>{key}</dt>
                  <dd>{value}</dd>
                </div>
              ))}
            </dl>
          </section>

          <div className="profile-note">
            <Info size={20}/>
            <p>Les données affichées illustrent la structure de l'ontologie MedSemantic.</p>
          </div>
          <Link to="/search" className="profile-side-link">
            <BookOpenText size={18}/> Parcourir les concepts liés <ArrowUpRight size={18}/>
          </Link>
        </aside>
      </div>
    </div>
  );
}
