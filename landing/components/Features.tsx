'use client';
import { strings } from '@/lib/i18n';
import { useEffect, useRef, useState } from 'react';

/* ── Demo components ────────────────────────────────── */

function AlertsDemo() {
  const CYCLE = 4000;
  const [tick, setTick] = useState(0);
  const [progress, setProgress] = useState(0);
  const rafRef = useRef<number | null>(null);
  const startRef = useRef<number | null>(null);

  useEffect(() => {
    const id = setInterval(() => setTick(t => t + 1), CYCLE);
    return () => clearInterval(id);
  }, []);

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
    { name: 'Pikachu ex 276/217', price: '$600', platform: 'TCGPlayer', platformColor: '#0968F6' },
    { name: 'Mega Gengar ex 284', price: '$890', platform: 'eBay', platformColor: '#e53238' },
    { name: 'Ascended Heroes ETB', price: '$310', platform: 'eBay', platformColor: '#e53238' },
  ];
  const thresholds = [0.62, 0.76, 0.90];

  const totalSeconds = Math.floor(progress * 420);
  const mins = Math.floor(totalSeconds / 60);
  const secs = totalSeconds % 60;
  const done = progress >= 0.95;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <style>{`
        @keyframes pop-in {
          0%   { opacity: 0; transform: translateY(6px) scale(0.97); }
          100% { opacity: 1; transform: translateY(0) scale(1); }
        }
      `}</style>

      {/* Timer */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        marginBottom: 4,
      }}>
        <span style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>scanning markets…</span>
        <span style={{
          fontSize: '1rem', fontWeight: 800, fontFamily: 'monospace',
          color: done ? 'var(--accent-teal)' : 'var(--accent-gold)',
          transition: 'color 0.3s',
        }}>
          {mins}:{secs.toString().padStart(2, '0')} <span style={{ fontSize: '0.65rem', opacity: 0.5 }}>/ 7:00</span>
        </span>
      </div>
      <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 4, height: 4, marginBottom: 4 }}>
        <div style={{
          width: `${progress * 100}%`, height: '100%',
          background: done ? 'var(--accent-teal)' : 'var(--accent-gold)',
          borderRadius: 4, transition: 'background 0.3s',
        }} />
      </div>

      {/* Listings */}
      {listings.map((item, i) => progress >= thresholds[i] ? (
        <div key={i} style={{
          display: 'flex', alignItems: 'center', gap: 10,
          background: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.2)',
          borderRadius: 12, padding: '10px 14px',
          animation: 'pop-in 0.3s ease forwards',
        }}>
          <span style={{
            width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
            background: 'var(--accent-teal)', boxShadow: '0 0 8px var(--accent-teal)',
          }} />
          <span style={{ flex: 1, color: 'var(--text-secondary)', fontFamily: 'monospace', fontSize: '0.82rem' }}>{item.name}</span>
          <span style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.82rem' }}>{item.price}</span>
          <span style={{
            fontSize: '0.62rem', color: item.platformColor, background: `${item.platformColor}22`,
            padding: '2px 8px', borderRadius: 20, flexShrink: 0,
          }}>{item.platform}</span>
        </div>
      ) : (
        <div key={i} style={{
          height: 42, background: 'rgba(255,255,255,0.02)',
          border: '1px solid rgba(255,255,255,0.05)', borderRadius: 12,
        }} />
      ))}
    </div>
  );
}

