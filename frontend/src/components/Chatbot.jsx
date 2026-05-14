import { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, Leaf, CloudSun, Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { useLanguage } from '../context/LanguageContext';
import { sendChatMessage, getWeather } from '../utils/api';
import { getFeatureContext } from '../utils/featureContext';
import './Chatbot.css';

const quickReplies = {
  en: [
    'Why are my leaves yellow?',
    'How to treat leaf spot?',
    'Best fertilizer tips',
    'Pest control help',
    'What should I do before rain?',
    'Summarize this project',
    'Summarize my latest crop analysis result',
    'Summarize my latest soil health result',
    'Summarize all my latest feature results',
  ],
  hi: [
    'पत्तियां पीली क्यों हैं?',
    'धब्बों का इलाज कैसे करें?',
    'खाद की सलाह दें',
    'कीट नियंत्रण मदद',
    'बारिश से पहले क्या करें?',
    'इस प्रोजेक्ट का सारांश दें',
    'मेरे नवीनतम फसल विश्लेषण परिणाम का सारांश दें',
    'मेरे नवीनतम मिट्टी स्वास्थ्य परिणाम का सारांश दें',
    'मेरे सभी नवीनतम फीचर परिणामों का सारांश दें',
  ],
  mr: [
    'माझी पाने पिवळी का होत आहेत?',
    'लीफ स्पॉटवर उपचार कसा करावा?',
    'खताबाबत सर्वोत्तम सल्ला द्या',
    'कीड नियंत्रणासाठी मदत हवी',
    'पावसापूर्वी काय करावे?',
    'या प्रोजेक्टचा सारांश द्या',
    'माझ्या ताज्या पीक विश्लेषण निकालाचा सारांश द्या',
    'माझ्या ताज्या माती आरोग्य निकालाचा सारांश द्या',
    'माझे सर्व ताजे फीचर निकाल एकत्रित सारांशित करा',
  ],
};

export default function Chatbot() {
  const { t, lang } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputVal, setInputVal] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [speechEnabled, setSpeechEnabled] = useState(true);
  const [assistantMode, setAssistantMode] = useState('local');
  const [weatherContext, setWeatherContext] = useState(null);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);
  const isAiMode = assistantMode !== 'local';

  const SPEECH_LOCALES = {
    en: 'en-US', hi: 'hi-IN', mr: 'mr-IN', ta: 'ta-IN', te: 'te-IN',
    kn: 'kn-IN', bn: 'bn-IN', gu: 'gu-IN', pa: 'pa-IN', ml: 'ml-IN',
    or: 'or-IN', ur: 'ur-PK',
  };
  const speechLocale = SPEECH_LOCALES[lang] || 'en-US';

  useEffect(() => {
    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch {
          // no-op
        }
      }

      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
    };
  }, []);

  const appendBotMessage = (text, source = 'local') => {
    setMessages((prev) => [...prev, { role: 'bot', text, source }]);
  };

  const speakText = (text) => {
    if (!speechEnabled || typeof window === 'undefined' || !window.speechSynthesis || !text) {
      return;
    }

    const sanitizedText = text.replace(/\s+/g, ' ').trim();
    if (!sanitizedText) {
      return;
    }

    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(sanitizedText);
      utterance.lang = speechLocale;
      utterance.rate = 0.95;
      window.speechSynthesis.speak(utterance);
    } catch {
      // no-op
    }
  };

  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([{ role: 'bot', text: t('chat_greeting'), source: 'local' }]);
    }
  }, [isOpen, messages.length, t]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  useEffect(() => {
    if (!isOpen) return;

    const fetchWeather = (params = {}) => {
      getWeather({ lang, location: t('weather_farm_label'), ...params })
        .then(setWeatherContext)
        .catch(() => setWeatherContext(null));
    };

    if (!navigator.geolocation) {
      fetchWeather();
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        fetchWeather({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
          location: t('weather_farm_label'),
        });
      },
      () => fetchWeather(),
      { enableHighAccuracy: false, timeout: 7000, maximumAge: 300000 },
    );
  }, [isOpen, lang, t]);

  const handleSend = async (text = inputVal) => {
    if (!text.trim()) return;

    const userMsg = { role: 'user', text: text.trim() };
    setMessages((prev) => [...prev, userMsg]);
    setInputVal('');
    setIsTyping(true);

    try {
      const storedFeatureContext = getFeatureContext();
      const featureContext = {
        ...storedFeatureContext,
      };

      if (weatherContext) {
        featureContext.weather = {
          condition: weatherContext.condition,
          temperature_c: weatherContext.temperature_c,
          humidity: weatherContext.humidity,
          precipitation_probability: weatherContext.precipitation_probability,
          disease_risk: weatherContext.disease_risk,
          irrigation: weatherContext.irrigation,
        };
      }

      const data = await sendChatMessage(text.trim(), lang, weatherContext, featureContext);
      setAssistantMode(data.source || 'local');
      appendBotMessage(data.response, data.source || 'local');
      speakText(data.response);
    } catch {
      appendBotMessage(t('chat_error_generic'), 'local');
    } finally {
      setIsTyping(false);
    }
  };

  const toggleListening = () => {
    if (isListening && recognitionRef.current) {
      recognitionRef.current.stop();
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      appendBotMessage(t('chat_voice_not_supported'), 'local');
      return;
    }

    try {
      const recognition = new SpeechRecognition();
      recognition.lang = speechLocale;
      recognition.interimResults = false;
      recognition.maxAlternatives = 1;

      recognition.onstart = () => setIsListening(true);
      recognition.onresult = (event) => {
        const transcript = event?.results?.[0]?.[0]?.transcript?.trim();
        if (transcript) {
          setInputVal(transcript);
          handleSend(transcript);
        }
      };
      recognition.onerror = () => {
        appendBotMessage(t('chat_voice_error'), 'local');
      };
      recognition.onend = () => {
        setIsListening(false);
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch {
      appendBotMessage(t('chat_voice_error'), 'local');
      setIsListening(false);
    }
  };

  const toggleSpeechOutput = () => {
    setSpeechEnabled((prev) => {
      const next = !prev;
      if (!next && typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel();
      }
      return next;
    });
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <>
      <button
        className={`chatbot-fab ${isOpen ? 'chatbot-fab-hidden' : ''}`}
        onClick={() => setIsOpen(true)}
        aria-label={t('chat_open_aria')}
      >
        <MessageCircle size={24} />
        <span className="chatbot-fab-pulse" />
      </button>

      {isOpen && (
        <div className="chatbot-panel glass-card-static animate-fade-in">
          <div className="chatbot-header">
            <div className="chatbot-header-info">
              <div className="chatbot-avatar">
                <Leaf size={18} />
              </div>
              <div>
                <div className="chatbot-header-title">{t('chat_title')}</div>
                <div className="chatbot-header-status">
                  {isAiMode ? t('chat_status_ai') : t('chat_status_local')}
                </div>
              </div>
            </div>

            {weatherContext && (
              <div className="chatbot-weather-pill">
                <CloudSun size={14} />
                <span>{weatherContext.temperature_c}°C</span>
              </div>
            )}

            <button
              className={`chatbot-voice-toggle ${speechEnabled ? 'chatbot-voice-toggle-active' : ''}`}
              onClick={toggleSpeechOutput}
              title={speechEnabled ? t('chat_speak_on') : t('chat_speak_off')}
              aria-label={speechEnabled ? t('chat_speak_on') : t('chat_speak_off')}
              type="button"
            >
              {speechEnabled ? <Volume2 size={16} /> : <VolumeX size={16} />}
            </button>

            <button className="chatbot-close" onClick={() => setIsOpen(false)} aria-label={t('chat_close_aria')}>
              <X size={18} />
            </button>
          </div>

          <div className="chatbot-messages">
            {messages.map((msg, i) => (
              <div key={i} className={`chatbot-msg chatbot-msg-${msg.role}`}>
                <div className={`chatbot-bubble chatbot-bubble-${msg.role}`}>
                  {msg.role === 'bot' ? (
                    <div className="chatbot-md">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.text}
                      </ReactMarkdown>
                    </div>
                  ) : (
                    msg.text.split('\n').map((line, j, arr) => (
                      <span key={j}>
                        {line}
                        {j < arr.length - 1 && <br />}
                      </span>
                    ))
                  )}
                  {msg.role === 'bot' && (
                    <div className="chatbot-msg-source">
                      {msg.source !== 'local' ? t('chat_source_ai') : t('chat_source_local')}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {isTyping && (
              <div className="chatbot-msg chatbot-msg-bot">
                <div className="chatbot-bubble chatbot-bubble-bot chatbot-typing">
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {messages.length <= 1 && (
            <div className="chatbot-quick-replies">
                {(quickReplies[lang] || quickReplies.en).map((q, i) => (
                <button key={i} className="chatbot-quick-btn" onClick={() => handleSend(q)}>
                  {q}
                </button>
              ))}
            </div>
          )}

          <div className="chatbot-input-area">
            <button
              className={`chatbot-voice-btn ${isListening ? 'chatbot-voice-btn-active' : ''}`}
              onClick={toggleListening}
              title={isListening ? t('chat_mic_stop') : t('chat_mic_start')}
              aria-label={isListening ? t('chat_mic_stop') : t('chat_mic_start')}
              type="button"
            >
              {isListening ? <MicOff size={17} /> : <Mic size={17} />}
            </button>

            <input
              ref={inputRef}
              className="chatbot-input"
              value={inputVal}
              onChange={(e) => setInputVal(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t('chat_placeholder')}
            />
            <button
              className="chatbot-send-btn"
              onClick={() => handleSend()}
              disabled={!inputVal.trim()}
            >
              <Send size={18} />
            </button>
          </div>

          {isListening && (
            <div className="chatbot-listening-indicator">{t('chat_voice_listening')}</div>
          )}
        </div>
      )}
    </>
  );
}
