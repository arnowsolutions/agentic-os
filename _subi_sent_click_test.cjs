const { chromium } = require('playwright');

(async () => {
  const URL = 'https://os.srv1738752.hstgr.cloud/api/subi-exit-invites?test=false';
  const text = async (pg) => (await pg.locator('#status-subi_10 a').innerText()).trim();
  const cls = async (pg) => (await pg.locator('#row-subi_10').getAttribute('class')) || '(none)';

  const b = await chromium.launch();
  const pg = await b.newPage();
  const errs = [];
  pg.on('pageerror', e => errs.push('pageerror: ' + String(e)));
  pg.on('console', m => { if (m.type() === 'error') errs.push('console.error: ' + m.text()); });

  await pg.goto(URL, { waitUntil: 'load', timeout: 45000 });
  console.log('on load      :', await text(pg), '| row class:', await cls(pg));

  await pg.locator('#status-subi_10 a').click();
  await pg.waitForTimeout(1500);
  console.log('after undo   :', await text(pg), '| row class:', await cls(pg));

  await pg.reload({ waitUntil: 'load' });
  console.log('after reload :', await text(pg), '| row class:', await cls(pg));

  await pg.locator('#status-subi_10 a').click();
  await pg.waitForTimeout(1500);
  console.log('re-marked    :', await text(pg), '| row class:', await cls(pg));

  await pg.reload({ waitUntil: 'load' });
  console.log('reload again :', await text(pg), '| row class:', await cls(pg));

  console.log('page errors  :', errs.length ? errs.join(' ;; ') : 'none');
  await b.close();
})().catch(e => { console.error('TEST FAILED:', e); process.exit(1); });
