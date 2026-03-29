import { useEffect, useRef, useState } from 'react'
import { AlertTriangle, ArrowRight, CheckCircle2, Download, FileText, MessageCircle, Send, ShieldCheck, Upload, X } from 'lucide-react'

export const LANGUAGES = [
  ['English', 'English'],
  ['Assamese', 'অসমীয়া'],
  ['Bengali', 'বাংলা'],
  ['Bodo', 'बड़ो'],
  ['Dogri', 'डोगरी'],
  ['Gujarati', 'ગુજરાતી'],
  ['Hindi', 'हिन्दी'],
  ['Kannada', 'ಕನ್ನಡ'],
  ['Kashmiri', 'कश्मीरी'],
  ['Konkani', 'कोंकणी'],
  ['Maithili', 'মৈথিলী'],
  ['Malayalam', 'മലയാളം'],
  ['Manipuri', 'মণিপুরী'],
  ['Marathi', 'मराठी'],
  ['Nepali', 'नेपाली'],
  ['Odia', 'ওড়িয়া'],
  ['Punjabi', 'ਪੰਜਾਬੀ'],
  ['Sanskrit', 'संस्कृतम्'],
  ['Santali', 'ᱥᱟᱱᱛᱟᱲᱤ'],
  ['Sindhi', 'سنڌي'],
  ['Tamil', 'தமிழ்'],
  ['Telugu', 'తెలుగు'],
  ['Urdu', 'اردو'],
]

export const SECTORS = [
  ['general', 'General'],
  ['fintech', 'Fintech'],
  ['healthtech', 'Healthtech'],
  ['edtech', 'Edtech'],
  ['ecommerce', 'E-commerce'],
  ['insurance', 'Insurance'],
  ['telecom', 'Telecom'],
  ['hrtech', 'HR Tech'],
  ['realestate', 'Real Estate'],
  ['logistics', 'Logistics'],
  ['media', 'Media'],
]

const PII_COLORS = {
  name:        { bg: '#eff6ff', text: '#1d4ed8' },
  identifier:  { bg: '#fef9c3', text: '#854d0e' },
  contact:     { bg: '#f0fdf4', text: '#15803d' },
  financial:   { bg: '#f0fdfa', text: '#0f766e' },
  health:      { bg: '#fdf2f8', text: '#9d174d' },
  biometric:   { bg: '#faf5ff', text: '#7e22ce' },
  location:    { bg: '#fff7ed', text: '#c2410c' },
  online:      { bg: '#f1f5f9', text: '#475569' },
  employment:  { bg: '#f8fafc', text: '#64748b' },
  non_pii:     { bg: '#f9fafb', text: '#9ca3af' },
}

