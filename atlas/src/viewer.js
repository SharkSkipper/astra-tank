import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { GLTFExporter } from 'three/addons/exporters/GLTFExporter.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { SYSTEMS, getSystemId, getPartLabel, getExplodeDirection } from './model-data.js';

const up = new THREE.Vector3(0, 1, 0);
const views = { perspective: [-10, 7, 11], front: [-1, 0, 0], back: [1, 0, 0], left: [0, 0, -1], right: [0, 0, 1], top: [0, 1, 0.0001] };
const turretPivot = new THREE.Vector3(0, 1.675, 0);
const gunPivot = new THREE.Vector3(-1.26, 2.009, 0);
// Blender procedural colors are absent from this GLB; use the source script's linear RGB values.
const proceduralColors = {
  'Paint | muted NATO olive': [.135, .173, .094],
  'Paint | recess and brackets': [.072, .092, .047],
  'Rubber | tire and track pads': [.025, .031, .028],
};
const translation = v => new THREE.Matrix4().makeTranslation(v.x, v.y, v.z);
const around = (pivot, rotation) => translation(pivot).multiply(rotation).multiply(translation(pivot.clone().negate()));
const downloadBlob = (blob, name) => {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url; link.download = name; link.click();
  setTimeout(() => URL.revokeObjectURL(url), 10000);
};