function SourcesDemo() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 14,
        background: 'rgba(255,255,255,0.04)', border: '1px solid #e5323833',
        borderRadius: 14, padding: '12px 16px',
      }}>
        <div style={{
          width: 40, height: 40, borderRadius: 10, flexShrink: 0,
          background: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          overflow: 'hidden',
        }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/ebay-logo.png" alt="eBay" style={{ width: 36, height: 36, objectFit: 'contain' }} />
        </div>
        <div>
          <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)' }}>eBay — Worldwide</div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', marginTop: 2 }}>Fixed price & auctions in real time</div>
        </div>
        <span style={{ marginInlineStart: 'auto', width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-teal)', boxShadow: '0 0 6px var(--accent-teal)', flexShrink: 0 }} />
      </div>
      <div style={{
        display: 'flex', alignItems: 'center', gap: 14,
        background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(9,104,246,0.3)',
        borderRadius: 14, padding: '12px 16px',
      }}>
        <div style={{
          width: 40, height: 40, borderRadius: 10, flexShrink: 0,
          background: '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          overflow: 'hidden', padding: 4,
        }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img src="/tcgplayer-logo.svg" alt="TCGPlayer" style={{ width: 32, height: 'auto', objectFit: 'contain' }} />
        </div>
        <div>
          <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)' }}>TCGPlayer — Marketplace</div>
          <div style={{ fontSize: '0.74rem', color: 'var(--text-secondary)', marginTop: 2 }}>Singles & sealed from verified sellers</div>
        </div>
        <span style={{ marginInlineStart: 'auto', width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-teal)', boxShadow: '0 0 6px var(--accent-teal)', flexShrink: 0 }} />
      </div>
    </div>
  );
}

function BrowseDemo() {
  const cards = [
    { name: 'Charizard ex', num: '199/165', color: '#f97316', img: 'https://images.pokemontcg.io/sv3pt5/199_hires.png' },
    { name: 'Blastoise ex', num: '200/165', color: '#60a5fa', img: 'https://images.pokemontcg.io/sv3pt5/200_hires.png' },
    { name: 'Pikachu IR',   num: '173/165', color: '#eab308', img: 'https://images.pokemontcg.io/sv3pt5/173_hires.png' },
    { name: 'Zapdos ex',    num: '202/165', color: '#facc15', img: 'https://images.pokemontcg.io/sv3pt5/202_hires.png' },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: 4, opacity: 0.6 }}>
        Scarlet &amp; Violet 151
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        {cards.map((c, i) => (
          <div key={i} style={{
            background: 'rgba(255,255,255,0.04)', border: `1px solid ${c.color}33`,
            borderRadius: 10, padding: '8px',
            transition: 'border-color .2s, background .2s', cursor: 'pointer',
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6,
          }}
            onMouseEnter={e => {
              (e.currentTarget as HTMLElement).style.borderColor = c.color;
              (e.currentTarget as HTMLElement).style.background = `${c.color}18`;
            }}
            onMouseLeave={e => {
              (e.currentTarget as HTMLElement).style.borderColor = `${c.color}33`;
              (e.currentTarget as HTMLElement).style.background = 'rgba(255,255,255,0.04)';
            }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src={c.img} alt={c.name} style={{ width: 52, borderRadius: 4, display: 'block' }} />
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontWeight: 700, color: 'var(--text-primary)', fontSize: '0.72rem' }}>{c.name}</div>
              <div style={{ fontSize: '0.6rem', opacity: 0.4, margin: '1px 0 4px' }}>{c.num}</div>
              <div style={{ fontSize: '0.62rem', color: 'var(--accent-teal)' }}>Alert</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AuctionDemo() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{
        background: 'rgba(0,212,170,0.06)', border: '1px solid rgba(0,212,170,0.25)',
        borderRadius: 14, padding: '16px',
      }}>
        <div style={{ fontSize: '0.88rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: 10 }}>
          Charizard ex SIR
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)' }}>Current bid</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-gold)' }}>$87</div>
          </div>
          <div style={{
            background: 'rgba(0,212,170,0.15)', color: 'var(--accent-teal)',
            padding: '4px 10px', borderRadius: 20, fontSize: '0.72rem', fontWeight: 700,
          }}>
            18% below target
          </div>
        </div>
        {/* Progress bar */}
        <div style={{ background: 'rgba(255,255,255,0.08)', borderRadius: 4, height: 6, marginBottom: 8 }}>
          <div style={{ width: '72%', height: '100%', background: 'var(--accent-teal)', borderRadius: 4 }} />
        </div>
        <div style={{ fontSize: '0.72rem', color: 'var(--text-secondary)', marginBottom: 12 }}>
          Ends in <span style={{ color: 'var(--accent-gold)', fontWeight: 700 }}>4h 12m</span>
        </div>
        <div style={{
          background: 'var(--accent-teal)', color: '#0a0a14',
          borderRadius: 8, padding: '6px 12px',
          fontSize: '0.72rem', fontWeight: 700, textAlign: 'center' as const,
        }}>
          Alert sent
        </div>
      </div>
    </div>
  );
}

