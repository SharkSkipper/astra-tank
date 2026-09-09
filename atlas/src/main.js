import { createIcons, Boxes, Box, Download, Eye, EyeOff, X, Search, PanelLeft, SlidersHorizontal, Layers, Scan, Network, RotateCcw, Focus, Orbit, Grid2x2, Cuboid, Camera, Maximize, Info, ScanLine, Contrast, Rotate3d, ArrowUpRight, ExternalLink, ChevronRight, ChevronDown } from 'lucide';
import { ModelViewer } from './viewer.js';
import { SYSTEMS, getPartDescription } from './model-data.js';
import './style.css';

const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const icons = {Boxes,Box,Download,Eye,EyeOff,X,Search,PanelLeft,SlidersHorizontal,Layers,Scan,Network,RotateCcw,Focus,Orbit,Grid2x2,Cuboid,Camera,Maximize,Info,ScanLine,Contrast,Rotate3d,ArrowUpRight,ExternalLink,ChevronRight,ChevronDown};
const icon = name => `<i data-lucide="${name}"></i>`;
const refreshIcons = () => createIcons({icons, attrs:{'aria-hidden':'true'}});
let viewer, ready = false, selected = null, stats, toastTimer;
let expanded = new Set(), limits = {}, searchLimit = 80;
let clipAxis = 'x';

function notify(message) {
  $('#toast').textContent = message; $('#toast').hidden = false;
  clearTimeout(toastTimer); toastTimer = setTimeout(() => { $('#toast').hidden = true; }, 3200);
}
function press(element, active) { element.classList.toggle('active',active); element.setAttribute('aria-pressed',String(active)); }
function setError(error) {
  ready = false; $('#loading').hidden = false;
  $('#loading-title').textContent = '模型载入失败';
  $('#loading-text').textContent = error.message || '无法读取模型文件';
  $('#loading-progress').hidden = true; $('#retry').hidden = false;
  $('#header-status').textContent = '载入失败'; $('#scene-status').textContent = '载入失败';
  $('#download').disabled = true;
}
function updateStats(value) {
  stats = value;
  $('#visible-count').textContent = `${value.visible.toLocaleString()} / ${value.parts.toLocaleString()} 部件`;
  $('#empty-scene').hidden = value.visible !== 0 || !ready;
  $('#scene-status').textContent = value.isolated ? '单独查看' : value.explode >= .8 ? '零件平铺' : value.explode > 0 ? '分解视图' : '模型就绪';
  $('#explode').value = Math.round(value.explode*100);
  $('#explode-value').innerHTML = `${Math.round(value.explode*100)}<span>%</span>`;
  $$('[data-explode]').forEach(button => button.classList.toggle('active', Number(button.dataset.explode) === Math.round(value.explode*100)));
  $('#auto-rotate').checked = value.autoRotate;
  $('#auto-rotate').disabled = value.explode >= .4;
  press($('#rotate'), value.autoRotate); $('#rotate').disabled = value.explode >= .4;
  $('#view').disabled = value.explode >= .8; $('#projection').disabled = value.explode >= .8;
  if(viewer) press($('#projection'), Boolean(viewer.camera.isOrthographicCamera));
  $('#isolate span').textContent = value.isolated ? '恢复装配' : '单独查看';
  $('#view').value = viewer?.currentView || 'perspective';
  $$('[data-system-visible]').forEach(button => {
    const s = value.systems[button.dataset.systemVisible];
    if (!s) return;
    const visible = s.visible > 0;
    button.setAttribute('aria-pressed',String(visible));
    button.closest('.system-row').classList.toggle('is-hidden',!visible);
    button.setAttribute('aria-label',`${visible ? '隐藏' : '显示'}${SYSTEMS.find(system => system.id === button.dataset.systemVisible).label}`);
  });
  $$('[data-part-visible]').forEach(button => {
    const part = viewer?.partMap.get(button.dataset.partVisible);
    button.closest('.part-row').classList.toggle('is-hidden',!part?.group.visible);
  });
}
function partRow(part) {
  return `<div class="part-row ${selected?.id === part.id ? 'selected' : ''} ${part.group.visible ? '' : 'is-hidden'}"><button class="part-select" data-part="${escape(part.id)}" title="${escape(part.label)} · ${escape(part.name)}">${icon('box')}<span>${escape(part.label)}</span></button><button class="icon-button" data-part-visible="${escape(part.id)}" aria-label="${part.group.visible ? '隐藏' : '显示'}${escape(part.label)}" title="${part.group.visible ? '隐藏部件' : '显示部件'}">${icon(part.group.visible ? 'eye':'eye-off')}</button></div>`;
}
function renderTree() {
  if (!ready) return;
  const query = $('#search').value.trim().toLocaleLowerCase();
  $('#system-tree').hidden = Boolean(query); $('#search-results').hidden = !query;
  if (query) {
    const matches = viewer.parts.filter(p => `${p.name} ${p.label} ${SYSTEMS.find(s=>s.id===p.systemId).label}`.toLocaleLowerCase().includes(query));
    $('#search-results').innerHTML = `<div class="search-summary">${matches.length ? `找到 ${matches.length} 个部件` : '未找到匹配部件'}</div>${matches.slice(0,searchLimit).map(partRow).join('')}${matches.length>searchLimit ? '<button class="more-parts" data-search-more>显示更多</button>' : ''}`;
  } else {
    const scroll = $('#system-tree').scrollTop;
    $('#system-tree').innerHTML = SYSTEMS.map(system => {
      const parts = viewer.parts.filter(p => p.systemId === system.id);
      const open = expanded.has(system.id), visible = stats.systems[system.id].visible > 0;
      const limit = limits[system.id] || 50;
      return `<div class="system-entry" role="listitem"><div class="system-row ${selected?.id === system.id ? 'selected' : ''} ${visible ? '' : 'is-hidden'}"><button class="icon-button expand" data-expand="${system.id}" aria-label="${open ? '折叠':'展开'}${system.label}" aria-expanded="${open}">${icon(open ? 'chevron-down':'chevron-right')}</button><button class="system-select" data-system="${system.id}"><span class="system-swatch" style="--system-color:${system.color}"></span><span class="system-text"><b>${system.label}</b><small>${parts.length} 个部件</small></span></button><button class="icon-button visibility" data-system-visible="${system.id}" aria-label="${visible ? '隐藏':'显示'}${system.label}" title="${visible ? '隐藏':'显示'}${system.label}">${icon(visible ? 'eye':'eye-off')}</button></div>${open ? `<div class="part-list">${parts.slice(0,limit).map(partRow).join('')}${parts.length>limit ? `<button class="more-parts" data-more="${system.id}">显示更多 · 余 ${parts.length-limit} 件</button>` : ''}</div>` : ''}</div>`;
    }).join('');
    $('#system-tree').scrollTop = scroll;
  }
  refreshIcons();
}
function onSelection(part) {
  selected = part;
  $('#selection-type').textContent = !part ? '整车模型' : part.isSystem ? '选中总成' : SYSTEMS.find(s => s.id === part.systemId).label;
  $('#selection-name').textContent = part?.label || '豹 2 早期原型';
  $('#selection-id').textContent = part?.name || part?.english || 'LEOPARD_2_EARLY_PROTOTYPE';
  $('#selection-description').textContent = !part ? '基于四视图重建的早期原型方案。' : part.isSystem ? part.description : getPartDescription(part.name);
  $('#selection-actions').hidden = !part; $('#clear-selection').hidden = !part;
  $('#download span').textContent = part ? '导出部件' : '导出模型';
  $('#opacity').value = Math.round((part?.opacity ?? 1)*100); $('#opacity-value').textContent = `${$('#opacity').value}%`;
  $('#auto-rotate').checked = false; press($('#rotate'),false);
  if (part?.isSystem) expanded.add(part.id);
  renderTree();
  if (part && innerWidth <= 1050) openPanel('inspector');
}

