import React, { useState, useRef, useEffect } from 'react';
import { chatWithCoach } from '../utils/api';
import './Chat.css';

export default function Chat({ parsedData }) {
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hi! I'm your PocketCoach. I've analyzed your spending. What would you like to know?"
    }
  ]);
  const [inputMsg, setInputMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const txData = parsedData?.transactions || [];

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSend = async (e) => {
    e?.preventDefault();
    if (!inputMsg.trim()) return;

    const userMsg = inputMsg.trim();
    setInputMsg('');
    
    const newMsgs = [...messages, { id: Date.now().toString(), role: 'user', content: userMsg }];
    setMessages(newMsgs);
    setLoading(true);

    try {
      // Format history for API (exclude the immediate new message and welcome msg if needed, but keeping simple)
      const history = newMsgs.slice(0, -1).map(m => ({
        role: m.role === 'assistant' ? 'model' : 'user',
        content: m.content
      }));

      const data = await chatWithCoach(userMsg, txData, history);
      
      setMessages(prev => [...prev, {
        id: Date.now().toString() + '_resp',
        role: 'assistant',
        content: data.reply
      }]);
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now().toString() + '_err',
        role: 'assistant',
        content: "Oops, I'm having trouble connecting to my servers. Please make sure the backend API is running and GEMINI_API_KEY is set."
      }]);
    } finally {
      setLoading(false);
    }
  };

  // Convert markdown-ish text to basic HTML (bolding)
  const formatMsg = (text) => {
    // Simple bold
    const bolded = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Lines to br
    return bolded.split('\n').map((line, i) => (
      <span key={i}>
        {line}
        <br />
      </span>
    ));
  };

  return (
    <div className="chat-page anim-fadein">
      <div className="chat-container glass">
        <div className="chat-header">
          <div className="coach-avatar">🤖</div>
          <div>
            <h2>PocketCoach</h2>
            <p>AI Financial Advisor powered by Gemini</p>
          </div>
        </div>

        <div className="chat-messages">
          {messages.map(msg => (
            <div key={msg.id} className={`chat-bubble-wrapper ${msg.role}`}>
              {msg.role === 'assistant' && <div className="bubble-avatar">🤖</div>}
              <div className={`chat-bubble ${msg.role} anim-fadeup`}>
                {formatMsg(msg.content)}
              </div>
            </div>
          ))}
          {loading && (
            <div className="chat-bubble-wrapper assistant">
              <div className="bubble-avatar">🤖</div>
              <div className="chat-bubble assistant typing">
                <span className="dot"></span>
                <span className="dot"></span>
                <span className="dot"></span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <form className="chat-input-area" onSubmit={handleSend}>
          <input
            type="text"
            className="chat-input"
            placeholder="Ask about your budget, spending habits, or financial tips..."
            value={inputMsg}
            onChange={(e) => setInputMsg(e.target.value)}
            disabled={loading}
          />
          <button type="submit" className="btn btn-primary btn-send" disabled={loading || !inputMsg.trim()}>
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
