'use client';
import { strings } from '@/lib/i18n';

const BOT_URL = 'https://t.me/PokeScoutBot';

const PokeballIcon = () => (
  <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
    <circle cx="14" cy="14" r="13" stroke="#f5b731" strokeWidth="2" fill="none"/>
    <path d="M1 14h26" stroke="#f5b731" strokeWidth="2"/>
    <circle cx="14" cy="14" r="4" fill="#f5b731"/>
    <circle cx="14" cy="14" r="2" fill="#0a0a14"/>
  </svg>
);

export default function Navbar() {
  return (
    <nav style={{
      position: 'fixed', top: 0, left: 0, right: 0, zIndex: 100,
      background: 'rgba(10,10,20,0.85)',
      backdropFilter: 'blur(12px)',
      borderBottom: '1px solid var(--border)',
      padding: '0 24px',
      height: '64px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
    }}>
      {/* Logo */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <PokeballIcon />
        <span style={{
          fontWeight: 800,
          fontSize: '1.25rem',
          color: 'var(--text-primary)',
          letterSpacing: '-0.02em',
        }}>
          TCG <span style={{ color: 'var(--accent-gold)' }}>Scout</span>
        </span>
      </div>

      {/* CTA */}
      <a href={BOT_URL} target="_blank" rel="noopener noreferrer"
        style={{
          background: 'var(--accent-gold)',
          color: '#0a0a14',
          fontWeight: 700,
          borderRadius: '50px',
          padding: '8px 20px',
          textDecoration: 'none',
          fontSize: '0.9rem',
          transition: 'background .2s, transform .2s',
          display: 'inline-flex',
          alignItems: 'center',
          gap: '6px',
        }}
        onMouseEnter={e => { (e.currentTarget as HTMLElement).style.background = 'var(--accent-gold-2)'; }}
        onMouseLeave={e => { (e.currentTarget as HTMLElement).style.background = 'var(--accent-gold)'; }}
      >
        <span className="nav-cta-text">{strings.nav.cta}</span>
      </a>
    </nav>
  );
}
