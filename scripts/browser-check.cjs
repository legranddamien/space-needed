/* Optional browser QA; run with the local preview server and Chrome installed. */
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const output=path.resolve(__dirname,'../.qa');fs.mkdirSync(output,{recursive:true});
const base=process.env.SITE_URL || 'http://localhost:8000/space-needed/';
const {chromium}=require('playwright');
const AxeBuilder=require('@axe-core/playwright').default;
const locales=['','fr-FR/','de/','es/','it/','ja/','ko/','pt-BR/','zh-Hans/'];
(async()=>{
 const browser=await chromium.launch({channel:'chrome',headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:1000}});
 const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 async function settle(){await page.evaluate(async()=>{await Promise.all(Array.from(document.images).filter(i=>i.loading!=='lazy'||i.getBoundingClientRect().top<innerHeight).map(i=>i.decode().catch(()=>{})));});await page.waitForTimeout(100);}
 const results=[];
 for(const locale of locales){for(const width of [1440,768,390,320]){await page.setViewportSize({width,height:1000});await page.goto(base+locale);for(const mode of ['light','dark']){
  await page.selectOption('#theme',mode);await settle();
  const metrics=await page.evaluate(()=>({viewport:innerWidth,width:document.documentElement.scrollWidth,broken:[...document.images].filter(i=>i.complete&&i.naturalWidth===0).map(i=>i.src),ice:getComputedStyle(document.documentElement).getPropertyValue('--ice')}));
  assert(metrics.width<=width,JSON.stringify({locale,mode,width,metrics}));assert.equal(metrics.broken.length,0);
  const lang=locale?locale.slice(0,-1):'en';
  await page.screenshot({path:path.join(output,`${lang}-${width}-${mode}.png`)});
  if(width===390||width===1440){await page.emulateMedia({reducedMotion:'reduce'});await page.waitForTimeout(200);const axe=await new AxeBuilder({page}).withTags(['wcag2a','wcag2aa','wcag21aa']).analyze();results.push({locale:lang,width,mode,violations:axe.violations.map(v=>({id:v.id,nodes:v.nodes.map(n=>n.target)}))});await page.emulateMedia({reducedMotion:'no-preference'});}
 }}}
 await page.setViewportSize({width:1440,height:1000});await page.goto(base);
 // Verify real frame advancement; an animation name alone does not prove motion.
 await page.waitForFunction(()=>getComputedStyle(document.querySelector('.ambient-arc')).animationPlayState==='running');
 const arcTransform=await page.locator('.ambient-arc').evaluate(e=>getComputedStyle(e).transform);
 await page.waitForTimeout(250);
 assert.notEqual(await page.locator('.ambient-arc').evaluate(e=>getComputedStyle(e).transform),arcTransform);
 await page.locator('#shot-onboarding').scrollIntoViewIfNeeded();await page.waitForFunction(()=>getComputedStyle(document.querySelector('[aria-labelledby="shot-onboarding"]')).opacity==='1');
 await page.selectOption('#theme','dark');await page.reload();assert.equal(await page.locator('#theme').inputValue(),'dark');
 await page.selectOption('#theme','system');await page.emulateMedia({colorScheme:'light'});await settle();assert((await page.locator('.hero-copy img').evaluate(e=>e.currentSrc)).includes('icon-light'));
 await page.emulateMedia({colorScheme:'dark'});await settle();assert((await page.locator('.hero-copy img').evaluate(e=>e.currentSrc)).includes('icon-dark'));
 await page.emulateMedia({reducedMotion:'reduce'});assert.equal(await page.locator('.ambient-arc').evaluate(e=>getComputedStyle(e).animationName),'none');
 await page.emulateMedia({reducedMotion:'no-preference'});await page.locator('#motion').click();assert.equal(await page.locator('#motion').getAttribute('aria-pressed'),'true');
 await page.reload();assert.equal(await page.locator('#motion').getAttribute('aria-pressed'),'true');
 await page.locator('.language summary').click();await page.keyboard.press('Escape');assert.equal(await page.locator('.language').getAttribute('open'),null);
 const published=/<item(?:\s|>)/.test(fs.readFileSync(path.resolve(__dirname,'../appcast.xml'),'utf8'));
 assert.equal(await page.locator('[data-download]').count(),published?3:0);assert.equal(await page.locator('button:disabled').count(),published?0:2);
 const nojs=await browser.newContext({javaScriptEnabled:false});const fallback=await nojs.newPage();await fallback.goto(base+'ja/');assert.equal(await fallback.locator('.showcase').count(),3);assert.equal(await fallback.locator('[data-source]').count(),24);
 fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({results,errors},null,2));
 console.log(JSON.stringify({pages:72,axeChecks:results.length,violations:results.filter(r=>r.violations.length).map(r=>({locale:r.locale,width:r.width,mode:r.mode,ids:r.violations.map(v=>v.id)})),errors},null,2));
 assert.equal(results.filter(r=>r.violations.length).length,0,'Accessibility violations; inspect .qa/results.json');assert.equal(errors.length,0);
 await browser.close();
})().catch(e=>{console.error(e);process.exit(1)});