function openPanel(name) {
  $$('.panel').forEach(panel => panel.classList.remove('is-open'));
  $(`#${name}-panel`).classList.add('is-open');
  $('#panel-backdrop').hidden = false;
  const target = name === 'structure' ? $('#search') : $('#tab-model'); target.focus();
}
function closePanels() {
  const previous = $('.panel.is-open');
  $$('.panel').forEach(panel=>panel.classList.remove('is-open'));
  $('#panel-backdrop').hidden = true;
  if (previous) $(previous.id === 'structure-panel' ? '#open-structure':'#open-inspector').focus();
}
function setExplosion(percent) { if (!ready) return; viewer.setExplode(percent/100); renderTree(); }
function setRotation(value) {
  if (!ready) return;
  viewer.setAutoRotate(value);
  $('#auto-rotate').checked = viewer.controls.autoRotate; press($('#rotate'),viewer.controls.autoRotate);
  if (value && !viewer.controls.autoRotate && matchMedia('(prefers-reduced-motion: reduce)').matches) notify('系统已开启减少动态效果');
}
function setGrid(value) { viewer?.setGrid(value); $('#ground-grid').checked = value; press($('#grid'),value); }
function applyClip() {
  if (!ready) return;
  viewer.setClip({enabled:$('#clip-enabled').checked,axis:clipAxis,position:Number($('#clip-position').value)/100,flip:$('#clip-flip').checked,showPlane:$('#clip-plane').checked});
  $('#clip-value').textContent = `${$('#clip-position').value}%`;
}
function showAll() { if (!ready) return; viewer.showAll(); $('#preset').value='all'; viewer.fit(); renderTree(); }
function reset() {
  if (!ready) return;
  $('#search').value=''; $('#preset').value='all'; expanded.clear();
  viewer.reset();
  $('#opacity').value='100'; $('#opacity-value').textContent='100%';
  $('#yaw').value='0'; $('#yaw-value').textContent='0°';
  $('#elevation').value='0'; $('#elevation-value').textContent='0°';
  $('#clip-enabled').checked=false; $('#clip-position').value='0'; $('#clip-value').textContent='0%';
  $('#clip-flip').checked=false; $('#clip-plane').checked=true; clipAxis='x';
  $$('[data-axis]').forEach(b=>press(b,b.dataset.axis==='x'));
  $$('[data-mode]').forEach(b=>press(b,b.dataset.mode==='material'));
  press($('#projection'),false); setGrid(true); $('#view').value='perspective'; $('#view-label').textContent='透视视图';
  renderTree();
}

