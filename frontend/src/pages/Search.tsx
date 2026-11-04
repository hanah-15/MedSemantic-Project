import { useMemo, useState, useEffect, useRef } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  ArrowRight, Filter, Search, SearchX, SlidersHorizontal,
  Sparkles, Bot, RefreshCw, FlaskConical, Layers3
} from 'lucide-react';
import { domains, entities } from '../data/ontology';
import EntityCard from '../components/EntityCard';
import { medicamentApi, type NlpSearchResponse } from '../lib/medicamentApi';
import { useClinicalCollection } from '../hooks/useClinicalRecords';
import ClinicalSource from '../components/ClinicalSource';
import { useMedicationCollection } from '../hooks/useMedicationRecord';

const clinicalIntentLabels:Record<string,string> = {
  patients_filter:'Patients', conditions_filter:'Conditions', patient_prend:'Médicaments du patient',
  patient_aPourMaladie:'Maladies du patient', patient_aPourCondition:'Conditions du patient',
  patient_ressentSymptome:'Symptômes du patient', clarification:'Précision nécessaire',
};

export default function SearchPage() {
  const [params, setParams] = useSearchParams();
  const query = params.get('q') ?? '';
  const [filter, setFilter] = useState('all');

  // États pour la recherche NLP
  const [nlpLoading, setNlpLoading] = useState(false);
  const [nlpResult, setNlpResult] = useState<NlpSearchResponse | null>(null);
  const [nlpError,setNlpError] = useState<string|null>(null);
  const nlpRequest = useRef(0);

  const patients = useClinicalCollection('patients');
  const conditions = useClinicalCollection('conditions');
  const medications = useMedicationCollection();
  const livePatients = patients.data;
  const liveConditions = conditions.data;
  const searchable = useMemo(() => [
    ...entities.filter(item => item.domain === 'patients' ? patients.status === 'unavailable' : item.domain === 'conditions' ? conditions.status === 'unavailable' : item.domain !== 'medications'),
    ...(livePatients ?? []),
    ...(liveConditions ?? []),
    ...(medications.data ?? []),
  ], [livePatients, liveConditions, patients.status, conditions.status, medications.data]);
  const matches = useMemo(() => searchable.filter(entity => {
    const text = [entity.id,entity.name,entity.type,entity.description,...Object.values(entity.properties ?? {})].join(' ').toLowerCase();
    return (filter === 'all' || entity.domain === filter) && text.includes(query.trim().toLowerCase());
  }),[filter,query,searchable]);


  // Déclencher la recherche NLP
  const runNlpQuery = async (text: string) => {
    if (!text.trim()) return;
    const request = ++nlpRequest.current;
    setNlpLoading(true);
    setNlpResult(null);
    setNlpError(null);
    try {
      const res = await medicamentApi.askNlp(text);
      if (request === nlpRequest.current) setNlpResult(res);
    } catch (err) {
      console.warn("Service NLP non disponible:", err);
      if (request === nlpRequest.current) setNlpError('La recherche est temporairement indisponible. Réessayez.');
    } finally {
      if (request === nlpRequest.current) setNlpLoading(false);
    }
  };

  // Déclencher automatiquement le NLP quand la requête ressemble à une question
  useEffect(() => {
    ++nlpRequest.current;
    setNlpResult(null);
    setNlpError(null);
    setNlpLoading(false);
    const trimmed = query.trim();
    const isQuestion = trimmed.includes('?') ||
      /^(quel|quelle|quels|quelles|comment|combien|composition|dosage|forme|quoi|patients?|conditions?|enfants?|adultes?)/i.test(trimmed) ||
      trimmed.split(' ').length >= 3;

    if (isQuestion) {
      const timer = setTimeout(() => runNlpQuery(trimmed), 400);
      return () => { clearTimeout(timer); ++nlpRequest.current; };
    } else {
      setNlpResult(null);
    }
  }, [query]);

  return (
    <div className="page-flow inner-page">
      <div className="page-topline">
        <span className="eyebrow"><span className="eyebrow-indicator" /> DISCOVERY & NLP ENGINE</span>
        <span className="topline-right">EXPLORE / SEARCH</span>
      </div>

      <div className="inner-page-title">
        <div>
          <span className="eyebrow">RECHERCHE SÉMANTIQUE & INTELLIGENCE ARTIFICIELLE</span>
          <h1>Explore the <em>knowledge.</em></h1>
          <p>Posez une question en langage naturel (ex: <em>"Quel est le dosage du Doliprane ?"</em>) ou recherchez des entités médicales.</p>
        </div>
        <div className="page-title-icon"><Search size={55} strokeWidth={1.3} /></div>
      </div>

      <section className="search-studio">
        <label className="studio-search">
          <Search size={24} />
          <input
            autoFocus
            value={query}
            placeholder="Posez une question ou cherchez (ex: 'Composition de l'Advil', 'dosage Doliprane')..."
            aria-label="Search knowledge"
            onChange={e => setParams(e.target.value ? { q: e.target.value } : {}, { replace: true })}
            onKeyDown={e => {
              if (e.key === 'Enter') {
                e.preventDefault();
                runNlpQuery(query);
              }
            }}
          />
          <button
            type="button"
            onClick={() => runNlpQuery(query)}
            style={{
              background: '#078b89',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              padding: '6px 14px',
              fontWeight: 700,
              fontSize: '13px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px'
            }}
          >
            {nlpLoading ? <RefreshCw size={16} className="spin" /> : <Sparkles size={16} />}
            <span>Demander à l'IA</span>
          </button>
        </label>

        {/* Suggestions rapides en langage naturel */}
        <div style={{ marginTop: '12px', display: 'flex', gap: '8px', alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Essayer :</span>
          {[
            "Quel est le dosage du Doliprane ?",
            "Quelle est la composition de l'Advil ?",
            "Forme galénique du Glucophage",
            "Quels médicaments prend Karim ?",
            "Quels patients ont plus de 65 ans ?",
            "Quelles conditions sont physiologiques ?"
          ].map(suggestion => (
            <button
              key={suggestion}
              type="button"
              onClick={() => {
                setParams({ q: suggestion });
                runNlpQuery(suggestion);
              }}
              style={{
                background: '#f1f5f9',
                border: '1px solid #e2e8f0',
                borderRadius: '6px',
                padding: '4px 10px',
                fontSize: '12px',
                color: '#334155',
                cursor: 'pointer'
              }}
            >
              💬 {suggestion}
            </button>
          ))}
        </div>

        <div className="studio-filters" style={{ marginTop: '16px' }}>
          <span className="filters-label"><SlidersHorizontal size={18} /> Narrow your search</span>
          <div className="filters-wrap">
            <button className={filter === 'all' ? 'filter-chip active' : 'filter-chip'} onClick={() => setFilter('all')}>
              Everything
            </button>
            {domains.map(d => (
              <button
                className={filter === d.slug ? 'filter-chip active' : 'filter-chip'}
                key={d.slug}
                onClick={() => setFilter(d.slug)}
              >
                {d.title}
              </button>
            ))}
          </div>
        </div>
      </section>

      {nlpError && <div className="source-status source-error" role="alert">{nlpError}</div>}
      {/* RÉSULTAT INTELLIGENT DU MODULE NLP */}
      {nlpResult && (
        <section
          style={{
            background: 'linear-gradient(135deg, #f0fdfa 0%, #e6fffa 100%)',
            border: '1px solid #99f6e4',
            borderRadius: '16px',
            padding: '24px',
            margin: '25px 0',
            boxShadow: '0 6px 20px rgba(13, 148, 136, 0.08)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <span style={{ background: '#0d9488', color: 'white', borderRadius: '8px', padding: '6px', display: 'flex' }}>
                <Bot size={20} />
              </span>
              <strong style={{ color: '#115e59', fontSize: '16px' }}>Réponse intelligente MedSemantic (NLP & SPARQL)</strong>
            </div>

            {nlpResult.intention && nlpResult.intention !== 'inconnu' && (
              <span
                style={{
                  fontSize: '11px',
                  background: '#ccfbf1',
                  color: '#0f766e',
                  padding: '4px 10px',
                  borderRadius: '6px',
                  fontWeight: 800,
                  textTransform: 'uppercase'
                }}
              >
                {clinicalIntentLabels[nlpResult.intention] ?? 'Intention : '+nlpResult.intention.replace('_', ' ')}
              </span>
            )}
          </div>

          <p style={{ fontSize: '16px', color: '#134e4a', margin: '12px 0 6px', lineHeight: 1.5, fontWeight: 500 }}>
            {nlpResult.reponse}
          </p>
          {nlpResult.records && nlpResult.records.length > 0 && <div className="entity-grid">{nlpResult.records.map(record=><EntityCard key={record.domain+record.id} item={record}/>)}</div>}

          {/* Molécules structurées extraites */}
          {nlpResult.data && nlpResult.data.length > 0 && (
            <div style={{ marginTop: '14px', display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              {nlpResult.data.map((m, idx) => (
                <div
                  key={idx}
                  style={{
                    background: 'white',
                    padding: '8px 14px',
                    borderRadius: '8px',
                    border: '1px solid #99f6e4',
                    fontSize: '13px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px'
                  }}
                >
                  <FlaskConical size={15} color="#0d9488" />
                  <strong style={{ color: '#0f766e' }}>{m.nom}</strong>
                  <span style={{ color: '#64748b', fontSize: '11px' }}>({m.type})</span>
                  {m.formule && <code style={{ fontSize: '11px', background: '#f1f5f9', padding: '2px 4px', borderRadius: '4px' }}>{m.formule}</code>}
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* RÉSULTATS CLASSIQUES PAR CARTES */}
      {((!nlpResult && !nlpLoading) || matches.length > 0) && <>
      <div className="section-intro result-intro">
        <div>
          <span className="eyebrow">KNOWLEDGE LIBRARY</span>
          <h2>{matches.length} {matches.length === 1 ? 'result' : 'results'} found<span className="heading-dot">.</span></h2>
          <p>{query ? `Showing concepts related to “${query}”` : 'Browse the concepts that make up the medical atlas.'}</p>
        </div>
        <span className="result-sort"><Filter size={17} /> All results</span>
      </div>

      {(patients.status !== 'connected' || conditions.status !== 'connected' || medications.status !== 'connected') && <div className="search-sources">{patients.status !== 'connected' && <><span>Patients</span><ClinicalSource status={patients.status} retry={patients.retry} preview/></>}{conditions.status !== 'connected' && <><span>Medical conditions</span><ClinicalSource status={conditions.status} retry={conditions.retry} preview/></>}{medications.status !== 'connected' && <><span>Medications</span><ClinicalSource status={medications.status} retry={medications.retry}/></>}</div>}
      {matches.length ? (
        <div className="entity-grid">
          {matches.map(entity => (
            <div className="search-result" key={entity.id}>{!(entity.domain === 'patients' && patients.status === 'connected' || entity.domain === 'conditions' && conditions.status === 'connected' || entity.domain === 'medications' && medications.status === 'connected') && <span className="record-source">Sample record</span>}<EntityCard item={entity}/></div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <span><SearchX size={38} /></span>
          <h3>No matching concepts</h3>
          <p>Try a broader term or remove a filter to explore more of the knowledge base.</p>
          <button className="button-primary" onClick={() => { setParams({}); setFilter('all'); }}>
            Clear search <ArrowRight size={17} />
          </button>
        </div>
      )}
      </>}
    </div>
  );
}
