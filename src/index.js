const puppeteer = require('puppeteer-core');
const path = require('path');
const fs = require('fs');

const CHROMIUM_PATH = process.env.CHROMIUM_PATH || '/usr/bin/chromium-browser' || '/snap/bin/chromium' || '/usr/bin/google-chrome';

async function run() {
  console.log('[BOT] Starting...');
  
  const browser = await puppeteer.launch({
    executablePath: CHROMIUM_PATH,
    headless: 'new',
    args: [
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--disable-gpu',
      '--window-size=1280,720'
    ]
  });

  try {
    const page = await browser.newPage();
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36');
    await page.setViewport({ width: 1280, height: 720 });

    console.log('[BOT] Navigating to sora89juli.com...');
    await page.goto('https://sora89juli.com/', { waitUntil: 'networkidle2', timeout: 60000 });
      
    await new Promise(r => setTimeout(r, 15000));
      
    const title = await page.title();
    console.log('[BOT] Title:', title);
      
    await page.screenshot({ path: 'screenshot-1.png' });
      
    const content = await page.content();
    if (content.includes('Just a moment') || content.includes('cf-challenge')) {
      console.log('[BOT] CF challenge detected, waiting...');
      await new Promise(r => setTimeout(r, 20000));
      await page.screenshot({ path: 'screenshot-cf.png' });
    }

    const user = process.env.SORA89_USER;
    const pass = process.env.SORA89_PASS;
      
    if (user && pass) {
      console.log('[BOT] Logging in...');
      const loginSelectors = [
        'input[type="text"]',
        'input[type="username"]',
        'input[name*="user"]',
        'input[name*="login"]',
        '#username',
        '#user'
      ];
        
      for (const sel of loginSelectors) {
        try {
          const el = await page.$(sel);
          if (el && await el.isVisible()) {
            await el.click({clickCount: 3});
            await el.type(user, { delay: 80 });
            console.log('[BOT] Username filled');
            break;
          }
        } catch(e) {}
      }
        
      const passSelectors = [
        'input[type="password"]',
        'input[name*="pass"]',
        '#password',
        '#pass'
      ];
        
      for (const sel of passSelectors) {
        try {
          const el = await page.$(sel);
          if (el && await el.isVisible()) {
            await el.click({clickCount: 3});
            await el.type(pass, { delay: 80 });
            console.log('[BOT] Password filled');
            break;
          }
        } catch(e) {}
      }
        
      await page.screenshot({ path: 'screenshot-login.png' });
        
      const btnSelectors = [
        'button[type="submit"]',
        'input[type="submit"]',
        '.login-btn',
        '.btn-login',
        '#login',
        '.btnSubmit'
      ];
        
      for (const sel of btnSelectors) {
        try {
          const el = await page.$(sel);
          if (el && await el.isVisible()) {
            await el.click();
            console.log('[BOT] Login clicked');
            break;
          }
        } catch(e) {}
      }
        
      await new Promise(r => setTimeout(r, 12000));
      await page.screenshot({ path: 'screenshot-logged-in.png' });
      console.log('[BOT] Logged in. Title:', await page.title());
        
      // Navigate to play/pragmatic/demo
      await new Promise(r => setTimeout(r, 5000));
        
      // Try to find and click PP/Pragmatic game
      const gameLinks = await page.$$('a, button, .game-item, .slot, [class*="game"]');
      for (let i = 0; i < gameLinks.length; i++) {
        try {
          const text = await page.evaluate(el => {
            return (el.innerText || el.textContent || '').toLowerCase();
          }, gameLinks[i]);
          if ((text.includes('pragmatic') || text.includes('pp')) && (text.includes('demo') || text.length < 80)) {
            console.log('[BOT] Clicking game:', text.substring(0, 40));
            await gameLinks[i].click();
            await new Promise(r => setTimeout(r, 10000));
            break;
          }
        } catch(e) {}
      }
        
      // Also try direct navigation or clicking any slot
      await page.screenshot({ path: 'screenshot-game.png' });
        
      // Try to play - click spin if exists
      await new Promise(r => setTimeout(r, 8000));
      const spinBtns = await page.$$('button, div[role="button"]');
      for (let i = 0; i < spinBtns.length; i++) {
        try {
          const text = await page.evaluate(el => {
            return (el.innerText || el.textContent || el.getAttribute('aria-label') || '').toLowerCase();
          }, spinBtns[i]);
          if (text.includes('spin') || text.includes('play') || text.includes('main')) {
            console.log('[BOT] Clicking play/spin');
            await spinBtns[i].click();
            await new Promise(r => setTimeout(r, 3000));
            await page.screenshot({ path: 'screenshot-spinning.png' });
            break;
          }
        } catch(e) {}
      }
        
      // Stay active for a while to look natural
      await new Promise(r => setTimeout(r, 30000));
      await page.screenshot({ path: 'screenshot-final.png' });
      console.log('[BOT] Session active');
    }
      
    console.log('[BOT] Done');
  } catch (e) {
    console.error('[BOT] Error:', e.message);
    try { await page.screenshot({ path: 'screenshot-error.png' }); } catch(ex){}
  } finally {
    await browser.close();
  }
}

run();