export class ModelViewer {
  constructor(canvas, callbacks = {}) {
    this.canvas = canvas; this.callbacks = callbacks;
    this.parts = []; this.partMap = new Map(); this.pickMeshes = [];
    this.selectedId = null; this.mode = 'material'; this.explode = 0;
    this.yaw = 0; this.elevation = 0; this.isolated = null;
    this.clip = { enabled: false, axis: 'x', position: 0, flip: false, showPlane: true };
    this.scene = new THREE.Scene(); this.scene.background = new THREE.Color('#141818');
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: true, powerPreference: 'high-performance' });
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = .95;
    this.renderer.localClippingEnabled = true;
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    const room = new RoomEnvironment();
    this.environment = pmrem.fromScene(room, .04);
    this.scene.environment = this.environment.texture;
    room.dispose(); pmrem.dispose();
    this.scene.add(new THREE.HemisphereLight('#dcebe4', '#555c51', 1.1));
    const key = new THREE.DirectionalLight('#fff4e4', 2.6); key.position.set(-5, 9, 7); this.scene.add(key);
    const rim = new THREE.DirectionalLight('#bfddd8', 1.4); rim.position.set(5, 5, -7); this.scene.add(rim);
    this.grid = new THREE.GridHelper(50, 50, '#455349', '#344339');
    this.grid.position.y = -.07;
    this.grid.material.transparent = true; this.grid.material.opacity = .4;
    this.grid.material.onBeforeCompile = shader => {
      shader.vertexShader = 'varying vec3 vGridPosition;\n' + shader.vertexShader;
      shader.vertexShader = shader.vertexShader.replace('#include <begin_vertex>', '#include <begin_vertex>\nvGridPosition = (modelMatrix * vec4(position, 1.0)).xyz;');
      shader.fragmentShader = 'varying vec3 vGridPosition;\n' + shader.fragmentShader;
      shader.fragmentShader = shader.fragmentShader.replace('#include <opaque_fragment>', 'diffuseColor.a *= 1.0 - smoothstep(6.0, 21.0, length(vGridPosition.xz));\n#include <opaque_fragment>');
    };
    this.scene.add(this.grid);
    this.root = new THREE.Group(); this.scene.add(this.root);
    this.perspective = new THREE.PerspectiveCamera(36, 1, .01, 1000);
    this.orthographic = new THREE.OrthographicCamera(-10, 10, 10, -10, .01, 1000);
    this.camera = this.perspective; this.camera.position.fromArray(views.perspective);
    this.controls = new OrbitControls(this.camera, canvas);
    this.controls.enableDamping = true; this.controls.dampingFactor = .1;
    this.controls.minDistance = .08; this.controls.maxDistance = 250;
    this.controls.autoRotateSpeed = .6;
    this.controls.target.set(0, 1.2, 0);
    this.controls.addEventListener('change', () => { this.dirty = true; });
    this.raycaster = new THREE.Raycaster(); this.pointer = new THREE.Vector2();
    this.clipPlane = new THREE.Plane(new THREE.Vector3(1, 0, 0), 0);
    this.planeHelper = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ color: '#82e6c2', transparent: true, opacity: .13, side: THREE.DoubleSide, depthWrite: false }));
    this.planeHelper.visible = false; this.scene.add(this.planeHelper);
    this.bindPointer();
    this.resizeObserver = new ResizeObserver(() => this.resize());
    this.resizeObserver.observe(canvas.parentElement);
    this.dirty = true;
    this.tick = () => {
      this.frame = requestAnimationFrame(this.tick);
      if (document.hidden) return;
      const moved = this.controls.update();
      if (moved || this.dirty) { this.renderer.render(this.scene, this.camera); this.dirty = false; }
    };
    this.resize(); this.tick();
    canvas.addEventListener('webglcontextlost', event => { event.preventDefault(); callbacks.onError?.(new Error('图形上下文已中断，请重新载入')); });
  }

  async load(url) {
    try {
      const gltf = await new GLTFLoader().loadAsync(url, event => this.callbacks.onProgress?.(event.total ? event.loaded / event.total * 100 : 0));
      gltf.scene.updateMatrixWorld(true);
      const logicalNodes = [];
      gltf.scene.traverse(node => {
        const association = gltf.parser.associations.get(node);
        const source = association?.nodes !== undefined ? gltf.parser.json.nodes[association.nodes] : null;
        if (source?.mesh !== undefined) logicalNodes.push({ node, name: source.name || node.name });
      });
      const seen = new Set();
      for (const {node, name} of logicalNodes) {
        if (seen.has(name)) continue;
        seen.add(name);
        const group = new THREE.Group(); group.name = name;
        let inGun = false, inTurret = false;
        for (let ancestor = node; ancestor; ancestor = ancestor.parent) {
          if (ancestor.name === 'Gun_Elevation_Pivot') inGun = true;
          if (ancestor.name === 'Turret_Pivot') inTurret = true;
        }
        const bounds = new THREE.Box3().setFromObject(node);
        const center = bounds.getCenter(new THREE.Vector3());
        const part = { id: name, name, label: getPartLabel(name), systemId: getSystemId(name), group, meshes: [], center, bounds, inGun, inTurret, opacity: 1, visible: true };
        node.traverse(original => {
          if (!original.isMesh) return;
          const materials = (Array.isArray(original.material) ? original.material : [original.material]).map(material => {
            const copy = material.clone(); copy.side = THREE.DoubleSide; copy.envMapIntensity = .75;
            if (proceduralColors[material.name]) copy.color.setRGB(...proceduralColors[material.name]);
            copy.userData.original = { color: copy.color.clone(), opacity: copy.opacity, transparent: copy.transparent, map: copy.map, metalness: copy.metalness, roughness: copy.roughness };
            return copy;
          });
          const mesh = new THREE.Mesh(original.geometry, Array.isArray(original.material) ? materials : materials[0]);
          mesh.name = original.name;
          const matrix = translation(center.clone().negate()).multiply(original.matrixWorld);
          matrix.decompose(mesh.position, mesh.quaternion, mesh.scale);
          mesh.userData.partId = name;
          group.add(mesh); part.meshes.push(mesh); this.pickMeshes.push(mesh);
        });
        part.mesh = part.meshes[0];
        part.localBounds = bounds.clone().translate(center.clone().negate());
        group.position.copy(center); this.root.add(group);
        this.parts.push(part); this.partMap.set(name, part);
      }
      this.baseBounds = new THREE.Box3().setFromObject(this.root);
      this.totalTriangles = this.parts.reduce((sum, p) => sum + p.meshes.reduce((n, m) => n + (m.geometry.index?.count ?? m.geometry.attributes.position.count) / 3, 0), 0);
      this.updateAppearance(); this.setView('perspective');
      this.callbacks.onLoad?.({ parts: this.parts, stats: this.getStats() });
      this.changed();
    } catch (error) { this.callbacks.onError?.(error); throw error; }
  }

  matches(part, id) { return part.id === id || part.systemId === id; }
  selectedPart() { return this.partMap.get(this.selectedId) || (SYSTEMS.some(s => s.id === this.selectedId) ? { ...SYSTEMS.find(s => s.id === this.selectedId), systemId: this.selectedId, isSystem: true } : null); }
  select(id) {
    if (id && !this.partMap.has(id) && !SYSTEMS.some(s => s.id === id)) return;
    if (this.isolated) this.restoreIsolation();
    this.selectedId = id;
    if (id) for (const p of this.parts) if (this.matches(p, id)) { p.visible = true; p.group.visible = true; }
    this.setAutoRotate(false);
    if (this.explode > 0) this.updateTransforms();
    this.updateAppearance(); this.callbacks.onSelect?.(this.selectedPart()); this.changed();
  }
  setSystemVisibility(id, visible) { this.restoreIsolation(); for (const p of this.parts) if (p.systemId === id) { p.visible = visible; p.group.visible = visible; } this.visibilityChanged(); }
  setPartVisibility(id, visible) { this.restoreIsolation(); const p = this.partMap.get(id); if (p) { p.visible = visible; p.group.visible = visible; } this.visibilityChanged(); }
  visibilityChanged() { if (this.explode) { this.updateTransforms(); this.fit(); } this.changed(); }
  showAll() { this.isolated = null; for (const p of this.parts) { p.visible = true; p.group.visible = true; } this.visibilityChanged(); }
  restoreIsolation() {
    if (!this.isolated) return;
    for (const p of this.parts) p.group.visible = p.visible;
    this.isolated = null;
  }
  isolate(id) {
    if (this.isolated === id) { this.restoreIsolation(); this.fit(); this.changed(); return; }
    this.restoreIsolation(); this.explode = 0; this.isolated = id;
    for (const p of this.parts) p.group.visible = this.matches(p, id);
    this.updateTransforms(); this.controls.enableRotate = true; this.grid.visible = this.gridEnabled !== false;
    this.fit(id); this.changed();
  }
  setOpacity(value, id = null) { for (const p of this.parts) if (!id || this.matches(p, id)) p.opacity = value; this.updateAppearance(); this.changed(); }
  setRenderMode(mode) { this.mode = mode; this.updateAppearance(); this.changed(); }
  updateAppearance() {
    for (const part of this.parts) {
      const selected = this.matches(part, this.selectedId);
      for (const mesh of part.meshes) for (const material of (Array.isArray(mesh.material) ? mesh.material : [mesh.material])) {
        const original = material.userData.original;
        material.color.copy(original.color); material.map = original.map;
        material.metalness = original.metalness; material.roughness = original.roughness;
        material.wireframe = this.mode === 'wireframe';
        if (this.mode !== 'material') {
          material.map = null;
          material.color.set(this.mode === 'systems' ? SYSTEMS.find(s => s.id === part.systemId).color : this.mode === 'xray' ? '#abd9c6' : '#86cdb1');
          material.metalness = .1; material.roughness = .6;
        }
        material.opacity = part.opacity * (this.mode === 'xray' ? .22 : 1);
        material.transparent = material.opacity < 1;
        material.depthWrite = material.opacity >= .5;
        material.emissive.set(selected ? '#53ca9c' : '#000000');
        material.emissiveIntensity = selected ? .38 : 0;
        material.clippingPlanes = this.clip.enabled ? [this.clipPlane] : [];
        material.needsUpdate = true;
      }
    }
    this.dirty = true;
  }

  poseMatrix(part) {
    const pose = new THREE.Matrix4();
    if (part.inTurret) pose.multiply(around(turretPivot, new THREE.Matrix4().makeRotationY(THREE.MathUtils.degToRad(this.yaw))));
    if (part.inGun) pose.multiply(around(gunPivot, new THREE.Matrix4().makeRotationZ(THREE.MathUtils.degToRad(-this.elevation))));
    return pose.multiply(translation(part.center));
  }
  updateTransforms() {
    const spread = Math.min(this.explode / .45, 1);
    const inventory = Math.max(0, (this.explode - .45) / .55);
    const posed = this.parts.map(part => {
      const matrix = this.poseMatrix(part);
      const bounds = part.localBounds.clone().applyMatrix4(matrix);
      return {part, matrix, bounds, center: bounds.getCenter(new THREE.Vector3()), size: bounds.getSize(new THREE.Vector3())};
    });
    if (inventory > 0) {
      const visible = posed.filter(p => p.part.group.visible).sort((a,b) => SYSTEMS.findIndex(s => s.id === a.part.systemId) - SYSTEMS.findIndex(s => s.id === b.part.systemId) || b.size.y - a.size.y);
      const padding = .13;
      const area = visible.reduce((sum,p) => sum + (p.size.z + padding) * (p.size.y + padding), 0);
      const targetWidth = Math.max(5, ...visible.map(p => p.size.z + padding), Math.sqrt(area * Math.max(.6, this.camera.aspect || this.canvas.clientWidth / this.canvas.clientHeight)) * 1.2);
      let horizontal = 0, vertical = 0, rowHeight = 0;
      for (const entry of visible) {
        const width = entry.size.z + padding, height = entry.size.y + padding;
        if (horizontal && horizontal + width > targetWidth) { horizontal = 0; vertical += rowHeight; rowHeight = 0; }
        entry.inventoryCenter = new THREE.Vector3(0, -vertical - entry.size.y / 2, horizontal + entry.size.z / 2 - targetWidth / 2);
        horizontal += width; rowHeight = Math.max(rowHeight, height);
      }
    }
    for (const entry of posed) {
      const offset = new THREE.Vector3(...getExplodeDirection(entry.part.systemId)).multiplyScalar(spread);
      if (entry.part.systemId === 'running-gear') offset.z += (entry.part.name.startsWith('L_') ? -1 : 1) * spread * 1.3;
      if (entry.inventoryCenter) offset.lerp(entry.inventoryCenter.sub(entry.center), inventory);
      entry.part.group.matrixAutoUpdate = false;
      entry.part.group.matrix.copy(translation(offset).multiply(entry.matrix));
    }
    this.root.updateMatrixWorld(true); this.dirty = true;
  }
  setExplode(value) {
    this.restoreIsolation();
    const previous = this.explode; this.explode = THREE.MathUtils.clamp(value, 0, 1);
    if (value >= .4) this.setAutoRotate(false);
    this.controls.enableRotate = value < .8;
    this.grid.visible = value < .8 && this.gridEnabled !== false;
    this.updateTransforms();
    if (value >= .8) {
      if (previous < .8) this.beforeInventoryProjection = this.camera.isOrthographicCamera ? 'orthographic' : 'perspective';
      this.setProjection('orthographic'); this.setView('front');
    }
    else if (previous >= .8) { this.setProjection(this.beforeInventoryProjection || 'perspective'); this.setView('perspective'); }
    else this.fit();
    this.changed();
  }
  setArticulation(yaw, elevation) { this.yaw = yaw; this.elevation = elevation; this.updateTransforms(); if(this.explode > .45)this.fit(); this.changed(); }
  setClip(config) {
    this.clip = {...this.clip, ...config};
    const axis = this.clip.axis;
    const normal = new THREE.Vector3(); normal[axis] = this.clip.flip ? -1 : 1;
    const point = new THREE.Vector3();
    point[axis] = THREE.MathUtils.lerp(this.baseBounds?.min[axis] ?? -5, this.baseBounds?.max[axis] ?? 5, (this.clip.position + 1) / 2);
    this.clipPlane.setFromNormalAndCoplanarPoint(normal, point);
    const bounds = this.baseBounds || new THREE.Box3(new THREE.Vector3(-5,0,-2), new THREE.Vector3(5,4,2));
    const center = bounds.getCenter(new THREE.Vector3()); center[axis] = point[axis];
    this.planeHelper.position.copy(center);
    this.planeHelper.quaternion.setFromUnitVectors(new THREE.Vector3(0,0,1), normal);
    const size = bounds.getSize(new THREE.Vector3());
    this.planeHelper.scale.set(axis === 'x' ? size.z + .6 : size.x + .6, axis === 'y' ? size.z + .6 : size.y + .6, 1);
    this.planeHelper.visible = this.clip.enabled && this.clip.showPlane;
    this.updateAppearance(); this.changed();
  }
  visibleBounds(id) {
    const bounds = new THREE.Box3();
    this.root.updateMatrixWorld(true);
    for (const p of this.parts) if (p.group.visible && (!id || this.matches(p,id))) bounds.union(p.localBounds.clone().applyMatrix4(p.group.matrixWorld));
    return bounds;
  }
  fit(id) {
    const bounds = this.visibleBounds(id); if (bounds.isEmpty()) return;
    const center = bounds.getCenter(new THREE.Vector3());
    const direction = this.camera.position.clone().sub(this.controls.target).normalize();
    if (direction.lengthSq() < .1) direction.fromArray(views.perspective).normalize();
    this.camera.position.copy(center).add(direction); this.camera.lookAt(center); this.camera.updateMatrixWorld(true);
    const projected = new THREE.Box3();
    for (const part of this.parts) {
      if (part.group.visible && (!id || this.matches(part,id))) {
        projected.union(part.localBounds.clone().applyMatrix4(new THREE.Matrix4().multiplyMatrices(this.camera.matrixWorldInverse,part.group.matrixWorld)));
      }
    }
    const size = projected.getSize(new THREE.Vector3());
    const aspect = this.canvas.clientWidth / Math.max(this.canvas.clientHeight,1);
    const canvasHeight = this.canvas.clientHeight;
    const topInset = Math.min(200, canvasHeight * .3), bottomInset = Math.min(85, canvasHeight * .15);
    const usableHeight = Math.max(.35, (canvasHeight - topInset - bottomInset) / canvasHeight);
    const height = Math.max(size.y / usableHeight, size.x / (aspect * .92), .1) * 1.1;
    const distance = height / (2 * Math.tan(THREE.MathUtils.degToRad(18))) + size.z / 2;
    const screenUp = new THREE.Vector3().setFromMatrixColumn(this.camera.matrixWorld,1);
    const visibleHeight = this.camera.isOrthographicCamera ? height : 2 * distance * Math.tan(THREE.MathUtils.degToRad(18));
    const framedCenter = center.clone().addScaledVector(screenUp, (topInset-bottomInset) / canvasHeight * visibleHeight / 2);
    this.camera.position.copy(framedCenter).addScaledVector(direction, distance);
    this.controls.target.copy(framedCenter);
    this.orthoHeight = height;
    this.orthographic.left = -height * aspect / 2; this.orthographic.right = height * aspect / 2;
    this.orthographic.top = height / 2; this.orthographic.bottom = -height / 2; this.orthographic.zoom = 1;
    this.camera.updateProjectionMatrix(); this.controls.update(); this.dirty = true;
  }
  setView(view) {
    if (!views[view]) return;
    this.currentView = view;
    this.camera.up.copy(up);
    this.camera.position.copy(this.controls.target).add(new THREE.Vector3(...views[view]).normalize().multiplyScalar(15));
    this.controls.update(); this.fit(); this.dirty = true;
  }
  setProjection(mode) {
    const target = mode === 'orthographic' ? this.orthographic : this.perspective;
    if (target === this.camera) return;
    target.position.copy(this.camera.position); target.quaternion.copy(this.camera.quaternion);
    this.camera = target; this.controls.object = target; this.fit(); this.changed();
  }
  setAutoRotate(value) { this.controls.autoRotate = value && this.explode < .4 && !matchMedia('(prefers-reduced-motion: reduce)').matches; this.dirty = true; }
  setGrid(value) { this.gridEnabled = value; this.grid.visible = value && this.explode < .8; this.dirty = true; }
  reset() {
    this.selectedId = null; this.isolated = null; this.explode = 0; this.yaw = 0; this.elevation = 0;
    this.mode = 'material'; this.controls.enableRotate = true;
    this.setAutoRotate(false); this.setGrid(true);
    for (const p of this.parts) { p.visible = true; p.group.visible = true; p.opacity = 1; }
    this.setClip({enabled:false,axis:'x',position:0,flip:false,showPlane:true});
    this.updateTransforms(); this.setProjection('perspective'); this.setView('perspective'); this.updateAppearance();
    this.callbacks.onSelect?.(null); this.changed();
  }
  bindPointer() {
    let down = null; const active = new Set(); let hoverTime = 0;
    this.canvas.addEventListener('pointerdown', event => {
      active.add(event.pointerId);
      down = active.size === 1 ? { x:event.clientX,y:event.clientY,type:event.pointerType, button:event.button } : null;
    });
    this.canvas.addEventListener('pointerup', event => {
      active.delete(event.pointerId);
      if (down && down.button === 0 && Math.hypot(event.clientX-down.x,event.clientY-down.y) < (down.type === 'touch' ? 12 : 5)) {
        const part = this.pick(event.clientX,event.clientY,down.type === 'touch' ? 12 : 6); this.select(part?.id || null);
      }
      down = null;
    });
    this.canvas.addEventListener('pointercancel', event => { active.delete(event.pointerId); down = null; });
    this.canvas.addEventListener('pointermove', event => {
      if (active.size || event.pointerType === 'touch' || performance.now()-hoverTime < 80) return;
      hoverTime = performance.now();
      this.callbacks.onHover?.(this.pick(event.clientX,event.clientY), {x:event.clientX,y:event.clientY});
    });
    this.canvas.addEventListener('pointerleave', () => this.callbacks.onHover?.(null));
  }
  pick(x,y,tolerance=6) {
    const rect = this.canvas.getBoundingClientRect();
    this.pointer.set((x-rect.left)/rect.width*2-1,-(y-rect.top)/rect.height*2+1);
    this.root.updateMatrixWorld(true); this.camera.updateMatrixWorld(true);
    this.raycaster.setFromCamera(this.pointer,this.camera);
    const candidates = this.pickMeshes.filter(m => m.parent.visible);
    const hit = this.raycaster.intersectObjects(candidates,false).find(h => !this.clip.enabled || this.clipPlane.distanceToPoint(h.point) >= 0);
    if(hit) return this.partMap.get(hit.object.userData.partId);
    if(this.explode < .45) return null;
    let nearest = null, distance = tolerance;
    for(const part of this.parts) {
      if(!part.group.visible) continue;
      const center = new THREE.Vector3().setFromMatrixPosition(part.group.matrixWorld);
      if(this.clip.enabled && this.clipPlane.distanceToPoint(center)<0) continue;
      const projected=center.clone().project(this.camera);
      if(Math.abs(projected.x)>1 || Math.abs(projected.y)>1 || Math.abs(projected.z)>1) continue;
      const candidateDistance=Math.hypot(rect.left+(projected.x+1)*rect.width/2-x,rect.top+(1-projected.y)*rect.height/2-y);
      if(candidateDistance<distance) { nearest=part; distance=candidateDistance; }
    }
    return nearest;
  }
  resize() {
    const w = Math.max(1,this.canvas.clientWidth), h = Math.max(1,this.canvas.clientHeight);
    this.renderer.setSize(w,h,false); this.perspective.aspect = w/h; this.perspective.updateProjectionMatrix();
    const height = this.orthoHeight || 12; this.orthographic.left = -height*w/h/2; this.orthographic.right = height*w/h/2;
    this.orthographic.updateProjectionMatrix();
    if (this.parts.length) { if (this.explode > .45) this.updateTransforms(); this.fit(); }
    this.dirty = true;
  }
  getStats() {
    const systems = Object.fromEntries(SYSTEMS.map(s => [s.id,{total:0,visible:0}]));
    for (const p of this.parts) { systems[p.systemId].total++; if (p.group.visible) systems[p.systemId].visible++; }
    return { parts:this.parts.length, meshes:this.pickMeshes.length, visible:this.parts.filter(p => p.group.visible).length, triangles:this.totalTriangles || 0, systems, explode:this.explode, isolated:this.isolated, autoRotate:this.controls.autoRotate };
  }
  changed() { this.dirty = true; this.callbacks.onChange?.(this.getStats()); }
  screenshot() { this.renderer.render(this.scene,this.camera); this.canvas.toBlob(blob => { if(blob) downloadBlob(blob,'leopard2-view.png'); },'image/png'); }
  async exportSelection() {
    const selected = this.selectedId;
    const parts = this.parts.filter(p => p.group.visible && (!selected || this.matches(p,selected)));
    if (!parts.length) throw new Error('没有可导出的可见部件');
    const output = new THREE.Group(); output.name = selected || 'Leopard_2_visible_parts';
    const disposable = [];
    for (const part of parts) {
      const group = new THREE.Group(); group.name = part.name;
      group.matrix.copy(part.group.matrix); group.matrix.decompose(group.position,group.quaternion,group.scale);
      for (const mesh of part.meshes) {
        const copy = mesh.clone();
        const material = (Array.isArray(mesh.material) ? mesh.material : [mesh.material]).map(m => {
          const result = m.clone(), original = m.userData.original;
          result.color.copy(original.color); result.map = original.map; result.emissive.set(0);
          result.opacity = 1; result.transparent = false; result.wireframe = false; result.clippingPlanes = []; result.userData = {};
          result.metalness = original.metalness; result.roughness = original.roughness;
          disposable.push(result); return result;
        });
        copy.material = Array.isArray(mesh.material) ? material : material[0]; group.add(copy);
      }
      output.add(group);
    }
    try {
      const buffer = await new GLTFExporter().parseAsync(output,{binary:true,onlyVisible:true});
      downloadBlob(new Blob([buffer],{type:'model/gltf-binary'}),`${selected || 'leopard2-visible'}.glb`);
      return {parts:parts.length,bytes:buffer.byteLength};
    } finally { disposable.forEach(m => m.dispose()); }
  }
}
