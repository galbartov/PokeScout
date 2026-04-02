'use client';

import { useState, useEffect, useCallback, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

/* ── Types ─────────────────────────────────────────────────────────────────── */

interface Product {
  id: string;
  name_en: string;
  set_name: string;
  product_type: 'card' | 'sealed' | string;
  image_url?: string;
  score?: number;
}

interface Alert {
  product_id: string | null;
  name: string;
  product_type: string;
  price_min: number | null;
  price_max: number | null;
  keywords: string[];
}

/* ── Config ─────────────────────────────────────────────────────────────────── */

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? '';
const BOT_URL = 'https://t.me/PokeScoutBot';

/* ── API helpers ────────────────────────────────────────────────────────────── */

async function apiSearch(query: string, type: string): Promise<Product[]> {
  const params = new URLSearchParams({ q: query, limit: '12' });
  if (type) params.set('type', type);
  const res = await fetch(`${API_BASE}/api/setup/products?${params}`);
  if (!res.ok) return [];
  return res.json();
}

async function apiPopular(): Promise<Product[]> {
  const res = await fetch(`${API_BASE}/api/setup/popular`);
  if (!res.ok) return [];
  return res.json();
}

async function apiPrice(name: string): Promise<number | null> {
  const res = await fetch(`${API_BASE}/api/setup/price?name=${encodeURIComponent(name)}`);
  if (!res.ok) return null;
  const data = await res.json();
  return data.price ?? null;
}

async function apiConfirm(token: string, alerts: Alert[]): Promise<{ saved: number; skipped: number }> {
  const res = await fetch(`${API_BASE}/api/setup/confirm`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ token, alerts }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { detail?: string }).detail ?? 'Submit failed');
  }
  return res.json();
}

/* ── Pokéball SVG ───────────────────────────────────────────────────────────── */

const PokeballIcon = () => (
  <svg width="26" height="26" viewBox="0 0 28 28" fill="none">
    <circle cx="14" cy="14" r="13" stroke="#f5b731" strokeWidth="2" fill="none"/>
    <path d="M1 14h26" stroke="#f5b731" strokeWidth="2"/>
    <circle cx="14" cy="14" r="4" fill="#f5b731"/>
    <circle cx="14" cy="14" r="2" fill="#0a0a14"/>
  </svg>
);

/* ── ProductCard ────────────────────────────────────────────────────────────── */

