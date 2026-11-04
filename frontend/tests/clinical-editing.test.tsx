// @vitest-environment jsdom
import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import Collection from '../src/pages/Collection';
import SearchPage from '../src/pages/Search';

const patient = {id:'Patient_Test',name:'Patient Test',domain:'patients',type:'Patient',description:'Patient profile',properties:{age:'30',sexe:'F',ageCategory:'Adulte'},relations:[{predicate:'aPourCondition',target:'Condition_Test'}]};
const condition = {id:'Condition_Test',name:'Condition Test',domain:'conditions',type:'Allergie',description:'Condition',properties:{category:'EtatPathologique',severite:'modérée'},relations:[]};
const options = {aPourMaladie:[],aPourCondition:[{id:'Condition_Test',name:'Condition Test'}],ressentSymptome:[],prend:[{id:'Glucophage',name:'Glucophage'}]};
const types = [{id:'Allergie',parent:'EtatPathologique'},{id:'Grossesse',parent:'EtatPhysiologique'}];
const response = (data:unknown,status=200) => Promise.resolve(new Response(status === 204 ? null : JSON.stringify(data),{status}));
function show(path:string) {
  render(<MemoryRouter initialEntries={[path]}><Routes><Route path="/catalog/:slug" element={<Collection/>}/><Route path="/search" element={<SearchPage/>}/></Routes></MemoryRouter>);
}
afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.restoreAllMocks();});

it('creates a patient with explicit selected relationships',async()=>{
  let saved=false;
  const fetch=vi.fn((url:string,init?:RequestInit)=>{
    if (url.endsWith('/options')) return response(options);
    if (init?.method === 'POST') {saved=true;return response(patient,201);}
    return response(saved ? [patient] : []);
  });
  vi.stubGlobal('fetch',fetch);
  show('/catalog/patients');
  await screen.findByRole('heading',{name:'No records found'});
  fireEvent.click(screen.getByRole('button',{name:'Add patient'}));
  const dialog=screen.getByRole('dialog',{name:'Add patient'});
  fireEvent.change(within(dialog).getByLabelText('Record ID'),{target:{value:'Patient_Test'}});
  fireEvent.change(within(dialog).getByLabelText('Age'),{target:{value:'30'}});
  fireEvent.change(within(dialog).getByLabelText('Sex'),{target:{value:'F'}});
  fireEvent.click(await within(dialog).findByRole('checkbox',{name:'Condition Test'}));
  fireEvent.click(within(dialog).getByRole('checkbox',{name:'Glucophage'}));
  fireEvent.click(within(dialog).getByRole('button',{name:'Save record'}));
  await screen.findByRole('heading',{name:'Patient Test'});
  const request=fetch.mock.calls.find(([,init])=>init?.method === 'POST');
  expect(JSON.parse(String(request?.[1]?.body))).toMatchObject({id:'Patient_Test',age:30,sexe:'F',aPourCondition:['Condition_Test'],prend:['Glucophage']});
});

it('edits a patient without dropping existing condition links',async()=>{
  let age='30';
  const fetch=vi.fn((url:string,init?:RequestInit)=>{
    if (url.endsWith('/options')) return response(options);
    if (init?.method === 'PUT') {age='65';return response(patient);}
    return response([{...patient,properties:{...patient.properties,age}}]);
  });
  vi.stubGlobal('fetch',fetch);
  show('/catalog/patients');
  fireEvent.click(await screen.findByRole('button',{name:'Edit Patient Test'}));
  const dialog=screen.getByRole('dialog',{name:'Edit patient'});
  expect((await within(dialog).findByRole('checkbox',{name:'Condition Test'}) as HTMLInputElement).checked).toBe(true);
  fireEvent.change(within(dialog).getByLabelText('Age'),{target:{value:'65'}});
  fireEvent.click(within(dialog).getByRole('button',{name:'Save record'}));
  await screen.findByText('Record saved.');
  const request=fetch.mock.calls.find(([,init])=>init?.method === 'PUT');
  expect(JSON.parse(String(request?.[1]?.body))).toMatchObject({age:65,aPourCondition:['Condition_Test']});
});