function ScoreBar({ value, label, color }) {
  if (value == null) return null
  const pct = Math.round(value * 100)
  const barColor = color || (pct >= 60 ? '#22c55e' : pct >= 40 ? '#f59e0b' : '#ef4444')
  return (
    <div style={{ marginBottom: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.78rem', marginBottom: 4 }}>
        <span style={{ color: '#64748b' }}>{label}</span>
        <span style={{ fontWeight: 700 }}>{pct}%</span>
      </div>
      <div style={{ height: 6, borderRadius: 999, background: '#e2e8f0', overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${pct}%`, background: barColor, borderRadius: 999, transition: 'width 0.4s' }} />
      </div>
    </div>
  )
}

function DataTable({ rows, columns }) {
  return (
    <div style={{ border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'auto', maxHeight: 400 }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', minWidth: 500 }}>
        <thead style={{ position: 'sticky', top: 0, background: '#f8fafc', zIndex: 1 }}>
          <tr>
            {columns.map(([, label]) => (
              <th key={label} style={{ padding: '8px 10px', textAlign: 'left', fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b', fontWeight: 700, borderBottom: '1px solid #e2e8f0', whiteSpace: 'nowrap' }}>
                {label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx} style={{ borderBottom: idx < rows.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
              {columns.map(([key]) => {
                const val = row[key]
                const color = key === 'pii_category' ? (PII_COLORS[val] || PII_COLORS.non_pii) : null
                return (
                  <td key={key} style={{ padding: '7px 10px', fontSize: '0.82rem', color: color ? color.text : 'inherit', background: color ? color.bg : 'transparent' }}>
                    {String(val ?? '—')}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function SectionNav({ sections, active, onSelect, result }) {
  return (
    <div style={{ display: 'flex', gap: 6, background: '#fff', borderRadius: 12, border: '1px solid #e2e8f0', padding: '6px 8px', flexWrap: 'wrap' }}>
      {sections.map(([id, label]) => {
        const count = id === 'obligations' ? result.obligations.length
          : id === 'conflicts' ? result.conflicts.length
          : 0
        const isActive = active === id
        return (
          <button key={id} onClick={() => onSelect(id)} style={{
            display: 'flex', alignItems: 'center', gap: 5, border: '1px solid', borderColor: isActive ? '#99f6e4' : '#e2e8f0',
            background: isActive ? '#f0fdfa' : '#fff', color: isActive ? '#0f766e' : '#475569',
            borderRadius: 8, padding: '5px 10px', fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer',
          }}>
            {label}
            {count > 0 && (
              <span style={{ background: isActive ? '#0f766e' : '#e2e8f0', color: isActive ? '#fff' : '#64748b', borderRadius: 99, padding: '0 5px', fontSize: '0.68rem' }}>
                {count}
              </span>
            )}
          </button>
        )
      })}
    </div>
  )
}

function LandingPage({ onStart }) {
  return (
    <div style={{ background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', overflow: 'hidden', boxShadow: '0 1px 3px rgba(15,23,42,0.06)' }}>
      <div style={{ background: 'linear-gradient(135deg, #0f172a 0%, #1e293b 100%)', padding: '1.5rem 2rem', color: '#fff', position: 'relative', overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ background: 'rgba(255,255,255,0.1)', borderRadius: 12, padding: 10, flexShrink: 0 }}>
            <ShieldCheck size={26} color='#fff' />
          </div>
          <div>
            <div style={{ fontSize: '0.7rem', color: '#64748b', marginBottom: 2 }}>India's DPDP Act Compliance Tool</div>
            <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 900, lineHeight: 1.2 }}>DPDP Kavach</h1>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 20, marginTop: 14, flexWrap: 'wrap' }}>
          {[['22', 'Languages'], ['10', 'Sectors'], ['₹250Cr', 'Max Fine'], ['5 Docs', 'Kit']].map(([v, l]) => (
            <div key={l} style={{ textAlign: 'center' }}>
              <div style={{ fontSize: '1.2rem', fontWeight: 900, color: '#38bdf8' }}>{v}</div>
              <div style={{ fontSize: '0.68rem', color: '#64748b' }}>{l}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ padding: '1rem 2rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
          {[
            [Upload, 'Upload Schema', 'SQL · CSV · JSON'],
            [ShieldCheck, 'Classify PII', 'Auto-detect fields'],
            [Download, 'Get Compliance Kit', 'Download in minutes'],
          ].map(([Icon, title, sub], i) => (
            <div key={i} style={{ border: '1px solid #e2e8f0', borderRadius: 10, padding: '10px 12px', textAlign: 'center' }}>
              <div style={{ background: '#f0fdf4', borderRadius: 8, width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '0 auto 6px' }}>
                <Icon size={15} color='#15803d' />
              </div>
              <div style={{ fontWeight: 800, fontSize: '0.8rem' }}>{title}</div>
              <div style={{ fontSize: '0.7rem', color: '#64748b' }}>{sub}</div>
            </div>
          ))}
        </div>
      </div>

      <div style={{ borderTop: '1px solid #e2e8f0', padding: '0.8rem 2rem', background: '#fef2f2', display: 'flex', alignItems: 'center', gap: 10 }}>
        <AlertTriangle size={13} color='#991b1b' />
        <span style={{ fontSize: '0.8rem', color: '#991b1b' }}>
          <strong>Non-compliance penalty:</strong> Up to ₹250 Crore under the DPDP Act, 2023
        </span>
      </div>

      <div style={{ borderTop: '1px solid #e2e8f0', padding: '1rem 2rem', textAlign: 'center' }}>
        <button onClick={onStart} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, background: '#0f172a', color: '#fff', border: 'none', borderRadius: 8, padding: '9px 20px', fontSize: '0.85rem', fontWeight: 800, cursor: 'pointer' }}>
          Start Scan <ArrowRight size={14} />
        </button>
      </div>
    </div>
  )
}

export default function App() {
  const [businessName, setBusinessName] = useState('My Organization')
  const [sector, setSector] = useState('fintech')
  const [language, setLanguage] = useState('English')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [translating, setTranslating] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [translatedResult, setTranslatedResult] = useState(null)
  const [grievanceLog, setGrievanceLog] = useState([])
  const [activeSection, setActiveSection] = useState('inventory')
  const [showLanding, setShowLanding] = useState(true)
  const [chatOpen, setChatOpen] = useState(false)
  const [chatMessages, setChatMessages] = useState([])
  const [chatInput, setChatInput] = useState('')
  const [chatLoading, setChatLoading] = useState(false)
  const fileRef = useRef(null)
  const chatBottomRef = useRef(null)

  const sections = [
    ['inventory', 'Data Inventory'],
    ['obligations', 'Obligations'],
    ['conflicts', 'Conflicts'],
    ['artifacts', 'Artifacts'],
    ['grievance', 'Grievance'],
  ]

  const displayResult = translatedResult || result
  const metrics = displayResult?.metrics

  async function runScan() {
    if (!file) { setError('Upload a .sql/.csv/.json schema file first'); return }
    setLoading(true); setError('')
    const fd = new FormData()
    fd.append('file', file)
    fd.append('business_name', businessName)
    fd.append('sector', sector)
    fd.append('language', language)
    try {
      const res = await fetch('/api/scan', { method: 'POST', body: fd })
      if (!res.ok) {
        const p = await res.json().catch(() => ({}))
        throw new Error(p.detail || 'Scan failed')
      }
      const data = await res.json()
      setResult(data)
      setTranslatedResult(null)
      setActiveSection('inventory')
      setShowLanding(false)
    } catch (e) {
      setError(e.message || 'Scan failed')
    } finally {
      setLoading(false)
    }
  }

  async function switchLanguage(lang) {
    setLanguage(lang)
    if (!result || lang === 'English') {
      setTranslatedResult(null)
      return
    }
    setTranslating(true)
    try {
      const ctrl = new AbortController()
      const tid = setTimeout(() => ctrl.abort(), 15000)
      const fetchOne = (data) =>
        fetch('/api/translate', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ language: lang, data }),
          signal: ctrl.signal,
        }).then(r => r.json())
      const [inv, obls, conf] = await Promise.all([
        fetchOne(result.classified_elements),
        fetchOne(result.obligations),
        fetchOne(result.conflicts),
      ])
      clearTimeout(tid)
      setTranslatedResult({
        ...result,
        classified_elements: inv.translated || result.classified_elements,
        obligations: obls.translated || result.obligations,
        conflicts: conf.translated || result.conflicts,
      })
    } catch {
      setTranslatedResult(null)
    } finally {
      setTranslating(false)
    }
  }

  useEffect(() => {
    if (!result) return
    fetch('/api/grievance')
      .then(r => r.json())
      .then(p => setGrievanceLog(p.items || []))
      .catch(() => {})
  }, [result])

  const suggestedPrompts = (() => {
    if (!result || chatMessages.length > 0) return []
    const hasObl = result.obligations.length > 0
    const hasConf = result.conflicts.length > 0
    const p = [
      'What PII fields did you find?',
      'How do I reduce my penalty exposure?',
    ]
    if (hasObl) p.splice(1, 0, 'What are my key obligations?')
    if (hasConf) p.splice(p.length - 1, 0, 'What conflicts should I worry about?')
    return p
  })()

  async function sendMessage(text) {
    if (!text.trim() || !result) return
    const userMsg = { role: 'user', content: text.trim() }
    setChatMessages(prev => [...prev, userMsg])
    setChatInput('')
    setChatLoading(true)
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: text.trim(),
          conversation_history: chatMessages.slice(-10),
          scan_context: {
            classified_elements: result.classified_elements,
            obligations: result.obligations,
            conflicts: result.conflicts,
            sector: result.sector || sector,
            metrics: result.metrics || {},
          },
          language,
        }),
      })
      const data = await res.json()
      setChatMessages(prev => [...prev, { role: 'assistant', content: data.reply || 'Sorry, no response.' }])
    } catch {
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I couldn\'t reach the assistant. Please try again.' }])
    } finally {
      setChatLoading(false)
    }
  }

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [chatMessages, chatOpen])

  const exposure = metrics?.penalty_exposure_current_crore
  const exposurePct = exposure != null ? Math.min(1, exposure / 250) : 0

  if (showLanding && !result) {
    return (
      <div style={{ minHeight: '100vh', background: '#f6f8fc', fontFamily: "'Inter','SF Pro Text','Segoe UI',sans-serif", color: '#0f172a' }}>
        <header style={{ background: '#fff', borderBottom: '1px solid #e2e8f0', padding: '0 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0.9rem 0' }}>
            <ShieldCheck size={18} color='#0f172a' />
            <div>
              <div style={{ fontSize: '0.95rem', fontWeight: 800, lineHeight: 1.2 }}>DPDP Kavach</div>
              <div style={{ fontSize: '0.7rem', color: '#64748b' }}>DPDP Act Compliance Scanner</div>
            </div>
          </div>
          <button onClick={() => setShowLanding(false)} style={{ background: '#0f172a', color: '#fff', border: 'none', borderRadius: 8, padding: '7px 14px', fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer' }}>
            Open Scanner →
          </button>
        </header>
        <div style={{ maxWidth: 1100, margin: '0 auto', padding: '1.5rem 1rem' }}>
          <LandingPage onStart={() => setShowLanding(false)} />
        </div>
      </div>
    )
  }

  return (
    <div style={{ minHeight: '100vh', background: '#f6f8fc', fontFamily: "'Inter','SF Pro Text','Segoe UI',sans-serif", color: '#0f172a' }}>
      <header style={{ background: '#fff', borderBottom: '1px solid #e2e8f0', padding: '0 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '0.9rem 0' }}>
          <ShieldCheck size={18} color='#0f172a' />
          <div>
            <div style={{ fontSize: '0.95rem', fontWeight: 800, lineHeight: 1.2 }}>DPDP Kavach</div>
            <div style={{ fontSize: '0.7rem', color: '#64748b' }}>DPDP Act Compliance Scanner</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <select value={language} onChange={e => switchLanguage(e.target.value)} disabled={!result || translating} style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: '6px 10px', fontSize: '0.8rem', cursor: result ? 'pointer' : 'not-allowed', opacity: result ? 1 : 0.5 }}>
            {LANGUAGES.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
          </select>
          {translating && <span style={{ fontSize: '0.75rem', color: '#64748b' }}>Translating...</span>}
          {result && (
            <a href={result.download_url} style={{ display: 'flex', alignItems: 'center', gap: 5, background: '#0f172a', color: '#fff', borderRadius: 8, padding: '7px 14px', fontSize: '0.8rem', fontWeight: 700, textDecoration: 'none' }}>
              <Download size={13} /> Kit
            </a>
          )}
        </div>
      </header>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '1.2rem 1rem', display: 'grid', gridTemplateColumns: result ? '280px 1fr' : '1fr', gap: '1rem', alignItems: 'start' }}>
        {/* Left Panel */}
        <div style={{ background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', padding: '1rem', boxShadow: '0 1px 3px rgba(15,23,42,0.06)' }}>
          <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#64748b', fontWeight: 700, marginBottom: 10 }}>Scan Configuration</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: 3 }}>Business Name</div>
              <input value={businessName} onChange={e => setBusinessName(e.target.value)} style={{ width: '100%', border: '1px solid #e2e8f0', borderRadius: 8, padding: '7px 10px', fontSize: '0.85rem' }} />
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: 3 }}>Industry Sector</div>
              <select value={sector} onChange={e => setSector(e.target.value)} style={{ width: '100%', border: '1px solid #e2e8f0', borderRadius: 8, padding: '7px 10px', fontSize: '0.85rem' }}>
                {SECTORS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
              </select>
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: 3 }}>Output Language</div>
              <select value={language} onChange={e => switchLanguage(e.target.value)} style={{ width: '100%', border: '1px solid #e2e8f0', borderRadius: 8, padding: '7px 10px', fontSize: '0.85rem' }}>
                {LANGUAGES.map(([code, name]) => <option key={code} value={code}>{name}</option>)}
              </select>
            </div>
            <div>
              <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: 3 }}>Schema File</div>
              <label style={{ display: 'block', border: '2px dashed #e2e8f0', borderRadius: 8, padding: '12px 10px', textAlign: 'center', cursor: 'pointer', fontSize: '0.82rem', color: '#64748b' }}>
                <Upload size={14} style={{ display: 'block', margin: '0 auto 4px' }} />
                {file ? file.name : 'Click to upload .sql / .csv / .json'}
                <input ref={fileRef} type="file" accept=".sql,.csv,.json" onChange={e => setFile(e.target.files?.[0] || null)} style={{ display: 'none' }} />
              </label>
            </div>
            <button onClick={runScan} disabled={loading} style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 6, background: '#0f172a', color: '#fff', border: 'none', borderRadius: 8, padding: '9px', fontSize: '0.85rem', fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer', opacity: loading ? 0.65 : 1 }}>
              <ShieldCheck size={13} /> {loading ? 'Scanning...' : 'Run Compliance Scan'}
            </button>
          </div>

          {error && (
            <div style={{ marginTop: 8, display: 'flex', alignItems: 'center', gap: 5, background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, padding: '7px 9px', fontSize: '0.8rem', color: '#991b1b' }}>
              <AlertTriangle size={12} /> {error}
            </div>
          )}

          {result && (
            <div style={{ marginTop: 14, borderTop: '1px solid #e2e8f0', paddingTop: 12 }}>
              <div style={{ fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.06em', color: '#64748b', fontWeight: 700, marginBottom: 10 }}>Risk Overview</div>
              <div style={{ background: '#f9fafb', borderRadius: 8, padding: '10px', marginBottom: 10 }}>
                <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: 2 }}>Est. Penalty Exposure</div>
                <div style={{ fontSize: '1.4rem', fontWeight: 800 }}>{exposure != null ? `₹${exposure} Cr` : '—'}</div>
              </div>
              <ScoreBar value={exposurePct} label="Risk Score" color="#ef4444" />
              <ScoreBar value={metrics?.grounding_score} label="Grounding Confidence" />
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 6, fontSize: '0.75rem' }}>
                <div style={{ textAlign: 'center', background: '#f0f9ff', borderRadius: 6, padding: '6px 4px' }}>
                  <div style={{ fontWeight: 800 }}>{metrics?.fields_scanned ?? '—'}</div>
                  <div style={{ color: '#64748b' }}>Fields</div>
                </div>
                <div style={{ textAlign: 'center', background: '#f0fdf4', borderRadius: 6, padding: '6px 4px' }}>
                  <div style={{ fontWeight: 800 }}>{metrics?.obligation_count ?? '—'}</div>
                  <div style={{ color: '#64748b' }}>Obligations</div>
                </div>
                <div style={{ textAlign: 'center', background: '#fff7ed', borderRadius: 6, padding: '6px 4px' }}>
                  <div style={{ fontWeight: 800 }}>{metrics?.conflict_count ?? '—'}</div>
                  <div style={{ color: '#64748b' }}>Conflicts</div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Main Content */}
        {result ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.8rem' }}>
            <SectionNav sections={sections} active={activeSection} onSelect={setActiveSection} result={displayResult} />

            {/* Data Inventory */}
            {activeSection === 'inventory' && (
              <div style={{ background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', padding: '1rem', boxShadow: '0 1px 3px rgba(15,23,42,0.06)' }}>
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: '0.95rem', fontWeight: 800 }}>Data Inventory</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>PII-classified fields — {displayResult.classified_elements.length} total</div>
                </div>
                <DataTable
                  rows={displayResult.classified_elements}
                  columns={[['column_name', 'Column'], ['table_name', 'Table'], ['pii_category', 'Category'], ['purpose', 'Purpose']]}
                />
              </div>
            )}

            {/* Obligations */}
            {activeSection === 'obligations' && (
              <div style={{ background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', padding: '1rem', boxShadow: '0 1px 3px rgba(15,23,42,0.06)' }}>
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: '0.95rem', fontWeight: 800 }}>DPDP Obligations</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Applicable sections triggered by your schema</div>
                </div>
                {displayResult.obligations.length === 0 ? (
                  <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b', fontSize: '0.85rem' }}>No obligations triggered</div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {displayResult.obligations.map((o, i) => (
                      <div key={i} style={{ border: '1px solid #e2e8f0', borderRadius: 10, padding: '10px 12px', borderLeft: '3px solid #0f172a' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          <span style={{ fontWeight: 700, fontSize: '0.82rem' }}>{o.obligation_type}</span>
                          <span style={{ fontSize: '0.7rem', background: '#f1f5f9', color: '#64748b', borderRadius: 4, padding: '1px 6px' }}>{o.section}</span>
                        </div>
                        <div style={{ fontSize: '0.8rem', color: '#475569', lineHeight: 1.5 }}>{o.description}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Conflicts */}
            {activeSection === 'conflicts' && (
              <div style={{ background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', padding: '1rem', boxShadow: '0 1px 3px rgba(15,23,42,0.06)' }}>
                <div style={{ marginBottom: 12 }}>
                  <div style={{ fontSize: '0.95rem', fontWeight: 800 }}>Cross-Law Conflicts</div>
                  <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Regulatory overlaps requiring attention</div>
                </div>
                {displayResult.conflicts.length === 0 ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '1.5rem', background: '#f0fdf4', borderRadius: 10, color: '#166534', fontSize: '0.85rem' }}>
                    <CheckCircle2 size={16} /> No conflicts detected for {displayResult.sector}
                  </div>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {displayResult.conflicts.map((c, i) => (
                      <div key={i} style={{ border: '1px solid #fecaca', background: '#fef2f2', borderRadius: 10, padding: '10px 12px', borderLeft: '3px solid #ef4444' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          <span style={{ fontWeight: 700, fontSize: '0.82rem', color: '#991b1b' }}>{c.regulation}</span>
                          <span style={{ fontSize: '0.7rem', background: '#fee2e2', color: '#991b1b', borderRadius: 4, padding: '1px 6px' }}>{c.dpdp_section}</span>
                        </div>
                        <div style={{ fontSize: '0.8rem', color: '#7f1d1d', lineHeight: 1.5, marginBottom: 4 }}>{c.summary}</div>
                        <div style={{ fontSize: '0.78rem', background: '#fff', borderRadius: 6, padding: '6px 8px', color: '#166534' }}>
                          → {c.resolution}
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Artifacts */}
            {activeSection === 'artifacts' && (
              <div style={{ background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', padding: '1rem', boxShadow: '0 1px 3px rgba(15,23,42,0.06)' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
                  <div>
                    <div style={{ fontSize: '0.95rem', fontWeight: 800 }}>Compliance Kit</div>
                    <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Generated legal documents ready for use</div>
                  </div>
                  <a href={result.download_url} style={{ display: 'flex', alignItems: 'center', gap: 5, background: '#0f172a', color: '#fff', borderRadius: 8, padding: '7px 14px', fontSize: '0.8rem', fontWeight: 700, textDecoration: 'none' }}>
                    <Download size={13} /> Download ZIP
                  </a>
                </div>
                <div style={{ display: 'grid', gap: 8 }}>
                  {Object.entries(result.artifacts || {}).map(([name, content]) => (
                    <details key={name} style={{ border: '1px solid #e2e8f0', borderRadius: 10, background: '#fff', overflow: 'hidden' }}>
                      <summary style={{ listStyle: 'none', cursor: 'pointer', padding: '8px 12px', fontSize: '0.84rem', fontWeight: 700, display: 'flex', alignItems: 'center', gap: 6, background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                        <FileText size={13} style={{ color: '#64748b' }} />
                        <span style={{ fontSize: '0.7rem', background: '#0f172a', color: '#fff', borderRadius: 4, padding: '1px 5px' }}>{name}</span>
                      </summary>
                      <pre style={{ margin: 0, padding: '12px', fontSize: '0.74rem', lineHeight: 1.5, background: '#0b1020', color: '#dbeafe', overflow: 'auto', maxHeight: 320 }}>
                        {content}
                      </pre>
                    </details>
                  ))}
                </div>
              </div>
            )}

            {/* Grievance */}
            {activeSection === 'grievance' && <GrievancePanel grievanceLog={grievanceLog} setGrievanceLog={setGrievanceLog} />}
          </div>
        ) : (
          <div style={{ background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', padding: '3rem 2rem', textAlign: 'center', boxShadow: '0 1px 3px rgba(15,23,42,0.06)' }}>
            <ShieldCheck size={28} style={{ margin: '0 auto 12px', display: 'block', color: '#e2e8f0' }} />
            <div style={{ fontSize: '1rem', fontWeight: 700, marginBottom: 6 }}>Ready to Scan</div>
            <div style={{ fontSize: '0.82rem', color: '#64748b', maxWidth: 360, margin: '0 auto', lineHeight: 1.6 }}>
              Fill in the left panel and upload your database schema (SQL, CSV, or JSON) to start your DPDP compliance assessment.
            </div>
            <button onClick={() => setShowLanding(true)} style={{ marginTop: 16, background: '#f1f5f9', color: '#475569', border: '1px solid #e2e8f0', borderRadius: 8, padding: '8px 16px', fontSize: '0.8rem', fontWeight: 700, cursor: 'pointer' }}>
              ← View Landing Page
            </button>
          </div>
        )}
      </div>

      {/* Floating Chat */}
      {result && (
        <>
          {!chatOpen && (
            <button
              onClick={() => setChatOpen(true)}
              style={{ position: 'fixed', bottom: 20, right: 20, width: 52, height: 52, borderRadius: '50%', background: '#0f172a', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 4px 16px rgba(15,23,42,0.3)', zIndex: 1000 }}
            >
              <MessageCircle size={22} color='#fff' />
            </button>
          )}
          {chatOpen && (
            <div style={{ position: 'fixed', bottom: 20, right: 20, width: 360, height: 500, background: '#fff', borderRadius: 16, boxShadow: '0 8px 32px rgba(15,23,42,0.18)', display: 'flex', flexDirection: 'column', zIndex: 1000, overflow: 'hidden' }}>
              <div style={{ background: '#0f172a', color: '#fff', padding: '12px 14px', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
                <div>
                  <div style={{ fontWeight: 800, fontSize: '0.88rem' }}>Compliance Assistant</div>
                  <div style={{ fontSize: '0.7rem', color: '#64748b' }}>{language}</div>
                </div>
                <button onClick={() => setChatOpen(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 4 }}>
                  <X size={16} color='#94a3b8' />
                </button>
              </div>

              <div style={{ flex: 1, overflowY: 'auto', padding: '12px 14px', display: 'flex', flexDirection: 'column', gap: 8 }}>
                {chatMessages.length === 0 && (
                  <div style={{ textAlign: 'center', marginTop: 8 }}>
                    <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: 10 }}>Ask about your compliance scan</div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                      {suggestedPrompts.map(p => (
                        <button key={p} onClick={() => sendMessage(p)} style={{ textAlign: 'left', background: '#f1f5f9', border: '1px solid #e2e8f0', borderRadius: 8, padding: '7px 10px', fontSize: '0.78rem', cursor: 'pointer', color: '#475569' }}>
                          {p}
                        </button>
                      ))}
                    </div>
                  </div>
                )}
                {chatMessages.map((m, i) => (
                  <div key={i} style={{ display: 'flex', justifyContent: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
                    <div style={{ maxWidth: '78%', padding: '7px 10px', borderRadius: m.role === 'user' ? '12px 12px 4px 12px' : '12px 12px 12px 4px', background: m.role === 'user' ? '#0f172a' : '#f1f5f9', color: m.role === 'user' ? '#fff' : '#0f172a', fontSize: '0.8rem', lineHeight: 1.5 }}>
                      {m.content}
                    </div>
                  </div>
                ))}
                {chatLoading && (
                  <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                    <div style={{ padding: '7px 10px', borderRadius: '12px 12px 12px 4px', background: '#f1f5f9', color: '#94a3b8', fontSize: '0.8rem' }}>
                      Thinking...
                    </div>
                  </div>
                )}
                <div ref={chatBottomRef} />
              </div>

              <div style={{ borderTop: '1px solid #e2e8f0', padding: '10px 12px', display: 'flex', gap: 8, flexShrink: 0 }}>
                <input
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(chatInput) } }}
                  placeholder='Ask about your compliance...'
                  disabled={chatLoading}
                  style={{ flex: 1, border: '1px solid #e2e8f0', borderRadius: 8, padding: '7px 10px', fontSize: '0.82rem', outline: 'none' }}
                />
                <button
                  onClick={() => sendMessage(chatInput)}
                  disabled={chatLoading || !chatInput.trim()}
                  style={{ background: '#0f172a', border: 'none', borderRadius: 8, width: 34, height: 34, display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: chatLoading ? 'not-allowed' : 'pointer', opacity: chatLoading ? 0.5 : 1 }}
                >
                  <Send size={14} color='#fff' />
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  )
}

function GrievancePanel({ grievanceLog, setGrievanceLog }) {
  const [requestType, setRequestType] = useState('Access')
  const [principalId, setPrincipalId] = useState('')
  const [details, setDetails] = useState('')
  const [saving, setSaving] = useState(false)

  async function submit(e) {
    e.preventDefault()
    if (!principalId.trim()) return
    setSaving(true)
    const item = { request_type: requestType, principal_id: principalId, details }
    try {
      await fetch('/api/grievance', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(item) })
    } catch {}
    setGrievanceLog(prev => [...prev, item])
    setPrincipalId(''); setDetails('')
    setSaving(false)
  }

  return (
    <div style={{ background: '#fff', borderRadius: 14, border: '1px solid #e2e8f0', padding: '1rem', boxShadow: '0 1px 3px rgba(15,23,42,0.06)' }}>
      <div style={{ marginBottom: 12 }}>
        <div style={{ fontSize: '0.95rem', fontWeight: 800 }}>Grievance & Data Requests</div>
        <div style={{ fontSize: '0.75rem', color: '#64748b' }}>Section 11–14 request intake — Access, Correction, Erasure, Nomination</div>
      </div>
      <form onSubmit={submit} style={{ display: 'grid', gridTemplateColumns: '1fr 1fr auto', gap: 8, marginBottom: 14 }}>
        <select value={requestType} onChange={e => setRequestType(e.target.value)} style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: '7px 10px', fontSize: '0.82rem' }}>
          {['Access', 'Correction', 'Erasure', 'Nomination', 'Complaint'].map(t => <option key={t}>{t}</option>)}
        </select>
        <input value={principalId} onChange={e => setPrincipalId(e.target.value)} placeholder="Data Principal ID" required style={{ border: '1px solid #e2e8f0', borderRadius: 8, padding: '7px 10px', fontSize: '0.82rem' }} />
        <button type="submit" disabled={saving} style={{ background: '#0f172a', color: '#fff', border: 'none', borderRadius: 8, padding: '7px 14px', fontSize: '0.82rem', fontWeight: 700, cursor: 'pointer', opacity: saving ? 0.65 : 1 }}>
          Submit
        </button>
      </form>
      <div style={{ border: '1px solid #e2e8f0', borderRadius: 10, overflow: 'auto', maxHeight: 260 }}>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead style={{ position: 'sticky', top: 0, background: '#f8fafc' }}>
            <tr>
              {['Type', 'Principal ID', 'Details'].map(h => (
                <th key={h} style={{ padding: '7px 10px', textAlign: 'left', fontSize: '0.72rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#64748b', fontWeight: 700, borderBottom: '1px solid #e2e8f0' }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {grievanceLog.length === 0 ? (
              <tr><td colSpan={3} style={{ padding: '16px 10px', textAlign: 'center', color: '#94a3b8', fontSize: '0.82rem' }}>No requests submitted yet</td></tr>
            ) : grievanceLog.map((r, i) => (
              <tr key={i} style={{ borderBottom: i < grievanceLog.length - 1 ? '1px solid #f1f5f9' : 'none' }}>
                <td style={{ padding: '7px 10px', fontSize: '0.82rem', fontWeight: 700 }}>{r.request_type}</td>
                <td style={{ padding: '7px 10px', fontSize: '0.82rem', color: '#64748b' }}>{r.principal_id}</td>
                <td style={{ padding: '7px 10px', fontSize: '0.82rem' }}>{r.details}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
