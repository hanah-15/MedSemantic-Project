// @vitest-environment jsdom
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import Collection from '../src/pages/Collection';
import Detail from '../src/pages/Detail';
import SearchPage from '../src/pages/Search';

const medication = {uri:'NewMedication',nom_commercial:'New medication',dosage:'10 mg',forme_galenique:'sirop',molecules:[{nom:'NewMolecule',type_molecule:'Principe actif',formule_chimique:'C2H6'}]};
const response = (data:unknown,status=200) => Promise.resolve(new Response(JSON.stringify(data),{status}));
function show(path:string) {
  return render(<MemoryRouter initialEntries={[path]}><Routes>
    <Route path="/catalog/:slug" element={<Collection/>}/>
    <Route path="/entity/:id" element={<Detail/>}/>
    <Route path="/search" element={<SearchPage/>}/>
  </Routes></MemoryRouter>);
}
afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.restoreAllMocks();});

it('keeps medication CRUD controls separate from the patient collection',async()=>{
  vi.stubGlobal('fetch',vi.fn(()=>response([])));
  show('/catalog/patients');
  await screen.findByRole('heading',{name:'No records found'});
  expect(screen.queryByRole('button',{name:'Ajouter un médicament'})).toBeNull();
});

it('displays live medications without substituting samples for an empty dataset',async()=>{
  vi.stubGlobal('fetch',vi.fn(()=>response([])));
  show('/catalog/medications');
  await screen.findByRole('heading',{name:'Aucun médicament trouvé'});
  expect(screen.queryByText('Doliprane')).toBeNull();
  expect(screen.getByRole('button',{name:'Ajouter un médicament'})).toBeTruthy();
});

it('creates a medication and refreshes the shared collection',async()=>{
  let records:typeof medication[] = [];
  const fetch = vi.fn((url:string,options?:RequestInit)=>{
    if (options?.method === 'POST') { records=[medication]; return response(medication,201); }
    return response(records);
  });
  vi.stubGlobal('fetch',fetch);
  show('/catalog/medications');
  await screen.findByRole('heading',{name:'Aucun médicament trouvé'});
  fireEvent.click(screen.getByRole('button',{name:'Ajouter un médicament'}));
  fireEvent.change(screen.getByPlaceholderText('ex: Doliprane 1000mg'),{target:{value:medication.nom_commercial}});
  fireEvent.change(screen.getByPlaceholderText('ex: 1000 mg'),{target:{value:medication.dosage}});
  fireEvent.change(screen.getByPlaceholderText('ex: Comprimé, Gélule, Sirop...'),{target:{value:medication.forme_galenique}});
  fireEvent.click(screen.getByRole('button',{name:/Enregistrer dans Fuseki/}));
  await screen.findByRole('heading',{name:'New medication'});
  expect(fetch.mock.calls.some(([,options])=>options?.method === 'POST')).toBe(true);
  expect(screen.getByRole('link',{name:/New medication/}).getAttribute('href')).toContain('NewMedication?domain=medications');
});

it('updates a medication using Hana’s edit form',async()=>{
  let record={...medication};
  const fetch=vi.fn((url:string,options?:RequestInit)=>{
    if (options?.method === 'PUT') { record={...record,...JSON.parse(String(options.body))}; return response({status:'success'}); }
    return response([record]);
  });
  vi.stubGlobal('fetch',fetch);
  show('/catalog/medications');
  await screen.findByRole('heading',{name:'New medication'});
  fireEvent.click(screen.getByTitle('Modifier ce médicament'));
  fireEvent.change(screen.getByDisplayValue('10 mg'),{target:{value:'20 mg'}});
  fireEvent.click(screen.getByRole('button',{name:/Sauvegarder les modifications/}));
  await waitFor(()=>expect(fetch.mock.calls.some(([,options])=>options?.method === 'PUT')).toBe(true));
  await screen.findByText(/Dosage : 20 mg/);
});

it('deletes only the selected medication after confirmation',async()=>{
  let records=[medication];
  const fetch=vi.fn((url:string,options?:RequestInit)=>{
    if (options?.method === 'DELETE') { records=[]; return response({status:'success'}); }
    return response(records);
  });
  vi.stubGlobal('fetch',fetch);
  vi.spyOn(window,'confirm').mockReturnValue(true);
  show('/catalog/medications');
  await screen.findByRole('heading',{name:'New medication'});
  fireEvent.click(screen.getByTitle('Supprimer ce médicament'));
  await screen.findByRole('heading',{name:'Aucun médicament trouvé'});
  expect(fetch.mock.calls.some(([url,options])=>url.endsWith('/NewMedication') && options?.method === 'DELETE')).toBe(true);
});

it('opens new medication profiles and molecule composition without a preview entry',async()=>{
  vi.stubGlobal('fetch',vi.fn((url:string)=>response(url.includes('/api/patients') ? [] : medication)));
  show('/entity/NewMedication?domain=medications');
  await screen.findByRole('heading',{name:'New medication.'});
  expect(screen.getByRole('heading',{name:'Composition chimique'})).toBeTruthy();
  expect(screen.getByText('C2H6')).toBeTruthy();
  expect(screen.getByRole('link',{name:/NewMolecule.*Sample profile/}).getAttribute('href')).toBe('/entity/NewMolecule?domain=molecules');
});

it('links medication profiles back to actual patients from the other module',async()=>{
  vi.stubGlobal('fetch',vi.fn((url:string)=>response(url.includes('/api/patients') ? [{id:'Patient_New',name:'New patient',domain:'patients',type:'Patient',description:'',relations:[{predicate:'prend',target:'NewMedication'}]}] : medication)));
  show('/entity/NewMedication?domain=medications');
  await screen.findByRole('heading',{name:'Patients taking this medication'});
  expect(screen.getByRole('link',{name:'New patient'}).getAttribute('href')).toBe('/entity/Patient_New?domain=patients');
});

it('includes live medication records in the combined search',async()=>{
  vi.stubGlobal('fetch',vi.fn((url:string)=>response(url.includes('/api/medicaments/') ? [medication] : [])));
  show('/search?q=NewMedication');
  const card = await screen.findByRole('heading',{name:'New medication'});
  expect(card.closest('.search-result')?.querySelector('.record-source')).toBeNull();
});

it('shows Hana’s natural-language answer alongside the shared search',async()=>{
  vi.stubGlobal('fetch',vi.fn((url:string)=>url.includes('/api/recherche/') ? response({query:'dosage Doliprane',intention:'dosage',medicament:'Doliprane',reponse:'Le dosage de Doliprane est de 1000 mg.'}) : response([])));
  show('/search?q=dosage%20Doliprane');
  await screen.findByText('Le dosage de Doliprane est de 1000 mg.');
});
