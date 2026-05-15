import React, { useState, useEffect } from 'react';
import { 
  Activity, Droplet, Thermometer, Wind, AlertTriangle, 
  UploadCloud, File, CheckCircle, ArrowRight, Sprout, 
  Beaker, Clock, ShieldCheck, IndianRupee, Home, Leaf
} from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import * as api from '../utils/api';
import './SoilHealth.css';

const SoilHealth = () => {
  const { t } = useLanguage();
  const [activeScreen, setActiveScreen] = useState('dashboard'); // 'dashboard', 'upload', 'results'
  const [healthScore, setHealthScore] = useState(0);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [manualData, setManualData] = useState(null);

  // Animate meter on dashboard load
  useEffect(() => {
    if (activeScreen === 'dashboard') {
      const timer = setTimeout(() => {
        setHealthScore(68); // Example score for dashboard
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [activeScreen]);

  const getRotation = (score) => {
    return -45 + (score / 100) * 180;
  };

  const handleStartAnalysis = () => {
    setActiveScreen('upload');
  };

  const handleAnalysisComplete = (result, input) => {
    setAnalysisResult(result);
    setManualData(input);
    setActiveScreen('results');
  };

  return (
    <div className="bhoomi-container p-6 max-w-2xl mx-auto">
      {activeScreen === 'dashboard' && (
        <DashboardView 
          t={t} 
          healthScore={healthScore} 
          getRotation={getRotation} 
          onStart={handleStartAnalysis} 
        />
      )}
      
      {activeScreen === 'upload' && (
        <UploadView 
          t={t} 
          onComplete={handleAnalysisComplete} 
          onBack={() => setActiveScreen('dashboard')}
        />
      )}
      
      {activeScreen === 'results' && (
        <ResultsView 
          t={t} 
          result={analysisResult} 
          inputData={manualData}
          onReset={() => setActiveScreen('dashboard')}
        />
      )}
    </div>
  );
};

/* ── Dashboard View ──────────────────────────────────────────────────────── */
const DashboardView = ({ t, healthScore, getRotation, onStart }) => (
  <div className="animate-fade-in">
    <div className="flex items-center gap-2 mb-6">
      <Leaf className="text-success" size={28} />
      <h1 className="text-2xl font-bold text-gradient">{t('app_title_bhoomi')}</h1>
    </div>

    <div className="glass-card text-center">
      <h2 className="text-xl font-semibold mb-2">{t('overall_health_bhoomi')}</h2>
      <div className="meter-container">
        <div className="meter-circle"></div>
        <div 
          className="meter-value" 
          style={{ transform: `rotate(${getRotation(healthScore)}deg)` }}
        ></div>
        <div className="absolute inset-0 flex flex-col items-center justify-end pb-2" style={{position: 'absolute', bottom: '10px', left: '0', right: '0'}}>
          <span className="text-3xl font-bold text-success">{healthScore}</span>
          <span className="text-xs text-muted">/100</span>
        </div>
      </div>
      <p className="text-sm mt-4">
        {t('status_bhoomi')}: <span className="text-warning font-medium">{t('needs_attention_bhoomi')}</span>
      </p>
    </div>

    <div className="grid-2">
      <div className="glass-card flex flex-col items-center justify-center p-4">
        <Activity className="text-success mb-2" />
        <span className="text-2xl font-bold">Medium</span>
        <span className="text-xs text-muted mt-1">{t('fertility_level_bhoomi')}</span>
      </div>
      <div className="glass-card flex flex-col items-center justify-center p-4">
        <Droplet className="text-secondary mb-2" />
        <span className="text-2xl font-bold">Sodic</span>
        <span className="text-xs text-muted mt-1">{t('soil_type_bhoomi')}</span>
      </div>
    </div>

    <div className="glass-card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold flex items-center gap-2">
          <AlertTriangle className="text-warning" size={20} />
          {t('recent_alerts_bhoomi')}
        </h3>
      </div>
      <div className="bg-[#0f172a] rounded-lg p-3 border border-orange-500/20 mb-2">
        <p className="text-sm font-medium">High Salinity Detected</p>
        <p className="text-xs text-muted mt-1">pH level is 9.2. Gypsum application recommended.</p>
      </div>
    </div>
    
    <button className="btn-primary" onClick={onStart}>
      {t('analyze_new_bhoomi')}
    </button>
  </div>
);

/* ── Upload View ─────────────────────────────────────────────────────────── */
const UploadView = ({ t, onComplete, onBack }) => {
  const [isDragging, setIsDragging] = useState(false);
  const [file, setFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [manualData, setManualData] = useState({
    ph: 7.2, ec: 1.5, organic_carbon: 0.6,
    nitrogen: 200, phosphorus: 20, potassium: 150,
    cation_exchange_capacity: 20.0, exchangeable_sodium_percentage: 5.0,
    sulphur: 10.0, zinc: 0.6, iron: 4.5, copper: 0.2, manganese: 2.0, boron: 0.5
  });

  const handleUpload = async () => {
    if (!file) return;
    setIsUploading(true);
    try {
      const data = await api.uploadSoilReport(file);
      if (data.error) {
        alert(data.error);
        setIsUploading(false);
        return;
      }
      const result = await api.performBhoomiAnalysis(data);
      onComplete(result, data);
    } catch (error) {
      alert(error.message || "Analysis failed. Please check your connection.");
      console.error(error);
    } finally {
      setIsUploading(false);
    }
  };

  const handleManualSubmit = async (e) => {
    e.preventDefault();
    setIsUploading(true);
    try {
      const result = await api.performBhoomiAnalysis(manualData);
      onComplete(result, manualData);
    } catch (error) {
      alert("Analysis failed.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <button onClick={onBack} className="text-muted text-sm mb-4 flex items-center gap-1 hover:text-white transition-colors">
        <Home size={14} /> Back to Dashboard
      </button>
      <h2 className="text-xl font-bold mb-4">{t('upload_title_bhoomi')}</h2>
      
      {!showForm ? (
        <>
          <p className="text-sm text-muted mb-6">{t('upload_desc_bhoomi')}</p>
          <div 
            className={`upload-area ${isDragging ? 'drag-active' : ''}`}
            onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={(e) => { e.preventDefault(); setIsDragging(false); setFile(e.dataTransfer.files[0]); }}
            onClick={() => document.getElementById('file-upload').click()}
          >
            <input 
              type="file" id="file-upload" className="hidden" style={{display: 'none'}}
              onChange={(e) => setFile(e.target.files[0])}
            />
            {!file ? (
              <div className="flex flex-col items-center">
                <UploadCloud size={48} className="upload-icon" />
                <h3 className="font-semibold text-lg mb-1">Tap or Drag & Drop</h3>
                <p className="text-xs text-muted">Supports PDF, JPG, PNG, Excel</p>
              </div>
            ) : (
              <div className="flex flex-col items-center">
                <File size={48} className="text-success mb-2" />
                <h3 className="font-semibold text-lg mb-1">{file.name}</h3>
                <p className="text-xs text-success flex items-center gap-1 mt-2">
                  <CheckCircle size={14} /> Ready to analyze
                </p>
              </div>
            )}
          </div>

          <div className="glass-card text-center mt-6">
            <h3 className="text-sm font-semibold mb-2">Or Enter Manually:</h3>
            <button 
              className="btn-primary" 
              style={{background: 'transparent', border: '1px solid var(--primary)', color: 'var(--primary)'}}
              onClick={() => setShowForm(true)}
            >
              {t('enter_manual_bhoomi')}
            </button>
          </div>

          <button className="btn-primary mt-6" onClick={handleUpload} disabled={!file || isUploading}>
            {isUploading ? <span className="animate-pulse">{t('processing_bhoomi')}</span> : t('analyze_btn_bhoomi')}
          </button>
        </>
      ) : (
        <form onSubmit={handleManualSubmit} className="glass-card">
          <h3 className="font-bold mb-4 border-b border-white/10 pb-2">Soil Parameters</h3>
          <div className="grid grid-cols-2 gap-4 mb-4">
            {['ph', 'ec', 'organic_carbon', 'nitrogen', 'phosphorus', 'potassium'].map(field => (
              <div key={field}>
                <label className="block text-xs text-muted mb-1">{field.replace('_', ' ').toUpperCase()}</label>
                <input 
                  type="number" step="0.01" required 
                  value={manualData[field]} 
                  onChange={(e) => setManualData({...manualData, [field]: parseFloat(e.target.value)})}
                  className="w-full bg-[#0f172a] border border-white/20 rounded p-2 text-sm text-white"
                />
              </div>
            ))}
          </div>
          <div className="flex gap-2">
            <button type="button" onClick={() => setShowForm(false)} className="btn-primary flex-1 bg-gray-800 text-muted border border-white/10">Cancel</button>
            <button type="submit" disabled={isUploading} className="btn-primary flex-1">
              {isUploading ? <span className="animate-pulse">{t('processing_bhoomi')}</span> : t('analyze_btn_bhoomi')}
            </button>
          </div>
        </form>
      )}
    </div>
  );
};

/* ── Results View ────────────────────────────────────────────────────────── */
const ResultsView = ({ t, result, inputData, onReset }) => {
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState(null);

  useEffect(() => {
    if (result?.recommendations?.length > 0) {
      const verifyRec = async () => {
        setVerifying(true);
        try {
          const res = await api.verifyBhoomiRecommendation(t(result.recommendations[0].action + '_bhoomi'));
          setVerificationResult(res);
        } catch (e) { console.error(e); }
        finally { setVerifying(false); }
      };
      verifyRec();
    }
  }, [result]);

  if (!result) return null;

  return (
    <div className="animate-fade-in pb-8">
      <h2 className="text-2xl font-bold mb-6">{t('results_title_bhoomi')}</h2>
      
      <div className="grid-2">
        <div className="glass-card">
          <p className="text-xs text-muted">{t('overall_health_bhoomi')}</p>
          <div className="text-3xl font-bold text-success mt-1">{result.health_score}</div>
        </div>
        <div className="glass-card">
          <p className="text-xs text-muted">{t('soil_type_bhoomi')}</p>
          <div className="text-lg font-bold text-warning mt-1 leading-tight">{t(result.soil_type + '_bhoomi') || result.soil_type}</div>
        </div>
      </div>

      <div className="grid-2">
        <div className="glass-card" style={{background: 'linear-gradient(to bottom right, var(--bg-card), rgba(59,130,246,0.1))'}}>
          <div className="flex items-center gap-2 text-secondary mb-1">
            <Activity size={16} />
            <p className="text-xs font-semibold">{t('probability_bhoomi')}</p>
          </div>
          <div className="text-2xl font-bold text-white mt-1">{result.recovery_probability}%</div>
          <div className="w-full bg-white/10 rounded-full h-1.5 mt-2">
            <div className="bg-secondary h-1.5 rounded-full" style={{width: `${result.recovery_probability}%`}}></div>
          </div>
        </div>
        <div className="glass-card" style={{background: 'linear-gradient(to bottom right, var(--bg-card), rgba(245,158,11,0.1))'}}>
          <div className="flex items-center gap-2 text-warning mb-1">
            <IndianRupee size={16} />
            <p className="text-xs font-semibold">{t('cost_estimation_bhoomi')}</p>
          </div>
          <div className="text-2xl font-bold text-white mt-1">₹{result.total_cost_inr}</div>
          <p className="text-xs text-muted mt-1">/ acre</p>
        </div>
      </div>

      <div className="glass-card">
        <h3 className="font-semibold flex items-center gap-2 mb-4">
          <Clock size={20} className="text-secondary" />
          {t('recovery_prediction_bhoomi')}
        </h3>
        <div className="flex flex-col gap-4">
          {[
            { t: 'icar_step1_title_bhoomi', d: 'icar_step1_desc_bhoomi', c: 'secondary' },
            { t: 'icar_step2_title_bhoomi', d: 'icar_step2_desc_bhoomi', c: 'primary' },
            { t: 'icar_step3_title_bhoomi', d: 'icar_step3_desc_bhoomi', c: 'success' }
          ].map((step, i) => (
            <div key={i} className="flex items-start gap-3">
              <div className={`flex-shrink-0 w-10 h-10 rounded-full bg-${step.c}/20 flex items-center justify-center text-${step.c} text-xs font-bold`}>
                {i === 0 ? '1-15d' : `Yr ${i}`}
              </div>
              <div>
                <p className="text-sm font-semibold">{t(step.t)}</p>
                <p className="text-xs text-muted">{t(step.d)}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="glass-card border-orange-500/50">
        <h3 className="font-semibold flex items-center gap-2 mb-3 text-warning">
          <AlertTriangle size={20} />
          {t('identified_issues_bhoomi')}
        </h3>
        <ul className="list-disc pl-5 text-sm space-y-2">
          {result.issues.map((issue, idx) => <li key={idx}>{t(issue + '_bhoomi') || issue}</li>)}
        </ul>
      </div>

      <h3 className="font-bold text-lg mb-4">{t('rehab_plan_bhoomi')}</h3>
      {verifying ? (
        <div className="bg-blue-500/10 border border-secondary text-secondary p-3 rounded-xl mb-4 text-xs flex items-center gap-2 animate-pulse">
           <ShieldCheck size={16} /> Verifying against State Agriculture Data...
        </div>
      ) : verificationResult?.verified ? (
        <div className="bg-green-500/10 border border-primary p-3 rounded-xl mb-4">
           <div className="text-success text-sm font-bold flex items-center gap-2 mb-1">
             <ShieldCheck size={16} /> {t('verify_badge_bhoomi')}
           </div>
           <p className="text-xs text-muted leading-relaxed">{verificationResult.explanation}</p>
        </div>
      ) : null}

      <div className="space-y-4 mb-6">
        {result.recommendations.map((rec, idx) => (
          <div key={idx} className="glass-card border-l-4 border-l-primary p-4" style={{background: 'linear-gradient(to right, var(--bg-card), rgba(16,185,129,0.05))'}}>
            <div className="flex justify-between items-start mb-2">
              <span className="text-xs font-semibold px-2 py-1 bg-primary/20 text-primary rounded-full">{t(rec.category + '_bhoomi')}</span>
              <span className="text-sm font-bold text-white">{rec.quantity}</span>
            </div>
            <h4 className="font-bold text-md mb-1">{t(rec.action + '_bhoomi')}</h4>
            <p className="text-xs text-muted leading-relaxed mb-2">{t(rec.reason + '_bhoomi')}</p>
            {rec.cost_estimate_inr > 0 && (
              <div className="text-xs font-medium text-warning flex items-center gap-1 border-t border-white/10 pt-2 mt-2">
                <IndianRupee size={12} /> Est. Cost: ₹{rec.cost_estimate_inr}
              </div>
            )}
          </div>
        ))}
      </div>

      <h3 className="font-bold text-lg mb-4 flex items-center gap-2">
        <Sprout size={20} className="text-success" />
        {t('suitable_crops_bhoomi')}
      </h3>
      <div className="grid-2 mb-8">
        {result.crops.map((crop, idx) => (
          <div key={idx} className="glass-card p-3 flex flex-col items-center text-center">
            <h4 className="font-bold mb-1">{t(crop.name + '_bhoomi')}</h4>
            <span className={`text-xs px-2 py-1 rounded-full ${crop.suitability === 'high' ? 'bg-green-500/20 text-success' : 'bg-orange-500/20 text-warning'}`}>
              {t(crop.suitability + '_bhoomi')}
            </span>
            <p className="text-xs text-muted mt-2">{t(crop.reason + '_bhoomi')}</p>
          </div>
        ))}
      </div>
      
      <button className="btn-primary" onClick={onReset}>Return to Dashboard</button>
    </div>
  );
};

export default SoilHealth;