function ProductCard({ product, onAdd, index }: {
  product: Product;
  onAdd: (product: Product, priceMax: number | null) => void;
  index: number;
}) {
  const [marketPrice, setMarketPrice] = useState<number | null | undefined>(undefined);
  const [priceInput, setPriceInput] = useState('');
  const [showInput, setShowInput] = useState(false);
  const [hovered, setHovered] = useState(false);
  const [added, setAdded] = useState(false);

  useEffect(() => {
    // Stagger price fetches
    const timer = setTimeout(() => {
      apiPrice(product.name_en).then(setMarketPrice);
    }, index * 80);
    return () => clearTimeout(timer);
  }, [product.name_en, index]);

  const handleAdd = () => {
    if (!showInput) {
      setShowInput(true);
      if (marketPrice) setPriceInput(String(Math.round(marketPrice)));
      return;
    }
    const val = parseFloat(priceInput);
    onAdd(product, isNaN(val) || val <= 0 ? null : val);
    setShowInput(false);
    setPriceInput('');
    setAdded(true);
    setTimeout(() => setAdded(false), 2000);
  };

  return (
    <div
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => { setHovered(false); }}
      style={{
        borderRadius: 16,
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        background: 'linear-gradient(160deg, #1a1a2e 0%, #12121f 100%)',
        border: `1px solid ${hovered ? 'rgba(245,183,49,0.4)' : 'rgba(245,183,49,0.12)'}`,
        boxShadow: hovered
          ? '0 20px 50px rgba(0,0,0,0.7), 0 0 20px rgba(245,183,49,0.12)'
          : '0 4px 20px rgba(0,0,0,0.4)',
        transform: hovered ? 'translateY(-4px) scale(1.02)' : 'translateY(0) scale(1)',
        transition: 'all 0.35s cubic-bezier(.22,1,.36,1)',
        animationDelay: `${index * 60}ms`,
        animation: 'card-in 0.5s cubic-bezier(.22,1,.36,1) both',
        position: 'relative',
      }}
    >
      {/* Image area */}
      <div style={{ position: 'relative', background: '#0a0a14' }}>
        {product.image_url ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={product.image_url}
            alt={product.name_en}
            style={{
              width: '100%',
              aspectRatio: product.product_type === 'card' ? '2.5 / 3.5' : '4 / 3',
              objectFit: product.product_type === 'card' ? 'contain' : 'cover',
              display: 'block',
              transition: 'transform 0.35s cubic-bezier(.22,1,.36,1)',
              transform: hovered ? 'scale(1.04)' : 'scale(1)',
              padding: product.product_type === 'card' ? '8px' : '0',
            }}
            loading="lazy"
          />
        ) : (
          <div style={{
            width: '100%',
            aspectRatio: '2.5 / 3.5',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontSize: 48,
            color: 'rgba(245,183,49,0.3)',
          }}>
            {product.product_type === 'sealed' ? '📦' : '🃏'}
          </div>
        )}

        {/* Holographic shimmer on hover */}
        {hovered && (
          <div style={{
            position: 'absolute', inset: 0,
            background: 'conic-gradient(from var(--holo-angle, 0deg), transparent 0%, rgba(245,183,49,0.06) 15%, rgba(0,212,170,0.06) 30%, transparent 45%)',
            pointerEvents: 'none',
            animation: 'holo-shimmer 1.5s linear infinite',
          }} />
        )}

        {/* Market price badge */}
        {marketPrice !== undefined && marketPrice !== null && (
          <div style={{
            position: 'absolute', bottom: 8, right: 8,
            background: 'rgba(10,10,20,0.88)',
            backdropFilter: 'blur(8px)',
            border: '1px solid rgba(0,212,170,0.3)',
            borderRadius: 20,
            padding: '3px 10px',
            fontSize: 11,
            fontWeight: 700,
            color: 'var(--accent-teal)',
            letterSpacing: '0.02em',
          }}>
            ~${Math.round(marketPrice)}
          </div>
        )}
        {marketPrice === undefined && (
          <div style={{
            position: 'absolute', bottom: 8, right: 8,
            width: 48, height: 18,
            background: 'rgba(255,255,255,0.05)',
            borderRadius: 10,
            animation: 'pulse-skeleton 1.4s ease-in-out infinite',
          }} />
        )}
      </div>

      {/* Info + CTA */}
      <div style={{ padding: '10px 12px 12px', display: 'flex', flexDirection: 'column', gap: 6 }}>
        <div style={{
          fontSize: 12,
          fontWeight: 700,
          color: 'var(--text-primary)',
          lineHeight: 1.3,
          letterSpacing: '-0.01em',
          overflow: 'hidden',
          display: '-webkit-box',
          WebkitLineClamp: 2,
          WebkitBoxOrient: 'vertical',
        } as React.CSSProperties}>
          {product.name_en}
        </div>
        {product.set_name && (
          <div style={{ fontSize: 10, color: 'var(--text-secondary)', letterSpacing: '0.03em', textTransform: 'uppercase' }}>
            {product.set_name}
          </div>
        )}

        {showInput && (
          <div style={{ display: 'flex', gap: 6, marginTop: 2 }}>
            <input
              type="number"
              placeholder="Max $"
              value={priceInput}
              onChange={e => setPriceInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleAdd()}
              style={{
                flex: 1,
                background: 'rgba(245,183,49,0.06)',
                border: '1px solid rgba(245,183,49,0.3)',
                borderRadius: 8,
                padding: '6px 8px',
                color: 'var(--text-primary)',
                fontSize: 13,
                fontWeight: 600,
                outline: 'none',
                width: 0,
              }}
              autoFocus
            />
          </div>
        )}

        <button
          onClick={handleAdd}
          style={{
            background: added
              ? 'rgba(0,212,170,0.15)'
              : showInput
              ? 'var(--accent-gold)'
              : 'rgba(245,183,49,0.1)',
            color: added
              ? 'var(--accent-teal)'
              : showInput
              ? '#0a0a14'
              : 'var(--accent-gold)',
            border: `1px solid ${added ? 'rgba(0,212,170,0.3)' : showInput ? 'transparent' : 'rgba(245,183,49,0.2)'}`,
            borderRadius: 50,
            padding: '7px 0',
            fontSize: 11,
            fontWeight: 700,
            cursor: 'pointer',
            transition: 'all 0.2s ease',
            width: '100%',
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
          } as React.CSSProperties}
        >
          {added ? '✓ Added' : showInput ? 'Confirm →' : '+ Set Alert'}
        </button>
      </div>
    </div>
  );
}

