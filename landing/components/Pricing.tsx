'use client';
import { strings } from '@/lib/i18n';
import { useEffect, useRef } from 'react';

const BOT_URL = 'https://t.me/PokeScoutBot';

export default function Pricing() {
  const ref = useRef<HTMLElement>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => entries.forEach(e => e.target.classList.toggle('visible', e.isIntersecting)),
      { threshold: 0.1 }
    );
    ref.current?.querySelectorAll('.reveal').forEach(el => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <>
      <style>{`
        .pricing-ticker {
          display: flex;
          gap: 48px;
          animation: ticker-scroll 18s linear infinite;
          white-space: nowrap;
        }
        @keyframes ticker-scroll {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }
        .pricing-card {
          transition: transform .2s cubic-bezier(.22,1,.36,1), box-shadow .2s;
          will-change: transform;
        }
        @media (max-width: 768px) {
          .pricing-grid-inner {
            grid-template-columns: 1fr !important;
          }
        }
      `}</style>

      <section ref={ref} className="section-pad-lg" style={{
        background: 'var(--bg-deep)',
        position: 'relative',
        overflow: 'hidden',
      }}>

        {/* Diagonal gold scan line */}
        <div style={{
          position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
          background: 'repeating-linear-gradient(105deg, transparent 0px, transparent 120px, rgba(245,183,49,0.018) 120px, rgba(245,183,49,0.018) 121px)',
          pointerEvents: 'none',
        }} />

        <div style={{ maxWidth: 760, margin: '0 auto', position: 'relative', zIndex: 1 }}>
          <h2 className="reveal" style={{
            fontSize: 'clamp(1.8rem, 3vw, 2.8rem)',
            textAlign: 'center',
            marginBottom: 16,
            letterSpacing: '-0.02em',
          }}>
            {strings.pricing.title}
          </h2>

          <p className="reveal" style={{
            textAlign: 'center',
            color: 'var(--accent-teal)',
            fontSize: '0.85rem',
            fontWeight: 600,
            letterSpacing: '0.06em',
            textTransform: 'uppercase',
            marginBottom: 60,
          }}>
            {strings.pricing.badge}
          </p>

          {/* Single unified card */}
          <div
            className="reveal pricing-card"
            style={{
              background: 'linear-gradient(150deg, #1c1500 0%, #0f0f1e 50%, #0a0a14 100%)',
              border: '1px solid rgba(245,183,49,0.4)',
              borderRadius: 28,
              padding: 'clamp(32px, 5vw, 52px)',
              position: 'relative',
              overflow: 'hidden',
              boxShadow: '0 0 0 1px rgba(245,183,49,0.08), 0 40px 80px rgba(0,0,0,0.5), inset 0 1px 0 rgba(245,183,49,0.15)',
            }}
            onMouseMove={(e) => {
              const el = e.currentTarget as HTMLElement;
              const rect = el.getBoundingClientRect();
              const dx = (e.clientX - (rect.left + rect.width / 2)) / (rect.width / 2);
              const dy = (e.clientY - (rect.top + rect.height / 2)) / (rect.height / 2);
              el.style.transform = `perspective(1200px) rotateY(${dx * 3}deg) rotateX(${-dy * 3}deg) translateZ(6px)`;
              el.style.boxShadow = `0 0 0 1px rgba(245,183,49,0.15), 0 60px 100px rgba(0,0,0,0.6), 0 0 60px rgba(245,183,49,0.1), inset 0 1px 0 rgba(245,183,49,0.2)`;
            }}
            onMouseLeave={(e) => {
              const el = e.currentTarget as HTMLElement;
              el.style.transform = '';
              el.style.boxShadow = '0 0 0 1px rgba(245,183,49,0.08), 0 40px 80px rgba(0,0,0,0.5), inset 0 1px 0 rgba(245,183,49,0.15)';
            }}
          >
            {/* Corner glow */}
            <div style={{
              position: 'absolute', top: -80, right: -80, width: 280, height: 280,
              background: 'radial-gradient(circle, rgba(245,183,49,0.12) 0%, transparent 70%)',
              pointerEvents: 'none',
            }} />

            {/* Coming Soon badge */}
            <div style={{
              position: 'absolute', top: 20, right: 20,
              background: 'rgba(245,183,49,0.15)',
              border: '1px solid rgba(245,183,49,0.4)',
              borderRadius: 50,
              padding: '4px 14px',
              fontSize: '0.72rem',
              fontWeight: 700,
              color: 'var(--accent-gold)',
              letterSpacing: '0.07em',
              textTransform: 'uppercase',
            }}>
              Pro · Coming Soon
            </div>

            {/* Pricing display */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              textAlign: 'center',
              marginBottom: 40,
            }}>
              {/* Free line */}
              <div style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 10,
                background: 'rgba(0,212,170,0.1)',
                border: '1px solid rgba(0,212,170,0.3)',
                borderRadius: 50,
                padding: '8px 20px',
                marginBottom: 16,
              }}>
                <span style={{ color: 'var(--accent-teal)', fontSize: '1.2rem', fontWeight: 700 }}>—</span>
                <span style={{ color: 'var(--accent-teal)', fontWeight: 700, fontSize: '1rem' }}>
                  {strings.pricing.freeLine}
                </span>
              </div>

              {/* Arrow */}
              <div style={{ color: 'rgba(255,255,255,0.2)', fontSize: '1.4rem', lineHeight: 1, marginBottom: 16 }}>↓</div>

              {/* Then line */}
              <div style={{ display: 'flex', alignItems: 'baseline', gap: 6, marginBottom: 4 }}>
                <span style={{
                  fontSize: 'clamp(3rem, 6vw, 4.5rem)',
                  fontWeight: 800,
                  color: 'var(--accent-gold)',
                  lineHeight: 1,
                }}>$9.99</span>
                <span style={{ color: 'var(--text-secondary)', fontSize: '1rem' }}>/ mo</span>
              </div>
              <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: 0 }}>
                {strings.pricing.thenLine}
              </div>
            </div>

            {/* Savings callout */}
            <div style={{
              background: 'rgba(245,183,49,0.06)',
              border: '1px solid rgba(245,183,49,0.2)',
              borderRadius: 16,
              padding: '20px 24px',
              marginBottom: 36,
              position: 'relative',
            }}>
              <div style={{
                fontSize: '1rem',
                fontWeight: 700,
                color: 'var(--accent-gold)',
                marginBottom: 8,
              }}>
                {strings.pricing.savingsHeadline}
              </div>
              <div style={{ fontSize: '0.88rem', color: 'var(--text-secondary)', lineHeight: 1.7 }}>
                {strings.pricing.savingsBody}
              </div>
            </div>

            {/* Feature grid */}
            <div className="pricing-grid-inner" style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr',
              gap: '12px 24px',
              marginBottom: 40,
            }}>
              {strings.pricing.features.map((f, i) => (
                <div key={i} style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 10,
                  fontSize: '0.9rem',
                  color: 'var(--text-primary)',
                  lineHeight: 1.5,
                }}>
                  <span style={{
                    color: '#0a0a14',
                    background: 'var(--accent-gold)',
                    width: 18, height: 18,
                    borderRadius: '50%',
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.6rem',
                    fontWeight: 900,
                    flexShrink: 0,
                    marginTop: 2,
                  }}>✓</span>
                  {f}
                </div>
              ))}
            </div>

            {/* Divider */}
            <div style={{ height: 1, background: 'rgba(245,183,49,0.12)', marginBottom: 32 }} />

            {/* CTA */}
            <a
              href={BOT_URL}
              target="_blank"
              rel="noopener noreferrer"
              className="btn-telegram"
              style={{ width: '100%', justifyContent: 'center', fontSize: '1.05rem', padding: '18px' }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M22.265 2.428a1.5 1.5 0 0 0-1.52-.234L2.095 9.582a1.5 1.5 0 0 0 .101 2.82l4.25 1.36 2.04 6.44a1.5 1.5 0 0 0 2.55.534l2.406-2.758 4.73 3.477a1.5 1.5 0 0 0 2.328-1.01l2.999-16.5a1.5 1.5 0 0 0-.234-1.517zM10.12 14.52l-.9 3.14-.9-2.84 7.96-7.26-7.16 6.96z" fill="white"/></svg>
              {strings.pricing.cta}
            </a>
            <p style={{
              textAlign: 'center',
              fontSize: '0.78rem',
              color: 'var(--text-secondary)',
              marginTop: 14,
              opacity: 0.6,
            }}>
              {strings.pricing.note}
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
