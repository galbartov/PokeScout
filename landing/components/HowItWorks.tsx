'use client';
import { strings } from '@/lib/i18n';
import { useEffect, useRef } from 'react';

/* ── Telegram UI primitives ───────────────────────── */

function TgBubble({ text, isBot = true }: { text: string; isBot?: boolean }) {
  return (
    <div style={{ display: 'flex', justifyContent: isBot ? 'flex-start' : 'flex-end', marginBottom: 6 }}>
      <div style={{
        background: isBot ? '#2a2a3e' : '#4a6fa5',
        color: '#f0f0f0',
        borderRadius: isBot ? '4px 16px 16px 16px' : '16px 4px 16px 16px',
        padding: '8px 12px',
        fontSize: '0.78rem',
        lineHeight: 1.5,
        maxWidth: '80%',
        fontFamily: 'var(--font-inter), sans-serif',
      }}>{text}</div>
    </div>
  );
}

function TgButton({ label, selected = false }: { label: string; selected?: boolean }) {
  return (
    <div style={{
      background: selected ? 'rgba(74,111,165,0.5)' : 'rgba(74,111,165,0.2)',
      border: `1px solid ${selected ? '#4a6fa5' : 'rgba(74,111,165,0.4)'}`,
      borderRadius: 8, padding: '7px 12px',
      fontSize: '0.75rem', color: selected ? '#fff' : '#c0c0d0',
      textAlign: 'center' as const, cursor: 'default',
      fontFamily: 'var(--font-inter), sans-serif',
    }}>{label}</div>
  );
}

function PhoneMockup({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      width: '100%', maxWidth: 240,
      background: '#111827', borderRadius: 20, overflow: 'hidden',
      boxShadow: '0 24px 48px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.06)',
    }}>
      <div style={{
        background: '#1a1a2e', padding: '10px 14px',
        display: 'flex', alignItems: 'center', gap: 10,
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img src="/bot-avatar.png" alt="TCG Scout" style={{ width: 32, height: 32, borderRadius: '50%', flexShrink: 0, objectFit: 'cover' }} />
        <div>
          <div style={{ fontSize: '0.78rem', fontWeight: 600, color: '#f0f0f0', fontFamily: 'var(--font-inter)' }}>TCG Scout</div>
          <div style={{ fontSize: '0.65rem', color: 'var(--accent-teal)', fontFamily: 'var(--font-inter)' }}>● online</div>
        </div>
      </div>
      <div style={{ padding: '12px 10px' }}>{children}</div>
    </div>
  );
}

function Step1Mockup() {
  return (
    <PhoneMockup>
      <TgBubble text="What are you looking for?" />
      <div style={{ display: 'flex', flexDirection: 'column', gap: 5, marginTop: 6 }}>
        <TgButton label="Single Cards" selected />
        <TgButton label="ETB / Booster Box" />
        <TgButton label="Graded Cards" />
        <TgButton label="Lots / Bulk" />
      </div>
    </PhoneMockup>
  );
}

function Step2Mockup() {
  return (
    <PhoneMockup>
      {/* ETB box art */}
      <div style={{
        borderRadius: 8, marginBottom: 8, overflow: 'hidden',
        border: '1px solid rgba(245,183,49,0.2)',
        background: '#1a1a3e',
      }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/sealed/sv-151-etb.jpg"
          alt="Scarlet & Violet 151 Elite Trainer Box"
          style={{ width: '100%', display: 'block' }}
        />
      </div>
      <div style={{
        background: 'rgba(245,183,49,0.07)',
        border: '1px solid rgba(245,183,49,0.2)',
        borderRadius: 8, padding: '6px 10px', marginBottom: 8,
        fontSize: '0.72rem', color: 'var(--text-secondary)',
        fontFamily: 'var(--font-inter)',
      }}>
        <span style={{ color: 'var(--accent-gold)', fontWeight: 700 }}>Last sold on eBay: </span>~$58
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
        <TgButton label="Alert on this item" selected />
        <TgButton label="Back to list" />
      </div>
    </PhoneMockup>
  );
}

function Step3Mockup() {
  return (
    <PhoneMockup>
      <TgBubble text="Deal found!" />
      <div style={{
        background: 'rgba(0,212,170,0.08)', border: '1px solid rgba(0,212,170,0.25)',
        borderRadius: 12, padding: '10px 12px', marginTop: 4,
      }}>
        <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--accent-teal)', marginBottom: 4, fontFamily: 'var(--font-inter)' }}>
          SV 151 ETB — Sealed
        </div>
        <div style={{ fontSize: '0.72rem', color: '#c0c0d0', marginBottom: 6, fontFamily: 'var(--font-inter)' }}>
          $89 · TCGPlayer
        </div>
        <div style={{
          background: 'var(--accent-teal)', color: '#0a0a14', borderRadius: 8,
          padding: '5px 10px', fontSize: '0.7rem', fontWeight: 700,
          textAlign: 'center' as const, fontFamily: 'var(--font-inter)',
        }}>→ View on TCGPlayer</div>
      </div>
      <div style={{ fontSize: '0.65rem', color: 'var(--text-secondary)', textAlign: 'center' as const, marginTop: 8, fontFamily: 'var(--font-inter)' }}>
        3 minutes ago
      </div>
    </PhoneMockup>
  );
}

