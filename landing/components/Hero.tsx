'use client';
import { strings } from '@/lib/i18n';

const BOT_URL = 'https://t.me/PokeScoutBot';

const CARDS = [
  { video: '/charizard.mp4', alt: 'Charizard ex SIR',  rotate: '-18deg', translateX: '-140%', translateY: '-60%', zIndex: 1, floatCls: 'hero-card-f1' },
  { video: '/umbreon.mp4',   alt: 'Umbreon VMAX',       rotate:   '0deg', translateX:  '-50%', translateY: '-52%', zIndex: 2, floatCls: 'hero-card-f2' },
  { video: '/pikachu.mp4',   alt: 'Pikachu 151 IR',     rotate:  '16deg', translateX:  '40%',  translateY: '-58%', zIndex: 1, floatCls: 'hero-card-f3' },
];

export default function Hero() {
  return (
    <>
      <style>{`
        .hero-card {
          position: absolute;
          top: 50%;
          left: 50%;
          width: 200px;
          border-radius: 14px;
          overflow: hidden;
          box-shadow: 0 24px 60px rgba(0,0,0,0.7);
          cursor: pointer;
        }
        .hero-card video {
          display: block;
          width: 100%;
          height: auto;
          border-radius: 14px;
        }
        @keyframes card-float-1 {
          0%, 100% { margin-top: 0px; }
          50%       { margin-top: -14px; }
        }
        @keyframes card-float-2 {
          0%, 100% { margin-top: -8px; }
          50%       { margin-top: 8px; }
        }
        @keyframes card-float-3 {
          0%, 100% { margin-top: 0px; }
          50%       { margin-top: -18px; }
        }
        .hero-card-f1 { animation: card-float-1 6s   ease-in-out infinite; }
        .hero-card-f2 { animation: card-float-2 7.5s ease-in-out infinite; }
        .hero-card-f3 { animation: card-float-3 5.5s ease-in-out infinite; }
        @media (max-width: 768px) {
          .hero-card { width: 120px; }
        }
      `}</style>

      <section className="noise" style={{
        position: 'relative',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        paddingTop: '80px',
        paddingBottom: '60px',
        overflow: 'hidden',
      }}>

        {/* Background video */}
        <video
          autoPlay
          loop
          muted
          playsInline
          style={{
            position: 'absolute', inset: 0,
            width: '100%', height: '100%',
            objectFit: 'cover',
            zIndex: 0,
            pointerEvents: 'none',
          }}
        >
          <source src="/hero-bg.mp4" type="video/mp4" />
        </video>

        {/* Dark overlay for text contrast */}
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(135deg, rgba(8,8,18,0.88) 0%, rgba(8,8,18,0.72) 50%, rgba(8,8,18,0.82) 100%)',
          zIndex: 1,
          pointerEvents: 'none',
        }} />

        {/* 2-col grid */}
        <div className="hero-grid" style={{ padding: '0 clamp(20px, 5vw, 80px)', position: 'relative', zIndex: 2 }}>

          {/* Text */}
          <div className="hero-text" style={{ display: 'flex', flexDirection: 'column', gap: 28, alignItems: 'flex-start', textAlign: 'left' }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 8,
              background: 'rgba(245,183,49,0.1)', border: '1px solid var(--border)',
              borderRadius: '50px', padding: '6px 16px', width: 'fit-content',
              fontSize: '0.8rem', fontWeight: 600, color: 'var(--accent-gold)',
              letterSpacing: '0.05em', textTransform: 'uppercase',
            }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--accent-teal)', display: 'inline-block', boxShadow: '0 0 8px var(--accent-teal)' }} />
              {strings.hero.badge}
            </div>

            <h1 style={{ fontSize: 'clamp(2.2rem, 4.5vw, 3.8rem)', lineHeight: 1.08, letterSpacing: '-0.03em', color: 'var(--text-primary)' }}>
              {strings.hero.headline}
            </h1>

            <p style={{ fontSize: '1.05rem', lineHeight: 1.8, color: 'var(--text-secondary)', maxWidth: 440 }}>
              {strings.hero.sub}
            </p>

            <a href={BOT_URL} target="_blank" rel="noopener noreferrer" className="btn-telegram">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M22.265 2.428a1.5 1.5 0 0 0-1.52-.234L2.095 9.582a1.5 1.5 0 0 0 .101 2.82l4.25 1.36 2.04 6.44a1.5 1.5 0 0 0 2.55.534l2.406-2.758 4.73 3.477a1.5 1.5 0 0 0 2.328-1.01l2.999-16.5a1.5 1.5 0 0 0-.234-1.517zM10.12 14.52l-.9 3.14-.9-2.84 7.96-7.26-7.16 6.96z" fill="white"/></svg>
              {strings.hero.cta}
            </a>

            <p style={{ fontSize: '0.82rem', color: 'var(--text-secondary)', opacity: 0.6 }}>
              {strings.hero.smallPrint}
            </p>
          </div>

          {/* Fan stack */}
          <div className="hero-fan-cards" style={{ position: 'relative', width: '100%', height: 460, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
            {CARDS.map((card) => (
              <div
                key={card.alt}
                className={`hero-card holo-card ${card.floatCls}`}
                style={{
                  transform: `translate(${card.translateX}, ${card.translateY}) rotate(${card.rotate})`,
                  zIndex: card.zIndex,
                }}
                onMouseEnter={(e) => {
                  (e.currentTarget as HTMLElement).style.transform = `translate(${card.translateX}, calc(${card.translateY} - 16px)) rotate(${card.rotate}) scale(1.06)`;
                  (e.currentTarget as HTMLElement).style.boxShadow = '0 40px 80px rgba(0,0,0,0.85), 0 0 40px rgba(245,183,49,0.25)';
                  (e.currentTarget as HTMLElement).style.zIndex = '10';
                }}
                onMouseLeave={(e) => {
                  (e.currentTarget as HTMLElement).style.transform = `translate(${card.translateX}, ${card.translateY}) rotate(${card.rotate})`;
                  (e.currentTarget as HTMLElement).style.boxShadow = '0 24px 60px rgba(0,0,0,0.7)';
                  (e.currentTarget as HTMLElement).style.zIndex = String(card.zIndex);
                }}
              >
                <video src={card.video} autoPlay loop muted playsInline />
              </div>
            ))}
          </div>
        </div>

        {/* Ticker */}
        <div style={{
          position: 'absolute', bottom: 60, left: 0, right: 0,
          overflow: 'hidden',
          borderTop: '1px solid rgba(245,183,49,0.08)',
          borderBottom: '1px solid rgba(245,183,49,0.08)',
          padding: '8px 0',
          opacity: 0.5,
          zIndex: 3,
        }}>
          <div className="pricing-ticker">
            {[...Array(2)].map((_, rep) => (
              ['Charizard ex SIR · $312', 'Umbreon VMAX Alt Art · $1,290', 'Pikachu 151 IR · $59', 'Base Set Charizard · $334', 'Lugia Neo Genesis · $231'].map((item, i) => (
                <span key={`${rep}-${i}`} style={{
                  fontSize: '0.72rem',
                  color: 'var(--accent-gold)',
                  letterSpacing: '0.06em',
                  fontFamily: 'monospace',
                  textTransform: 'uppercase',
                }}>
                  {item} <span style={{ opacity: 0.4, margin: '0 8px' }}>◆</span>
                </span>
              ))
            )).flat()}
          </div>
        </div>

        {/* Bottom fade */}
        <div style={{
          position: 'absolute', bottom: 0, left: 0, right: 0, height: 140,
          background: 'linear-gradient(transparent, var(--bg-deep))',
          pointerEvents: 'none', zIndex: 4,
        }} />
      </section>
    </>
  );
}
