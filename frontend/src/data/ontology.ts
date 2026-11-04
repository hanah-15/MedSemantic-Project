/** Shared educational sample data based on the MedSemantic specification; NOT live Fuseki data or clinical advice. */
export const domains = [
  {slug:'medications',title:'Medications',owl:'Medicament',owner:'Hana',group:'Pharmaceutical',description:'Treatments, drug classes and medical links',icon:'pill'},
  {slug:'molecules',title:'Molecules',owl:'Molecule',owner:'Hana',group:'Pharmaceutical',description:'Active compounds, excipients and metabolites',icon:'atom'},
  {slug:'diseases',title:'Diseases',owl:'Maladie',owner:'Mari',group:'Clinical',description:'Diseases and their relationships',icon:'heart'},
  {slug:'symptoms',title:'Symptoms',owl:'Symptome',owner:'Mari',group:'Clinical',description:'Physical signs and symptoms',icon:'activity'},
  {slug:'side-effects',title:'Side effects',owl:'EffetSecondaire',owner:'Oussema',group:'Safety',description:'Documented adverse effects',icon:'alert'},
  {slug:'contraindications',title:'Contraindications',owl:'ContreIndication',owner:'Oussema',group:'Safety',description:'Documented medication limitations',icon:'shield'},
  {slug:'patients',title:'Patients',owl:'Patient',owner:'Sofiene',group:'Clinical',description:'Patient profiles and related clinical knowledge',icon:'users'},
  {slug:'conditions',title:'Medical conditions',owl:'ConditionMedicale',owner:'Sofiene',group:'Clinical',description:'Physiological and pathological conditions',icon:'stethoscope'},
  {slug:'studies',title:'Clinical studies',owl:'EtudeClinique',owner:'Aymen',group:'Research',description:'Studies and trial information',icon:'flask'},
  {slug:'results',title:'Clinical results',owl:'ResultatClinique',owner:'Aymen',group:'Research',description:'Efficacy, safety and tolerance results',icon:'chart'}
] as const;
export type DomainSlug = typeof domains[number]['slug'];
export type Entity = {id:string; name:string; domain:DomainSlug; type:string; description:string; properties?:Record<string,string>; relations?:{predicate:string;target:string}[]};
export const entities:Entity[] = [
 {id:'Doliprane',name:'Doliprane',domain:'medications',type:'Antalgique',description:'Analgesic linked to paracetamol and fever relief',relations:[{predicate:'contientPrincipeActif',target:'Paracetamol'},{predicate:'soulage',target:'Fievre'},{predicate:'aPourContreIndication',target:'CI_Paracetamol_InsufHepatique'}]},
 {id:'Glucophage',name:'Glucophage',domain:'medications',type:'Antidiabetique',description:'Antidiabetic treatment connected to metformin',relations:[{predicate:'contientPrincipeActif',target:'Metformine'},{predicate:'traite',target:'DiabeteType2'},{predicate:'aPourContreIndication',target:'CI_Metformine_InsufRenale'}]},
 {id:'Advil',name:'Advil',domain:'medications',type:'Antalgique / AntiInflammatoire',description:'Analgesic and anti-inflammatory medication',relations:[{predicate:'contientPrincipeActif',target:'Ibuprofene'},{predicate:'aPourContreIndication',target:'CI_Ibuprofene_Grossesse'}]},
 {id:'Amlor',name:'Amlor',domain:'medications',type:'Antihypertenseur',description:'Treatment associated with hypertension',relations:[{predicate:'contientPrincipeActif',target:'Amlodipine'},{predicate:'traite',target:'Hypertension'}]},
 {id:'Paracetamol',name:'Paracetamol',domain:'molecules',type:'PrincipeActif',description:'Active pharmaceutical ingredient',relations:[{predicate:'seMetaboliseEn',target:'NAPQI'}]},
 {id:'Metformine',name:'Metformine',domain:'molecules',type:'PrincipeActif',description:'Active pharmaceutical ingredient'},
 {id:'Ibuprofene',name:'Ibuprofene',domain:'molecules',type:'PrincipeActif',description:'Active pharmaceutical ingredient'},
 {id:'Amlodipine',name:'Amlodipine',domain:'molecules',type:'PrincipeActif',description:'Active pharmaceutical ingredient'},
 {id:'Lactose',name:'Lactose',domain:'molecules',type:'Excipient',description:'Pharmaceutical excipient'},
 {id:'NAPQI',name:'NAPQI',domain:'molecules',type:'Metabolite',description:'Metabolic transformation product'},
 {id:'Grippe',name:'Grippe',domain:'diseases',type:'MaladieInfectieuse',description:'Infectious disease associated with fever and cough',relations:[{predicate:'presenteSymptome',target:'Fievre'},{predicate:'presenteSymptome',target:'Toux'}]},
 {id:'DiabeteType2',name:'DiabeteType2',domain:'diseases',type:'MaladieMetabolique',description:'Metabolic condition classified as chronic',properties:{estChronique:'true'}},
 {id:'Hypertension',name:'Hypertension',domain:'diseases',type:'MaladieCardiovasculaire',description:'Cardiovascular condition classified as chronic',properties:{estChronique:'true'}},
 {id:'Asthme',name:'Asthme',domain:'diseases',type:'MaladieRespiratoire',description:'Respiratory condition associated with cough',relations:[{predicate:'presenteSymptome',target:'Toux'}]},
 {id:'Fievre',name:'Fievre',domain:'symptoms',type:'SymptomeGeneral',description:'Common general symptom'},
 {id:'Toux',name:'Toux',domain:'symptoms',type:'SymptomeRespiratoire',description:'Respiratory symptom'},
 {id:'Nausee',name:'Nausee',domain:'symptoms',type:'SymptomeDigestif',description:'Gastrointestinal symptom'},
 {id:'TroublesGastriques',name:'TroublesGastriques',domain:'side-effects',type:'EffetDigestif',description:'Gastrointestinal adverse effect',relations:[{predicate:'manifesteSymptome',target:'Nausee'}]},
 {id:'Oedemes',name:'Oedemes',domain:'side-effects',type:'EffetCardiovasculaire',description:'Cardiovascular adverse effect'},
 {id:'EruptionCutanee',name:'EruptionCutanee',domain:'side-effects',type:'EffetAllergique',description:'Allergic adverse effect'},
 {id:'CI_Ibuprofene_Grossesse',name:'Ibuprofen / pregnancy',domain:'contraindications',type:'ContreIndicationAbsolue',description:'Documented contraindication relationship in the ontology',relations:[{predicate:'concerneCondition',target:'Grossesse_T3'}]},
 {id:'CI_Metformine_InsufRenale',name:'Metformin / renal insufficiency',domain:'contraindications',type:'ContreIndicationAbsolue',description:'Documented contraindication relationship in the ontology',relations:[{predicate:'concerneCondition',target:'InsufRenaleSevere'}]},
 {id:'CI_Paracetamol_InsufHepatique',name:'Paracetamol / hepatic insufficiency',domain:'contraindications',type:'ContreIndicationRelative',description:'Documented contraindication relationship in the ontology',relations:[{predicate:'concerneCondition',target:'InsufHepatiqueModeree'}]},
 {id:'Patient_Sarah',name:'Patient Sarah',domain:'patients',type:'Patient',description:'Illustrative patient profile',properties:{age:'8',ageCategory:'Enfant (age-based category)'},relations:[{predicate:'ressentSymptome',target:'Fievre'},{predicate:'prend',target:'Doliprane'}]},
 {id:'Patient_Karim',name:'Patient Karim',domain:'patients',type:'Patient',description:'Illustrative patient profile',properties:{age:'45',ageCategory:'Adulte (age-based category)'},relations:[{predicate:'aPourMaladie',target:'DiabeteType2'},{predicate:'prend',target:'Glucophage'}]},
 {id:'Patient_Fatma',name:'Patient Fatma',domain:'patients',type:'Patient',description:'Illustrative patient profile',properties:{age:'72',ageCategory:'PersonneAgee (age-based category)'},relations:[{predicate:'aPourMaladie',target:'Hypertension'},{predicate:'prend',target:'Amlor'}]},
 {id:'Grossesse_T3',name:'Grossesse T3',domain:'conditions',type:'EtatPhysiologique',description:'Physiological health condition'},
 {id:'InsufRenaleSevere',name:'Severe renal insufficiency',domain:'conditions',type:'EtatPathologique',description:'Pathological medical condition'},
 {id:'InsufHepatiqueModeree',name:'Moderate hepatic insufficiency',domain:'conditions',type:'EtatPathologique',description:'Pathological medical condition'},
 {id:'AllergiePenicilline',name:'Penicillin allergy',domain:'conditions',type:'EtatPathologique',description:'Allergic medical condition'},
 {id:'Essai_Metformine_2024',name:'Metformin trial 2024',domain:'studies',type:'EssaiClinique',description:'Clinical study of metformin (Glucophage) on Type 2 Diabetes',properties:{phaseEssai:'3',nombreParticipants:'500',anneePublication:'2024',estComparative:'true'},relations:[{predicate:'testeMedicament',target:'Glucophage'},{predicate:'porteSurMaladie',target:'DiabeteType2'},{predicate:'aPourResultat',target:'Res_Efficacite_Glucophage'},{predicate:'aPourResultat',target:'Res_Tolerance_Glucophage'}]},
 {id:'Etude_Paracetamol_Obs',name:'Paracetamol observational study',domain:'studies',type:'EtudeObservationnelle',description:'Observational study of paracetamol (Doliprane) without phase or clinical results',properties:{nombreParticipants:'1200',anneePublication:'2023',estComparative:'false'},relations:[{predicate:'testeMedicament',target:'Doliprane'}]},
 {id:'Res_Efficacite_Glucophage',name:'Glucophage efficacy',domain:'results',type:'Efficacite',description:'Clinical efficacy measurement: 1.2 % HbA1c (baisse)',properties:{valeurMesuree:'1.2',uniteMesure:'% HbA1c (baisse)'}},
 {id:'Res_Tolerance_Glucophage',name:'Glucophage tolerance',domain:'results',type:'Tolerance',description:'Clinical tolerance measurement: 85 % patients sans effet gênant',properties:{valeurMesuree:'85',uniteMesure:'% patients sans effet gênant'}}
];
export const links = [
 ['medications','molecules','contientPrincipeActif'],['medications','diseases','traite'],['medications','symptoms','soulage'],['medications','side-effects','provoque'],['medications','contraindications','aPourContreIndication'],['contraindications','conditions','concerneCondition'],['patients','diseases','aPourMaladie'],['patients','conditions','aPourCondition'],['patients','symptoms','ressentSymptome'],['patients','medications','prend'],['studies','medications','testeMedicament'],['studies','results','aPourResultat'],['studies','diseases','porteSurMaladie']
] as const;
export const getDomain=(slug:string)=>domains.find(x=>x.slug===slug);
export const getEntity=(id:string)=>entities.find(x=>x.id===id);