refreshIcons();
try {
  viewer = new ModelViewer($('#scene'), {
    onLoad({parts,stats:value}) {
      ready=true; stats=value;
      $('#loading').hidden=true; $('#header-status').textContent='模型已就绪';
      $('#total-parts').textContent=parts.length.toLocaleString(); $('#model-part-count').textContent=parts.length.toLocaleString(); $('#about-parts').textContent=parts.length.toLocaleString();
      $('#render-status').textContent=`${(value.triangles/1000).toFixed(0)}k 三角面 · WebGL 2`;
      $('#download').disabled=false; renderTree(); updateStats(value);
      window.__atlasReady = true;
    },
    onProgress(value) { $('#loading-progress').value=value; $('#loading-text').textContent=value>0 ? `${Math.round(value)}% · 正在解析模型` : 'Leopard 2 · 10.96 MB'; },
    onSelect:onSelection, onChange:updateStats, onError:setError,
    onHover(part,point) {
      const label=$('#hover-label'); label.hidden=!part;
      if(part) { label.textContent=part.label; label.style.left=`${Math.min(point.x+15,innerWidth-260)}px`; label.style.top=`${Math.min(point.y+15,innerHeight-70)}px`; }
    },
  });
  window.__atlasViewer = viewer;
  viewer.load(`${import.meta.env.BASE_URL}models/leopard2.glb`).catch(()=>{});
} catch(error) { setError(error); }

