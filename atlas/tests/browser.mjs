import { chromium } from 'playwright';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { PNG } from 'pngjs';

const url=process.env.ATLAS_URL || 'http://localhost:4173';
fs.mkdirSync('qa',{recursive:true});
const browser=await chromium.launch({channel:'chrome',headless:true,args:['--enable-webgl','--ignore-gpu-blocklist']});
const results=[];
const errors=[];
const page=await browser.newPage({viewport:{width:1536,height:960},deviceScaleFactor:1});
page.on('pageerror',error=>errors.push(error.message));
const stats=()=>page.evaluate(()=>window.__atlasViewer.getStats());
const settle=()=>page.waitForTimeout(140);
const range=async(id,value)=>{await page.locator(id).fill(String(value));await page.locator(id).dispatchEvent('input');await settle();};
const check=async(name,fn)=>{await fn();results.push(name);console.log(`PASS ${name}`);};
const shot=async(name)=>{await settle();await page.screenshot({path:`qa/${name}.png`});};
function foreground(buffer) {
  const png=PNG.sync.read(buffer);let count=0;
  for(let i=0;i<png.data.length;i+=4) if(Math.max(png.data[i],png.data[i+1],png.data[i+2])>80)count++;
  return count;
}

try {
  await page.goto(url);await page.waitForFunction(()=>window.__atlasReady,null,{timeout:60000});
  await check('source asset loads as 1857 parts / 2197 render meshes',async()=>{
    const data=await stats();assert.equal(data.parts,1857);assert.equal(data.meshes,2197);assert.equal(data.triangles,453552);
    assert.equal(data.systems['track-left'].total,85);assert.equal(data.systems['track-right'].total,85);
    const material=await page.evaluate(()=>window.__atlasViewer.partMap.get('Hull_Main_WeldedShell').mesh.material.color.toArray());
    assert.deepEqual(material,[.135,.173,.094]);
    assert.ok(foreground(await page.locator('#scene').screenshot())>30000);
    await shot('desktop');
  });
  await check('orbit gesture changes camera without selecting a part',async()=>{
    const before=await page.evaluate(()=>window.__atlasViewer.camera.position.toArray());
    await page.mouse.move(790,570);await page.mouse.down();await page.mouse.move(890,610,{steps:10});await page.mouse.up();await settle();
    const after=await page.evaluate(()=>window.__atlasViewer.camera.position.toArray());assert.notDeepEqual(before,after);
    assert.equal(await page.evaluate(()=>window.__atlasViewer.selectedId),null);
    await page.locator('#reset').click();
  });
  await check('raycast selection and clear selection work through pointer events',async()=>{
    const point=await page.evaluate(()=>{
      const v=window.__atlasViewer,r=v.canvas.getBoundingClientRect();
      for(let y=r.top+r.height*.4;y<r.bottom-100;y+=18)for(let x=r.left+80;x<r.right-80;x+=18)if(v.pick(x,y))return{x,y};
    });
    assert.ok(point);await page.mouse.click(point.x,point.y);await settle();
    assert.ok(await page.evaluate(()=>window.__atlasViewer.selectedId));
    await page.locator('#clear-selection').click();assert.equal(await page.evaluate(()=>window.__atlasViewer.selectedId),null);
  });
  await check('visibility, hidden selection, isolation and restoration retain expected state',async()=>{
    await page.locator('[data-system-visible="engine-deck"]').click();assert.equal((await stats()).visible,1642);
    await page.locator('[data-system="turret"]').click();await page.locator('#isolate').click();assert.equal((await stats()).visible,88);
    await page.locator('#isolate').click();assert.equal((await stats()).visible,1642);
    await page.locator('[data-system="engine-deck"]').click();assert.equal((await stats()).visible,1857);
    await page.locator('#hide-all').click();assert.equal((await stats()).visible,0);assert.equal(await page.locator('#empty-scene').isVisible(),true);
    await page.locator('#search').fill('L_TrackLink_001');await page.locator('[data-part="L_TrackLink_001"]').click();assert.equal((await stats()).visible,1);
    await page.locator('#show-all').click();await page.locator('#reset').click();assert.equal((await stats()).visible,1857);
  });
  await check('model presets and paginated search show the correct members',async()=>{
    await page.locator('#preset').selectOption('mobility');assert.equal((await stats()).visible,1224);
    await page.locator('#search').fill('负重轮');assert.equal(await page.locator('.search-results .part-row').count(),80);
    await page.locator('[data-search-more]').click();assert.equal(await page.locator('.search-results .part-row').count(),160);
    await page.locator('#reset').click();
  });
  await check('exploded and inventory layouts render and inventory avoids panel overlays',async()=>{
    await page.locator('[data-explode="35"]').click();assert.equal((await stats()).explode,.35);await shot('exploded');
    await page.locator('[data-explode="100"]').click();assert.equal((await stats()).explode,1);
    assert.equal(await page.evaluate(()=>window.__atlasViewer.controls.enableRotate),false);
    assert.equal(await page.evaluate(()=>window.__atlasViewer.camera.isOrthographicCamera),true);
    const layout=await page.evaluate(()=>{
      const v=window.__atlasViewer;v.camera.updateMatrixWorld(true);const bounds=[];
      for(const p of v.parts){const b=p.localBounds.clone().applyMatrix4(p.group.matrixWorld);const c=b.getCenter(p.center.clone()).project(v.camera);bounds.push(c.y);}
      return{maxY:Math.max(...bounds),minY:Math.min(...bounds)};
    });
    assert.ok(layout.maxY<.6,JSON.stringify(layout));assert.ok(layout.minY>-.9,JSON.stringify(layout));
    await shot('inventory');await page.locator('[data-explode="0"]').click();assert.equal(await page.evaluate(()=>window.__atlasViewer.controls.enableRotate),true);
  });
  await check('articulation rotates turret and gun without moving hull',async()=>{
    const matrix=async(id)=>page.evaluate(id=>window.__atlasViewer.partMap.get(id).group.matrix.toArray(),id);
    const hull=await matrix('Hull_Main_WeldedShell'),turret=await matrix('Turret_Main_WeldedShell'),gun=await matrix('Gun_ExternalTube_HollowMuzzle');
    await range('#yaw',45);await range('#elevation',15);
    assert.deepEqual(await matrix('Hull_Main_WeldedShell'),hull);assert.notDeepEqual(await matrix('Turret_Main_WeldedShell'),turret);assert.notDeepEqual(await matrix('Gun_ExternalTube_HollowMuzzle'),gun);
    await page.locator('#reset').click();
  });
  await check('clipping changes pixels, flips correctly, and rejects clipped raycast hits',async()=>{
    await page.locator('#grid').click();
    const baseline=foreground(await page.locator('#scene').screenshot());
    await page.locator('#tab-section').click();await page.locator('#clip-enabled').check();await range('#clip-position',100);
    const clipped=foreground(await page.locator('#scene').screenshot());assert.ok(clipped<baseline*.25,`${clipped}/${baseline}`);
    const picked=await page.evaluate(()=>{
      const v=window.__atlasViewer,r=v.canvas.getBoundingClientRect();
      return v.pick(r.x+r.width/2,r.y+r.height/2)?.id || null;
    });assert.equal(picked,null);
    await page.locator('#clip-flip').check();await settle();assert.ok(foreground(await page.locator('#scene').screenshot())>baseline*.8);
    await range('#clip-position',0);await shot('section');await page.locator('#reset').click();await page.locator('#tab-model').click();
  });
  await check('render modes and projection are operational',async()=>{
    for(const mode of ['systems','xray','wireframe','material']) {
      await page.locator(`[data-mode="${mode}"]`).click();assert.equal(await page.evaluate(()=>window.__atlasViewer.mode),mode);await settle();
      assert.ok(foreground(await page.locator('#scene').screenshot())>1000);
    }
    await page.locator('#projection').click();assert.equal(await page.evaluate(()=>window.__atlasViewer.camera.isOrthographicCamera),true);
    await page.locator('#projection').click();await page.locator('#rotate').click();
    const before=await page.evaluate(()=>window.__atlasViewer.camera.position.toArray());await page.waitForTimeout(300);
    assert.notDeepEqual(await page.evaluate(()=>window.__atlasViewer.camera.position.toArray()),before);await page.locator('#rotate').click();
  });
  await check('export preserves all three material primitives in a selected track link',async()=>{
    await page.locator('#search').fill('L_TrackLink_001');await page.locator('[data-part="L_TrackLink_001"]').click();
    const downloading=page.waitForEvent('download');await page.locator('#download').click();const download=await downloading;
    await download.saveAs('qa/exported-track.glb');const buffer=fs.readFileSync('qa/exported-track.glb');
    assert.equal(buffer.toString('utf8',0,4),'glTF');const gltf=JSON.parse(buffer.subarray(20,20+buffer.readUInt32LE(12)));
    assert.equal(gltf.meshes.length,3);assert.ok(buffer.length>10000);
    await page.locator('#reset').click();const capture=page.waitForEvent('download');await page.locator('#screenshot').click();const png=await capture;await png.saveAs('qa/exported-screenshot.png');assert.ok(fs.statSync('qa/exported-screenshot.png').size>10000);
  });
  await check('mobile and tablet are framed, interactive and free of page overflow',async()=>{
    for(const size of [{width:390,height:844},{width:768,height:1024},{width:1920,height:1080}]) {
      await page.setViewportSize(size);await settle();
      assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
      assert.ok(foreground(await page.locator('#scene').screenshot())>6000);
      await shot(`viewport-${size.width}`);
    }
    await page.setViewportSize({width:390,height:844});await settle();
    await page.locator('#open-structure').click();await page.locator('#search').fill('车体主壳');await page.locator('[data-part="Hull_Main_WeldedShell"]').click();
    assert.equal(await page.locator('#inspector-panel').evaluate(e=>e.classList.contains('is-open')),true);
    await page.locator('#isolate').click();assert.equal((await stats()).visible,1);await shot('mobile-inspector');
    await page.locator('#inspector-panel [data-close-panel]').click();await settle();assert.equal(await page.locator('#panel-backdrop').isVisible(),false);
    await page.locator('#reset').click();
  });
  assert.deepEqual(errors,[]);console.log(`PASS no browser exceptions; ${results.length} workflows verified`);
  fs.writeFileSync('qa/report.json',JSON.stringify({url,checks:results,errors,passed:true},null,2));
} finally { await browser.close(); }
