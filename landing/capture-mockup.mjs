import puppeteer from 'puppeteer';
import { execSync } from 'child_process';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const HTML_PATH = `file://${path.join(__dirname, 'public/bot-mockup.html')}`;
const FRAMES_DIR = path.join(__dirname, 'gif-frames');
const OUTPUT_GIF = path.join(__dirname, 'public/bot-mockup.gif');

const WIDTH = 640;
const HEIGHT = 360;
const FPS = 20;
const DURATION_MS = 28000; // full animation cycle

if (fs.existsSync(FRAMES_DIR)) fs.rmSync(FRAMES_DIR, { recursive: true });
fs.mkdirSync(FRAMES_DIR);

const browser = await puppeteer.launch({
  headless: true,
  args: ['--no-sandbox', '--disable-setuid-sandbox'],
});

const page = await browser.newPage();
await page.setViewport({ width: WIDTH, height: HEIGHT, deviceScaleFactor: 1 });
await page.goto(HTML_PATH, { waitUntil: 'networkidle0' });

// Wait for images to load
await new Promise(r => setTimeout(r, 1000));

const totalFrames = Math.floor((DURATION_MS / 1000) * FPS);
const frameInterval = 1000 / FPS;

console.log(`Capturing ${totalFrames} frames at ${FPS}fps...`);

for (let i = 0; i < totalFrames; i++) {
  const framePath = path.join(FRAMES_DIR, `frame-${String(i).padStart(5, '0')}.png`);
  await page.screenshot({ path: framePath });
  await new Promise(r => setTimeout(r, frameInterval));
  if (i % 20 === 0) process.stdout.write(`\r  Frame ${i}/${totalFrames}`);
}

await browser.close();
console.log('\nFrames captured. Converting to GIF...');

// Use ffmpeg to create GIF with palette for quality
execSync(`ffmpeg -y -framerate ${FPS} -i "${FRAMES_DIR}/frame-%05d.png" \
  -vf "fps=${FPS},scale=${WIDTH}:${HEIGHT}:flags=lanczos,split[s0][s1];[s0]palettegen=max_colors=128[p];[s1][p]paletteuse=dither=bayer" \
  "${OUTPUT_GIF}"`, { stdio: 'inherit' });

fs.rmSync(FRAMES_DIR, { recursive: true });
console.log(`\nDone! GIF saved to: ${OUTPUT_GIF}`);