/* ── Main component ───────────────────────────────── */

export default function HowItWorks() {
  const ref = useRef<HTMLElement>(null);
  const mockups = [
    <Step1Mockup key={0} />,
    <Step2Mockup key={1} />,
    <Step3Mockup key={2} />,
  ];

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => entries.forEach(e => e.target.classList.toggle('visible', e.isIntersecting)),
      { threshold: 0.05 }
    );
    ref.current?.querySelectorAll('.reveal').forEach(el => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  return (
    <section ref={ref} className="section-pad" style={{ background: 'var(--bg-surface)', position: 'relative' }}>
      <div style={{ maxWidth: 1100, margin: '0 auto' }}>

        <h2 className="reveal" style={{
          fontSize: 'clamp(1.8rem, 3vw, 2.8rem)',
          textAlign: 'center', marginBottom: 72, letterSpacing: '-0.02em',
        }}>
          {strings.how.title}
        </h2>

        {/* Timeline + cards */}
        <div style={{ position: 'relative' }}>

          {/* Timeline bar */}
          <div className="hiw-timeline-bar" style={{
            position: 'absolute',
            top: 20,
            left: '16.66%', right: '16.66%',
            height: 1,
            background: 'linear-gradient(90deg, transparent, rgba(245,183,49,0.3) 15%, rgba(245,183,49,0.3) 85%, transparent)',
            zIndex: 0,
          }} />

          {/* 3-column grid */}
          <div className="hiw-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 32, alignItems: 'stretch' }}>
            {strings.how.steps.map((step, i) => (
              <div key={i} className="reveal" style={{ transitionDelay: `${i * 120}ms`, display: 'flex', flexDirection: 'column', alignItems: 'center', height: '100%' }}>

                {/* Timeline dot */}
                <div style={{
                  width: 40, height: 40, borderRadius: '50%', flexShrink: 0,
                  background: 'var(--bg-surface)',
                  border: '2px solid rgba(245,183,49,0.5)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  zIndex: 1, marginBottom: 28,
                  boxShadow: '0 0 16px rgba(245,183,49,0.15)',
                }}>
                  <span style={{
                    fontWeight: 800, fontSize: '0.8rem',
                    color: 'var(--accent-gold)',
                  }}>{step.num}</span>
                </div>

                {/* Step title */}
                <h3 style={{
                  fontSize: '1rem', fontWeight: 700, marginBottom: 20,
                  color: 'var(--text-primary)', letterSpacing: '-0.01em',
                  textAlign: 'center',
                }}>
                  {step.title}
                </h3>

                {/* Phone mockup — grows to fill space */}
                <div style={{ width: '100%', display: 'flex', justifyContent: 'center', marginBottom: 20, flex: 1 }}>
                  {mockups[i]}
                </div>

                {/* Description — pinned to bottom */}
                <p style={{
                  fontSize: '0.85rem', lineHeight: 1.75,
                  color: 'var(--text-secondary)', textAlign: 'center',
                  minHeight: 60,
                }}>
                  {step.body}
                </p>

              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
