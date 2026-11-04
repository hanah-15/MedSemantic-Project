import { useEffect, useState, type FormEvent } from 'react';
import { X } from 'lucide-react';
import type { Entity } from '../data/ontology';
import { apiGet, apiWrite } from '../lib/api';

type ClinicalDomain = 'patients'|'conditions';
const linkLabels = {aPourMaladie:'Diseases',aPourCondition:'Medical conditions',ressentSymptome:'Symptoms',prend:'Medications'};
type Links = Record<keyof typeof linkLabels,string[]>;
type Options = Record<keyof typeof linkLabels,{id:string;name:string}[]>;

export default function ClinicalEditor({domain,record,onClose,onSaved}:{domain:ClinicalDomain;record:Entity|null;onClose:()=>void;onSaved:()=>void}) {
  const patient = domain === 'patients';
  const [id,setId] = useState(record?.id ?? '');
  const [age,setAge] = useState(record?.properties?.age ?? '');
  const [sex,setSex] = useState(record?.properties?.sexe ?? '');
  const [type,setType] = useState(record?.type ?? '');
  const [severity,setSeverity] = useState(record?.properties?.severite ?? '');
  const [links,setLinks] = useState<Links>(()=>Object.fromEntries(Object.keys(linkLabels).map(predicate=>[predicate,(record?.relations ?? []).filter(link=>link.predicate === predicate).map(link=>link.target)])) as Links);
  const [options,setOptions] = useState<Options|null>(null);
  const [types,setTypes] = useState<{id:string;parent:string}[]>([]);
  const [ready,setReady] = useState(false);
  const [saving,setSaving] = useState(false);
  const [error,setError] = useState('');

  useEffect(()=>{
    const controller = new AbortController();
    const request = patient ? apiGet<Options>('/api/patients/options',controller.signal).then(setOptions)
      : apiGet<{id:string;parent:string}[]>('/api/conditions/types',controller.signal).then(setTypes);
    request.then(()=>{if (!controller.signal.aborted) setReady(true);}).catch(()=>{
      if (!controller.signal.aborted) setError('Form options could not be loaded. Close this form and try again.');
    });
    return ()=>controller.abort();
  },[patient]);

  async function submit(event:FormEvent) {
    event.preventDefault();
    setError('');setSaving(true);
    const data = patient ? {age:Number(age),sexe:sex,...links} : {type,severite:severity.trim() || null};
    try {
      await apiWrite('/api/'+domain+(record ? '/'+encodeURIComponent(record.id) : ''),record ? 'PUT' : 'POST',record ? data : {id,...data});
      onSaved();
    } catch(error) {setError(error instanceof Error ? error.message : 'Unable to save this record.');}
    finally {setSaving(false);}
  }

  function toggle(predicate:keyof Links,target:string,checked:boolean) {
    setLinks(current=>({...current,[predicate]:checked ? [...new Set([...current[predicate],target])] : current[predicate].filter(id=>id !== target)}));
  }

  return <div className="clinical-modal-backdrop" onKeyDown={event=>{if(event.key === 'Escape' && !saving) onClose();}}>
    <section className="clinical-modal" role="dialog" aria-modal="true" aria-labelledby="clinical-editor-title">
      <header><h2 id="clinical-editor-title">{record ? 'Edit' : 'Add'} {patient ? 'patient' : 'medical condition'}</h2><button type="button" aria-label="Close form" onClick={onClose} disabled={saving}><X size={22}/></button></header>
      <form onSubmit={submit}>
        <label>Record ID<input autoFocus={!record} required pattern="[A-Za-z][A-Za-z0-9_]*" maxLength={120} value={id} onChange={event=>setId(event.target.value)} disabled={!!record || saving} placeholder={patient ? 'Patient_Ali' : 'Condition_Allergie'}/></label>
        {patient ? <>
          <div className="clinical-form-row"><label>Age<input autoFocus={!!record} type="number" min="0" step="1" required value={age} onChange={event=>setAge(event.target.value)} disabled={saving}/></label><label>Sex<select required value={sex} onChange={event=>setSex(event.target.value)} disabled={saving}><option value="">Choose sex</option><option value="F">Female (F)</option><option value="M">Male (M)</option>{sex && !['F','M'].includes(sex) && <option value={sex}>{sex}</option>}</select></label></div>
          {options && (Object.keys(linkLabels) as (keyof Links)[]).map(predicate=><fieldset key={predicate} className="clinical-link-options"><legend>{linkLabels[predicate]}</legend>{options[predicate].length ? options[predicate].map(option=><label key={option.id}><input type="checkbox" checked={links[predicate].includes(option.id)} onChange={event=>toggle(predicate,option.id,event.target.checked)} disabled={saving}/>{option.name}</label>) : <p>No records available.</p>}</fieldset>)}
        </> : <>
          <label>Condition type<select required value={type} onChange={event=>setType(event.target.value)} disabled={!ready || saving}><option value="">Choose a type</option>{types.map(option=><option key={option.id} value={option.id}>{option.id}</option>)}</select></label>
          <label>Severity<input autoFocus={!!record} maxLength={500} placeholder="Optional" value={severity} onChange={event=>setSeverity(event.target.value)} disabled={saving}/></label>
        </>}
        {!ready && !error && <p role="status">Loading form options…</p>}
        {error && <p className="clinical-error" role="alert">{error}</p>}
        <footer><button type="button" className="button-outline" onClick={onClose} disabled={saving}>Cancel</button><button type="submit" className="button-primary" disabled={!ready || saving}>{saving ? 'Saving…' : 'Save record'}</button></footer>
      </form>
    </section>
  </div>;
}
