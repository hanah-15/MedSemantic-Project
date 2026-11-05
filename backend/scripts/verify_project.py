"""Read-only verification of every module, ontology structure and local NLP."""
import argparse
from pathlib import Path
from urllib.parse import quote

import requests
from rdflib import Graph, Namespace
from rdflib.compare import isomorphic
from rdflib.namespace import RDF, OWL

from verify_live import normalize_strings

NS = Namespace('http://www.semanticweb.org/medsemantic#')
MODULES = [
    ('Medicament','/api/medicaments/','/api/medicaments/details/','uri'),
    ('Molecule','/api/molecules','/api/molecules/','id'),
    ('Maladie','/api/diseases','/api/diseases/','uri'),
    ('Symptome','/api/symptoms','/api/symptoms/','uri'),
    ('EffetSecondaire','/api/effets-secondaires','/api/effets-secondaires/','id'),
    ('ContreIndication','/api/contre-indications','/api/contre-indications/','id'),
    ('Patient','/api/patients','/api/patients/','id'),
    ('ConditionMedicale','/api/conditions','/api/conditions/','id'),
    ('EtudeClinique','/etudes/','/etudes/','id'),
    ('ResultatClinique','/resultats/','/resultats/','id'),
]


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--api',default='http://127.0.0.1:8000')
    parser.add_argument('--fuseki',default='http://localhost:3030/medsemantic')
    parser.add_argument('--ontology',type=Path,default=Path(__file__).resolve().parents[2]/'ontology'/'MedSemantic.owl')
    args=parser.parse_args()
    graph=Graph().parse(args.ontology)
    live=requests.get(args.fuseki.rstrip('/')+'/get',timeout=15)
    live.raise_for_status()
    live_graph=Graph().parse(data=live.content,format=live.headers['Content-Type'].split(';')[0])
    assert isomorphic(normalize_strings(graph),normalize_strings(live_graph)), 'Fuseki differs from the supplied ontology'
    counts={str(kind).split('#')[-1]:len(set(graph.subjects(RDF.type,kind))) for kind in [OWL.Class,OWL.ObjectProperty,OWL.DatatypeProperty,OWL.NamedIndividual,OWL.Restriction]}
    assert counts['ObjectProperty'] and counts['DatatypeProperty'] and counts['NamedIndividual']
    assert list(graph.triples((None,OWL.equivalentClass,None)))
    assert list(graph.triples((None,OWL.inverseOf,None)))
    assert list(graph.subjects(RDF.type,OWL.AllDisjointClasses))
    print('PASS ontology:',len(graph),'triples;',counts)

    def get(path,params=None):
        response=requests.get(args.api.rstrip('/')+path,params=params,timeout=20)
        response.raise_for_status()
        return response.json()

    for root,path,detail,key in MODULES:
        expected={str(row[0]).split('#')[-1] for row in graph.query(f'SELECT DISTINCT ?entity WHERE {{ ?entity a/<http://www.w3.org/2000/01/rdf-schema#subClassOf>* <{NS[root]}> }}')}
        records=get(path)
        actual={item[key].split('#')[-1] for item in records}
        assert actual==expected,(root,actual,expected)
        for identifier in sorted(actual):
            record=get(detail+quote(identifier,safe=''))
            assert record[key].split('#')[-1]==identifier
        print('PASS',root,':',len(actual),'records and all details')

    checks=[
        ('/api/effets-secondaires',{'type_effet':'digestif','frequence':'rare'},set()),
        ('/api/effets-secondaires',{'medicament':'Glucophage'},{'TroublesGastriques'}),
        ('/api/contre-indications',{'type_ci':'relative','medicament':'Advil'},set()),
        ('/api/contre-indications',{'medicament':'Advil'},{'CI_Ibuprofene_Grossesse'}),
        ('/api/diseases',{'symptom':'Toux'},{'Grippe','Asthme'}),
        ('/etudes/sans-resultat',None,{'Etude_Paracetamol_Obs'}),
        ('/resultats/type/securite',None,{'Res_Tolerance_Glucophage'}),
    ]
    for path,params,expected in checks:
        data=get(path,params)
        assert {item.get('id',item.get('uri','')).split('#')[-1] for item in data}==expected,path
    print('PASS combined filters, relationships, OPTIONAL, FILTER NOT EXISTS and subclass paths')
    questions=[
        'Quel est le dosage du Doliprane ?', 'Composition du Doliprane',
        'Quels patients ont plus de 65 ans ?', 'Quelles conditions sont physiologiques ?',
        'Quels effets secondaires du Glucophage ?', 'Quelles contre-indications pour Advil ?',
    ]
    for question in questions:
        answer=get('/api/recherche/',{'q':question})
        assert 'spaCy' in answer.get('tools',[]),(question,'NLP tools missing')
        assert answer.get('sparql'),(question,answer)
        rows=list(graph.query(answer['sparql']))
        assert rows,(question,'Generated SPARQL has no expected result')
        print('PASS local NLP:',answer['intention'],'-> executable SPARQL')
    print('All project read checks passed. No data was changed.')


if __name__=='__main__':
    main()
