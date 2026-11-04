import React, { useState, useEffect } from 'react';
import { medicamentService } from '../../services/medicamentService';
import MedicamentList from './MedicamentList';
import MedicamentForm from './MedicamentForm';
import MedicamentEditModal from './MedicamentEditModal';
import MoleculeDetails from './MoleculeDetails';
import './Pharmacologie.css';

function PharmacologieModule() {
  const [medicaments, setMedicaments] = useState([]);
  const [selectedMed, setSelectedMed] = useState(null);
  const [molecules, setMolecules] = useState([]);
  const [loading, setLoading] = useState(false);
  const [alert, setAlert] = useState(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [editingMed, setEditingMed] = useState(null);

  const showAlert = (message, type = 'success') => {
    setAlert({ message, type });
    setTimeout(() => setAlert(null), 4000);
  };

  const loadMedicaments = () => {
    setLoading(true);
    medicamentService.getAll()
      .then((data) => setMedicaments(data))
      .catch((err) => {
        console.error("Erreur API:", err);
        showAlert("Erreur lors de la récupération des médicaments.", "error");
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadMedicaments();
  }, []);

  const handleSelectMed = (med) => {
    setSelectedMed(med);
    medicamentService.getMoleculesByNom(med.nom_commercial)
      .then((data) => setMolecules(data))
      .catch((err) => {
        console.error("Erreur molécules:", err);
        setMolecules([]);
      });
  };

  const handleCreate = (payload) => {
    medicamentService.create(payload)
      .then(() => {
        showAlert(`Médicament "${payload.nom_commercial}" ajouté avec succès !`);
        setShowAddForm(false);
        loadMedicaments();
      })
      .catch((err) => {
        console.error("Erreur création:", err);
        const msg = err.response?.data?.detail || "Erreur lors de l'ajout.";
        showAlert(msg, "error");
      });
  };

  const handleSaveEdit = (uri, updateData) => {
    medicamentService.update(uri, updateData)
      .then(() => {
        showAlert("Médicament mis à jour avec succès !");
        if (selectedMed && selectedMed.uri === uri) {
          setSelectedMed({ ...selectedMed, ...updateData });
        }
        setEditingMed(null);
        loadMedicaments();
      })
      .catch((err) => {
        console.error("Erreur modification:", err);
        const msg = err.response?.data?.detail || "Erreur lors de la modification.";
        showAlert(msg, "error");
      });
  };

  const handleDelete = (uri, nomCommercial) => {
    if (!window.confirm(`Êtes-vous sûr de vouloir supprimer "${nomCommercial}" ?`)) {
      return;
    }
    medicamentService.delete(uri)
      .then(() => {
        showAlert(`Médicament "${nomCommercial}" supprimé avec succès !`);
        if (selectedMed && selectedMed.uri === uri) {
          setSelectedMed(null);
          setMolecules([]);
        }
        loadMedicaments();
      })
      .catch((err) => {
        console.error("Erreur suppression:", err);
        const msg = err.response?.data?.detail || "Erreur lors de la suppression.";
        showAlert(msg, "error");
      });
  };

  return (
    <div className="pharmaco-container">
      <header className="pharmaco-header">
        <h2>🏥 MedSemantic - Pharmacologie</h2>
        <p>Géré par Hana — Classes : Médicament & Molécule</p>
      </header>

      {alert && (
        <div className={`pharmaco-alert pharmaco-alert-${alert.type}`}>
          <span>{alert.message}</span>
          <button className="pharmaco-alert-close" onClick={() => setAlert(null)}>×</button>
        </div>
      )}

      <div style={{ marginBottom: '18px', display: 'flex', justifyContent: 'flex-end' }}>
        <button
          className={`pharmaco-btn ${showAddForm ? 'pharmaco-btn-secondary' : 'pharmaco-btn-success'}`}
          onClick={() => setShowAddForm(!showAddForm)}
        >
          {showAddForm ? '✖ Fermer' : '➕ Nouveau Médicament'}
        </button>
      </div>

      {showAddForm && (
        <MedicamentForm
          onSubmit={handleCreate}
          onCancel={() => setShowAddForm(false)}
        />
      )}

      <div className="pharmaco-grid">
        <MedicamentList
          medicaments={medicaments}
          selectedMed={selectedMed}
          onSelectMed={handleSelectMed}
          onEditMed={(med) => setEditingMed({ ...med })}
          onDeleteMed={handleDelete}
          loading={loading}
        />

        <MoleculeDetails
          selectedMed={selectedMed}
          molecules={molecules}
        />
      </div>

      {editingMed && (
        <MedicamentEditModal
          medicament={editingMed}
          onSave={handleSaveEdit}
          onClose={() => setEditingMed(null)}
        />
      )}
    </div>
  );
}

export default PharmacologieModule;
