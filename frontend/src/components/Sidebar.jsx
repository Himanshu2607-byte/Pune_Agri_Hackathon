import { NavLink, useLocation } from 'react-router-dom';
import { useLanguage, SUPPORTED_LANGUAGES } from '../context/LanguageContext';
import {
  LayoutDashboard,
  ScanLine,
  Map,
  BarChart3,
  Leaf,
  Languages,
  Menu,
  X,
  BookOpen,
  BookMarked,
  ClipboardList,
  FlaskConical,
  FileText,
  DollarSign,
  Microscope,
  ChevronDown,
} from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import './Sidebar.css';

const navItems = [
  { path: '/', icon: LayoutDashboard, labelKey: 'nav_dashboard' },
  { path: '/analyze', icon: ScanLine, labelKey: 'nav_analyze' },
  { path: '/farm-map', icon: Map, labelKey: 'nav_farm_map' },
  { path: '/analytics', icon: BarChart3, labelKey: 'nav_analytics' },
  { path: '/profit', icon: DollarSign, labelKey: 'nav_profit_estimator' },
  { path: '/soil-health', icon: FlaskConical, labelKey: 'nav_soil_health' },
  { path: '/journal', icon: BookOpen, labelKey: 'nav_journal' },
  { path: '/library', icon: BookMarked, labelKey: 'nav_library' },
  { path: '/tasks', icon: ClipboardList, labelKey: 'nav_tasks' },
  { path: '/summarizer', icon: FileText, labelKey: 'nav_summarizer' },
  { path: '/soil-analysis', icon: Microscope, labelKey: 'nav_soil_analysis' },
];

export default function Sidebar() {
  const { t, lang, changeLang } = useLanguage();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [langDropdownOpen, setLangDropdownOpen] = useState(false);
  const dropdownRef = useRef(null);

  const currentLang = SUPPORTED_LANGUAGES.find(l => l.code === lang) || SUPPORTED_LANGUAGES[0];

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setLangDropdownOpen(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <>
      {/* Mobile hamburger */}
      <button
        className="sidebar-mobile-toggle"
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label={t('sidebar_toggle_menu')}
      >
        {mobileOpen ? <X size={22} /> : <Menu size={22} />}
      </button>

      {/* Overlay */}
      {mobileOpen && (
        <div className="sidebar-overlay" onClick={() => setMobileOpen(false)} />
      )}

      <aside className={`sidebar ${mobileOpen ? 'sidebar-open' : ''}`}>
        {/* Brand */}
        <div className="sidebar-brand">
          <div className="sidebar-logo">
            <Leaf size={28} strokeWidth={2.5} />
          </div>
          <div className="sidebar-brand-text">
            <span className="sidebar-brand-name">{t('brand_name')}</span>
            <span className="sidebar-brand-tagline">{t('brand_tagline')}</span>
          </div>
        </div>

        {/* Nav */}
        <nav className="sidebar-nav">
          {navItems.map(item => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={`sidebar-link ${isActive ? 'sidebar-link-active' : ''}`}
                onClick={() => setMobileOpen(false)}
              >
                {isActive && <div className="sidebar-active-indicator" />}
                <Icon size={20} />
                <span>{t(item.labelKey)}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="sidebar-footer">
          {/* Language Picker Dropdown */}
          <div className="sidebar-lang-picker" ref={dropdownRef}>
            <button
              className="sidebar-lang-btn"
              onClick={() => setLangDropdownOpen(!langDropdownOpen)}
            >
              <Languages size={18} />
              <span className="sidebar-lang-current">
                {currentLang.flag} {currentLang.nativeName}
              </span>
              <ChevronDown
                size={14}
                className={`sidebar-lang-chevron ${langDropdownOpen ? 'sidebar-lang-chevron-open' : ''}`}
              />
            </button>

            {langDropdownOpen && (
              <div className="sidebar-lang-dropdown">
                <div className="sidebar-lang-dropdown-header">
                  🌐 Select Language
                </div>
                <div className="sidebar-lang-dropdown-list">
                  {SUPPORTED_LANGUAGES.map(l => (
                    <button
                      key={l.code}
                      className={`sidebar-lang-option ${l.code === lang ? 'sidebar-lang-option-active' : ''}`}
                      onClick={() => {
                        changeLang(l.code);
                        setLangDropdownOpen(false);
                      }}
                    >
                      <span className="sidebar-lang-option-flag">{l.flag}</span>
                      <span className="sidebar-lang-option-native">{l.nativeName}</span>
                      <span className="sidebar-lang-option-name">{l.name}</span>
                      {l.code === lang && <span className="sidebar-lang-option-check">✓</span>}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
          <div className="sidebar-version">{t('sidebar_version')}</div>
        </div>
      </aside>
    </>
  );
}
