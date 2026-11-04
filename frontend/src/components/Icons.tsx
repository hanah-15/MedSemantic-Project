import {Activity,Atom,ChartNoAxesCombined,FlaskConical,HeartPulse,Pill,ShieldAlert,ShieldCheck,Stethoscope,UsersRound,type LucideProps} from 'lucide-react';
export const iconSet={pill:Pill,atom:Atom,heart:HeartPulse,activity:Activity,alert:ShieldAlert,shield:ShieldCheck,users:UsersRound,stethoscope:Stethoscope,flask:FlaskConical,chart:ChartNoAxesCombined};
export function DomainIcon({name,...props}:{name:keyof typeof iconSet}&LucideProps){const Icon=iconSet[name];return <Icon {...props}/>;}
