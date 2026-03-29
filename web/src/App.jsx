import { useEffect, useMemo, useState } from 'react'
import { AlertTriangle, Download, ShieldCheck, Upload } from 'lucide-react'

const tabs = [
  ['overview', 'Overview'],
  ['inventory', 'Inventory'],
  ['obligations', 'Obligations'],
  ['conflicts', 'Conflicts'],
  ['grounding', 'Grounding'],
  ['artifacts', 'Artifacts'],
  ['grievance', 'Grievance'],
  ['audit', 'Audit'],
]

function StatCard({ title, value, hint }) {
  return (
    <div className="stat-card">
      <div className="stat-title">{title}</div>
      <div className="stat-value">{value}</div>
      <div className="stat-hint">{hint}</div>
    </div>
  )
}

function SectionTitle({ title, subtitle }) {
  return (
    <div className="section-title">
      <h3>{title}</h3>
      {subtitle ? <p>{subtitle}</p> : null}
    </div>
  )
}

export default function App() {
  const [businessName, setBusinessName] = useState('Demo MSME')
  const [sector, setSector] = useState('fintech')
  const [language, setLanguage] = useState('English')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [grievanceLog, setGrievanceLog] = useState([])

  const metrics = result?.metrics
  const groundingPct = useMemo(() => Math.round((metrics?.grounding_score || 0) * 100), [metrics])
  const penaltyCurrent = useMemo(
    () => (metrics?.penalty_exposure_current_crore != null ? `${metrics.penalty_exposure_current_crore} Cr` : '--'),
    [metrics]
  )
  const mllibPredictions = useMemo(() => (metrics?.mllib_predictions != null ? metrics.mllib_predictions : '--'), [metrics])
  const groundingBackend = useMemo(() => (metrics?.grounding_backend ? metrics.grounding_backend : '--'), [metrics])
  const indianModel = useMemo(() => {
    if (!metrics) return '--'
    const name = metrics.indian_model_name || 'sarvam-m'
    const status = metrics.indian_model_status || 'unavailable'
    return `${name} (${status})`
  }, [metrics])

  async function runScan() {
    if (!file) {
      setError('Upload a .sql/.csv/.json file first')
      return
    }

    setLoading(true)
    setError('')
    const formData = new FormData()
    formData.append('file', file)
    formData.append('business_name', businessName)
    formData.append('sector', sector)
    formData.append('language', language)

    try {
      const res = await fetch('/api/scan', { method: 'POST', body: formData })
      if (!res.ok) {
        const payload = await res.json().catch(() => ({}))
        throw new Error(payload.detail || 'Scan failed')
      }
      const data = await res.json()
      setResult(data)
      setActiveTab('overview')
    } catch (e) {
      setError(e.message || 'Scan failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="page">
      <aside className="sidebar card">
        <div className="brand">
          <ShieldCheck size={16} />
          <div>
            <h2>DPDP Kavach</h2>
            <span>Compliance Workbench</span>
          </div>
        </div>

        <div className="form-stack">
          <label>Business Name</label>
          <input value={businessName} onChange={(e) => setBusinessName(e.target.value)} />

          <label>Sector</label>
          <select value={sector} onChange={(e) => setSector(e.target.value)}>
            <option value="fintech">Fintech</option>
            <option value="healthtech">Healthtech</option>
            <option value="general">General</option>
          </select>

          <label>Language</label>
          <select value={language} onChange={(e) => setLanguage(e.target.value)}>
            <option>English</option>
            <option>Hindi</option>
            <option>Marathi</option>
            <option>Tamil</option>
          </select>

          <label>Schema File</label>
          <input type="file" accept=".sql,.csv,.json" onChange={(e) => setFile(e.target.files?.[0] || null)} />

          <button className="primary" onClick={runScan} disabled={loading}>
            <Upload size={14} /> {loading ? 'Running Scan...' : 'Run Compliance Scan'}
          </button>
        </div>
      </aside>

      <main className="main">
        <header className="card header">
          <h1>Compliance Dashboard</h1>
          <p>Discover data, map obligations, detect conflicts, and generate compliance kit artifacts.</p>
        </header>

        {error ? (
          <div className="error-banner">
            <AlertTriangle size={15} /> {error}
          </div>
        ) : null}

        {result ? (
          <>
            <section className="stats-grid">
              <StatCard title="Fields Scanned" value={metrics.fields_scanned} hint="Data inventory size" />
              <StatCard title="Obligations" value={metrics.obligation_count} hint="Triggered legal controls" />
              <StatCard title="Conflicts" value={metrics.conflict_count} hint="Cross-law findings" />
              <StatCard title="Grounding" value={`${groundingPct}%`} hint="Claim confidence" />
              <StatCard title="Exposure" value={penaltyCurrent} hint="Estimated current risk" />
              <StatCard title="MLlib Overrides" value={mllibPredictions} hint="Purpose fields refined" />
              <StatCard title="Grounding Engine" value={groundingBackend} hint="Vector retrieval backend" />
              <StatCard title="Indian Model" value={indianModel} hint="Indic model runtime status" />
            </section>

            <section className="card tabs-shell">
              {tabs.map(([id, label]) => (
                <button
                  key={id}
                  className={activeTab === id ? 'tab active' : 'tab'}
                  onClick={() => setActiveTab(id)}
                >
                  {label}
                </button>
              ))}
            </section>

            <section className="card content">
              {activeTab === 'overview' && (
                <>
                  <SectionTitle title="Scan Summary" subtitle="core output snapshot" />
                  <div className="summary-grid">
                    <div className="summary-item"><b>Business:</b> {result.business_name}</div>
                    <div className="summary-item"><b>Sector:</b> {result.sector}</div>
                    <div className="summary-item"><b>Language:</b> {result.language}</div>
                    <div className="summary-item"><b>Scan ID:</b> {result.metrics.scan_id}</div>
                    <div className="summary-item"><b>Lakehouse Write:</b> {result.lakehouse_status || 'n/a'}</div>
                    <div className="summary-item"><b>Lakehouse Reason:</b> {result.lakehouse_reason || 'n/a'}</div>
                    <div className="summary-item"><b>ML Used:</b> {result.metrics.ml_model_used ? '✅ Yes' : '❌ No'}</div>
                    <div className="summary-item"><b>ML Engine:</b> {result.metrics.ml_engine || 'none'}</div>
                    <div className="summary-item"><b>MLlib Status:</b> {result.metrics.mllib_status || 'n/a'}</div>
                    <div className="summary-item"><b>Classifier Version:</b> {result.metrics.purpose_classifier_version || 'unknown'}</div>
                    <div className="summary-item"><b>MLflow Run:</b> {result.metrics.mlflow_run_id || 'unavailable'}</div>
                    <div className="summary-item"><b>Indian Model Used:</b> {String(result.metrics.indian_model_used)}</div>
                  </div>
                </>
              )}

              {activeTab === 'inventory' && (
                <>
                  <SectionTitle title="Classified Data Inventory" subtitle="table/column/category mapping" />
                  <Table
                    rows={result.classified_elements}
                    columns={[
                      ['table_name', 'Table'],
                      ['column_name', 'Column'],
                      ['pii_category', 'Category'],
                      ['purpose', 'Purpose'],
                      ['confidence', 'Confidence'],
                    ]}
                  />
                </>
              )}

              {activeTab === 'obligations' && (
                <>
                  <SectionTitle title="Triggered Obligations" subtitle="DPDP requirement list" />
                  <Table
                    rows={result.obligations}
                    columns={[
                      ['obligation_type', 'Type'],
                      ['section', 'Section'],
                      ['description', 'Description'],
                    ]}
                  />
                </>
              )}

              {activeTab === 'conflicts' && (
                <>
                  <SectionTitle title="Cross-Law Conflicts" subtitle="sector conflict detection" />
                  {result.conflicts.length === 0 ? (
                    <p className="muted">No conflicts detected for this scan.</p>
                  ) : (
                    <Table
                      rows={result.conflicts}
                      columns={[
                        ['regulation', 'Regulation'],
                        ['dpdp_section', 'DPDP Section'],
                        ['summary', 'Summary'],
                        ['resolution', 'Resolution'],
                      ]}
                    />
                  )}
                </>
              )}

              {activeTab === 'grounding' && (
                <>
                  <SectionTitle title="Grounding Confidence" subtitle="claim-level confidence report" />
                  <div className="progress-wrap">
                    <div className="progress"><span style={{ width: `${groundingPct}%` }} /></div>
                    <small>{groundingPct}% claims meet threshold ({result.grounding_report?.filter(r => r.is_grounded).length}/{result.grounding_report?.length || 0} claims)</small>
                  </div>
                  <div style={{ marginBottom: '8px', display: 'flex', gap: 16, fontSize: 12 }}>
                    <span><span style={{ color: '#22c55e' }}>●</span> Green: ≥0.60 (strong)</span>
                    <span><span style={{ color: '#f59e0b' }}>●</span> Amber: 0.40–0.59 (moderate)</span>
                    <span><span style={{ color: '#ef4444' }}>●</span> Red: &lt;0.40 (review)</span>
                  </div>
                  <div className="table-wrap">
                    <table>
                      <thead>
                        <tr>
                          <th>Tier</th>
                          <th>Claim</th>
                          <th>Score</th>
                          <th>Grounded</th>
                          <th>Matched Snippet</th>
                        </tr>
                      </thead>
                      <tbody>
                        {(result.grounding_report || []).map((row, idx) => (
                          <tr key={idx} style={{
                            backgroundColor: row.tier === 'green' ? 'rgba(34,197,94,0.07)' : row.tier === 'amber' ? 'rgba(245,158,11,0.07)' : 'rgba(239,68,68,0.05)'
                          }}>
                            <td><span style={{ color: row.tier === 'green' ? '#22c55e' : row.tier === 'amber' ? '#f59e0b' : '#ef4444', fontWeight: 600 }}>{row.tier?.toUpperCase()}</span></td>
                            <td>{String(row.claim)}</td>
                            <td>{row.score?.toFixed(3)}</td>
                            <td>{row.is_grounded ? '✓' : '✗'}</td>
                            <td style={{ fontSize: 11, color: '#666', maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{String(row.matched_snippet || '')}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </>
              )}

              {activeTab === 'artifacts' && (
                <>
                  <SectionTitle title="Compliance Kit" subtitle="generated legal artifacts" />
                  <a className="primary inline" href={result.download_url}>
                    <Download size={14} /> Download Compliance Kit (ZIP)
                  </a>
                  <div className="artifact-list">
                    {Object.entries(result.artifacts).map(([name, content]) => (
                      <details key={name} className="artifact-box">
                        <summary>{name}</summary>
                        <pre>{content}</pre>
                      </details>
                    ))}
                  </div>
                </>
              )}

              {activeTab === 'grievance' && (
                <GrievancePanel grievanceLog={grievanceLog} setGrievanceLog={setGrievanceLog} />
              )}

              {activeTab === 'audit' && (
                <>
                  <SectionTitle title="Audit JSON" subtitle="full scan payload" />
                  <pre className="audit-box">{JSON.stringify(result, null, 2)}</pre>
                </>
              )}
            </section>
          </>
        ) : (
          <section className="card empty">
            <ShieldCheck size={24} />
            <h3>Ready to Scan</h3>
            <p>Upload a schema and run the pipeline from the left panel.</p>
          </section>
        )}
      </main>
    </div>
  )
}

function Table({ rows, columns }) {
  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map(([, label]) => (
              <th key={label}>{label}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx}>
              {columns.map(([key]) => (
                <td key={key}>{String(row[key])}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function GrievancePanel({ grievanceLog, setGrievanceLog }) {
  const [requestType, setRequestType] = useState('Access')
  const [principalId, setPrincipalId] = useState('dp-001')
  const [details, setDetails] = useState('Please process this DPDP request.')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let active = true
    fetch('/api/grievance')
      .then((res) => res.json())
      .then((payload) => {
        if (active) {
          setGrievanceLog(payload.items || [])
        }
      })
      .catch(() => {})
    return () => {
      active = false
    }
  }, [setGrievanceLog])

  async function submit(e) {
    e.preventDefault()
    const item = { request_type: requestType, principal_id: principalId, details }
    setSaving(true)
    try {
      const res = await fetch('/api/grievance', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(item),
      })
      if (!res.ok) {
        throw new Error('Failed to save grievance')
      }
      setGrievanceLog((prev) => [...prev, item])
    } catch {
      setGrievanceLog((prev) => [...prev, item])
    } finally {
      setSaving(false)
    }
  }

  return (
    <>
      <SectionTitle title="Grievance Desk" subtitle="Section 11-14 request intake" />
      <form className="grievance-form" onSubmit={submit}>
        <select value={requestType} onChange={(e) => setRequestType(e.target.value)}>
          <option>Access</option>
          <option>Correction</option>
          <option>Erasure</option>
          <option>Nomination</option>
          <option>Complaint</option>
        </select>
        <input value={principalId} onChange={(e) => setPrincipalId(e.target.value)} placeholder="Data Principal ID" />
        <textarea value={details} onChange={(e) => setDetails(e.target.value)} rows={3} />
        <button className="primary inline" type="submit" disabled={saving}>
          {saving ? 'Saving...' : 'Submit Request'}
        </button>
      </form>

      <Table
        rows={grievanceLog}
        columns={[
          ['request_type', 'Type'],
          ['principal_id', 'Principal'],
          ['details', 'Details'],
        ]}
      />
    </>
  )
}
