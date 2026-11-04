import React from 'react';
import PharmacologieModule from './components/pharmacologie/PharmacologieModule';
import './App.css';

function App() {
  return (
    <div className="App">
      {/* Module Pharmacologie (Hana) */}
      <PharmacologieModule />

      {/* 
        Espace collaboratif : les membres du groupe peuvent importer 
        et intégrer leurs modules ici (ex: Maladies, Patients, etc.)
      */}
    </div>
  );
}

export default App;
