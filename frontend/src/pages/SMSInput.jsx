import React, { useState } from 'react';
import { parseMessages, getSamples } from '../utils/api';
import './SMSInput.css';

export default function SMSInput({ onParsed }) {
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleParse = async () => {
    if (!inputText.trim()) {
      setError('Please paste some SMS messages First.');
      return;
    }
    setError('');
    setLoading(true);

    try {
      // Split by newline and filter empty
      const messages = inputText.split('\n').filter(msg => msg.trim() !== '');
      const data = await parseMessages(messages);
      onParsed(data); // Send to App
    } catch (err) {
      console.error(err);
      setError('Failed to parse messages. Ensure backend is running.');
    } finally {
      setLoading(false);
    }
  };

  const loadDemo = async () => {
    setLoading(true);
    setError('');
    try {
        const data = await getSamples();
        setInputText(data.samples.join('\n\n'));
    } catch (err) {
      setError('Failed to load demo data.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sms-input-page anim-fadeup">
      <div className="header-text text-center">
        <h1 className="gradient-text">Welcome to FinSight</h1>
        <p>Your AI-powered personal finance coach. Paste your bank SMS below.</p>
      </div>

      <div className="glass sms-card">
        <textarea
          className="sms-textarea"
          placeholder="Paste your bank SMS messages here...&#10;&#10;e.g., 'Your A/c XX4521 debited INR 450.00 on 12-Apr-24 at Zomato...'"
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
        />
        
        {error && <div className="error-msg">{error}</div>}

        <div className="actions">
          <button className="btn btn-secondary" onClick={loadDemo} disabled={loading}>
            Try Demo Data
          </button>
          <button className="btn btn-primary" onClick={handleParse} disabled={loading}>
            {loading ? <span className="spinner" /> : 'Analyze Spending'}
          </button>
        </div>
      </div>
    </div>
  );
}
