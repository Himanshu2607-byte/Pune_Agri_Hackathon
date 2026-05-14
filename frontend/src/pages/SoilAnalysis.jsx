import { useState } from 'react';
import { FlaskConical, Sparkles, AlertTriangle, Leaf, Loader2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { analyzeSoilChatGPT } from '../utils/api';
import { setFeatureContext } from '../utils/featureContext';
import './SoilAnalysis.css';

const initialForm = {
  nitrogen: '',
  phosphorus: '',
  potassium: '',
  ph: '',
  moisture: '',
  organic_carbon: '',
  ec: '',
  // Micronutrients (ppm) — adapted from Himanshu's soil_health work
  phosphorus_ppm: '',
  sulfur: '',
  zinc: '',
  iron: '',
  manganese: '',
  copper: '',
  potassium_ppm: '',
  calcium: '',
  magnesium: '',
  sodium: '',
};

const opt = (v) => (v === '' ? null : Number(v));

export default function SoilAnalysis() {
  const [form, setForm] = useState(initialForm);
  const [report, setReport] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setReport('');
    setLoading(true);

    try {
      const payload = {
        nitrogen: Number(form.nitrogen),
        phosphorus: Number(form.phosphorus),
        potassium: Number(form.potassium),
        ph: Number(form.ph),
        moisture: Number(form.moisture),
        organic_carbon: opt(form.organic_carbon),
        ec: opt(form.ec),
        // Micronutrients
        phosphorus_ppm: opt(form.phosphorus_ppm),
        sulfur: opt(form.sulfur),
        zinc: opt(form.zinc),
        iron: opt(form.iron),
        manganese: opt(form.manganese),
        copper: opt(form.copper),
        potassium_ppm: opt(form.potassium_ppm),
        calcium: opt(form.calcium),
        magnesium: opt(form.magnesium),
        sodium: opt(form.sodium),
      };

      const data = await analyzeSoilChatGPT(payload);
      setReport(data.report || '');

      // Feed the report into the local chat assistant context
      setFeatureContext('soil_analysis', {
        inputs: payload,
        ai_report_summary: (data.report || '').slice(0, 800),
        report_source: 'ChatGPT',
      });
    } catch (err) {
      setError(err.message || 'Failed to fetch report. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="sa-page">
      <div className="page-header animate-fade-in-up">
        <div className="sa-header-left">
          <div className="sa-header-icon">
            <FlaskConical size={24} />
          </div>
          <div>
            <h1 className="heading-xl">Soil Health Analysis</h1>
            <p className="text-secondary" style={{ marginTop: 4 }}>
              Enter your soil test values and let AI generate a detailed agronomist report.
            </p>
          </div>
        </div>
      </div>

      <div className="sa-grid">
        {/* ── Form Card ──────────────────────────────── */}
        <form className="sa-form-card glass-card-static animate-fade-in-up" onSubmit={handleSubmit}>
          <h2 className="heading-md sa-section-title">🧪 Soil Test Inputs</h2>

          <div className="sa-fields-grid">
            <div className="sa-field">
              <label className="sa-label">Nitrogen (N) <span className="sa-unit">kg/ha</span></label>
              <input
                id="sa-nitrogen"
                className="sa-input"
                type="number"
                min="0"
                step="0.1"
                value={form.nitrogen}
                onChange={(e) => handleChange('nitrogen', e.target.value)}
                placeholder="e.g. 80"
                required
              />
            </div>

            <div className="sa-field">
              <label className="sa-label">Phosphorus (P) <span className="sa-unit">kg/ha</span></label>
              <input
                id="sa-phosphorus"
                className="sa-input"
                type="number"
                min="0"
                step="0.1"
                value={form.phosphorus}
                onChange={(e) => handleChange('phosphorus', e.target.value)}
                placeholder="e.g. 35"
                required
              />
            </div>

            <div className="sa-field">
              <label className="sa-label">Potassium (K) <span className="sa-unit">kg/ha</span></label>
              <input
                id="sa-potassium"
                className="sa-input"
                type="number"
                min="0"
                step="0.1"
                value={form.potassium}
                onChange={(e) => handleChange('potassium', e.target.value)}
                placeholder="e.g. 180"
                required
              />
            </div>

            <div className="sa-field">
              <label className="sa-label">Soil pH <span className="sa-unit">0–14</span></label>
              <input
                id="sa-ph"
                className="sa-input"
                type="number"
                min="0"
                max="14"
                step="0.1"
                value={form.ph}
                onChange={(e) => handleChange('ph', e.target.value)}
                placeholder="e.g. 6.8"
                required
              />
            </div>

            <div className="sa-field">
              <label className="sa-label">Moisture <span className="sa-unit">%</span></label>
              <input
                id="sa-moisture"
                className="sa-input"
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={form.moisture}
                onChange={(e) => handleChange('moisture', e.target.value)}
                placeholder="e.g. 48"
                required
              />
            </div>

            <div className="sa-field">
              <label className="sa-label">Organic Carbon <span className="sa-unit">% · Optional</span></label>
              <input
                id="sa-organic-carbon"
                className="sa-input"
                type="number"
                min="0"
                step="0.01"
                value={form.organic_carbon}
                onChange={(e) => handleChange('organic_carbon', e.target.value)}
                placeholder="Optional"
              />
            </div>

            <div className="sa-field sa-field-full">
              <label className="sa-label">Electrical Conductivity <span className="sa-unit">dS/m · Optional</span></label>
              <input
                id="sa-ec"
                className="sa-input"
                type="number"
                min="0"
                step="0.01"
                value={form.ec}
                onChange={(e) => handleChange('ec', e.target.value)}
                placeholder="Optional"
              />
            </div>

            {/* ── Micronutrients Section (from Himanshu's soil_health work) ── */}
            <div className="sa-field-full sa-micro-divider">
              <h3 className="sa-micro-title">🔬 Micronutrients &amp; Secondary Macronutrients <span className="sa-unit">ppm · All Optional</span></h3>
            </div>

            <div className="sa-field">
              <label className="sa-label">Phosphorus (P) <span className="sa-unit">ppm</span></label>
              <input className="sa-input" type="number" min="0" step="0.1"
                value={form.phosphorus_ppm}
                onChange={(e) => handleChange('phosphorus_ppm', e.target.value)}
                placeholder="Optional" />
            </div>

            <div className="sa-field">
              <label className="sa-label">Sulfur (S) <span className="sa-unit">ppm</span></label>
              <input className="sa-input" type="number" min="0" step="0.1"
                value={form.sulfur}
                onChange={(e) => handleChange('sulfur', e.target.value)}
                placeholder="Optional" />
            </div>

            <div className="sa-field">
              <label className="sa-label">Zinc (Zn) <span className="sa-unit">ppm</span></label>
              <input className="sa-input" type="number" min="0" step="0.01"
                value={form.zinc}
                onChange={(e) => handleChange('zinc', e.target.value)}
                placeholder="Optional" />
            </div>

            <div className="sa-field">
              <label className="sa-label">Iron (Fe) <span className="sa-unit">ppm</span></label>
              <input className="sa-input" type="number" min="0" step="0.1"
                value={form.iron}
                onChange={(e) => handleChange('iron', e.target.value)}
                placeholder="Optional" />
            </div>

            <div className="sa-field">
              <label className="sa-label">Manganese (Mn) <span className="sa-unit">ppm</span></label>
              <input className="sa-input" type="number" min="0" step="0.1"
                value={form.manganese}
                onChange={(e) => handleChange('manganese', e.target.value)}
                placeholder="Optional" />
            </div>

            <div className="sa-field">
              <label className="sa-label">Copper (Cu) <span className="sa-unit">ppm</span></label>
              <input className="sa-input" type="number" min="0" step="0.01"
                value={form.copper}
                onChange={(e) => handleChange('copper', e.target.value)}
                placeholder="Optional" />
            </div>

            <div className="sa-field">
              <label className="sa-label">Potassium (K) <span className="sa-unit">ppm</span></label>
              <input className="sa-input" type="number" min="0" step="1"
                value={form.potassium_ppm}
                onChange={(e) => handleChange('potassium_ppm', e.target.value)}
                placeholder="Optional" />
            </div>

            <div className="sa-field">
              <label className="sa-label">Calcium (Ca) <span className="sa-unit">ppm</span></label>
              <input className="sa-input" type="number" min="0" step="1"
                value={form.calcium}
                onChange={(e) => handleChange('calcium', e.target.value)}
                placeholder="Optional" />
            </div>

            <div className="sa-field">
              <label className="sa-label">Magnesium (Mg) <span className="sa-unit">ppm</span></label>
              <input className="sa-input" type="number" min="0" step="0.1"
                value={form.magnesium}
                onChange={(e) => handleChange('magnesium', e.target.value)}
                placeholder="Optional" />
            </div>

            <div className="sa-field">
              <label className="sa-label">Sodium (Na) <span className="sa-unit">ppm</span></label>
              <input className="sa-input" type="number" min="0" step="0.1"
                value={form.sodium}
                onChange={(e) => handleChange('sodium', e.target.value)}
                placeholder="Optional" />
            </div>
          </div>

          <div className="sa-submit-wrap">
            <button id="sa-submit-btn" className="btn btn-primary sa-submit-btn" type="submit" disabled={loading}>
              {loading ? (
                <>
                  <Loader2 size={18} className="sa-spinner" />
                  Analyzing…
                </>
              ) : (
                <>
                  <Sparkles size={18} />
                  ✨ Analyze Soil &amp; Generate Report
                </>
              )}
            </button>
          </div>
        </form>

        {/* ── Output Column ─────────────────────────── */}
        <div className="sa-output-wrap">
          {error && (
            <div className="sa-error-card glass-card-static animate-fade-in-up">
              <AlertTriangle size={22} color="var(--status-critical)" />
              <span>{error}</span>
            </div>
          )}

          {!report && !error && !loading && (
            <div className="sa-placeholder glass-card-static animate-fade-in-up">
              <Leaf size={40} color="var(--text-tertiary)" />
              <p className="heading-md">Your AI Report Will Appear Here</p>
              <p className="text-secondary">Fill in your soil test values and click &quot;Analyze&quot; to generate a detailed agronomist report powered by ChatGPT.</p>
            </div>
          )}

          {loading && (
            <div className="sa-placeholder glass-card-static animate-fade-in-up">
              <Loader2 size={40} className="sa-spinner" color="var(--accent-primary)" />
              <p className="heading-md">Generating AI Report…</p>
              <p className="text-secondary">Our AI agronomist is analyzing your soil data. This may take a few seconds.</p>
            </div>
          )}

          {report && (
            <div className="sa-report-card glass-card-static animate-fade-in-up">
              <h3 className="heading-md sa-report-title">📋 Agronomist Report</h3>
              <div className="sa-report-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>
                  {report}
                </ReactMarkdown>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
