"""Verify clinical CRUD/NLP through real Fuseki in a disposable memory dataset.

Requires a running local Fuseki with dataset-management access. The team's
medsemantic dataset is only read. The temporary dataset is removed in finally.
"""

import argparse
import os
from pathlib import Path
import sys
from uuid import uuid4

import requests
from rdflib import Graph
from rdflib.compare import isomorphic

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from verify_live import normalize_strings  # noqa: E402


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fuseki',default='http://localhost:3030')
    parser.add_argument('--ontology',type=Path,default=Path(__file__).resolve().parents[2]/'ontology'/'MedSemantic.owl')
    args=parser.parse_args()
    server=args.fuseki.rstrip('/')
    name='sofiene_check_'+uuid4().hex[:12]
    endpoint=server+'/'+name
    official=Graph().parse(args.ontology)
    response=requests.get(server+'/medsemantic/get',timeout=15)
    response.raise_for_status()
    original=Graph().parse(data=response.content,format=response.headers['Content-Type'].split(';')[0])
    datasets=requests.get(server+'/$/datasets',timeout=15)
    datasets.raise_for_status()
    if any(item['ds.name']=='/'+name for item in datasets.json()['datasets']):
        raise RuntimeError('Temporary dataset name already exists; nothing was changed')
    created=requests.post(server+'/$/datasets',data={'dbName':name,'dbType':'mem'},timeout=20)
    created.raise_for_status()
    try:
        uploaded=requests.put(endpoint+'/data',params={'default':''},data=args.ontology.read_bytes(),
                              headers={'Content-Type':'application/rdf+xml'},timeout=20)
        uploaded.raise_for_status()
        os.environ['FUSEKI_URL']=endpoint
        os.environ['FUSEKI_QUERY_URL']=endpoint+'/query'
        os.environ['FUSEKI_UPDATE_URL']=endpoint+'/update'
        from fastapi.testclient import TestClient
        from main import app
        with TestClient(app) as client:
            def check(method,path,status,body=None,params=None):
                response=client.request(method,path,json=body,params=params)
                if response.status_code != status:
                    raise RuntimeError(f'{method} {path}: expected {status}, got {response.status_code}: {response.text}')
                return response.json() if response.content else None
            check('POST','/api/conditions',201,{'id':'Condition_Verification','type':'InsuffisanceRenale','severite':'sévère "test"'})
            patient={'id':'Patient_Verification','age':17,'sexe':'F','prend':['Glucophage'],'aPourCondition':['Condition_Verification']}
            record=check('POST','/api/patients',201,patient)
            assert record['properties']['ageCategory']=='Enfant'
            assert check('GET','/api/patients/Patient_Verification/conditions',200)==['Condition_Verification']
            record=check('PUT','/api/patients/Patient_Verification',200,{**{key:value for key,value in patient.items() if key!='id'},'age':65})
            assert record['properties']['ageCategory']=='PersonneAgee'
            condition=check('PUT','/api/conditions/Condition_Verification',200,{'type':'Allaitement','severite':None})
            assert condition['properties']['category']=='EtatPhysiologique'
            assert 'severite' not in condition['properties']
            filtered=check('GET','/api/patients',200,params={'min_age':65})
            assert 'Patient_Verification' in [item['id'] for item in filtered]
            filtered=check('GET','/api/conditions',200,params={'category':'EtatPhysiologique'})
            assert 'Condition_Verification' in [item['id'] for item in filtered]
            answer=check('GET','/api/recherche/',200,params={'q':'Quels médicaments prend Verification ?'})
            assert [item['id'] for item in answer['records']]==['Glucophage']
            answer=check('GET','/api/recherche/',200,params={'q':'Quels patients ont au moins 65 ans ?'})
            assert 'Patient_Verification' in [item['id'] for item in answer['records']]
            check('DELETE','/api/conditions/Condition_Verification',204)
            assert check('GET','/api/patients/Patient_Verification/conditions',200)==[]
            check('DELETE','/api/patients/Patient_Verification',204)
            check('GET','/api/patients/Patient_Verification',404)
            check('GET','/api/conditions/Condition_Verification',404)
        result=requests.get(endpoint+'/get',timeout=15)
        result.raise_for_status()
        final=Graph().parse(data=result.content,format=result.headers['Content-Type'].split(';')[0])
        assert isomorphic(normalize_strings(official),normalize_strings(final))
        print('PASS: patient and condition create/read/update/delete, links, filters and clinical NLP against real Fuseki')
    finally:
        deleted=requests.delete(server+'/$/datasets/'+name,timeout=20)
        deleted.raise_for_status()
        print('PASS: temporary verification dataset removed')
    response=requests.get(server+'/medsemantic/get',timeout=15)
    response.raise_for_status()
    after=Graph().parse(data=response.content,format=response.headers['Content-Type'].split(';')[0])
    assert isomorphic(normalize_strings(original),normalize_strings(after)), 'Team dataset changed during verification'
    print(f'PASS: team dataset unchanged ({len(after)} triples)')


if __name__=='__main__':
    main()