it('creates and edits a condition using ontology class choices',async()=>{
  let saved=false;
  const fetch=vi.fn((url:string,init?:RequestInit)=>{
    if (url.endsWith('/types')) return response(types);
    if (init?.method === 'POST' || init?.method === 'PUT') {saved=true;return response(condition,init.method === 'POST' ? 201 : 200);}
    return response(saved ? [condition] : []);
  });
  vi.stubGlobal('fetch',fetch);
  show('/catalog/conditions');
  await screen.findByRole('heading',{name:'No records found'});
  fireEvent.click(screen.getByRole('button',{name:'Add condition'}));
  let dialog=screen.getByRole('dialog',{name:'Add medical condition'});
  await within(dialog).findByRole('option',{name:'Allergie'});
  fireEvent.change(within(dialog).getByLabelText('Record ID'),{target:{value:'Condition_Test'}});
  fireEvent.change(within(dialog).getByLabelText('Condition type'),{target:{value:'Allergie'}});
  fireEvent.change(within(dialog).getByLabelText('Severity'),{target:{value:'modérée'}});
  fireEvent.click(within(dialog).getByRole('button',{name:'Save record'}));
  fireEvent.click(await screen.findByRole('button',{name:'Edit Condition Test'}));
  dialog=screen.getByRole('dialog',{name:'Edit medical condition'});
  await within(dialog).findByRole('option',{name:'Grossesse'});
  fireEvent.change(within(dialog).getByLabelText('Condition type'),{target:{value:'Grossesse'}});
  fireEvent.change(within(dialog).getByLabelText('Severity'),{target:{value:''}});
  fireEvent.click(within(dialog).getByRole('button',{name:'Save record'}));
  await waitFor(()=>expect(fetch.mock.calls.some(([,init])=>init?.method === 'PUT')).toBe(true));
  const request=fetch.mock.calls.find(([,init])=>init?.method === 'PUT');
  expect(JSON.parse(String(request?.[1]?.body))).toEqual({type:'Grossesse',severite:null});
});

it.each(['patients','conditions'])('deletes a %s record only after confirmation',async(domain)=>{
  let deleted=false;
  const record=domain === 'patients' ? patient : condition;
  const fetch=vi.fn((url:string,init?:RequestInit)=>{
    if (init?.method === 'DELETE') {deleted=true;return response(null,204);}
    return response(deleted ? [] : [record]);
  });
  vi.stubGlobal('fetch',fetch);
  const confirm=vi.spyOn(window,'confirm').mockReturnValueOnce(false).mockReturnValueOnce(true);
  show('/catalog/'+domain);
  const button=await screen.findByRole('button',{name:'Delete '+record.name});
  fireEvent.click(button);
  expect(fetch.mock.calls.some(([,init])=>init?.method === 'DELETE')).toBe(false);
  fireEvent.click(button);
  await screen.findByRole('heading',{name:'No records found'});
  expect(confirm).toHaveBeenCalledTimes(2);
});

it('keeps the editor open and shows server validation errors',async()=>{
  vi.stubGlobal('fetch',vi.fn((url:string,init?:RequestInit)=>url.endsWith('/types') ? response(types) : init?.method === 'POST' ? response({detail:'This identifier is already in use.'},409) : response([])));
  show('/catalog/conditions');
  await screen.findByRole('heading',{name:'No records found'});
  fireEvent.click(screen.getByRole('button',{name:'Add condition'}));
  const dialog=screen.getByRole('dialog');
  await within(dialog).findByRole('option',{name:'Allergie'});
  fireEvent.change(within(dialog).getByLabelText('Record ID'),{target:{value:'Condition_Test'}});
  fireEvent.change(within(dialog).getByLabelText('Condition type'),{target:{value:'Allergie'}});
  fireEvent.click(within(dialog).getByRole('button',{name:'Save record'}));
  expect(await within(dialog).findByRole('alert')).toHaveProperty('textContent','This identifier is already in use.');
  expect(screen.getByRole('dialog')).toBeTruthy();
});

it('sends age and category filters to the API',async()=>{
  const fetch=vi.fn(()=>response([patient]));
  vi.stubGlobal('fetch',fetch);
  show('/catalog/patients');
  await screen.findByRole('heading',{name:'Patient Test'});
  fireEvent.change(screen.getByLabelText('Minimum age'),{target:{value:'65'}});
  await waitFor(()=>expect(fetch.mock.calls.some(([url])=>String(url).includes('min_age=65'))).toBe(true));
  fireEvent.change(screen.getByLabelText('Age category'),{target:{value:'PersonneAgee'}});
  await waitFor(()=>expect(fetch.mock.calls.some(([url])=>String(url).includes('age_category=PersonneAgee'))).toBe(true));
});

it('shows clinical NLP records as navigable results',async()=>{
  vi.stubGlobal('fetch',vi.fn((url:string)=>response(url.includes('/api/recherche/') ? {query:'patients adultes',intention:'patients_filter',medicament:null,reponse:'1 patient trouvé.',records:[patient]} : [])));
  show('/search?q=patients%20adultes');
  await screen.findByText('1 patient trouvé.');
  expect(screen.getByRole('link',{name:/Patient Test/}).getAttribute('href')).toBe('/entity/Patient_Test?domain=patients');
});
