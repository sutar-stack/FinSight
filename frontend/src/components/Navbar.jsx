import React from 'react'
import './Navbar.css'

const tabs = [
  { id: 'input',     label: 'Import SMS',    icon: '📥' },
  { id: 'dashboard', label: 'Dashboard',     icon: '📊' },
  { id: 'chat',      label: 'PocketCoach',   icon: '🤖' },
]

export default function Navbar({ activeTab, onTabChange, txCount }) {
  return (
    <nav className="navbar">
      <div className="navbar-inner">
        {/* Brand */}
        <div className="navbar-brand">
          <div className="navbar-logo">
            <span className="logo-icon">💎</span>
          </div>
          <div>
            <span className="navbar-title">FinSight</span>
            <span className="navbar-sub">AI Finance Coach</span>
          </div>
        </div>

        {/* Tabs */}
        <div className="navbar-tabs">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
              onClick={() => onTabChange(tab.id)}
            >
              <span>{tab.icon}</span>
              <span>{tab.label}</span>
              {tab.id === 'dashboard' && txCount > 0 && (
                <span className="tx-badge">{txCount}</span>
              )}
            </button>
          ))}
        </div>

        {/* Right hint */}
        <div className="navbar-right">
          <span className="hint-text">Powered by Gemini</span>
          <span className="gemini-dot" />
        </div>
      </div>
    </nav>
  )
}
