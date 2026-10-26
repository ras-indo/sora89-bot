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
      console.log('[BOT] Credentials found, attempting login...');
      // Try to find login form
      const loginSelectors = [
        'input[type="text"]',
        'input[type="username"]',
        'input[name*="user"]',
        'input[name*="login"]'
      ];
      
      for (const sel of loginSelectors) {
        try {
          const el = await page.$(sel);
          if (el) {
            await el.type(user, { delay: 50 });
            console.log('[BOT] Username filled');
            break;
          }
        } catch(e) {}
      }
      
      const passSelectors = [
        'input[type="password"]',
        'input[name*="pass"]'
      ];
      
      for (const sel of passSelectors) {
        try {
          const el = await page.$(sel);
          if (el) {
            await el.type(pass, { delay: 50 });
            console.log('[BOT] Password filled');
            break;
          }
        } catch(e) {}
      }
      
      await page.screenshot({ path: 'screenshot-login-filled.png' });
      
      // Try to click login
      const btnSelectors = [
        'button[type="submit"]',
        'input[type="submit"]',
        '.login-btn',
        '.btn-login'
      ];
      
      for (const sel of btnSelectors) {
        try {
          const el = await page.$(sel);
          if (el) {
            await el.click();
            console.log('[BOT] Login button clicked');
            break;
          }
        } catch(e) {}
      }
      
      await new Promise(r => setTimeout(r, 10000));
      await page.screenshot({ path: 'screenshot-after-login.png' });
      console.log('[BOT] Title after login:', await page.title());
      
      // Try to find and click PP Demo / Pragmatic Play Demo
      console.log('[BOT] Searching for PP Demo...');
      await new Promise(r => setTimeout(r, 5000));
      
      const demoKeywords = ['demo', 'pragmatic', 'pp', 'slot demo', 'main demo'];
      const links = await page.$$('a, button, .game-item, .slot-item');
      
      for (let i = 0; i < Math.min(links.length, 50); i++) {
        try {
          const text = await page.evaluate(el => el.innerText.toLowerCase(), links[i]);
          if (text.includes('demo') || text.includes('pragmatic') || text.includes('pp')) {
            console.log('[BOT] Found demo link:', text.substring(0, 50));
            await links[i].click();
            await new Promise(r => setTimeout(r, 8000));
            break;
          }
        } catch(e) {}
      }
      
      await page.screenshot({ path: 'screenshot-demo.png' });
      console.log('[BOT] Current URL:', page.url());
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