function SealedDemo() {
  const items = [
    { name: 'SV 151 ETB',           price: '$58',   color: '#f97316', isNew: true  },
    { name: 'Evolving Skies ETB',    price: '$120',  color: '#6366f1', isNew: false },
    { name: 'Base Set Booster Box',  price: '$2,400',color: '#eab308', isNew: false },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {items.map((item, i) => (
        <div key={i} style={{
          display: 'flex', alignItems: 'center', gap: 10,
          background: 'rgba(255,255,255,0.03)', border: `1px solid ${item.color}22`,
          borderRadius: 12, padding: '10px 14px',
        }}>
          <div style={{
            width: 8, height: 8, borderRadius: '50%', flexShrink: 0,
            background: `${item.color}88`,
          }} />
          <span style={{ flex: 1, color: 'var(--text-secondary)', fontSize: '0.78rem', fontFamily: 'monospace' }}>{item.name}</span>
          <span style={{ color: 'var(--text-primary)', fontWeight: 700, fontSize: '0.78rem' }}>{item.price}</span>
          {item.isNew && <span style={{
            fontSize: '0.62rem', background: `${item.color}22`, color: item.color,
            padding: '2px 8px', borderRadius: 20, flexShrink: 0,
          }}>new</span>}
        </div>
      ))}
    </div>
  );
}

function GradedDemo() {
  const grades = [
    { label: 'PSA 10',  name: 'Charizard Holo 1st Ed.',  color: '#f5b731' },
    { label: 'PSA 9',   name: 'Lugia Neo Genesis',        color: '#94a3b8' },
    { label: 'CGC 9.5', name: 'Pikachu Illustrator',      color: '#60a5fa' },
  ];
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
      {grades.map((g, i) => (
        <div key={i} style={{
          display: 'flex', alignItems: 'center', gap: 12,
          background: 'rgba(255,255,255,0.03)', border: `1px solid ${g.color}33`,
          borderRadius: 12, padding: '10px 14px',
        }}>
          <div style={{
            background: `${g.color}22`, border: `1px solid ${g.color}66`,
            borderRadius: 8, padding: '4px 10px', fontSize: '0.72rem', fontWeight: 800,
            color: g.color, flexShrink: 0,
          }}>{g.label}</div>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>{g.name}</span>
        </div>
      ))}
    </div>
  );
}

