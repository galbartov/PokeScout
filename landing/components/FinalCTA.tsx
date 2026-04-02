'use client';
import { strings } from '@/lib/i18n';
import { useEffect, useRef } from 'react';

const BOT_URL = 'https://t.me/PokeScoutBot';

export default function FinalCTA() {
  const ref = useRef<HTMLElement>(null);
  const btnRef = useRef<HTMLAnchorElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => entries.forEach(e => e.target.classList.toggle('visible', e.isIntersecting)),
      { threshold: 0.2 }
    );
    ref.current?.querySelectorAll('.reveal').forEach(el => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={ref} className="section-pad-xl" style={{
      background: 'var(--bg-deep)',
      position: 'relative',
      overflow: 'hidden',
      textAlign: 'center',
    }}>
      {/* Large faint Pokéball watermark */}
      <div style={{
        position: 'absolute', top: '50%', left: '50%',
        transform: 'translate(-50%, -50%)',
        width: 600, height: 600,
        pointerEvents: 'none', opacity: 0.025,
      }}>
        <svg viewBox="0 0 100 100" width="100%" height="100%">
          <circle cx="50" cy="50" r="48" stroke="#f5b731" strokeWidth="2" fill="none"/>
          <path d="M2,50 h96" stroke="#f5b731" strokeWidth="2"/>
          <circle cx="50" cy="50" r="14" stroke="#f5b731" strokeWidth="2" fill="none"/>
          <circle cx="50" cy="50" r="7" fill="#f5b731"/>
        </svg>
      </div>

      <div style={{
        position: 'absolute', top: 0, left: '10%', right: '10%',
        height: 1,
        background: 'linear-gradient(90deg, transparent, rgba(245,183,49,0.3), transparent)',
      }} />

      <div className="reveal" style={{ position: 'relative', zIndex: 1, maxWidth: 700, margin: '0 auto' }}>
        <div style={{
          display: 'inline-block',
          fontSize: '0.72rem', fontWeight: 700, letterSpacing: '0.14em',
          color: 'var(--accent-gold)', textTransform: 'uppercase',
          marginBottom: 24, opacity: 0.7,
        }}>
          TCG Scout
        </div>

        <h2 style={{
          fontSize: 'clamp(1.8rem, 5vw, 4rem)',
          letterSpacing: '-0.03em',
          lineHeight: 1.05,
          marginBottom: 16,
          fontWeight: 800,
        }}>
          {strings.finalCta.headline}
        </h2>

        <div style={{
          width: 64, height: 3,
          background: 'var(--accent-gold)',
          borderRadius: 2,
          margin: '0 auto 48px',
        }} />

        <a
          ref={btnRef}
          href={BOT_URL}
          target="_blank"
          rel="noopener noreferrer"
          className="btn-telegram"
          style={{ fontSize: '1.1rem', padding: '18px 52px' }}
          onMouseMove={(e) => {
            const el = e.currentTarget as HTMLElement;
            const rect = el.getBoundingClientRect();
            const dx = (e.clientX - (rect.left + rect.width / 2)) / (rect.width / 2);
            const dy = (e.clientY - (rect.top + rect.height / 2)) / (rect.height / 2);
            el.style.transform = `translateY(-4px) perspective(400px) rotateX(${-dy * 8}deg) rotateY(${dx * 8}deg)`;
          }}
          onMouseLeave={(e) => {
            (e.currentTarget as HTMLElement).style.transform = '';
          }}
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M22.265 2.428a1.5 1.5 0 0 0-1.52-.234L2.095 9.582a1.5 1.5 0 0 0 .101 2.82l4.25 1.36 2.04 6.44a1.5 1.5 0 0 0 2.55.534l2.406-2.758 4.73 3.477a1.5 1.5 0 0 0 2.328-1.01l2.999-16.5a1.5 1.5 0 0 0-.234-1.517zM10.12 14.52l-.9 3.14-.9-2.84 7.96-7.26-7.16 6.96z" fill="white"/></svg>
          {strings.finalCta.cta}
        </a>
      </div>

      <div style={{
        position: 'absolute', bottom: 0, left: '10%', right: '10%',
        height: 1,
        background: 'linear-gradient(90deg, transparent, rgba(245,183,49,0.15), transparent)',
      }} />
    </section>
  );
}