/* ── AlertRow ───────────────────────────────────────────────────────────────── */

function AlertRow({ alert, onRemove }: { alert: Alert; onRemove: () => void }) {
  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: 10,
      padding: '10px 14px',
      background: 'rgba(245,183,49,0.04)',
      borderRadius: 10,
      border: '1px solid rgba(245,183,49,0.12)',
      transition: 'border-color 0.2s',
      animation: 'alert-in 0.3s cubic-bezier(.22,1,.36,1) both',
    }}>
      <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--accent-teal)', flexShrink: 0 }} />
      <span style={{
        flex: 1,
        fontSize: 13,
        color: 'var(--text-primary)',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
        whiteSpace: 'nowrap',
        fontWeight: 600,
      }}>
        {alert.name}
      </span>
      {alert.price_max && (
        <span style={{
          fontSize: 11,
          color: 'var(--accent-gold)',
          fontWeight: 700,
          flexShrink: 0,
          background: 'rgba(245,183,49,0.08)',
          padding: '2px 8px',
          borderRadius: 20,
        }}>
          ≤${alert.price_max}
        </span>
      )}
      <button
        onClick={onRemove}
        style={{
          background: 'none', border: 'none',
          color: 'var(--text-secondary)',
          cursor: 'pointer', fontSize: 16,
          padding: '0 0 0 4px', lineHeight: 1,
          transition: 'color 0.15s',
          flexShrink: 0,
        }}
        onMouseEnter={e => (e.currentTarget.style.color = '#ff6b6b')}
        onMouseLeave={e => (e.currentTarget.style.color = 'var(--text-secondary)')}
      >×</button>
    </div>
  );
}

/* ── Main page ──────────────────────────────────────────────────────────────── */

