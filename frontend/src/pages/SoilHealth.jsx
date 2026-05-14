import { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { FlaskConical, Sparkles, AlertTriangle, Droplets, Leaf } from 'lucide-react';
import { analyzeSoilHealth } from '../utils/api';
import { setFeatureContext } from '../utils/featureContext';
import './SoilHealth.css';

const initialForm = {
  nitrogen: 80,
  phosphorus: 35,
  potassium: 180,
  ph: 6.8,
  moisture: 48,
  organic_carbon: '',
  ec: '',
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

const statusClassMap = {
  healthy: 'badge-healthy',
  moderate: 'badge-warning',
  critical: 'badge-critical',
};

export default function SoilHealth() {
  const { t, lang } = useLanguage();
  const [form, setForm] = useState(initialForm);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleChange = (key, value) => {
    setForm((prev) => ({ ...prev, [key]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const payload = {
        nitrogen: Number(form.nitrogen),
        phosphorus: Number(form.phosphorus),
        potassium: Number(form.potassium),
        ph: Number(form.ph),
        moisture: Number(form.moisture),
        organic_carbon: form.organic_carbon === '' ? null : Number(form.organic_carbon),
        ec: form.ec === '' ? null : Number(form.ec),
        phosphorus_ppm: form.phosphorus_ppm === '' ? null : Number(form.phosphorus_ppm),
        sulfur: form.sulfur === '' ? null : Number(form.sulfur),
        zinc: form.zinc === '' ? null : Number(form.zinc),
        iron: form.iron === '' ? null : Number(form.iron),
        manganese: form.manganese === '' ? null : Number(form.manganese),
        copper: form.copper === '' ? null : Number(form.copper),
        potassium_ppm: form.potassium_ppm === '' ? null : Number(form.potassium_ppm),
        calcium: form.calcium === '' ? null : Number(form.calcium),
        magnesium: form.magnesium === '' ? null : Number(form.magnesium),
        sodium: form.sodium === '' ? null : Number(form.sodium),
        lang,
      };

      const data = await analyzeSoilHealth(payload);
      setResult(data);
      setFeatureContext('soil_health', {
        health_status: data.health_status,
        score: data.score,
        reasons: data.reasons,
        solutions: data.solutions,
        suggested_crops: data.suggested_crops,
        report_source: data.report_source,
      });
    } catch (err) {
      setError(err.message || t('soil_error_default'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="soil-page">
      <div className="page-header animate-fade-in-up">
        <div className="soil-header-left">
          <div className="soil-header-icon">
            <FlaskConical size={24} />
          </div>
          <div>
            <h1 className="heading-xl">{t('soil_title')}</h1>
            <p className="text-secondary" style={{ marginTop: 4 }}>{t('soil_subtitle')}</p>
          </div>
        </div>
      </div>

      <div className="soil-grid">
        <form className="soil-form-card glass-card-static animate-fade-in-up" onSubmit={handleSubmit}>
          <h2 className="heading-md soil-section-title">{t('soil_input_title')}</h2>

          <div className="soil-fields-grid">
            <div className="soil-field">
              <label className="soil-label">{t('soil_field_nitrogen')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                step="0.1"
                value={form.nitrogen}
                onChange={(e) => handleChange('nitrogen', e.target.value)}
                required
              />
            </div>

            <div className="soil-field">
              <label className="soil-label">{t('soil_field_phosphorus')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                step="0.1"
                value={form.phosphorus}
                onChange={(e) => handleChange('phosphorus', e.target.value)}
                required
              />
            </div>

            <div className="soil-field">
              <label className="soil-label">{t('soil_field_potassium')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                step="0.1"
                value={form.potassium}
                onChange={(e) => handleChange('potassium', e.target.value)}
                required
              />
            </div>

            <div className="soil-field">
              <label className="soil-label">{t('soil_field_ph')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                max="14"
                step="0.1"
                value={form.ph}
                onChange={(e) => handleChange('ph', e.target.value)}
                required
              />
            </div>

            <div className="soil-field">
              <label className="soil-label">{t('soil_field_moisture')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                max="100"
                step="0.1"
                value={form.moisture}
                onChange={(e) => handleChange('moisture', e.target.value)}
                required
              />
            </div>

            <div className="soil-field">
              <label className="soil-label">{t('soil_field_organic_carbon')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                step="0.01"
                value={form.organic_carbon}
                onChange={(e) => handleChange('organic_carbon', e.target.value)}
                placeholder={t('soil_optional')}
              />
            </div>

            <div className="soil-field soil-field-full">
              <label className="soil-label">{t('soil_field_ec')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                step="0.01"
                value={form.ec}
                onChange={(e) => handleChange('ec', e.target.value)}
                placeholder={t('soil_optional')}
              />
            </div>

            {/* Micronutrients Section */}
            <div style={{ gridColumn: '1 / -1', marginTop: '12px', paddingTop: '12px', borderTop: '1px solid var(--border-light)' }}>
              <h3 style={{ fontSize: '0.95rem', fontWeight: 600, marginBottom: '8px', opacity: 0.8 }}>{t('soil_micronutrients_title')}</h3>
            </div>

            <div className="soil-field">
              <label className="soil-label">{t('soil_field_phosphorus_ppm')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                step="0.1"
                value={form.phosphorus_ppm}
                onChange={(e) => handleChange('phosphorus_ppm', e.target.value)}
                placeholder={t('soil_optional')}
              />
            </div>

            <div className="soil-field">
              <label className="soil-label">{t('soil_field_sulfur')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                step="0.1"
                value={form.sulfur}
                onChange={(e) => handleChange('sulfur', e.target.value)}
                placeholder={t('soil_optional')}
              />
            </div>

            <div className="soil-field">
              <label className="soil-label">{t('soil_field_zinc')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                step="0.01"
                value={form.zinc}
                onChange={(e) => handleChange('zinc', e.target.value)}
                placeholder={t('soil_optional')}
              />
            </div>

            <div className="soil-field">
              <label className="soil-label">{t('soil_field_iron')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                step="0.1"
                value={form.iron}
                onChange={(e) => handleChange('iron', e.target.value)}
                placeholder={t('soil_optional')}
              />
            </div>

            <div className="soil-field">
              <label className="soil-label">{t('soil_field_manganese')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                step="0.1"
                value={form.manganese}
                onChange={(e) => handleChange('manganese', e.target.value)}
                placeholder={t('soil_optional')}
              />
            </div>

            <div className="soil-field">
              <label className="soil-label">{t('soil_field_copper')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                step="0.01"
                value={form.copper}
                onChange={(e) => handleChange('copper', e.target.value)}
                placeholder={t('soil_optional')}
              />
            </div>

            <div className="soil-field">
              <label className="soil-label">{t('soil_field_potassium_ppm')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                step="0.1"
                value={form.potassium_ppm}
                onChange={(e) => handleChange('potassium_ppm', e.target.value)}
                placeholder={t('soil_optional')}
              />
            </div>

            <div className="soil-field">
              <label className="soil-label">{t('soil_field_calcium')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                step="1"
                value={form.calcium}
                onChange={(e) => handleChange('calcium', e.target.value)}
                placeholder={t('soil_optional')}
              />
            </div>

            <div className="soil-field">
              <label className="soil-label">{t('soil_field_magnesium')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                step="0.1"
                value={form.magnesium}
                onChange={(e) => handleChange('magnesium', e.target.value)}
                placeholder={t('soil_optional')}
              />
            </div>

            <div className="soil-field soil-field-full">
              <label className="soil-label">{t('soil_field_sodium')}</label>
              <input
                className="soil-input"
                type="number"
                min="0"
                step="0.1"
                value={form.sodium}
                onChange={(e) => handleChange('sodium', e.target.value)}
                placeholder={t('soil_optional')}
              />
            </div>
          </div>

          <div className="soil-submit-wrap">
            <button className="btn btn-primary" type="submit" disabled={loading}>
              <Sparkles size={18} />
              {loading ? t('soil_generating') : t('soil_generate_report')}
            </button>
          </div>
        </form>

        <div className="soil-output-wrap">
          {error && (
            <div className="soil-error-card glass-card-static animate-fade-in-up">
              <AlertTriangle size={22} color="var(--status-critical)" />
              <span>{error}</span>
            </div>
          )}

          {!result && !error && (
            <div className="soil-placeholder glass-card-static animate-fade-in-up">
              <Leaf size={40} color="var(--text-tertiary)" />
              <p className="heading-md">{t('soil_placeholder_title')}</p>
              <p className="text-secondary">{t('soil_placeholder_desc')}</p>
            </div>
          )}

          {result && (
            <div className="soil-report-panel animate-fade-in-up">
              <div className="soil-summary glass-card-static">
                <div className="soil-summary-top">
                  <span className={`badge ${statusClassMap[result.health_status_code] || 'badge-warning'}`}>
                    {result.health_status}
                  </span>
                  <span className="soil-score">{result.score}/100</span>
                </div>

                <div className="soil-source-row">
                  <Droplets size={14} />
                  <span>{result.report_source === 'ai' ? t('soil_source_ai') : t('soil_source_local')}</span>
                </div>
              </div>

              <div className="soil-sections-grid">
                <section className="soil-section glass-card-static">
                  <h3 className="heading-md">{t('soil_reasons_title')}</h3>
                  <ul className="soil-list">
                    {result.reasons.map((item, i) => (
                      <li key={`${item}-${i}`}>{item}</li>
                    ))}
                  </ul>
                </section>

                <section className="soil-section glass-card-static">
                  <h3 className="heading-md">{t('soil_solutions_title')}</h3>
                  <ul className="soil-list">
                    {result.solutions.map((item, i) => (
                      <li key={`${item}-${i}`}>{item}</li>
                    ))}
                  </ul>
                </section>
              </div>

              <section className="soil-section glass-card-static">
                <h3 className="heading-md">{t('soil_crops_title')}</h3>
                <div className="soil-crop-chips">
                  {result.suggested_crops.map((crop) => (
                    <span key={crop} className="soil-crop-chip">{crop}</span>
                  ))}
                </div>
              </section>

              <section className="soil-section glass-card-static">
                <h3 className="heading-md">{t('soil_metrics_title')}</h3>
                <div className="soil-metric-grid">
                  {Object.entries(result.metric_breakdown || {}).map(([key, metric]) => (
                    <div key={key} className="soil-metric-card">
                      <div className="soil-metric-top">
                        <span>{metric.label}</span>
                        <span className="soil-metric-score">{metric.score}</span>
                      </div>
                      <div className="soil-metric-meta">
                        <span>{metric.value} {metric.unit}</span>
                        <span>{metric.status}</span>
                      </div>
                      <div className="soil-metric-note">{metric.note}</div>
                    </div>
                  ))}
                </div>
              </section>

              <section className="soil-section glass-card-static">
                <h3 className="heading-md">{t('soil_report_title')}</h3>
                <p className="soil-report-text">{result.report}</p>
              </section>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
