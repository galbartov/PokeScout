import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Subscribed — TCG Scout',
};

export default function SubscribeSuccessPage() {
  return (
    <main style={{
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--bg-deep)',
      fontFamily: 'var(--font-inter), sans-serif',
      padding: '40px 24px',
      textAlign: 'center',
    }}>
      <div style={{ maxWidth: 480 }}>
        <div style={{ fontSize: '3rem', marginBottom: 20 }}>✅</div>
        <h1 style={{ fontSize: '1.8rem', fontWeight: 800, color: 'var(--text-primary)', marginBottom: 12, letterSpacing: '-0.02em' }}>
          You&apos;re all set!
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem', lineHeight: 1.7, marginBottom: 32 }}>
          Your TCG Scout Pro subscription is now active. Head back to Telegram — you&apos;ll receive unlimited deal alerts starting now.
        </p>
        <Link href="https://t.me/PokeScoutBot" style={{
          display: 'inline-block',
          background: 'var(--accent-teal)',
          color: '#0a0a14',
          fontWeight: 700,
          padding: '12px 28px',
          borderRadius: 10,
          textDecoration: 'none',
          fontSize: '0.95rem',
        }}>
          Open TCG Scout on Telegram
        </Link>
      </div>
    </main>
  );
}
