// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { act, cleanup, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import Collection from '../src/pages/Collection';
import Detail from '../src/pages/Detail';
import SearchPage from '../src/pages/Search';
import ClinicalGraph from '../src/components/ClinicalGraph';
import { useClinicalEntity } from '../src/hooks/useClinicalRecords';
import type { Entity } from '../src/data/ontology';

const patient: Entity = {id:'Patient_Karim', name:'Patient Karim live', domain:'patients', type:'Patient', description:'From the API', properties:{age:'45', ageCategory:'Adulte'}, relations:[]};
const condition: Entity = {id:'LiveCondition', name:'Live condition', domain:'conditions', type:'Allergie', description:'From the API', properties:{category:'EtatPathologique'}, relations:[], incomingRelations:[{predicate:'aPourCondition',source:'Patient_New',sourceDomain:'patients'}]};
const response = (body: unknown, status = 200) => Promise.resolve(new Response(JSON.stringify(body), {status, headers:{'Content-Type':'application/json'}}));
function show(path: string) {
  return render(<MemoryRouter initialEntries={[path]}><Routes>
    <Route path="/catalog/:slug" element={<Collection/>}/>
    <Route path="/entity/:id" element={<Detail/>}/>
    <Route path="/search" element={<SearchPage/>}/>
    <Route path="/graph" element={<ClinicalGraph/>}/>
  </Routes></MemoryRouter>);
}
afterEach(()=>{cleanup();vi.unstubAllGlobals();});

describe('clinical record sources and states', ()=>{
  it('does not display preview records while loading or for a successful empty dataset', async()=>{
    let resolve!: (value: Response) => void;
    vi.stubGlobal('fetch',vi.fn(()=>new Promise<Response>(done=>{resolve=done;})));
    show('/catalog/patients');
    expect(screen.queryByText('Patient Karim')).toBeNull();
    expect(screen.getByRole('heading',{name:'Loading records…'})).toBeTruthy();
    resolve(new Response('[]'));
    await screen.findByRole('heading',{name:'No records found'});
    expect(screen.getByRole('heading',{name:'No records found'})).toBeTruthy();
    expect(screen.queryByText('Patient Karim')).toBeNull();
  });

  it('filters live patients by computed age category', async()=>{
    vi.stubGlobal('fetch',vi.fn(()=>response([patient,{...patient,id:'Patient_Child',name:'Child profile',properties:{age:'8',ageCategory:'Enfant'}}])));
    show('/catalog/patients');
    await screen.findByText('Patient Karim live');
    expect(screen.queryByText(/Fuseki|FastAPI|LIVE ONTOLOGY/)).toBeNull();
    fireEvent.change(screen.getByRole('combobox',{name:'Age category'}),{target:{value:'Enfant'}});
    expect(screen.queryByText('Patient Karim live')).toBeNull();
    expect(screen.getByText('Child profile')).toBeTruthy();
  });

  it('never replaces a live 404 with a matching preview profile', async()=>{
    vi.stubGlobal('fetch',vi.fn(()=>response({detail:'Patient not found'},404)));
    show('/entity/Patient_Karim?domain=patients');
    await screen.findByText('Record not found.');
    expect(screen.queryByRole('heading',{name:'Patient Karim.'})).toBeNull();
    expect(screen.queryByText('Illustrative patient profile')).toBeNull();
  });

  it('labels unavailable preview data and can retry into a live profile', async()=>{
    const fetch = vi.fn().mockImplementationOnce(()=>response({},503)).mockImplementation(()=>response(patient));
    vi.stubGlobal('fetch',fetch);
    show('/entity/Patient_Karim?domain=patients');
    await screen.findAllByText('Showing sample records. Current records are unavailable.');
    fireEvent.click(screen.getByRole('button',{name:'Try again'}));
    await screen.findByRole('heading',{name:'Patient Karim live.'});
    expect(screen.queryByText('Illustrative patient profile')).toBeNull();
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it('shows API errors without substituting a preview profile', async()=>{
    vi.stubGlobal('fetch',vi.fn(()=>response({},500)));
    show('/entity/Patient_Karim?domain=patients');
    await screen.findByText('Unable to load records. Please try again.');
    expect(screen.queryByRole('heading',{name:'Patient Karim.'})).toBeNull();
  });

  it('uses live incoming condition links and routes patients absent from preview data', async()=>{
    vi.stubGlobal('fetch',vi.fn(()=>response(condition)));
    show('/entity/LiveCondition?domain=conditions');
    await screen.findByRole('heading',{name:'Live condition.'});
    expect(screen.getByRole('link',{name:'Patient New'}).getAttribute('href')).toBe('/entity/Patient_New?domain=patients');
    expect(screen.getByLabelText('Condition hierarchy').textContent).toContain('EtatPathologique');
  });

  it('does not show static incoming relationships as live ontology assertions', async()=>{
    vi.stubGlobal('fetch',vi.fn(()=>response({...condition,id:'Grossesse_T3',incomingRelations:[]})));
    show('/entity/Grossesse_T3?domain=conditions');
    await screen.findByRole('heading',{name:'Live condition.'});
    expect(screen.queryByRole('link',{name:/CI Ibuprofene Grossesse/})).toBeNull();
  });

  it('includes explicit incoming links in condition card connection counts', async()=>{
    vi.stubGlobal('fetch',vi.fn(()=>response([condition])));
    show('/catalog/conditions');
    await screen.findByText('Live condition');
    expect(screen.getByText('1 connection')).toBeTruthy();
  });

  it('labels preview search results when a clinical service is unavailable', async()=>{
    vi.stubGlobal('fetch',vi.fn((url: string)=>url.endsWith('/api/patients') ? response([patient]) : response({},503)));
    show('/search');
    await screen.findByText('Patient Karim live');
    await screen.findAllByText('Showing sample records. Current records are unavailable.');
    expect(screen.queryByText('LIVE ONTOLOGY')).toBeNull();
    expect(screen.getAllByText('Sample record').length).toBeGreaterThan(0);
  });

  it('draws only API graph edges and never substitutes preview edges', async()=>{
    vi.stubGlobal('fetch',vi.fn(()=>response([condition])));
    show('/graph?domain=conditions&id=LiveCondition');
    await screen.findByRole('img',{name:'Relationships for Live condition'});
    expect(screen.getByRole('link',{name:'Patient_New'}).getAttribute('href')).toBe('/entity/Patient_New?domain=patients');
    expect(screen.queryByText('concerneCondition')).toBeNull();
  });

  it('ignores a stale response after navigating to a different record', async()=>{
    let resolveOld!: (response: Response) => void;
    vi.stubGlobal('fetch',vi.fn((url: string)=>url.includes('Patient_Old') ? new Promise<Response>(resolve=>{resolveOld=resolve;}) : response({...patient,id:'Patient_New'})));
    function Probe({id}: {id:string}) {
      const result = useClinicalEntity('patients',id);
      return <span>{result.data?.id ?? result.status}</span>;
    }
    const view = render(<Probe id="Patient_Old"/>);
    view.rerender(<Probe id="Patient_New"/>);
    await screen.findByText('Patient_New');
    await act(async()=>{
      resolveOld(new Response(JSON.stringify({...patient,id:'Patient_Old'})));
    });
    expect(screen.getByText('Patient_New')).toBeTruthy();
    expect(screen.queryByText('Patient_Old')).toBeNull();
  });
});
