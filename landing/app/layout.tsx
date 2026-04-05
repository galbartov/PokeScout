import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import { Analytics } from '@vercel/analytics/next';
import './globals.css';

const inter = Inter({ subsets: ['latin'], weight: ['400', '500', '600', '700', '800'], variable: '--font-inter' });

export const metadata: Metadata = {
  title: 'TCG Scout — Your Personal Pokémon TCG Deal Hunter',
  description: 'Real-time Telegram alerts for Pokémon cards, ETBs, and graded slabs listed below market price on eBay worldwide.',
  icons: {
    icon: [
      { url: '/favicon.png', sizes: '32x32', type: 'image/png' },
      { url: '/icon-192.png', sizes: '192x192', type: 'image/png' },
      { url: '/icon-512.png', sizes: '512x512', type: 'image/png' },
    ],
    apple: '/apple-touch-icon.png',
  },
  openGraph: {
    title: 'TCG Scout — Your Personal Pokémon TCG Deal Hunter',
    description: 'Never overpay for a Pokémon card again. Get Telegram alerts the moment a deal appears on eBay.',
    type: 'website',
    images: [{ url: '/og-image.png', width: 1200, height: 630 }],
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${inter.variable}`}>
      <body>
        {children}
        <Analytics />
      </body>
    </html>
  );
}
