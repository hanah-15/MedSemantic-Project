import { useEffect, useState } from 'react';
import { medicamentApi, type Medicament } from '../lib/medicamentApi';
import type { Entity } from '../data/ontology';
import type { LoadStatus } from './useClinicalRecords';
import { useClinicalResource } from './useClinicalRecords';

export function useMedicationCollection() {
  const result = useClinicalResource<Medicament[]>('medications','/api/medicaments/');
  return {...result,data:result.data?.map(medicationToEntity) ?? null};
}

function medicationToEntity(medication:Medicament):Entity {
  return {
    id:medication.uri, name:medication.nom_commercial, domain:'medications', type:'Medicament',
    description:[medication.dosage,medication.forme_galenique].filter(Boolean).join(' · '),
    properties:{dosage:medication.dosage,formeGalenique:medication.forme_galenique},
    relations:(medication.molecules ?? []).map(molecule=>({
      predicate:molecule.type_molecule.toLowerCase().includes('actif') ? 'contientPrincipeActif' : 'contientExcipient',
      target:molecule.nom,
    })),
  };
}

export function useMedicationRecord(enabled: boolean, id?: string) {
  const [result,setResult] = useState<{id?:string; status:LoadStatus; data:Medicament|null}>({status:'idle',data:null});
  const [attempt,setAttempt] = useState(0);
  const retry = () => setAttempt(value=>value+1);
  useEffect(()=>{
    if (!enabled || !id) return;
    const controller = new AbortController();
    setResult({id,status:'loading',data:null});
    medicamentApi.getDetails(id,controller.signal).then(data=>{
      if (!controller.signal.aborted) setResult({id,status:'connected',data});
    }).catch(error=>{
      if (!controller.signal.aborted) setResult({id,status:String(error).includes('404') ? 'not-found' : 'unavailable',data:null});
    });
    return ()=>controller.abort();
  },[enabled,id,attempt]);
  const active = enabled && !!id;
  const status:LoadStatus = !active ? 'idle' : result.id === id ? result.status : 'loading';
  const medication = active && result.id === id ? result.data : null;
  const entity = medication ? medicationToEntity(medication) : null;
  return {entity,medication,status,retry};
}
