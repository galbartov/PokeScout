'use client';
import { strings } from '@/lib/i18n';

const BOT_URL = 'https://t.me/PokeScoutBot';

export default function Footer() {
  return (
    <footer style={{
      background: 'var(--bg-deep)',
      borderTop: '1px solid var(--border)',
      padding: '48px 20px',
    }}>
      <div style={{
        maxWidth: 1100, margin: '0 auto',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 20,
        textAlign: 'center',
      }}>
        <div style={{ fontWeight: 800, fontSize: '1.1rem' }}>
          Poke<span style={{ color: 'var(--accent-gold)' }}>Scout</span>
        </div>

        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>{strings.footer.tagline}</p>

        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', justifyContent: 'center' }}>
          <a href={BOT_URL} target="_blank" rel="noopener noreferrer"
            style={{ color: 'var(--accent-gold)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 600 }}>
            {strings.footer.links[0]}
          </a>
          <a href="#" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.9rem' }}>
            {strings.footer.links[1]}
          </a>
          <a href={BOT_URL} target="_blank" rel="noopener noreferrer"
            style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.9rem' }}>
            {strings.footer.links[2]}
          </a>
        </div>

        <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', opacity: 0.5, maxWidth: 500 }}>
          {strings.footer.disclaimer}
        </p>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.75rem', opacity: 0.4 }}>
          © 2025 TCG Scout
        </p>
      </div>
    </footer>
  );
}
