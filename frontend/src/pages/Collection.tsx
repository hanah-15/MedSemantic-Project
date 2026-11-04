import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import {
  ArrowLeft, ArrowRight, ArrowUpRight, Network, Search, SearchX,
  Plus, Pencil, Trash2, X, RefreshCw, AlertCircle, CheckCircle2
} from 'lucide-react';
import { domains, entities, type Entity } from '../data/ontology';
import { DomainIcon } from '../components/Icons';
import EntityCard from '../components/EntityCard';
import { medicamentApi, type Medicament, type MedicamentCreate } from '../lib/medicamentApi';

export default function Collection() {
  const { slug } = useParams();
  const domain = domains.find(d => d.slug === slug);
  const [query, setQuery] = useState('');

  // États pour l'intégration FastAPI (Pharmacologie)
  const [liveMedicaments, setLiveMedicaments] = useState<Medicament[]>([]);
  const [loading, setLoading] = useState(false);
  const [feedback, setFeedback] = useState<{ message: string; type: 'success' | 'error' } | null>(null);

  // Modals CRUD
  const [showAddModal, setShowAddModal] = useState(false);
  const [editingMed, setEditingMed] = useState<Medicament | null>(null);

  // Formulaire d'ajout
  const [newMed, setNewMed] = useState<MedicamentCreate>({
    nom_commercial: '',
    dosage: '',
    forme_galenique: '',
  });

  const isMedicationsDomain = slug === 'medications';

  // Charger les médicaments depuis l'API FastAPI
  const loadMedicaments = async () => {
    if (!isMedicationsDomain) return;
    setLoading(true);
    try {
      const data = await medicamentApi.getAll();
      setLiveMedicaments(data);
    } catch (err: any) {
      console.warn("API FastAPI non joignable, fallback sur les données d'exemple:", err);
      // Ne bloque pas l'utilisateur, garde les mock si l'API est éteinte
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMedicaments();
  }, [slug]);

  const showNotification = (message: string, type: 'success' | 'error' = 'success') => {
    setFeedback({ message, type });
    setTimeout(() => setFeedback(null), 4000);
  };

  if (!domain) {
    return (
      <div className="empty-state">
        <SearchX size={32} />
        <h2>Collection non trouvée</h2>
        <Link className="button-primary" to="/">Retour au tableau de bord <ArrowRight size={17} /></Link>
      </div>
    );
  }

  // 1. Liste des entités à afficher (Live API si dispo, sinon mock initial)
  const baseItems: Entity[] = isMedicationsDomain && liveMedicaments.length > 0
    ? liveMedicaments.map(m => ({
        id: m.uri,
        name: m.nom_commercial,
        domain: 'medications',
        type: m.forme_galenique || 'Médicament',
        description: `Dosage : ${m.dosage} | Forme : ${m.forme_galenique}`,
        properties: { Dosage: m.dosage, 'Forme Galénique': m.forme_galenique },
      }))
    : entities.filter(entity => entity.domain === slug);

  const filteredItems = baseItems.filter(item =>
    [item.name, item.type, item.id].join(' ').toLowerCase().includes(query.trim().toLowerCase())
  );

  // 2. Action CREATE
  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newMed.nom_commercial || !newMed.dosage || !newMed.forme_galenique) {
      showNotification('Veuillez remplir tous les champs.', 'error');
      return;
    }
    try {
      await medicamentApi.create(newMed);
      showNotification(`Médicament "${newMed.nom_commercial}" ajouté avec succès !`);
      setShowAddModal(false);
      setNewMed({ nom_commercial: '', dosage: '', forme_galenique: '' });
      await loadMedicaments();
    } catch (err: any) {
      showNotification(err.message || "Erreur lors de l'ajout.", 'error');
    }
  };

  // 3. Action UPDATE
  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingMed) return;
    try {
      await medicamentApi.update(editingMed.uri, {
        nom_commercial: editingMed.nom_commercial,
        dosage: editingMed.dosage,
        forme_galenique: editingMed.forme_galenique,
      });
      showNotification(`Médicament "${editingMed.nom_commercial}" mis à jour avec succès !`);
      setEditingMed(null);
      await loadMedicaments();
    } catch (err: any) {
      showNotification(err.message || 'Erreur lors de la modification.', 'error');
    }
  };

  // 4. Action DELETE
  const handleDelete = async (uri: string, name: string) => {
    if (!window.confirm(`Supprimer définitivement le médicament "${name}" de l'ontologie ?`)) return;
    try {
      await medicamentApi.delete(uri);
      showNotification(`Médicament "${name}" supprimé avec succès !`);
      await loadMedicaments();
    } catch (err: any) {
      showNotification(err.message || 'Erreur lors de la suppression.', 'error');
    }
  };

  return (
    <div className="page-flow inner-page">
      <div className="page-topline">
        <span className="eyebrow"><span className="eyebrow-indicator" /> THE MEDICAL ATLAS</span>
        <span className="topline-right">ONTOLOGY / {domain.owl.toUpperCase()}</span>
      </div>
      <Link className="back-link" to="/"><ArrowLeft size={17} /> Back to overview</Link>

      <section className={'collection-hero collection-' + domain.group.toLowerCase()}>
        <div className={'collection-icon tone-' + domain.group.toLowerCase()}>
          <DomainIcon name={domain.icon} size={36} />
        </div>
        <div className="collection-heading">
          <span className="eyebrow">ONTOLOGY CLASS / {domain.owl}</span>
          <h1>{domain.title}<span className="heading-dot">.</span></h1>
          <p>{domain.description} — explore its records and discover their connections.</p>
        </div>
        <div className="collection-stat">
          <strong>{filteredItems.length.toString().padStart(2, '0')}</strong>
          <span>CONNECTED ENTRIES</span>
        </div>
      </section>

      {/* Toast Notification */}
      {feedback && (
        <div
          style={{
            padding: '12px 18px',
            borderRadius: '10px',
            marginTop: '15px',
            display: 'flex',
            alignItems: 'center',
            gap: '10px',
            fontWeight: 600,
            fontSize: '14px',
            background: feedback.type === 'success' ? '#e6fffa' : '#ffeef0',
            color: feedback.type === 'success' ? '#047481' : '#b91c1c',
            border: `1px solid ${feedback.type === 'success' ? '#a2f5ea' : '#fecdd3'}`,
          }}
        >
          {feedback.type === 'success' ? <CheckCircle2 size={18} /> : <AlertCircle size={18} />}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Barre d'action et boutons CRUD */}
      <div className="section-intro collection-intro" style={{ alignItems: 'center' }}>
        <div>
          <span className="eyebrow">EXPLORATION & GESTION</span>
          <h2>The collection<span className="heading-dot">.</span></h2>
          <p>Consultez, ajoutez, modifiez ou supprimez les entrées de l'ontologie.</p>
        </div>

        <div style={{ display: 'flex', gap: '12px', alignItems: 'center', flexWrap: 'wrap' }}>
          <label className="collection-search">
            <Search size={20} />
            <input
              aria-label={'Filter ' + domain.title}
              placeholder={'Rechercher dans ' + domain.title.toLowerCase() + '...'}
              value={query}
              onChange={e => setQuery(e.target.value)}
            />
          </label>

          {isMedicationsDomain && (
            <>
              <button
                className="button-primary"
                onClick={() => setShowAddModal(true)}
                style={{ cursor: 'pointer' }}
              >
                <Plus size={18} /> Ajouter un médicament
              </button>

              <button
                className="button-outline"
                title="Rafraîchir depuis Fuseki"
                onClick={loadMedicaments}
                disabled={loading}
                style={{ padding: '10px 14px', cursor: 'pointer' }}
              >
                <RefreshCw size={17} className={loading ? 'spin' : ''} />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Grille des cartes avec boutons Modifier & Supprimer */}
      {loading && liveMedicaments.length === 0 ? (
        <div style={{ padding: '50px', textAlign: 'center', color: '#64748b' }}>
          <RefreshCw size={28} className="spin" style={{ margin: '0 auto 10px', display: 'block' }} />
          Chargement depuis Fuseki...
        </div>
      ) : filteredItems.length ? (
        <div className="entity-grid">
          {filteredItems.map(item => {
            const liveMatch = liveMedicaments.find(m => m.uri === item.id || m.nom_commercial === item.name);
            return (
              <div key={item.id} style={{ position: 'relative', display: 'flex', flexDirection: 'column' }}>
                <EntityCard item={item} />

                {/* Boutons d'action CRUD sur chaque carte */}
                {isMedicationsDomain && (
                  <div
                    style={{
                      position: 'absolute',
                      top: '18px',
                      right: '54px',
                      display: 'flex',
                      gap: '6px',
                      zIndex: 10,
                    }}
                  >
                    <button
                      style={{
                        background: '#ffffff',
                        border: '1px solid #cbd5e1',
                        borderRadius: '6px',
                        padding: '6px 8px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '11px',
                        fontWeight: 700,
                        color: '#0369a1',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.06)',
                      }}
                      title="Modifier ce médicament"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        setEditingMed({
                          uri: item.id,
                          nom_commercial: item.name,
                          dosage: liveMatch?.dosage || item.properties?.Dosage || '',
                          forme_galenique: liveMatch?.forme_galenique || item.properties?.['Forme Galénique'] || item.type || '',
                        });
                      }}
                    >
                      <Pencil size={13} /> Modifier
                    </button>

                    <button
                      style={{
                        background: '#ffffff',
                        border: '1px solid #fecdd3',
                        borderRadius: '6px',
                        padding: '6px 8px',
                        cursor: 'pointer',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '11px',
                        fontWeight: 700,
                        color: '#be123c',
                        boxShadow: '0 2px 4px rgba(0,0,0,0.06)',
                      }}
                      title="Supprimer ce médicament"
                      onClick={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleDelete(item.id, item.name);
                      }}
                    >
                      <Trash2 size={13} /> Supprimer
                    </button>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <div className="empty-state">
          <SearchX size={35} />
          <h3>Aucun médicament trouvé</h3>
          <p>Essayez un autre mot-clé ou réinitialisez votre recherche.</p>
          <button className="button-primary" onClick={() => setQuery('')}>
            Afficher tous les médicaments <ArrowRight size={17} />
          </button>
        </div>
      )}

      {/* =========================================
          MODAL CREATE (Ajouter un médicament)
          ========================================= */}
      {showAddModal && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.65)',
            backdropFilter: 'blur(3px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
          }}
          onClick={() => setShowAddModal(false)}
        >
          <div
            style={{
              background: 'white',
              borderRadius: '16px',
              padding: '28px',
              maxWidth: '480px',
              width: '90%',
              boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)',
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div>
                <span className="eyebrow" style={{ color: '#078b89' }}>NOUVEAU MÉDICAMENT</span>
                <h3 style={{ margin: '4px 0 0', fontSize: '20px', color: '#0f2d3c' }}>Ajouter à l'ontologie</h3>
              </div>
              <button
                onClick={() => setShowAddModal(false)}
                style={{ background: '#f1f5f9', border: 'none', borderRadius: '50%', width: '32px', height: '32px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleCreate}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '6px', textTransform: 'uppercase' }}>
                  Nom commercial *
                </label>
                <input
                  required
                  placeholder="ex: Doliprane 1000mg"
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                  value={newMed.nom_commercial}
                  onChange={e => setNewMed({ ...newMed, nom_commercial: e.target.value })}
                />
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '6px', textTransform: 'uppercase' }}>
                  Dosage *
                </label>
                <input
                  required
                  placeholder="ex: 1000 mg"
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                  value={newMed.dosage}
                  onChange={e => setNewMed({ ...newMed, dosage: e.target.value })}
                />
              </div>

              <div style={{ marginBottom: '22px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '6px', textTransform: 'uppercase' }}>
                  Forme galénique *
                </label>
                <input
                  required
                  placeholder="ex: Comprimé, Gélule, Sirop..."
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                  value={newMed.forme_galenique}
                  onChange={e => setNewMed({ ...newMed, forme_galenique: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  style={{ padding: '10px 18px', borderRadius: '8px', border: '1px solid #cbd5e1', background: '#f8fafc', fontWeight: 700, cursor: 'pointer' }}
                >
                  Annuler
                </button>
                <button type="submit" className="button-primary" style={{ cursor: 'pointer' }}>
                  💾 Enregistrer dans Fuseki
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* =========================================
          MODAL UPDATE (Modifier un médicament)
          ========================================= */}
      {editingMed && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.65)',
            backdropFilter: 'blur(3px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 9999,
          }}
          onClick={() => setEditingMed(null)}
        >
          <div
            style={{
              background: 'white',
              borderRadius: '16px',
              padding: '28px',
              maxWidth: '480px',
              width: '90%',
              boxShadow: '0 25px 50px -12px rgba(0,0,0,0.25)',
            }}
            onClick={e => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <div>
                <span className="eyebrow" style={{ color: '#0284c7' }}>MODIFICATION</span>
                <h3 style={{ margin: '4px 0 0', fontSize: '20px', color: '#0f2d3c' }}>Modifier le médicament</h3>
              </div>
              <button
                onClick={() => setEditingMed(null)}
                style={{ background: '#f1f5f9', border: 'none', borderRadius: '50%', width: '32px', height: '32px', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              >
                <X size={18} />
              </button>
            </div>

            <form onSubmit={handleUpdate}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '6px', textTransform: 'uppercase' }}>
                  Nom commercial
                </label>
                <input
                  required
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                  value={editingMed.nom_commercial}
                  onChange={e => setEditingMed({ ...editingMed, nom_commercial: e.target.value })}
                />
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '6px', textTransform: 'uppercase' }}>
                  Dosage
                </label>
                <input
                  required
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                  value={editingMed.dosage}
                  onChange={e => setEditingMed({ ...editingMed, dosage: e.target.value })}
                />
              </div>

              <div style={{ marginBottom: '22px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, color: '#334155', marginBottom: '6px', textTransform: 'uppercase' }}>
                  Forme galénique
                </label>
                <input
                  required
                  style={{ width: '100%', padding: '10px 14px', borderRadius: '8px', border: '1px solid #cbd5e1', fontSize: '14px' }}
                  value={editingMed.forme_galenique}
                  onChange={e => setEditingMed({ ...editingMed, forme_galenique: e.target.value })}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button
                  type="button"
                  onClick={() => setEditingMed(null)}
                  style={{ padding: '10px 18px', borderRadius: '8px', border: '1px solid #cbd5e1', background: '#f8fafc', fontWeight: 700, cursor: 'pointer' }}
                >
                  Annuler
                </button>
                <button type="submit" className="button-primary" style={{ cursor: 'pointer' }}>
                  💾 Sauvegarder les modifications
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="related-banner">
        <span><Network size={26} /></span>
        <div>
          <strong>There’s more to the story.</strong>
          <p>Every concept is part of a larger system of relationships.</p>
        </div>
        <Link to="/graph">Explore the knowledge graph <ArrowUpRight size={18} /></Link>
      </div>
    </div>
  );
}
