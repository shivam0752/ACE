import React, { useState, useRef, useEffect } from 'react'
import axios from 'axios'
import './App.css'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

// Static User ID to test context persistence across sessions
const USER_ID = "test-user-ace-01"

function CurrencyConverter({ rateText }) {
  const [amount, setAmount] = useState(100);
  if (!rateText) return null;
  
  let rate = 1;
  let fromCurr = "USD";
  let toCurr = "INR";
  
  // Try to parse rate (e.g., "1 USD = 83.25 INR" or "83.25 INR per USD")
  try {
    const matches = rateText.match(/([\d\.,]+)\s*([A-Za-z]{3})\s*(?:=|\s+to\s+)\s*([\d\.,]+)\s*([A-Za-z]{3})/i);
    if (matches) {
      fromCurr = matches[2].toUpperCase();
      toCurr = matches[4].toUpperCase();
      const val1 = parseFloat(matches[1].replace(/,/g, ''));
      const val2 = parseFloat(matches[3].replace(/,/g, ''));
      rate = val2 / val1;
    } else {
      const simpleMatch = rateText.match(/([\d\.,]+)/g);
      if (simpleMatch && simpleMatch.length > 0) {
        rate = parseFloat(simpleMatch[simpleMatch.length - 1].replace(/,/g, ''));
        // Try to guess currencies from string
        const currencies = rateText.match(/[A-Z]{3}/g);
        if (currencies && currencies.length >= 2) {
          fromCurr = currencies[0];
          toCurr = currencies[1];
        }
      }
    }
  } catch (e) {
    console.error("Failed to parse currency rate", e);
  }
  
  return (
    <div className="currency-converter-card">
      <div className="converter-header">
        <span className="converter-icon">💱</span>
        <h4>Exchange Converter</h4>
      </div>
      <div className="converter-body">
        <div className="converter-input-wrapper">
          <label>{fromCurr}</label>
          <input 
            type="number" 
            value={amount} 
            onChange={(e) => setAmount(Math.max(0, parseFloat(e.target.value) || 0))}
            placeholder="Amount"
          />
        </div>
        <div className="converter-divider">
          <span>⇄</span>
        </div>
        <div className="converter-input-wrapper">
          <label>{toCurr}</label>
          <div className="converted-display">
            {(amount * rate).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </div>
        </div>
      </div>
      <div className="converter-footer">
        <span>Source Rate: {rateText}</span>
      </div>
    </div>
  );
}

function WeatherDisplay({ weatherText }) {
  if (!weatherText) return null;

  // Let's check if the weatherText is formatted like a list or has multiple details
  // We will display a beautiful card
  return (
    <div className="weather-forecast-card">
      <div className="weather-header">
        <span className="weather-title-icon">🌤️</span>
        <h4>Destination Weather</h4>
      </div>
      <div className="weather-content">
        <p className="weather-desc-text">{weatherText}</p>
      </div>
    </div>
  );
}

function ItineraryDashboard({ data, sessionId }) {
  const [activeTab, setActiveTab] = useState('itinerary');
  const [activeDay, setActiveDay] = useState(0);
  const [rating, setRating] = useState(0);
  const [ratingSubmitted, setRatingSubmitted] = useState(false);

  const destination = data.destination || "Personalized Travel Plan";
  const duration = data.duration_days || (data.itinerary ? data.itinerary.length : 0);
  const weather = data.weather_forecast;
  const currency = data.currency_conversion;
  const itinerary = data.itinerary || [];
  const budget = data.budget_breakdown || {};
  const accommodations = data.accommodation_suggestions || [];
  const tips = data.travel_tips || [];
  const intro = data.conversational_response;

  const handleRate = async (value) => {
    setRating(value);
    try {
      await axios.post(`${API_URL}/rate`, {
        session_id: sessionId,
        rating: value
      });
      setRatingSubmitted(true);
    } catch (err) {
      console.error("Error submitting rating", err);
    }
  };

  return (
    <div className="itinerary-dashboard glass-panel animate-fade-in">
      <div className="dashboard-header">
        <div className="header-meta">
          <div className="dest-tag">✈️ TRAVEL PLAN</div>
          <h3>🌴 {destination} ({duration} Days)</h3>
          <p className="intro-text">{intro}</p>
        </div>
        <div className="header-widgets">
          {weather && (
            <div className="widget weather-widget">
              <span className="widget-icon">🌤️</span>
              <div className="widget-body">
                <span className="widget-label">Weather Forecast</span>
                <span className="widget-value">{weather.length > 35 ? weather.substring(0, 32) + '...' : weather}</span>
              </div>
            </div>
          )}
          {currency && (
            <div className="widget currency-widget">
              <span className="widget-icon">💱</span>
              <div className="widget-body">
                <span className="widget-label">Exchange Rate</span>
                <span className="widget-value">{currency.length > 25 ? currency.substring(0, 22) + '...' : currency}</span>
              </div>
            </div>
          )}
        </div>
      </div>

      <div className="dashboard-tabs">
        <button 
          type="button"
          className={`tab-btn ${activeTab === 'itinerary' ? 'active' : ''}`}
          onClick={() => setActiveTab('itinerary')}
        >
          🗓️ Itinerary
        </button>
        <button 
          type="button"
          className={`tab-btn ${activeTab === 'budget' ? 'active' : ''}`}
          onClick={() => setActiveTab('budget')}
        >
          💰 Budget & Exchange
        </button>
        <button 
          type="button"
          className={`tab-btn ${activeTab === 'accommodations' ? 'active' : ''}`}
          onClick={() => setActiveTab('accommodations')}
        >
          🏨 Hotels
        </button>
        <button 
          type="button"
          className={`tab-btn ${activeTab === 'tips' ? 'active' : ''}`}
          onClick={() => setActiveTab('tips')}
        >
          💡 Tips
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'itinerary' && (
          <div className="itinerary-tab animate-fade-in">
            <div className="day-selector">
              {itinerary.map((dayData, idx) => (
                <button
                  key={idx}
                  type="button"
                  className={`day-chip ${activeDay === idx ? 'active' : ''}`}
                  onClick={() => setActiveDay(idx)}
                >
                  Day {dayData.day || idx + 1}
                </button>
              ))}
            </div>
            {itinerary[activeDay] && (
              <div className="day-plan animate-slide-up">
                <h4 className="day-theme">✨ Theme: {itinerary[activeDay].theme}</h4>
                <div className="timeline">
                  {itinerary[activeDay].activities.map((act, aIdx) => (
                    <div key={aIdx} className="timeline-item">
                      <div className="timeline-badge">{act.time}</div>
                      <div className="timeline-panel">
                        <h5>{act.activity}</h5>
                        <p>{act.description}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'budget' && (
          <div className="budget-tab animate-fade-in">
            <div className="budget-split-layout">
              <div className="budget-section">
                <div className="budget-grid">
                  {Object.entries(budget).map(([key, val]) => {
                    if (key === 'total_estimated') return null;
                    let icon = '🎟️';
                    if (key === 'accommodation') icon = '🏨';
                    else if (key === 'transport') icon = '✈️';
                    else if (key === 'food') icon = '🍔';
                    else if (key === 'activities') icon = '🎟️';
                    
                    return (
                      <div key={key} className="budget-card">
                        <span className="budget-icon">{icon}</span>
                        <div className="budget-info">
                          <span className="budget-label">{key.replace('_', ' ')}</span>
                          <span className="budget-value">{val}</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
                {budget.total_estimated && (
                  <div className="budget-total">
                    <span className="total-label">Total Estimated Cost</span>
                    <span className="total-value">{budget.total_estimated}</span>
                  </div>
                )}
              </div>
              
              <div className="utilities-section">
                {currency && <CurrencyConverter rateText={currency} />}
                {weather && <WeatherDisplay weatherText={weather} />}
              </div>
            </div>
          </div>
        )}

        {activeTab === 'accommodations' && (
          <div className="hotels-tab animate-fade-in">
            <div className="hotels-grid">
              {accommodations.map((hotel, hIdx) => (
                <div key={hIdx} className="hotel-card hover-glow">
                  <div className="hotel-header">
                    <h5>{hotel.name}</h5>
                    <span className="hotel-badge">{hotel.type}</span>
                  </div>
                  <p className="hotel-price">💰 {hotel.price_per_night} / night</p>
                  <p className="hotel-desc">{hotel.description}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === 'tips' && (
          <div className="tips-tab animate-fade-in">
            <ul className="tips-list">
              {tips.map((tip, tIdx) => (
                <li key={tIdx} className="tip-item">
                  <span className="tip-bullet">⚡</span>
                  <p>{tip}</p>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>

      <div className="rating-section">
        <span className="rating-title">Rate the relevance and quality of this plan:</span>
        {ratingSubmitted ? (
          <span className="rating-submitted-msg">Thank you for your feedback! (Rated: {rating}⭐)</span>
        ) : (
          <div className="stars-container">
            {[1, 2, 3, 4, 5].map((star) => (
              <button
                key={star}
                type="button"
                className="star-btn"
                onClick={() => handleRate(star)}
                onMouseEnter={() => setRating(star)}
                onMouseLeave={() => setRating(0)}
              >
                <span className={star <= (rating || 0) ? "star-filled" : "star-empty"}>★</span>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function MetricsDashboard() {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get(`${API_URL}/metrics`);
      setMetrics(response.data);
    } catch (err) {
      console.error(err);
      setError("Failed to load metrics. Ensure the backend is running.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, []);

  const handleAuditToggle = async (logId, field, currentValue) => {
    try {
      const payload = {
        log_id: logId,
        [field]: !currentValue
      };
      await axios.post(`${API_URL}/audit`, payload);
      // Update local state to reflect change immediately
      setMetrics(prev => {
        if (!prev) return prev;
        const updatedLogs = prev.recent_logs.map(log => {
          if (log.id === logId) {
            return { ...log, [field]: !currentValue };
          }
          return log;
        });
        
        // Re-calculate the hallucination rate or preference retention accuracy
        const hallucination_checks = updatedLogs.map(r => r.hallucination_detected).filter(v => v !== null && v !== undefined);
        const new_hallucination_rate = hallucination_checks.length > 0 
          ? (hallucination_checks.filter(v => v).length / hallucination_checks.length) * 100 
          : 0;

        const retention_checks = updatedLogs.map(r => r.preference_retention_accurate).filter(v => v !== null && v !== undefined);
        const new_retention_accuracy = retention_checks.length > 0
          ? (retention_checks.filter(v => v).length / retention_checks.length) * 100
          : 100;
          
        return {
          ...prev,
          recent_logs: updatedLogs,
          hallucination_rate: Math.round(new_hallucination_rate * 100) / 100,
          preference_retention_accuracy: Math.round(new_retention_accuracy * 100) / 100
        };
      });
    } catch (err) {
      console.error("Error updating audit", err);
    }
  };

  if (loading) {
    return (
      <div className="dashboard-view-container">
        <h3>📊 Performance & Evaluation Dashboard</h3>
        <p>Loading metrics...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-view-container">
        <h3>📊 Performance & Evaluation Dashboard</h3>
        <div className="error-banner">
          <span className="error-icon">⚠</span>
          <p className="error-text">{error}</p>
        </div>
        <button onClick={fetchMetrics} className="refresh-metrics-btn" style={{ margin: '0 auto' }}>Retry 🔄</button>
      </div>
    );
  }

  if (!metrics) return null;

  return (
    <div className="dashboard-view-container animate-fade-in">
      <div className="dashboard-panel-header">
        <h3>📊 Performance & Evaluation Dashboard</h3>
        <button onClick={fetchMetrics} className="refresh-metrics-btn">Refresh Metrics 🔄</button>
      </div>

      <div className="dashboard-summary-grid">
        <div className="metrics-summary-card">
          <span className="metric-title">Workflow Completion</span>
          <span className="metric-number">{metrics.workflow_completion_rate}%</span>
          <span className="metric-description">Percentage of pipe executions that completed without errors.</span>
        </div>
        <div className="metrics-summary-card">
          <span className="metric-title">Preference Retention</span>
          <span className="metric-number">{metrics.preference_retention_accuracy}%</span>
          <span className="metric-description">Context alignment verification based on stored preferences.</span>
        </div>
        <div className="metrics-summary-card">
          <span className="metric-title">Budget Variance</span>
          <span className="metric-number">{metrics.average_budget_variance}%</span>
          <span className="metric-description">Avg deviation between estimated costs and user requested budgets.</span>
        </div>
        <div className="metrics-summary-card">
          <span className="metric-title">Context Relevance</span>
          <span className="metric-number">{metrics.average_context_relevance} / 5</span>
          <span className="metric-description">Average rating of travel plans submitted by users.</span>
        </div>
        <div className="metrics-summary-card">
          <span className="metric-title">Avg API Latency</span>
          <span className="metric-number">{Math.round(metrics.average_latency_ms)} ms</span>
          <span className="metric-description">End-to-end execution time from input submit to response.</span>
        </div>
        <div className="metrics-summary-card">
          <span className="metric-title">Hallucination Rate</span>
          <span className="metric-number">{metrics.hallucination_rate}%</span>
          <span className="metric-description">Percentage of itineraries flagged during audits.</span>
        </div>
      </div>

      <div className="dashboard-row-split">
        <div className="glass-panel" style={{ padding: '20px', background: 'rgba(255,255,255,0.01)', border: '1px solid var(--border)', borderRadius: 'var(--radius-md)' }}>
          <h4 style={{ margin: '0 0 16px 0', color: '#fff' }}>Audit Trail & Recent Execution Logs</h4>
          <div className="metrics-table-wrapper">
            <table className="metrics-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Session ID</th>
                  <th>Latency</th>
                  <th>Status</th>
                  <th>Budget Var</th>
                  <th>Rating</th>
                  <th>Retention Accurate?</th>
                  <th>Hallucination?</th>
                </tr>
              </thead>
              <tbody>
                {metrics.recent_logs && metrics.recent_logs.length > 0 ? (
                  metrics.recent_logs.map((log) => (
                    <tr key={log.id}>
                      <td>{new Date(log.timestamp).toLocaleString()}</td>
                      <td title={log.session_id}>{log.session_id.substring(0, 12)}...</td>
                      <td>{Math.round(log.latency_ms)} ms</td>
                      <td>
                        <span style={{ color: log.status === 'success' ? '#10b981' : '#ef4444', fontWeight: 600 }}>
                          {log.status}
                        </span>
                      </td>
                      <td>
                        {log.budget_variance !== null && log.budget_variance !== undefined
                          ? `${Math.round(log.budget_variance * 100)}%`
                          : 'N/A'}
                      </td>
                      <td>{log.context_relevance_rating ? `${log.context_relevance_rating}⭐` : 'Pending'}</td>
                      <td>
                        <label className="audit-checkbox">
                          <input
                            type="checkbox"
                            checked={!!log.preference_retention_accurate}
                            onChange={() => handleAuditToggle(log.id, 'preference_retention_accurate', !!log.preference_retention_accurate)}
                          />
                          <span>{log.preference_retention_accurate ? 'Yes' : 'No'}</span>
                        </label>
                      </td>
                      <td>
                        <label className="audit-checkbox">
                          <input
                            type="checkbox"
                            checked={!!log.hallucination_detected}
                            onChange={() => handleAuditToggle(log.id, 'hallucination_detected', !!log.hallucination_detected)}
                          />
                          <span style={{ color: log.hallucination_detected ? '#ef4444' : 'inherit' }}>
                            {log.hallucination_detected ? 'Hallucination' : 'None'}
                          </span>
                        </label>
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan="8" style={{ textAlign: 'center', padding: '20px' }}>No logs recorded yet.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}

function App() {
  const [activeView, setActiveView] = useState('chat')
  const [sessionId, setSessionId] = useState(() => `session-${Date.now()}`)
  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      sender: 'ace',
      text: "Hello! I am ACE (Aether Context Engine). I'm ready to help you plan your next journey. What destination or ideas do you have in mind?",
      timestamp: new Date()
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const chatEndRef = useRef(null)

  const suggestionPrompts = [
    "I prefer budget accommodations and quiet, nature-focused destinations.",
    "Plan a 3-day weekend trip for 2 people to Manali.",
    "Weekend getaway to Goa from Delhi with conversion to USD",
  ]

  // Auto-scroll to the bottom of the chat
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  const handleSendMessage = async (textToSend) => {
    const trimmedText = textToSend || input.trim()
    if (!trimmedText) return

    if (!textToSend) {
      setInput('')
    }
    setError(null)

    // Append user message
    const userMessage = {
      id: Date.now().toString(),
      sender: 'user',
      text: trimmedText,
      timestamp: new Date()
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)

    try {
      const response = await axios.post(`${API_URL}/chat`, {
        message: trimmedText,
        user_id: USER_ID,
        session_id: sessionId
      })
      
      const aceMessage = {
        id: (Date.now() + 1).toString(),
        sender: 'ace',
        text: response.data.response,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, aceMessage])
    } catch (err) {
      console.error(err)
      setError('Failed to connect to the backend engine. Ensure the FastAPI backend is running.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleNewSession = () => {
    setSessionId(`session-${Date.now()}`)
    setMessages([
      {
        id: `welcome-${Date.now()}`,
        sender: 'ace',
        text: "Started a new session! My memory of your preferences is persistent. What would you like to plan next?",
        timestamp: new Date()
      }
    ])
    setError(null)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    handleSendMessage()
  }

  const renderMessageContent = (msg) => {
    if (msg.sender === 'user') {
      return (
        <div className="message-text">
          <p>{msg.text}</p>
        </div>
      )
    }

    try {
      const parsedData = JSON.parse(msg.text)
      if (parsedData.is_itinerary) {
        return <ItineraryDashboard data={parsedData} sessionId={sessionId} />
      }
      return (
        <div className="message-text">
          <p>{parsedData.conversational_response || msg.text}</p>
        </div>
      )
    } catch (e) {
      return (
        <div className="message-text">
          {msg.text.split('\n').map((line, i) => (
            <p key={i}>{line}</p>
          ))}
        </div>
      )
    }
  }

  return (
    <div className="app-container">
      {/* Sidebar / Branding Header */}
      <header className="app-header">
        <div className="brand">
          <div className="brand-logo">
            <span className="logo-spark">✦</span>
          </div>
          <div className="brand-info">
            <h1>Aether Context Engine</h1>
            <span className="status-badge">
              <span className="status-dot animate-pulse"></span> Phase 4: Performance Dashboard
            </span>
          </div>
        </div>
        <div className="session-controls">
          <div className="view-toggle-container">
            <button 
              type="button"
              className={`toggle-view-btn ${activeView === 'chat' ? 'active' : ''}`}
              onClick={() => setActiveView('chat')}
            >
              💬 Chat
            </button>
            <button 
              type="button"
              className={`toggle-view-btn ${activeView === 'dashboard' ? 'active' : ''}`}
              onClick={() => setActiveView('dashboard')}
            >
              📊 Dashboard
            </button>
          </div>
          <div className="session-info">
            <div className="session-info-item">
              <span className="info-label">User:</span>
              <span className="info-value">{USER_ID}</span>
            </div>
            <div className="session-info-item">
              <span className="info-label">Session ID:</span>
              <span className="info-value text-glow">{sessionId.split('-')[1] || sessionId}</span>
            </div>
          </div>
          <button onClick={handleNewSession} className="new-session-btn" title="Start a new chat session but keep user preferences">
            New Session 🔄
          </button>
        </div>
      </header>

      {/* Main Container */}
      <main className="chat-frame">
        {activeView === 'chat' ? (
          <>
            <div className="chat-window">
              {messages.map((msg) => (
                <div key={msg.id} className={`message-row ${msg.sender}-row ${msg.sender === 'ace' && msg.text.startsWith('{') ? 'full-width-message' : ''}`}>
                  <div className="message-avatar">
                    {msg.sender === 'ace' ? '🤖' : '👤'}
                  </div>
                  <div className="message-bubble animate-fade-in">
                    {renderMessageContent(msg)}
                    <span className="message-time">
                      {msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                </div>
              ))}

              {isLoading && (
                <div className="message-row ace-row">
                  <div className="message-avatar">🤖</div>
                  <div className="message-bubble loading-bubble">
                    <div className="typing-indicator">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                  </div>
                </div>
              )}

              {error && (
                <div className="error-banner animate-fade-in">
                  <span className="error-icon">⚠</span>
                  <p className="error-text">{error}</p>
                </div>
              )}
              
              <div ref={chatEndRef} />
            </div>

            {/* Floating Quick Suggestions (Only show when there is only the welcome message) */}
            {messages.length === 1 && !isLoading && (
              <div className="suggestions-container animate-fade-in">
                <p className="suggestions-title">Try asking / setting preferences:</p>
                <div className="suggestions-grid">
                  {suggestionPrompts.map((prompt, index) => (
                    <button 
                      key={index} 
                      className="suggestion-chip" 
                      onClick={() => handleSendMessage(prompt)}
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Input Bar */}
            <form onSubmit={handleSubmit} className="input-form">
              <div className="input-wrapper">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Ask ACE to plan a trip..."
                  disabled={isLoading}
                />
                <button type="submit" disabled={isLoading || !input.trim()} className="send-btn">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z" />
                  </svg>
                </button>
              </div>
            </form>
          </>
        ) : (
          <MetricsDashboard />
        )}
      </main>
    </div>
  )
}

export default App