/* ── Main ───────────────────────────────────────────── */
export default function Features() {
  const ref = useRef<HTMLElement>(null);
  const [active, setActive] = useState(0);
  const touchStart = useRef<number | null>(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => entries.forEach(e => e.target.classList.toggle('visible', e.isIntersecting)),
      { threshold: 0.08 }
    );
    ref.current?.querySelectorAll('.reveal').forEach(el => observer.observe(el));
    return () => observer.disconnect();
  }, []);

  const demos = [
    <AlertsDemo key={0} />,
    <SourcesDemo key={1} />,
    <BrowseDemo key={2} />,
    <AuctionDemo key={3} />,
    <SealedDemo key={4} />,
    <GradedDemo key={5} />,
  ];

  const total = strings.features.items.length;

  return (
    <>
      <style>{`
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; box-shadow: 0 0 8px var(--accent-teal); }
          50%       { opacity: 0.4; box-shadow: none; }
        }
        .feat-row {
          display: grid;
          grid-template-columns: 1fr 1fr;
          gap: 48px;
          align-items: center;
          padding: 48px 0;
          border-bottom: 1px solid rgba(245,183,49,0.07);
        }
        .feat-row:last-child { border-bottom: none; }
        .feat-demo {
          background: var(--bg-surface);
          border: 1px solid var(--border);
          border-radius: 20px;
          padding: 24px;
        }
        /* Mobile carousel */
        .feat-mobile { display: none; }
        @media (max-width: 768px) {
          .feat-desktop { display: none !important; }
          .feat-mobile  { display: block; }
        }
      `}</style>

      <section ref={ref} className="section-pad" style={{ background: 'var(--bg-deep)' }}>
        <div style={{ maxWidth: 960, margin: '0 auto' }}>
          <h2 className="reveal" style={{
            fontSize: 'clamp(1.8rem, 3vw, 2.8rem)',
            textAlign: 'center', marginBottom: 72, letterSpacing: '-0.02em',
          }}>
            {strings.features.title}
          </h2>

          {/* ── Desktop: alternating rows ── */}
          <div className="feat-desktop">
            {strings.features.items.map((feat, i) => {
              const textFirst = i % 2 === 0;
              return (
                <div key={i} className="feat-row reveal" style={{ transitionDelay: `${i * 80}ms`, direction: 'ltr' }}>
                  <div style={{ order: textFirst ? 0 : 1 }}>
                    <h3 style={{ fontSize: 'clamp(1.1rem, 2vw, 1.4rem)', letterSpacing: '-0.02em', marginBottom: 12, color: 'var(--text-primary)' }}>
                      {feat.title}
                    </h3>
                    <p style={{ fontSize: '0.95rem', lineHeight: 1.8, color: 'var(--text-secondary)' }}>
                      {feat.body}
                    </p>
                  </div>
                  <div className="feat-demo" style={{ order: textFirst ? 1 : 0 }}>{demos[i]}</div>
                </div>
              );
            })}
          </div>

          {/* ── Mobile: swipe carousel ── */}
          <div className="feat-mobile">
            {/* Slide */}
            <div
              style={{ overflow: 'hidden', touchAction: 'pan-y' }}
              onTouchStart={e => { touchStart.current = e.touches[0].clientX; }}
              onTouchEnd={e => {
                if (touchStart.current === null) return;
                const dx = e.changedTouches[0].clientX - touchStart.current;
                if (dx < -40 && active < total - 1) setActive(a => a + 1);
                if (dx > 40  && active > 0)          setActive(a => a - 1);
                touchStart.current = null;
              }}
            >
              {strings.features.items.map((feat, i) => (
                <div key={i} style={{
                  display: i === active ? 'flex' : 'none',
                  flexDirection: 'column',
                  gap: 24,
                }}>
                  {/* Text */}
                  <div>
                    <h3 style={{ fontSize: '1.25rem', letterSpacing: '-0.02em', marginBottom: 10, color: 'var(--text-primary)' }}>
                      {feat.title}
                    </h3>
                    <p style={{ fontSize: '0.92rem', lineHeight: 1.8, color: 'var(--text-secondary)' }}>
                      {feat.body}
                    </p>
                  </div>
                  {/* Demo */}
                  <div className="feat-demo">{demos[i]}</div>
                </div>
              ))}
            </div>

            {/* Dot indicators */}
            <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 28 }}>
              {strings.features.items.map((_, i) => (
                <div key={i} onClick={() => setActive(i)} style={{
                  width: i === active ? 20 : 7, height: 7, borderRadius: 4,
                  background: i === active ? 'var(--accent-gold)' : 'rgba(255,255,255,0.15)',
                  cursor: 'pointer',
                  transition: 'width 0.3s ease, background 0.3s ease',
                }} />
              ))}
            </div>
          </div>

        </div>
      </section>
    </>
  );
}
