import {Navigate,Route,Routes} from 'react-router-dom';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import SearchPage from './pages/Search';
import Collection from './pages/Collection';
import Detail from './pages/Detail';
import Graph from './pages/Graph';
export default function App(){return <Routes><Route element={<Layout/>}><Route index element={<Dashboard/>}/><Route path="search" element={<SearchPage/>}/><Route path="graph" element={<Graph/>}/><Route path="catalog/:slug" element={<Collection/>}/><Route path="entity/:id" element={<Detail/>}/><Route path="*" element={<Navigate to="/" replace/>}/></Route></Routes>}
