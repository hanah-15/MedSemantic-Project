// @vitest-environment jsdom
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import Collection from '../src/pages/Collection';
import Detail from '../src/pages/Detail';
import ClinicalGraph from '../src/components/ClinicalGraph';

const effect = {id:'NewEffect',iri:'urn:effect',type_effet:'EffetDigestif',gravite:'moderate',frequence:'rare',symptome_id:'NewSymptom',medicaments_lies:['Glucophage']};
const molecule = {id:'NewMolecule',name:'New molecule',domain:'molecules',type:'PrincipeActif',description:'Recorded molecule',properties:{formuleChimique:'C2H6'},relations:[{predicate:'seMetaboliseEn',target:'NewMetabolite'}]};
const response = (data:unknown,status=200)=>Promise.resolve(new Response(JSON.stringify(data),{status}));
function show(path:string) {
  render(<MemoryRouter initialEntries={[path]}><Routes>
    <Route path="/catalog/:slug" element={<Collection/>}/>
    <Route path="/entity/:id" element={<Detail/>}/>
    <Route path="/graph" element={<ClinicalGraph/>}/>
  </Routes></MemoryRouter>);
}
afterEach(()=>{cleanup();vi.unstubAllGlobals();});

it('combines select filters and keeps all choices after filtering to an empty result',async()=>{
  const fetch = vi.fn((url:string)=>response(url.includes('frequence=rare') ? [] : [effect]));
  vi.stubGlobal('fetch',fetch);
  show('/catalog/side-effects');
  await screen.findByRole('link',{name:/NewEffect/});
  fireEvent.change(screen.getByRole('combobox',{name:'Type'}),{target:{value:'EffetDigestif'}});
  fireEvent.change(screen.getByRole('combobox',{name:'Frequency'}),{target:{value:'rare'}});
  await screen.findByRole('heading',{name:'No records found'});
  expect(fetch.mock.calls.some(([url])=>url.includes('type_effet=EffetDigestif') && url.includes('frequence=rare'))).toBe(true);
  expect(screen.getByRole('option',{name:'moderate'})).toBeTruthy();
  fireEvent.click(screen.getByRole('button',{name:'Clear filters'}));
  await screen.findByRole('link',{name:/NewEffect/});
});

it('loads effect details and links symptoms and incoming medications',async()=>{
  vi.stubGlobal('fetch',vi.fn(()=>response({...effect,symptomes:[{id:'NewSymptom',iri:'urn:symptom'}],medicaments:[{id:'Glucophage',iri:'urn:med'}]})));
  show('/entity/NewEffect?domain=side-effects');
  await screen.findByRole('heading',{name:'NewEffect.'});
  expect(screen.getByRole('link',{name:'NewSymptom'}).getAttribute('href')).toBe('/entity/NewSymptom?domain=symptoms');
  expect(screen.getByRole('link',{name:'Glucophage'}).getAttribute('href')).toBe('/entity/Glucophage?domain=medications');
  expect(screen.queryByText('Sample record')).toBeNull();
});

it('loads molecule profiles with metabolism links from the backend',async()=>{
  vi.stubGlobal('fetch',vi.fn(()=>response(molecule)));
  show('/entity/NewMolecule?domain=molecules');
  await screen.findByRole('heading',{name:'New molecule.'});
  expect(screen.getByText('C2H6')).toBeTruthy();
  expect(screen.getByRole('link',{name:'NewMetabolite'}).getAttribute('href')).toBe('/entity/NewMetabolite?domain=molecules');
});

it('graphs real side effects rather than defaulting to patients',async()=>{
  vi.stubGlobal('fetch',vi.fn(()=>response([effect])));
  show('/graph?domain=side-effects&id=NewEffect');
  await screen.findByRole('img',{name:'Relationships for NewEffect'});
  expect((screen.getByRole('combobox',{name:'Graph collection'}) as HTMLSelectElement).value).toBe('side-effects');
  expect(screen.getByRole('link',{name:'NewSymptom'})).toBeTruthy();
});

it('keeps missing contraindications missing instead of showing samples',async()=>{
  vi.stubGlobal('fetch',vi.fn(()=>response({},404)));
  show('/entity/CI_Ibuprofene_Grossesse?domain=contraindications');
  await screen.findByText('Record not found.');
  expect(screen.queryByText('Sample record')).toBeNull();
});