function SetupPageInner() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token') ?? '';

  const [tokenError, setTokenError] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState<'' | 'card' | 'sealed'>('');
  const [results, setResults] = useState<Product[]>([]);
  const [popular, setPopular] = useState<Product[]>([]);
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState<{ saved: number; skipped: number } | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!token) setTokenError('No token provided. Type /setup in the bot to get a link.');
  }, [token]);

  useEffect(() => {
    apiPopular().then(setPopular);
  }, []);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setSearching(true);
    setSearched(false);
    const res = await apiSearch(query.trim(), typeFilter);
    setResults(res);
    setSearching(false);
    setSearched(true);
  }, [query, typeFilter]);

  const handleAdd = async (product: Product, priceMax: number | null) => {
    setAlerts(prev => {
      if (prev.find(a => a.product_id === product.id)) return prev;
      return [...prev, {
        product_id: product.id,
        name: product.name_en,
        product_type: product.product_type,
        price_min: null,
        price_max: priceMax,
        keywords: [product.name_en.toLowerCase()],
      }];
    });
  };

  const handleSubmit = async () => {
    if (!alerts.length) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      setDone(await apiConfirm(token, alerts));
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unknown error';
      if (msg.toLowerCase().includes('expired') || msg.toLowerCase().includes('used')) {
        setTokenError('This link has expired. Type /setup in the bot to get a new one.');
      } else {
        setSubmitError(msg);
      }
    } finally {
      setSubmitting(false);
    }
  };

  /* ── Styles injected once ────────────────────────────────────────────────── */
  const pageStyles = `
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&display=swap');

    * { box-sizing: border-box; }

    @keyframes card-in {
      from { opacity: 0; transform: translateY(16px) scale(0.96); }
      to   { opacity: 1; transform: translateY(0) scale(1); }
    }
    @keyframes alert-in {
      from { opacity: 0; transform: translateX(-8px); }
      to   { opacity: 1; transform: translateX(0); }
    }
    @keyframes holo-shimmer {
      from { --holo-angle: 0deg; }
      to   { --holo-angle: 360deg; }
    }
    @keyframes pulse-skeleton {
      0%, 100% { opacity: 0.3; }
      50%       { opacity: 0.7; }
    }
    @keyframes spin-search {
      from { transform: rotate(0deg); }
      to   { transform: rotate(360deg); }
    }
    @keyframes fade-up {
      from { opacity: 0; transform: translateY(24px); }
      to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes gold-pulse {
      0%, 100% { box-shadow: 0 0 0 0 rgba(245,183,49,0); }
      50%       { box-shadow: 0 0 0 8px rgba(245,183,49,0.15); }
    }
    @property --holo-angle {
      syntax: '<angle>';
      inherits: false;
      initial-value: 0deg;
    }

    .setup-input:focus {
      border-color: rgba(245,183,49,0.5) !important;
      box-shadow: 0 0 0 3px rgba(245,183,49,0.08);
    }
    .type-btn:hover {
      border-color: rgba(245,183,49,0.4) !important;
      color: var(--accent-gold) !important;
    }
    .save-btn:not(:disabled):hover {
      background: var(--accent-gold-2) !important;
      transform: translateY(-2px);
      box-shadow: 0 8px 30px rgba(245,183,49,0.3);
    }

    /* noise overlay */
    .setup-noise::before {
      content: '';
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      opacity: 0.035;
      background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
      background-size: 200px;
    }

    /* diagonal scan lines */
    .setup-noise::after {
      content: '';
      position: fixed;
      inset: 0;
      pointer-events: none;
      z-index: 0;
      background: repeating-linear-gradient(
        105deg,
        transparent 0px, transparent 120px,
        rgba(245,183,49,0.018) 120px, rgba(245,183,49,0.018) 121px
      );
    }

    /* scroll */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: var(--bg-deep); }
    ::-webkit-scrollbar-thumb { background: rgba(245,183,49,0.2); border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: rgba(245,183,49,0.4); }
  `;

  /* ── Token error state ───────────────────────────────────────────────────── */

  if (tokenError) {
    return (
      <>
        <style>{pageStyles}</style>
        <div className="setup-noise" style={{
          minHeight: '100vh',
          background: 'var(--bg-deep)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: "'Syne', sans-serif",
          padding: 24,
        }}>
          <div style={{
            background: 'linear-gradient(150deg, #1c1500 0%, #0f0f1e 50%, #0a0a14 100%)',
            border: '1px solid rgba(245,183,49,0.25)',
            borderRadius: 28,
            padding: 48,
            maxWidth: 440,
            textAlign: 'center',
            boxShadow: '0 40px 80px rgba(0,0,0,0.5)',
            animation: 'fade-up 0.6s cubic-bezier(.22,1,.36,1) both',
            position: 'relative',
            zIndex: 1,
          }}>
            <div style={{ fontSize: 52, marginBottom: 20 }}>⏰</div>
            <h2 style={{ fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: '1.4rem', color: 'var(--text-primary)', margin: '0 0 12px', letterSpacing: '-0.02em' }}>
              Link expired
            </h2>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, margin: '0 0 28px', fontSize: '0.95rem' }}>{tokenError}</p>
            <a href={BOT_URL} target="_blank" rel="noopener noreferrer" style={{
              display: 'inline-block',
              background: 'var(--accent-gold)',
              color: '#0a0a14',
              fontWeight: 700,
              borderRadius: 50,
              padding: '12px 28px',
              textDecoration: 'none',
              fontSize: '0.9rem',
              fontFamily: "'Syne', sans-serif",
              letterSpacing: '0.02em',
            }}>
              Open TCG Scout →
            </a>
          </div>
        </div>
      </>
    );
  }

  /* ── Success state ───────────────────────────────────────────────────────── */

  if (done) {
    return (
      <>
        <style>{pageStyles}</style>
        <div className="setup-noise" style={{
          minHeight: '100vh',
          background: 'var(--bg-deep)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontFamily: "'Syne', sans-serif",
          padding: 24,
        }}>
          <div style={{
            background: 'linear-gradient(150deg, #001a14 0%, #0f0f1e 50%, #0a0a14 100%)',
            border: '1px solid rgba(0,212,170,0.3)',
            borderRadius: 28,
            padding: 52,
            maxWidth: 480,
            textAlign: 'center',
            boxShadow: '0 40px 80px rgba(0,0,0,0.5), 0 0 60px rgba(0,212,170,0.08)',
            animation: 'fade-up 0.5s cubic-bezier(.22,1,.36,1) both',
            position: 'relative',
            zIndex: 1,
          }}>
            <div style={{ fontSize: 56, marginBottom: 20 }}>🎉</div>
            <h2 style={{ fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: '1.8rem', color: 'var(--accent-teal)', margin: '0 0 10px', letterSpacing: '-0.03em' }}>
              {done.saved} alert{done.saved !== 1 ? 's' : ''} created!
            </h2>
            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.7, fontSize: '1rem', margin: '0 0 8px' }}>
              Check your Telegram — I'll ping you the moment a deal appears.
            </p>
            {done.skipped > 0 && (
              <p style={{ color: 'rgba(136,136,170,0.6)', fontSize: '0.85rem', margin: '0 0 28px' }}>
                {done.skipped} skipped (duplicates or limit reached)
              </p>
            )}
            <a href={BOT_URL} target="_blank" rel="noopener noreferrer" style={{
              display: 'inline-block',
              background: 'var(--accent-gold)',
              color: '#0a0a14',
              fontWeight: 700,
              borderRadius: 50,
              padding: '13px 32px',
              textDecoration: 'none',
              fontSize: '0.95rem',
              fontFamily: "'Syne', sans-serif",
              letterSpacing: '0.02em',
              animation: 'gold-pulse 2.2s ease-in-out infinite',
              marginTop: done.skipped > 0 ? 0 : 24,
            }}>
              Open Telegram ↗
            </a>
          </div>
        </div>
      </>
    );
  }

  /* ── Main UI ─────────────────────────────────────────────────────────────── */

  const typeButtons: { label: string; value: '' | 'card' | 'sealed' }[] = [
    { label: 'All', value: '' },
    { label: '🃏 Cards', value: 'card' },
    { label: '📦 Sealed', value: 'sealed' },
  ];

  return (
    <>
      <style>{pageStyles}</style>
      <div className="setup-noise" style={{
        minHeight: '100vh',
        background: 'var(--bg-deep)',
        color: 'var(--text-primary)',
        fontFamily: "'Syne', sans-serif",
        display: 'flex',
        flexDirection: 'column',
      }}>

        {/* ── Navbar ──────────────────────────────────────────────────────── */}
        <nav style={{
          position: 'sticky', top: 0, zIndex: 100,
          background: 'rgba(10,10,20,0.88)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid var(--border)',
          padding: '0 28px',
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexShrink: 0,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <PokeballIcon />
            <span style={{ fontWeight: 800, fontSize: '1.2rem', letterSpacing: '-0.02em' }}>
              Poke<span style={{ color: 'var(--accent-gold)' }}>Scout</span>
              <span style={{ color: 'var(--text-secondary)', fontWeight: 400, fontSize: '0.8rem', marginLeft: 10 }}>
                Alert Setup
              </span>
            </span>
          </div>

          {/* Save button in navbar */}
          <button
            onClick={handleSubmit}
            disabled={!alerts.length || submitting}
            className="save-btn"
            style={{
              background: alerts.length ? 'var(--accent-gold)' : 'rgba(245,183,49,0.1)',
              color: alerts.length ? '#0a0a14' : 'var(--text-secondary)',
              border: `1px solid ${alerts.length ? 'transparent' : 'rgba(245,183,49,0.15)'}`,
              borderRadius: 50,
              padding: '9px 22px',
              fontWeight: 700,
              fontSize: '0.875rem',
              cursor: alerts.length ? 'pointer' : 'not-allowed',
              fontFamily: "'Syne', sans-serif",
              letterSpacing: '0.02em',
              transition: 'all 0.2s ease',
              animation: alerts.length ? 'gold-pulse 2.2s ease-in-out infinite' : 'none',
            }}
          >
            {submitting
              ? 'Saving…'
              : alerts.length
              ? `Save ${alerts.length} alert${alerts.length !== 1 ? 's' : ''} →`
              : 'Save alerts →'}
          </button>
        </nav>

        {/* ── Error banner ────────────────────────────────────────────────── */}
        {submitError && (
          <div style={{
            background: 'rgba(220,50,50,0.1)',
            borderBottom: '1px solid rgba(220,50,50,0.2)',
            color: '#ff8080',
            padding: '10px 28px',
            fontSize: '0.875rem',
            zIndex: 1,
          }}>
            ⚠ {submitError}
          </div>
        )}

        {/* ── Split body ──────────────────────────────────────────────────── */}
        <div style={{
          flex: 1,
          display: 'grid',
          gridTemplateColumns: '280px 1fr',
          minHeight: 0,
          position: 'relative',
          zIndex: 1,
        }}>

          {/* ── Left panel — saved alerts ──────────────────────────────────── */}
          <aside style={{
            borderRight: '1px solid rgba(245,183,49,0.08)',
            background: 'rgba(10,10,20,0.5)',
            overflowY: 'auto',
            padding: '24px 16px',
            display: 'flex',
            flexDirection: 'column',
            gap: 6,
          }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              marginBottom: 12,
              paddingBottom: 12,
              borderBottom: '1px solid rgba(245,183,49,0.08)',
            }}>
              <span style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                color: 'var(--text-secondary)',
                letterSpacing: '0.08em',
                textTransform: 'uppercase',
              }}>
                Your alerts
              </span>
              {alerts.length > 0 && (
                <span style={{
                  background: 'var(--accent-gold)',
                  color: '#0a0a14',
                  fontWeight: 800,
                  fontSize: '0.7rem',
                  borderRadius: 20,
                  padding: '2px 8px',
                  minWidth: 22,
                  textAlign: 'center',
                }}>
                  {alerts.length}
                </span>
              )}
            </div>

            {alerts.length === 0 ? (
              <div style={{
                textAlign: 'center',
                padding: '32px 16px',
                color: 'var(--text-secondary)',
                fontSize: '0.85rem',
                lineHeight: 1.7,
              }}>
                <div style={{ fontSize: 32, marginBottom: 12, opacity: 0.4 }}>🔔</div>
                Search for a card or product, then tap&nbsp;<strong style={{ color: 'var(--accent-gold)' }}>+ Set Alert</strong>.
              </div>
            ) : (
              alerts.map((alert, idx) => (
                <AlertRow key={idx} alert={alert} onRemove={() => setAlerts(prev => prev.filter((_, i) => i !== idx))} />
              ))
            )}
          </aside>

          {/* ── Right panel — search ───────────────────────────────────────── */}
          <main style={{
            overflowY: 'auto',
            padding: '28px 28px',
            display: 'flex',
            flexDirection: 'column',
            gap: 20,
          }}>
            {/* Search bar row */}
            <div style={{ display: 'flex', gap: 10 }}>
              <div style={{ position: 'relative', flex: 1 }}>
                <input
                  ref={inputRef}
                  type="text"
                  placeholder="Search cards or products…"
                  value={query}
                  onChange={e => setQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSearch()}
                  className="setup-input"
                  style={{
                    width: '100%',
                    background: 'rgba(18,18,31,0.9)',
                    border: '1px solid rgba(245,183,49,0.2)',
                    borderRadius: 50,
                    padding: '12px 20px 12px 44px',
                    color: 'var(--text-primary)',
                    fontSize: '0.95rem',
                    fontFamily: "'Syne', sans-serif",
                    fontWeight: 500,
                    outline: 'none',
                    transition: 'border-color 0.2s, box-shadow 0.2s',
                  }}
                />
                {/* Search icon */}
                <div style={{
                  position: 'absolute', left: 16, top: '50%', transform: 'translateY(-50%)',
                  color: 'var(--text-secondary)', fontSize: 16, pointerEvents: 'none',
                  animation: searching ? 'spin-search 0.8s linear infinite' : 'none',
                }}>
                  {searching ? '↻' : '🔍'}
                </div>
              </div>
              <button
                onClick={handleSearch}
                disabled={searching || !query.trim()}
                style={{
                  background: 'var(--accent-gold)',
                  color: '#0a0a14',
                  border: 'none',
                  borderRadius: 50,
                  padding: '12px 24px',
                  fontWeight: 700,
                  fontSize: '0.9rem',
                  fontFamily: "'Syne', sans-serif",
                  cursor: query.trim() ? 'pointer' : 'not-allowed',
                  transition: 'background 0.2s, transform 0.2s',
                  opacity: searching ? 0.7 : 1,
                  letterSpacing: '0.02em',
                  flexShrink: 0,
                }}
                onMouseEnter={e => { if (!searching) (e.currentTarget as HTMLElement).style.background = 'var(--accent-gold-2)'; }}
                onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'var(--accent-gold)'; }}
              >
                Search
              </button>
            </div>

            {/* Type filter pills */}
            <div style={{ display: 'flex', gap: 8 }}>
              {typeButtons.map(btn => (
                <button
                  key={btn.value}
                  onClick={() => setTypeFilter(btn.value)}
                  className="type-btn"
                  style={{
                    background: typeFilter === btn.value ? 'rgba(245,183,49,0.12)' : 'transparent',
                    color: typeFilter === btn.value ? 'var(--accent-gold)' : 'var(--text-secondary)',
                    border: `1px solid ${typeFilter === btn.value ? 'rgba(245,183,49,0.35)' : 'rgba(255,255,255,0.08)'}`,
                    borderRadius: 50,
                    padding: '6px 16px',
                    fontSize: '0.8rem',
                    fontWeight: 700,
                    fontFamily: "'Syne', sans-serif",
                    cursor: 'pointer',
                    transition: 'all 0.15s',
                    letterSpacing: '0.03em',
                  }}
                >
                  {btn.label}
                </button>
              ))}
            </div>

            {/* Divider */}
            <div style={{
              height: 1,
              background: 'linear-gradient(90deg, transparent 0%, rgba(245,183,49,0.15) 30%, rgba(245,183,49,0.15) 70%, transparent 100%)',
              flexShrink: 0,
            }} />

            {/* Results grid */}
            {results.length > 0 && (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
                gap: 14,
              }}>
                {results.map((product, i) => (
                  <ProductCard key={product.id} product={product} onAdd={handleAdd} index={i} />
                ))}
              </div>
            )}

            {/* No results */}
            {searched && results.length === 0 && !searching && (
              <div style={{
                textAlign: 'center',
                padding: '48px 24px',
                color: 'var(--text-secondary)',
                animation: 'fade-up 0.4s cubic-bezier(.22,1,.36,1) both',
              }}>
                <div style={{ fontSize: 40, marginBottom: 12, opacity: 0.4 }}>🔍</div>
                <p style={{ fontSize: '1rem', fontWeight: 600, color: 'var(--text-primary)', marginBottom: 6 }}>
                  No results for &quot;{query}&quot;
                </p>
                <p style={{ fontSize: '0.875rem' }}>Try a different spelling or a shorter name.</p>
              </div>
            )}

            {/* Popular items — shown when search bar is empty */}
            {!searched && !searching && (
              <div style={{ animation: 'fade-up 0.5s cubic-bezier(.22,1,.36,1) both' }}>
                {/* Section header */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 10,
                  marginBottom: 16,
                }}>
                  <span style={{
                    fontSize: '0.7rem',
                    fontWeight: 700,
                    color: 'var(--text-secondary)',
                    letterSpacing: '0.08em',
                    textTransform: 'uppercase',
                  }}>🔥 Popular right now</span>
                  <div style={{ flex: 1, height: 1, background: 'linear-gradient(90deg, rgba(245,183,49,0.15), transparent)' }} />
                </div>

                {popular.length > 0 ? (
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
                    gap: 14,
                  }}>
                    {popular.map((product, i) => (
                      <ProductCard key={product.id} product={product} onAdd={handleAdd} index={i} />
                    ))}
                  </div>
                ) : (
                  // Skeleton grid while loading
                  <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(150px, 1fr))',
                    gap: 14,
                  }}>
                    {Array.from({ length: 10 }).map((_, i) => (
                      <div key={i} style={{
                        borderRadius: 16,
                        overflow: 'hidden',
                        background: 'var(--bg-surface-2)',
                        border: '1px solid rgba(245,183,49,0.08)',
                        animationDelay: `${i * 60}ms`,
                        animation: 'pulse-skeleton 1.4s ease-in-out infinite',
                      }}>
                        <div style={{ width: '100%', aspectRatio: '2.5 / 3.5', background: 'rgba(255,255,255,0.03)' }} />
                        <div style={{ padding: '10px 12px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                          <div style={{ height: 12, borderRadius: 6, background: 'rgba(255,255,255,0.05)', width: '80%' }} />
                          <div style={{ height: 10, borderRadius: 6, background: 'rgba(255,255,255,0.03)', width: '55%' }} />
                          <div style={{ height: 28, borderRadius: 50, background: 'rgba(255,255,255,0.04)', marginTop: 2 }} />
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Quick-search chips below the grid */}
                <div style={{
                  display: 'flex',
                  flexWrap: 'wrap',
                  gap: 8,
                  marginTop: 24,
                }}>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', alignSelf: 'center', marginRight: 4 }}>
                    Or search:
                  </span>
                  {['Charizard ex SIR', 'Umbreon VMAX Alt Art', 'Pikachu VMAX', 'Rayquaza VMAX Alt Art'].map(example => (
                    <button
                      key={example}
                      onClick={() => { setQuery(example); setTimeout(handleSearch, 50); }}
                      style={{
                        background: 'rgba(245,183,49,0.06)',
                        border: '1px solid rgba(245,183,49,0.15)',
                        borderRadius: 50,
                        padding: '5px 13px',
                        color: 'var(--accent-gold)',
                        fontSize: '0.78rem',
                        fontWeight: 600,
                        fontFamily: "'Syne', sans-serif",
                        cursor: 'pointer',
                        transition: 'all 0.15s',
                        letterSpacing: '0.02em',
                      }}
                      onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(245,183,49,0.12)'; }}
                      onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'rgba(245,183,49,0.06)'; }}
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </main>
        </div>
      </div>
    </>
  );
}

export default function SetupPage() {
  return (
    <Suspense>
      <SetupPageInner />
    </Suspense>
  );
}
