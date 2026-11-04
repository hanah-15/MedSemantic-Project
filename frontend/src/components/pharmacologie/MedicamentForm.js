import React, { useState } from 'react';

function MedicamentForm({ onSubmit, onCancel }) {
  const [formData, setFormData] = useState({
    nom_commercial: '',
    dosage: '',
    forme_galenique: '',
    ajouter_molecule: false,
    molecule_nom: '',
    molecule_type: 'Principe actif',
    molecule_formule: ''
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!formData.nom_commercial || !formData.dosage || !formData.forme_galenique) {
      alert("Veuillez remplir tous les champs obligatoires du médicament.");
      return;
    }

    const payload = {
      nom_commercial: formData.nom_commercial,
      dosage: formData.dosage,
      forme_galenique: formData.forme_galenique,
      molecules: []
    };

    if (formData.ajouter_molecule && formData.molecule_nom) {
      payload.molecules.push({
        nom: formData.molecule_nom,
        type_molecule: formData.molecule_type,
        formule_chimique: formData.molecule_formule || null
      });
    }

    onSubmit(payload);
  };

  return (
    <div className="pharmaco-card">
      <h3 className="pharmaco-card-title">Ajouter un nouveau médicament</h3>
      <form onSubmit={handleSubmit}>
        <div className="pharmaco-form-grid">
          <div className="pharmaco-form-group">
            <label>Nom commercial *</label>
            <input
              type="text"
              className="pharmaco-form-control"
              placeholder="ex: Doliprane 1000mg"
              value={formData.nom_commercial}
              onChange={(e) => setFormData({ ...formData, nom_commercial: e.target.value })}
              required
            />
          </div>

          <div className="pharmaco-form-group">
            <label>Dosage *</label>
            <input
              type="text"
              className="pharmaco-form-control"
              placeholder="ex: 1000 mg"
              value={formData.dosage}
              onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
              required
            />
          </div>

          <div className="pharmaco-form-group">
            <label>Forme galénique *</label>
            <input
              type="text"
              className="pharmaco-form-control"
              placeholder="ex: Comprimé, Sirop..."
              value={formData.forme_galenique}
              onChange={(e) => setFormData({ ...formData, forme_galenique: e.target.value })}
              required
            />
          </div>
        </div>

        {/* Optionnel: Molécule associée */}
        <div style={{ margin: '15px 0' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontWeight: 600 }}>
            <input
              type="checkbox"
              checked={formData.ajouter_molecule}
              onChange={(e) => setFormData({ ...formData, ajouter_molecule: e.target.checked })}
            />
            Associer une molécule (Principe actif / Excipient)
          </label>
        </div>

        {formData.ajouter_molecule && (
          <div className="pharmaco-molecule-box">
            <h4 style={{ margin: '0 0 10px 0', color: '#4a5568' }}>Informations de la molécule</h4>
            <div className="pharmaco-form-grid">
              <div className="pharmaco-form-group">
                <label>Nom de la molécule</label>
                <input
                  type="text"
                  className="pharmaco-form-control"
                  placeholder="ex: Paracétamol"
                  value={formData.molecule_nom}
                  onChange={(e) => setFormData({ ...formData, molecule_nom: e.target.value })}
                />
              </div>

              <div className="pharmaco-form-group">
                <label>Type</label>
                <select
                  className="pharmaco-form-control"
                  value={formData.molecule_type}
                  onChange={(e) => setFormData({ ...formData, molecule_type: e.target.value })}
                >
                  <option value="Principe actif">Principe actif</option>
                  <option value="Excipient">Excipient</option>
                </select>
              </div>

              <div className="pharmaco-form-group">
                <label>Formule chimique (optionnel)</label>
                <input
                  type="text"
                  className="pharmaco-form-control"
                  placeholder="ex: C8H9NO2"
                  value={formData.molecule_formule}
                  onChange={(e) => setFormData({ ...formData, molecule_formule: e.target.value })}
                />
              </div>
            </div>
          </div>
        )}

        <div style={{ display: 'flex', gap: '10px', marginTop: '10px' }}>
          <button type="submit" className="pharmaco-btn pharmaco-btn-success">
            Enregistrer dans l'ontologie
          </button>
          <button type="button" className="pharmaco-btn pharmaco-btn-secondary" onClick={onCancel}>
            Annuler
          </button>
        </div>
      </form>
    </div>
  );
}

export default MedicamentForm;
