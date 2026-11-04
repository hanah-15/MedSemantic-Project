import React, { useState } from 'react';

function MedicamentEditModal({ medicament, onSave, onClose }) {
  const [formData, setFormData] = useState({
    nom_commercial: medicament.nom_commercial,
    dosage: medicament.dosage,
    forme_galenique: medicament.forme_galenique
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSave(medicament.uri, formData);
  };

  return (
    <div className="pharmaco-modal-overlay" onClick={onClose}>
      <div className="pharmaco-modal-content" onClick={(e) => e.stopPropagation()}>
        <h3 className="pharmaco-card-title">Modifier le médicament</h3>
        <p style={{ color: '#718096', fontSize: '0.85rem', marginTop: '-10px', marginBottom: '15px' }}>
          URI : <code>ms:{medicament.uri}</code>
        </p>

        <form onSubmit={handleSubmit}>
          <div className="pharmaco-form-group" style={{ marginBottom: '12px' }}>
            <label>Nom commercial</label>
            <input
              type="text"
              className="pharmaco-form-control"
              value={formData.nom_commercial}
              onChange={(e) => setFormData({ ...formData, nom_commercial: e.target.value })}
              required
            />
          </div>

          <div className="pharmaco-form-group" style={{ marginBottom: '12px' }}>
            <label>Dosage</label>
            <input
              type="text"
              className="pharmaco-form-control"
              value={formData.dosage}
              onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
              required
            />
          </div>

          <div className="pharmaco-form-group" style={{ marginBottom: '20px' }}>
            <label>Forme galénique</label>
            <input
              type="text"
              className="pharmaco-form-control"
              value={formData.forme_galenique}
              onChange={(e) => setFormData({ ...formData, forme_galenique: e.target.value })}
              required
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
            <button type="button" className="pharmaco-btn pharmaco-btn-secondary" onClick={onClose}>
              Annuler
            </button>
            <button type="submit" className="pharmaco-btn pharmaco-btn-primary">
              💾 Enregistrer les modifications
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default MedicamentEditModal;
