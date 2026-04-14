import React, { useState } from 'react'
import Navbar from './components/Navbar'
import SMSInput from './pages/SMSInput'
import Dashboard from './pages/Dashboard'
import Chat from './pages/Chat'
import './App.css'

function App() {
  const [activeTab, setActiveTab] = useState('input')
  const [parsedData, setParsedData] = useState(null)

  const handleParsed = (data) => {
    setParsedData(data)
    setActiveTab('dashboard')
  }

  const txCount = parsedData ? parsedData.transactions.length : 0

  return (
    <div className="app-container">
      <Navbar 
        activeTab={activeTab} 
        onTabChange={setActiveTab} 
        txCount={txCount} 
      />

      <main className="main-content">
        {activeTab === 'input' && <SMSInput onParsed={handleParsed} />}
        {activeTab === 'dashboard' && <Dashboard parsedData={parsedData} />}
        {activeTab === 'chat' && <Chat parsedData={parsedData} />}
        
        {/* Placeholder for no data */}
        {(activeTab === 'dashboard' || activeTab === 'chat') && !parsedData && (
          <div className="empty-state-page anim-fadein">
            <div className="glass empty-card">
              <div className="empty-icon">📊</div>
              <h2>No Data Available</h2>
              <p>Please import some SMS messages first to view your dashboard and chat with PocketCoach.</p>
              <button className="btn btn-primary" onClick={() => setActiveTab('input')}>
                Go to Import
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

export default App
