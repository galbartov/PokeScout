export const strings = {
  nav: {
    cta: 'Start on Telegram',
  },
  hero: {
    headline: 'Your Personal Pokémon TCG Deal Hunter.',
    sub: 'TCG Scout monitors eBay & TCGPlayer 24/7 and alerts you on Telegram the moment a card or sealed product drops below your target price.',
    cta: 'Start for Free on Telegram',
    badge: 'Live on eBay & TCGPlayer 24/7',
    smallPrint: '10 free alerts, no credit card required',
  },
  how: {
    title: 'How It Works',
    steps: [
      {
        num: '01',
        title: 'Browse & pick anything',
        body: 'Cards, ETBs, booster boxes. Browse by set or search by name. Tap any product to set up an alert.',
      },
      {
        num: '02',
        title: 'Set your target price',
        body: 'Enter the max you\'re willing to pay and we\'ll watch eBay and TCGPlayer for anything under it.',
      },
      {
        num: '03',
        title: 'Get alerted instantly',
        body: 'The moment a matching listing appears on eBay or TCGPlayer, you get a Telegram message with a direct link.',
      },
    ],
  },
  features: {
    title: 'Everything a Collector Needs',
    items: [
      { icon: '', title: 'Live alerts every 7 min', body: 'Listings are checked constantly. Be the first to grab the deal.' },
      { icon: '', title: 'eBay & TCGPlayer', body: 'Covers eBay listings globally and TCGPlayer marketplace. Fixed price and auctions, all in one place.' },
      { icon: '', title: 'Browse sets, alert any card', body: 'Use /browse to explore any TCG set and tap a card to create an alert. No typing needed.' },
      { icon: '', title: 'Auction alerts', body: 'Get alerted when an auction ends within 24h and the current bid is below your target price.' },
      { icon: '', title: 'Singles, sealed, graded, bulk', body: 'Filter by what you collect: single cards, sealed products, PSA/CGC graded, or bulk lots.' },
    ],
  },
  pricing: {
    title: 'Simple Pricing',
    badge: 'No credit card required',
    freeLine: '10 free alerts to get started',
    thenLine: 'then $9.99 / month for Pro',
    savingsHeadline: 'Serious collectors save hundreds',
    savingsBody: 'A single good deal on a Charizard ex SIR or an ETB can save you $50-$200. At $9.99/month, TCG Scout pays for itself on day one.',
    features: [
      'First 10 deal alerts free, no card needed',
      'Up to 10 saved alerts on free plan',
      'Up to 50 saved alerts on Pro',
      'Unlimited notifications on Pro',
      'eBay & TCGPlayer — fixed price & auctions',
      'Singles, sealed, graded & bulk',
      'Auction ending-soon alerts',
      'Condition, shipping & seller trust info',
      'Cancel anytime',
    ],
    cta: 'Start for Free on Telegram',
    note: 'Type /subscribe in the bot to upgrade after your free alerts',
  },
  faq: {
    title: 'Questions? Answers.',
    items: [
      {
        q: 'Which eBay listings do you monitor?',
        a: 'We monitor all eBay listings worldwide and TCGPlayer marketplace, both fixed price and auctions. New sources are added regularly.',
      },
      {
        q: 'How do auction alerts work?',
        a: 'When an auction\'s current bid is below your target price and it ends within 1 hour, you\'ll get a Telegram alert with a direct link so you can place your bid in time.',
      },
      {
        q: 'How quickly will I be alerted after a listing goes up?',
        a: 'Listings are checked roughly every 7 minutes. You\'ll typically be notified within minutes of a new listing going live.',
      },
      {
        q: 'Can I set alerts for multiple cards at once?',
        a: 'Yes. Create as many alert preferences as you want (unlimited on Pro). Each preference covers a different card, price range, and category.',
      },
      {
        q: 'Do I need a Telegram account?',
        a: 'Yes. TCG Scout is a Telegram bot. If you don\'t have Telegram yet, it\'s free to download and takes 30 seconds to sign up.',
      },
      {
        q: 'Is my payment secure?',
        a: 'Payments are processed by PayPal. We never see or store your card details.',
      },
    ],
  },
  finalCta: {
    headline: 'Ready to stop missing deals?',
    cta: 'Open TCG Scout on Telegram',
  },
  footer: {
    tagline: 'Built for Pokémon TCG collectors worldwide.',
    links: ['Telegram Bot', 'Terms of Service', 'Contact'],
    disclaimer: 'TCG Scout is not affiliated with Nintendo, The Pokémon Company, or Wizards of the Coast.',
  },
};

export type Strings = typeof strings;
