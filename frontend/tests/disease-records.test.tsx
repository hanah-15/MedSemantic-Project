// @vitest-environment jsdom
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import Collection from '../src/pages/Collection';
import Detail from '../src/pages/Detail';
import Search from '../src/pages/Search';

const ns = 'http://www.semanticweb.org/medsemantic#';
const symptom = {uri:ns+'NewSymptom',label:'New symptom',description:null,properties:[]};
const disease = {uri:ns+'NewDisease',label:'New disease',description:'Recorded disease',properties:[
  {predicate:ns+'codeCIM10',value:'X01',value_type:'literal'},
  {predicate:ns+'presenteSymptome',value:symptom.uri,value_type:'uri'},
]};
const response = (data:unknown,status=200)=>Promise.resolve(new Response(JSON.stringify(data),{status}));
function show(path:string) {
  render(<MemoryRouter initialEntries={[path]}><Routes>
    <Route path="/catalog/:slug" element={<Collection/>}/>
    <Route path="/entity/:id" element={<Detail/>}/>
    <Route path="/search" element={<Search/>}/>
  </Routes></MemoryRouter>);
}
afterEach(()=>{cleanup();vi.unstubAllGlobals();});

it('loads disease records and searches their recorded properties',async()=>{
  vi.stubGlobal('fetch',vi.fn(()=>response([disease])));
  show('/catalog/diseases');
  const card = await screen.findByRole('link',{name:/New disease/});
  expect(card.getAttribute('href')).toBe('/entity/NewDisease?domain=diseases');
  fireEvent.change(screen.getByRole('textbox',{name:'Filter Diseases'}),{target:{value:'X01'}});
  expect(screen.getByRole('link',{name:/New disease/})).toBeTruthy();
  fireEvent.change(screen.getByRole('textbox',{name:'Filter Diseases'}),{target:{value:'absent'}});
  expect(screen.getByRole('heading',{name:'No records found'})).toBeTruthy();
  expect(screen.queryByRole('link',{name:/Grippe/})).toBeNull();
});

it('navigates newly added diseases and symptoms with real incoming relationships',async()=>{
  vi.stubGlobal('fetch',vi.fn((url:string)=>response(url.includes('?symptom=') ? [disease] : url.includes('/symptoms/') ? symptom : disease)));
  show('/entity/NewDisease?domain=diseases');
  await screen.findByRole('heading',{name:'New disease.'});
  expect(screen.getByText('X01')).toBeTruthy();
  fireEvent.click(screen.getByRole('link',{name:'NewSymptom'}));
  await screen.findByRole('heading',{name:'New symptom.'});
  const incoming = await screen.findByRole('link',{name:'NewDisease'});
  expect(incoming.getAttribute('href')).toBe('/entity/NewDisease?domain=diseases');
  expect(screen.queryByText('Sample profile')).toBeNull();
});

it('shows empty collections and missing records without sample substitutions',async()=>{
  vi.stubGlobal('fetch',vi.fn(()=>response([])));
  show('/catalog/symptoms');
  await screen.findByRole('heading',{name:'No records found'});
  expect(screen.queryByText('Fever')).toBeNull();
  cleanup();
  vi.stubGlobal('fetch',vi.fn(()=>response({},404)));
  show('/entity/Grippe?domain=diseases');
  await screen.findByText('Record not found.');
  expect(screen.queryByRole('heading',{name:/Influenza/})).toBeNull();
});

it('can retry an unavailable collection',async()=>{
  vi.stubGlobal('fetch',vi.fn().mockImplementationOnce(()=>response({},503)).mockImplementation(()=>response([disease])));
  show('/catalog/diseases');
  await screen.findByRole('alert');
  fireEvent.click(screen.getByRole('button',{name:/Try again/}));
  await screen.findByRole('link',{name:/New disease/});
});

it('includes live diseases in shared search alongside the existing modules',async()=>{
  vi.stubGlobal('fetch',vi.fn((url:string)=>response(url.endsWith('/api/diseases') ? [disease] : [])));
  show('/search');
  await screen.findByRole('link',{name:/New disease/});
  fireEvent.click(screen.getByRole('button',{name:'Diseases'}));
  expect(screen.getByRole('link',{name:/New disease/})).toBeTruthy();
  expect(screen.queryByText('Sample record')).toBeNull();
});
