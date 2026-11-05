// @vitest-environment jsdom
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import Collection from '../src/pages/Collection';
import Detail from '../src/pages/Detail';

const study = {id:'NewTrial',iri:'urn:trial',type_etude:'EssaiClinique',participants:750,phase:2,medicament_id:'Glucophage',resultats:[{id:'NewResult',iri:'urn:result'}]};
const result = {id:'NewResult',iri:'urn:result',type_resultat:'Tolerance',valeur:87,unite:'%',etude_id:'NewTrial'};
const response = (data:unknown,status=200)=>Promise.resolve(new Response(JSON.stringify(data),{status}));
function show(path:string) {
  render(<MemoryRouter initialEntries={[path]}><Routes>
    <Route path="/catalog/:slug" element={<Collection/>}/>
    <Route path="/entity/:id" element={<Detail/>}/>
  </Routes></MemoryRouter>);
}
afterEach(()=>{cleanup();vi.unstubAllGlobals();});

it('loads studies, filters through the API, and links newly created identifiers',async()=>{
  const fetch = vi.fn((url:string)=>response(url.endsWith('/stats') ? [] : url.endsWith('/sans-resultat') ? [] : [study]));
  vi.stubGlobal('fetch',fetch);
  show('/catalog/studies');
  const card = await screen.findByRole('link',{name:/NewTrial/});
  expect(card.getAttribute('href')).toBe('/entity/NewTrial?domain=studies');
  expect(screen.queryByText(/SPARQL|FastAPI|Aymen/)).toBeNull();
  fireEvent.click(screen.getByRole('button',{name:'Without results'}));
  await screen.findByRole('heading',{name:'No records found'});
  expect(fetch.mock.calls.some(([url])=>url.endsWith('/etudes/sans-resultat'))).toBe(true);
  expect(screen.queryByRole('link',{name:/Paracetamol/})).toBeNull();
});

it('navigates a live study to its result and back using asserted relationships',async()=>{
  vi.stubGlobal('fetch',vi.fn((url:string)=>response(url.includes('/etudes/') ? study : result)));
  show('/entity/NewTrial?domain=studies');
  await screen.findByRole('heading',{name:'NewTrial.'});
  expect(screen.getByText('750')).toBeTruthy();
  fireEvent.click(screen.getByRole('link',{name:'NewResult'}));
  await screen.findByRole('heading',{name:'NewResult.'});
  expect(screen.getByText('87')).toBeTruthy();
  expect(screen.getByRole('link',{name:'NewTrial'}).getAttribute('href')).toBe('/entity/NewTrial?domain=studies');
  expect(screen.queryByText('Sample record')).toBeNull();
});

it('never replaces a missing study with a sample record',async()=>{
  vi.stubGlobal('fetch',vi.fn(()=>response({},404)));
  show('/entity/Essai_Metformine_2024?domain=studies');
  await screen.findByText('Record not found.');
  expect(screen.queryByRole('heading',{name:/Metformin trial/})).toBeNull();
});

it('filters results through the safety hierarchy endpoint',async()=>{
  const fetch = vi.fn((url:string)=>response(url.endsWith('/stats') ? [] : [result]));
  vi.stubGlobal('fetch',fetch);
  show('/catalog/results');
  await screen.findByRole('link',{name:/NewResult/});
  fireEvent.click(screen.getByRole('button',{name:'Safety (including tolerance)'}));
  await screen.findByRole('link',{name:/NewResult/});
  expect(fetch.mock.calls.some(([url])=>url.endsWith('/resultats/type/securite'))).toBe(true);
});
