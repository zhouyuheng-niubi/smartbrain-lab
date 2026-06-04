import { Route, Routes } from 'react-router-dom'
import Layout from './components/layout/Layout'
import MethodologyLibrary from './pages/MethodologyLibrary'
import MethodologyDetail from './pages/MethodologyDetail'
import MethodologyEditor from './pages/MethodologyEditor'
import RunWorkbench from './pages/RunWorkbench'
import RunHistory from './pages/RunHistory'
import Distill from './pages/Distill'
import Lens from './pages/Lens'
import Advisor from './pages/Advisor'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<MethodologyLibrary />} />
        <Route path="/methodology/:id" element={<MethodologyDetail />} />
        <Route path="/methodology/:id/edit" element={<MethodologyEditor />} />
        <Route path="/new" element={<MethodologyEditor />} />
        <Route path="/run/:id" element={<RunWorkbench />} />
        <Route path="/runs" element={<RunHistory />} />
        <Route path="/distill" element={<Distill />} />
        <Route path="/lens" element={<Lens />} />
        <Route path="/advisor" element={<Advisor />} />
        <Route path="/advisor/:id" element={<Advisor />} />
      </Route>
    </Routes>
  )
}
