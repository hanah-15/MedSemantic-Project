import React from 'react';

function MedicamentList({
  medicaments,
  selectedMed,
  onSelectMed,
  onEditMed,
  onDeleteMed,
  loading
}) {
  return (
    <div className="pharmaco-card">
      <h2 className="pharmaco-card-title">
        <span>📋 Liste des Médicaments ({medicaments.length})</span>
        {loading && <span style={{ fontSize: '0.85rem', color: '#718096' }}>Chargement...</span>}
      </h2>

      {medicaments.length === 0 && !loading ? (
        <div className="pharmaco-empty">Aucun médicament trouvé dans l'ontologie.</div>
      ) : (
        <ul className="pharmaco-med-list">
          {medicaments.map((med) => {
            const isSelected = selectedMed && selectedMed.uri === med.uri;
            return (
              <li
                key={med.uri}
                className={`pharmaco-med-item ${isSelected ? 'active' : ''}`}
                onClick={() => onSelectMed(med)}
              >
                <div className="pharmaco-med-info">
                  <h3>{med.nom_commercial}</h3>
                  <div className="pharmaco-med-meta">
                    <span>💊 <strong>Dosage :</strong> {med.dosage}</span>
                    <span style={{ margin: '0 8px' }}>|</span>
                    <span>🧪 <strong>Forme :</strong> {med.forme_galenique}</span>
                  </div>
                </div>

                <div className="pharmaco-med-actions">
                  <button
                    className="pharmaco-btn pharmaco-btn-primary pharmaco-btn-sm"
                    title="Modifier"
                    onClick={(e) => {
                      e.stopPropagation();
                      onEditMed(med);
                    }}
                  >
                    ✏️ Modifier
                  </button>
                  <button
                    className="pharmaco-btn pharmaco-btn-danger pharmaco-btn-sm"
                    title="Supprimer"
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteMed(med.uri, med.nom_commercial);
                    }}
                  >
                    🗑️
                  </button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}

export default MedicamentList;
