import { createContext, useContext, useState, useCallback } from 'react';
import translations from '../utils/translations';

const LanguageContext = createContext();

// All supported languages — add more anytime
export const SUPPORTED_LANGUAGES = [
  { code: 'en', name: 'English',    nativeName: 'English',    flag: '🇬🇧' },
  { code: 'hi', name: 'Hindi',      nativeName: 'हिन्दी',      flag: '🇮🇳' },
  { code: 'mr', name: 'Marathi',    nativeName: 'मराठी',       flag: '🇮🇳' },
  { code: 'ta', name: 'Tamil',      nativeName: 'தமிழ்',       flag: '🇮🇳' },
  { code: 'te', name: 'Telugu',     nativeName: 'తెలుగు',      flag: '🇮🇳' },
  { code: 'kn', name: 'Kannada',    nativeName: 'ಕನ್ನಡ',       flag: '🇮🇳' },
  { code: 'bn', name: 'Bengali',    nativeName: 'বাংলা',       flag: '🇮🇳' },
  { code: 'gu', name: 'Gujarati',   nativeName: 'ગુજરાતી',     flag: '🇮🇳' },
  { code: 'pa', name: 'Punjabi',    nativeName: 'ਪੰਜਾਬੀ',      flag: '🇮🇳' },
  { code: 'ml', name: 'Malayalam',  nativeName: 'മലയാളം',     flag: '🇮🇳' },
  { code: 'or', name: 'Odia',       nativeName: 'ଓଡ଼ିଆ',       flag: '🇮🇳' },
  { code: 'ur', name: 'Urdu',       nativeName: 'اردو',        flag: '🇵🇰' },
];

export function LanguageProvider({ children }) {
  const [lang, setLang] = useState('en');

  const changeLang = useCallback((code) => {
    setLang(code);
  }, []);

  // Legacy toggle (cycles through first 3) for backward compat
  const toggleLang = useCallback(() => {
    setLang((prev) => {
      const codes = SUPPORTED_LANGUAGES.map(l => l.code);
      const index = codes.indexOf(prev);
      const nextIndex = index >= 0 ? (index + 1) % codes.length : 0;
      return codes[nextIndex];
    });
  }, []);

  const t = useCallback((key) => {
    return translations[lang]?.[key] || translations['en']?.[key] || key;
  }, [lang]);

  return (
    <LanguageContext.Provider value={{ lang, changeLang, toggleLang, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}
