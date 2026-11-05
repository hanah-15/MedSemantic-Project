"""Compose the optional filters without silently dropping any selection."""
from rdflib import Literal

from sparql_queries.queries_effet_secondaire import (
    _valider_id, requete_lister_effets_secondaires, requete_effets_par_type,
)
from sparql_queries.queries_contre_indication import (
    requete_lister_contre_indications, requete_contre_indications_par_type,
)


def filter_query(query, filters):
    return query.replace('\n}\nORDER BY', '\n'+'\n'.join(filters)+'\n}\nORDER BY')


def select_effects(type_effet=None, gravite=None, frequence=None, medicament=None):
    query = requete_effets_par_type(type_effet) if type_effet else requete_lister_effets_secondaires()
    filters = []
    for variable, value in [('gravite', gravite), ('frequence', frequence)]:
        if value:
            filters.append(f'FILTER(LCASE(STR(?{variable})) = LCASE({Literal(value.strip()).n3()}))')
    if medicament:
        _valider_id(medicament, 'medicament')
        filters.append(f'FILTER(?medicament = :{medicament})')
    return filter_query(query, filters)


def select_contraindications(type_ci=None, medicament=None, condition=None):
    query = requete_contre_indications_par_type(type_ci) if type_ci else requete_lister_contre_indications()
    filters = []
    for variable, value in [('medicament', medicament), ('condition', condition)]:
        if value:
            _valider_id(value, variable)
            filters.append(f'FILTER(?{variable} = :{value})')
    return filter_query(query, filters)