$('#retry').addEventListener('click',()=>location.reload());
$('#search').addEventListener('input',()=>{searchLimit=80; renderTree();});
$('#structure-panel').addEventListener('click',event=>{
  if(!ready) return;
  const button=event.target.closest('button'); if(!button) return;
  const data=button.dataset;
  if(data.expand) { expanded.has(data.expand) ? expanded.delete(data.expand) : expanded.add(data.expand); renderTree(); }
  if(data.system) viewer.select(data.system);
  if(data.part) viewer.select(data.part);
  if(data.systemVisible) { viewer.setSystemVisibility(data.systemVisible,stats.systems[data.systemVisible].visible===0); renderTree(); }
  if(data.partVisible) { const part=viewer.partMap.get(data.partVisible); viewer.setPartVisibility(part.id,!part.group.visible); renderTree(); }
  if(data.more) { limits[data.more]=(limits[data.more]||50)+80; renderTree(); }
  if('searchMore' in data) { searchLimit+=80; renderTree(); }
});
$('#show-all').addEventListener('click',showAll); $('#empty-restore').addEventListener('click',showAll);
$('#hide-all').addEventListener('click',()=>{ if(ready) { SYSTEMS.forEach(s=>viewer.setSystemVisibility(s.id,false)); renderTree(); } });
$('#preset').addEventListener('change',event=>{
  if(!ready) return;
  const presets={all:SYSTEMS.map(s=>s.id),turret:['turret','gun','optics'],mobility:['running-gear','track-left','track-right'],hull:['hull','engine-deck'],equipment:['equipment','optics']};
  viewer.select(null);
  for(const system of SYSTEMS) viewer.setSystemVisibility(system.id,presets[event.target.value].includes(system.id));
  viewer.fit(); renderTree();
});
$('#clear-selection').addEventListener('click',()=>viewer?.select(null));
$('#isolate').addEventListener('click',()=>{if(selected){viewer.isolate(selected.id);renderTree();}});
$('#hide-selected').addEventListener('click',()=>{if(selected){selected.isSystem?viewer.setSystemVisibility(selected.id,false):viewer.setPartVisibility(selected.id,false);viewer.select(null);renderTree();}});
$('#focus-selected').addEventListener('click',()=>{if(selected){viewer.fit(selected.id);closePanels();}});
$('#explode').addEventListener('input',event=>setExplosion(Number(event.target.value)));
$$('[data-explode]').forEach(button=>button.addEventListener('click',()=>setExplosion(Number(button.dataset.explode))));
$('#opacity').addEventListener('input',event=>{const value=Number(event.target.value);$('#opacity-value').textContent=`${value}%`;viewer?.setOpacity(value/100,selected?.id);});
$('#auto-rotate').addEventListener('change',event=>setRotation(event.target.checked));
$('#rotate').addEventListener('click',()=>setRotation(!viewer?.controls.autoRotate));
$('#ground-grid').addEventListener('change',event=>setGrid(event.target.checked));
$('#grid').addEventListener('click',()=>setGrid(!$('#ground-grid').checked));
for(const id of ['yaw','elevation']) $(`#${id}`).addEventListener('input',()=>{
  $(`#${id}-value`).textContent=`${$(`#${id}`).value}°`;
  viewer?.setArticulation(Number($('#yaw').value),Number($('#elevation').value));
});
$$('[data-mode]').forEach(button=>button.addEventListener('click',()=>{
  if(!ready)return; viewer.setRenderMode(button.dataset.mode);
  $$('[data-mode]').forEach(b=>press(b,b===button));
}));
$('#view').addEventListener('change',event=>{viewer?.setView(event.target.value); $('#view-label').textContent=event.target.selectedOptions[0].textContent;});
$('#fit').addEventListener('click',()=>viewer?.fit()); $('#reset').addEventListener('click',reset);
$('#projection').addEventListener('click',()=>{
  if(!ready)return;
  const active=$('#projection').getAttribute('aria-pressed')!=='true'; press($('#projection'),active);
  viewer.setProjection(active?'orthographic':'perspective'); $('#view-label').textContent=active?'正交投影':'透视投影';
});
$('#screenshot').addEventListener('click',()=>{if(ready){viewer.screenshot();notify('截图已保存');}});
$('#fullscreen').addEventListener('click',async()=>{
  try { if(document.fullscreenElement) await document.exitFullscreen(); else await $('#app').requestFullscreen(); }
  catch { notify('当前浏览器不支持全屏'); }
});
document.addEventListener('fullscreenchange',()=>press($('#fullscreen'),Boolean(document.fullscreenElement)));
$('#download').addEventListener('click',async()=>{
  if(!ready)return; $('#download').disabled=true;
  try { const result=await viewer.exportSelection(); notify(`已导出 ${result.parts} 个部件`); }
  catch(error){notify(error.message || '导出失败');}
  finally{$('#download').disabled=false;}
});
function switchTab(name) {
  $$('[data-tab]').forEach(b=>{const active=b.dataset.tab===name;b.classList.toggle('active',active);b.setAttribute('aria-selected',String(active));b.tabIndex=active?0:-1;});
  $('#model-settings').hidden=name!=='model'; $('#section-settings').hidden=name!=='section';
}
$$('[data-tab]').forEach(button=>{
  button.addEventListener('click',()=>switchTab(button.dataset.tab));
  button.addEventListener('keydown',event=>{if(['ArrowLeft','ArrowRight'].includes(event.key)){event.preventDefault();const target=button.dataset.tab==='model'?'section':'model';switchTab(target);$(`#tab-${target}`).focus();}});
});
switchTab('model');
for(const id of ['clip-enabled','clip-flip','clip-plane']) $(`#${id}`).addEventListener('change',applyClip);
$('#clip-position').addEventListener('input',applyClip);
$$('[data-axis]').forEach(button=>button.addEventListener('click',()=>{clipAxis=button.dataset.axis;$$('[data-axis]').forEach(b=>press(b,b===button));applyClip();}));
$('#open-structure').addEventListener('click',()=>openPanel('structure'));
$('#open-inspector').addEventListener('click',()=>openPanel('inspector'));
$$('[data-close-panel]').forEach(button=>button.addEventListener('click',closePanels));
$('#panel-backdrop').addEventListener('click',closePanels);
for(const id of ['info','about-footer']) $(`#${id}`).addEventListener('click',()=>$('#about-dialog').showModal());
for(const id of ['close-about','about-done']) $(`#${id}`).addEventListener('click',()=>$('#about-dialog').close());
document.addEventListener('keydown',event=>{if(event.key==='Escape'){if($('.panel.is-open'))closePanels();else if(!$('#about-dialog').open)viewer?.select(null);}});
window.addEventListener('resize',()=>{if(innerWidth>1050)closePanels();});
