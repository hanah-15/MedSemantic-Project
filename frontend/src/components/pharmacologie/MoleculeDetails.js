import React from 'react';

function MoleculeDetails({ selectedMed, molecules }) {
  return (
    <div className="pharmaco-card" style={{ height: 'fit-content' }}>
      <h2 className="pharmaco-card-title" style={{ color: '#2c7a7b' }}>
        🔬 Composition Chimique
      </h2>

      {selectedMed ? (
        <div>
          <div style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '12px', marginBottom: '15px' }}>
            <h3 style={{ margin: '0 0 5px 0', color: '#2d3748' }}>{selectedMed.nom_commercial}</h3>
            <p style={{ margin: 0, color: '#718096', fontSize: '0.85rem' }}>
              URI : <code>ms:{selectedMed.uri}</code>
            </p>
          </div>

          {molecules.length === 0 ? (
            <p style={{ color: '#718096', fontStyle: 'italic' }}>
              Aucune molécule enregistrée pour ce médicament pour le moment.
            </p>
          ) : (
            <div>
              {molecules.map((mol, index) => {
                const isActif = mol.type_molecule && mol.type_molecule.toLowerCase().includes('actif');
                return (
                  <div key={index} className="pharmaco-mol-card">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <strong style={{ fontSize: '1rem', color: '#2d3748' }}>{mol.nom}</strong>
                      <span className={`pharmaco-badge ${isActif ? 'pharmaco-badge-actif' : 'pharmaco-badge-excipient'}`}>
                        {mol.type_molecule}
                      </span>
                    </div>
                    {mol.formule_chimique && (
                      <div style={{ marginTop: '5px', fontSize: '0.85rem', color: '#4a5568' }}>
                        Formule : <code>{mol.formule_chimique}</code>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>
      ) : (
        <div className="pharmaco-empty">
          👈 Cliquez sur un médicament dans la liste pour voir sa composition chimique.
        </div>
      )}
    </div>
  );
}

export default MoleculeDetails;
