'use client';
import { strings } from '@/lib/i18n';
import { useEffect, useRef, useState } from 'react';

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
  const CYCLE = 4000; // ms for one full cycle
  const [tick, setTick] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), CYCLE);
    return () => clearInterval(id);
  }, []);

  // progress 0→1 over CYCLE ms, then reset
  const [progress, setProgress] = useState(0);
  const rafRef = useRef<number | null>(null);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    startRef.current = null;
    setProgress(0);
    const animate = (now: number) => {
      if (!startRef.current) startRef.current = now;
      const p = Math.min((now - startRef.current) / CYCLE, 1);
      setProgress(p);
      if (p < 1) rafRef.current = requestAnimationFrame(animate);
    };
    rafRef.current = requestAnimationFrame(animate);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, [tick]);

  const listings = [
    { name: 'Pikachu ex 276/217', price: '$600', platform: 'TCGPlayer', color: '#0968F6' },
    { name: 'Mega Gengar ex 284', price: '$890', platform: 'eBay', color: '#e53238' },
    { name: 'Ascended Heroes ETB', price: '$310', platform: 'eBay', color: '#e53238' },
  ];

  // each listing appears after 60%, 75%, 90% progress
  const thresholds = [0.62, 0.76, 0.90];

  // minutes shown on timer: animate 0:00 → 7:00
  const totalSeconds = Math.floor(progress * 420);
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;

  return (
    <PhoneMockup>
      <style>{`
        @keyframes pop-in {
          0%   { opacity: 0; transform: translateY(8px) scale(0.95); }
          100% { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>

      {/* Timer */}
      <div style={{ textAlign: 'center' as const, marginBottom: 12 }}>
        <div style={{ fontSize: '0.62rem', color: 'var(--text-secondary)', marginBottom: 4, fontFamily: 'var(--font-inter)' }}>
          scanning markets…
        </div>
        <div style={{
          fontSize: '1.6rem', fontWeight: 800, fontFamily: 'monospace',
          color: progress >= 0.95 ? 'var(--accent-teal)' : 'var(--accent-gold)',
          letterSpacing: 2,
          transition: 'color 0.3s',
        }}>
          {mins}:{secs.toString().padStart(2, '0')}
        </div>
        {/* Progress bar */}
        <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 4, height: 4, marginTop: 6 }}>
          <div style={{
            width: `${progress * 100}%`, height: '100%',
            background: progress >= 0.95 ? 'var(--accent-teal)' : 'var(--accent-gold)',
            borderRadius: 4, transition: 'background 0.3s',
          }} />
        </div>
      </div>

      {/* Listings popping in */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
        {listings.map((item, i) => progress >= thresholds[i] ? (
          <div key={i} style={{
            display: 'flex', alignItems: 'center', gap: 8,
            background: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.2)',
            borderRadius: 10, padding: '7px 10px',
            animation: 'pop-in 0.3s ease forwards',
          }}>
            <span style={{
              width: 7, height: 7, borderRadius: '50%', flexShrink: 0,
              background: 'var(--accent-teal)', boxShadow: '0 0 6px var(--accent-teal)',
            }} />
            <span style={{ flex: 1, fontSize: '0.68rem', color: 'var(--text-secondary)', fontFamily: 'var(--font-inter)' }}>
              {item.name}
            </span>
            <span style={{ fontSize: '0.72rem', fontWeight: 700, color: 'var(--text-primary)', fontFamily: 'var(--font-inter)' }}>
              {item.price}
            </span>
            <span style={{
              fontSize: '0.58rem', color: item.color, background: `${item.color}22`,
              padding: '1px 6px', borderRadius: 20, flexShrink: 0, fontFamily: 'var(--font-inter)',
            }}>
              {item.platform}
            </span>
          </div>
        ) : (
          <div key={i} style={{
            height: 34, background: 'rgba(255,255,255,0.02)',
            border: '1px solid rgba(255,255,255,0.05)', borderRadius: 10,
          }} />
        ))}
      </div>
    </PhoneMockup>
  );
}

function Step2Mockup() {
  return (
    <PhoneMockup>
      {/* Card image */}
      <div style={{
        borderRadius: 8, marginBottom: 8, overflow: 'hidden',
        border: '1px solid rgba(245,183,49,0.2)',
        background: '#1a1a3e',
      }}>
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src="/pikachu-ex-276.jpg"
          alt="Pikachu ex 276/217"
          style={{ width: '100%', display: 'block' }}
        />
      </div>
      <div style={{
        fontSize: '0.68rem', color: 'var(--text-secondary)',
        fontFamily: 'var(--font-inter)', marginBottom: 4, textAlign: 'center' as const,
      }}>
        Pikachu ex · 276/217 · ME: Ascended Heroes
      </div>
      <div style={{
        background: 'rgba(245,183,49,0.07)',
        border: '1px solid rgba(245,183,49,0.2)',
        borderRadius: 8, padding: '6px 10px', marginBottom: 8,
        fontSize: '0.72rem', color: 'var(--text-secondary)',
        fontFamily: 'var(--font-inter)',
      }}>
        <span style={{ color: 'var(--accent-gold)', fontWeight: 700 }}>Last sold on eBay: </span>~$665
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
          Pikachu ex 276/217 — ASC
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginBottom: 6 }}>
          <span style={{ fontSize: '0.72rem', color: '#c0c0d0', fontFamily: 'var(--font-inter)' }}>$600 · TCGPlayer</span>
          <span style={{
            fontSize: '0.62rem', background: 'rgba(0,212,170,0.15)', color: 'var(--accent-teal)',
            padding: '1px 7px', borderRadius: 20, fontWeight: 700, fontFamily: 'var(--font-inter)',
          }}>−9.8%</span>
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
