import { useEffect, useRef, useState } from 'react';
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom';
import {
  ArrowRight, ArrowUpRight, ChevronDown, ChevronRight, Command,
  Github, HeartPulse, LayoutDashboard, Menu, Network, Search, X,
} from 'lucide-react';
import { domains, getDomain } from '../data/ontology';
import { DomainIcon } from './Icons';

const groups = [
  { name: 'Pharmaceutical', subtitle: 'Drugs & safety' },
  { name: 'Clinical', subtitle: 'Care & conditions' },
  { name: 'Safety', subtitle: 'Contraindications' },
  { name: 'Research', subtitle: 'Studies & evidence' },
];

export default function Layout() {
  const [menu, setMenu] = useState(false);
  const [search, setSearch] = useState('');
  const [quickSearchOpen, setQuickSearchOpen] = useState(false);
  const quickInput = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const location = useLocation();
  const pathname = location.pathname;
  const title = pathname === '/' ? 'Workspace' : pathname.startsWith('/search') ? 'Semantic search'
    : pathname.startsWith('/graph') ? 'Knowledge graph'
    : pathname.startsWith('/catalog/') ? getDomain(pathname.split('/')[2])?.title ?? 'Library'
    : 'Entity profile';

  useEffect(() => {
    setMenu(false);
    setQuickSearchOpen(false);
  }, [pathname]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault(); setQuickSearchOpen(current => !current);
      }
      if (event.key === 'Escape') setQuickSearchOpen(false);
    }
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);
  useEffect(() => { if (quickSearchOpen) quickInput.current?.focus(); }, [quickSearchOpen]);

  function submitSearch(value: string) {
    navigate('/search' + (value.trim() ? '?q=' + encodeURIComponent(value.trim()) : ''));
    setSearch(''); setQuickSearchOpen(false);
  }

  const navItem = ({ isActive }: { isActive: boolean }) => 'side-link' + (isActive ? ' selected' : '');

  return <div className="app-shell">
    {menu && <button className="mobile-overlay" aria-label="Close navigation" onClick={() => setMenu(false)} />}
    <aside className={'sidebar' + (menu ? ' open' : '')} aria-label="Main navigation">
      <div className="sidebar-top">
        <Link className="brand" to="/" onClick={() => setMenu(false)}>
          <span className="brand-symbol"><HeartPulse size={26} strokeWidth={2.1} /></span>
          <span className="brand-wordmark"><strong>MedSemantic<span className="brand-period">.</span></strong><small>KNOWLEDGE PLATFORM</small></span>
        </Link>
        <button className="mobile-close" aria-label="Close menu" onClick={() => setMenu(false)}><X size={22}/></button>
      </div>
      <div className="sidebar-scroll">
        <div className="nav-title">EXPLORE</div>
        <nav className="nav-links">
          <NavLink end to="/" className={navItem}><LayoutDashboard size={20} /><span>Overview</span></NavLink>
          <NavLink to="/search" className={navItem}><Search size={20}/><span>Semantic search</span></NavLink>
          <NavLink to="/graph" className={navItem}><Network size={20}/><span>Knowledge graph</span></NavLink>
        </nav>
        <div className="sidebar-rule" />
        {groups.map(group => <div className="nav-group" key={group.name}>
          <div className="nav-title">{group.name.toUpperCase()}<ChevronDown size={13}/></div>
          <nav className="nav-links">
            {domains.filter(d => d.group === group.name).map(d =>
              <NavLink to={'/catalog/' + d.slug} className={navItem} key={d.slug}>
                <DomainIcon name={d.icon} size={19}/><span>{d.title}</span>
              </NavLink>)}
          </nav>
        </div>)}
      </div>
      <div className="sidebar-bottom">
        <div className="sidebar-spotlight">
          <div className="spotlight-symbol"><Network size={19}/><span className="spotlight-pulse"/></div>
          <strong>Explore the connections</strong>
          <p>Discover how medical knowledge fits together.</p>
          <Link to="/graph">Open knowledge map <ArrowUpRight size={15}/></Link>
        </div>
        <div className="sidebar-footnote"><span className="footnote-mark"/> MedSemantic · 2026</div>
      </div>
    </aside>

    <div className="workspace">
      <header className="topbar">
        <div className="topbar-trail">
          <button className="mobile-menu" onClick={() => setMenu(true)} aria-label="Open navigation"><Menu size={23}/></button>
          <span className="topbar-root">MedSemantic</span><ChevronRight size={15} className="topbar-chevron"/>
          <strong>{title}</strong>
        </div>
        <div className="topbar-actions">
          <button className="command-search" onClick={() => setQuickSearchOpen(true)}><Search size={18}/><span>Search anything...</span><kbd><Command size={12}/> K</kbd></button>
          <span className="topbar-divider" />
          <a className="topbar-github" href="https://github.com/hanah-15/MedSemantic-Project" target="_blank" rel="noopener noreferrer" aria-label="Project on GitHub"><Github size={20}/></a>
          <Link className="topbar-explore" to="/graph"><Network size={17}/> Explore graph <ArrowUpRight size={15}/></Link>
        </div>
      </header>
      <main className="main-content" id="main-content"><Outlet/></main>
      <footer className="app-footer"><span><HeartPulse size={15}/> MedSemantic <span className="footer-separator">/</span> Semantic medicine research</span><span>Illustrative ontology content · Not medical guidance</span></footer>
    </div>

    {quickSearchOpen && <div className="command-backdrop" role="presentation" onMouseDown={() => setQuickSearchOpen(false)}>
      <form className="command-dialog" role="search" onMouseDown={e => e.stopPropagation()} onSubmit={e => { e.preventDefault(); submitSearch(search); }}>
        <div className="command-field"><Search size={23}/><input ref={quickInput} value={search} aria-label="Search medical concepts" placeholder="Search conditions, drugs, people, studies..." onChange={e => setSearch(e.target.value)}/><button type="button" aria-label="Close search" onClick={() => setQuickSearchOpen(false)}><X size={18}/></button></div>
        <div className="command-picks"><span>DISCOVER</span>{['Glucophage','Patient Karim','Hypertension'].map(item => <button type="button" key={item} onClick={() => submitSearch(item)}><Search size={16}/>{item}<ArrowRight size={15}/></button>)}</div>
        <div className="command-hint"><kbd>ENTER</kbd> to search <kbd>ESC</kbd> to close</div>
      </form>
    </div>}
  </div>;
}
