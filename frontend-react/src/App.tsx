import { useState } from 'react'
import ComplaintList from './ComplaintList'
import ComplaintDetail from './ComplaintDetail'

function App() {
    const [view, setView] = useState<'list' | 'detail'>('list');
    const [selectedId, setSelectedId] = useState<number | null>(null);

    return (
        <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
            <h1>ComplaintOps Copilot</h1>
            <hr />
            {view === 'list' ? (
                <ComplaintList onSelect={(id) => { setSelectedId(id); setView('detail'); }} />
            ) : (
                selectedId && <ComplaintDetail id={selectedId} onBack={() => setView('list')} />
            )}
        </div>
    )
}

export default App
