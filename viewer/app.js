import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

const canvas = document.querySelector("#scene");
const status = document.querySelector("#status");
const objectCount = document.querySelector("#object-count");
const toggleRoot = document.querySelector("#component-toggles");
const explodeInput = document.querySelector("#explode");
const selectionStatus = document.querySelector("#selection-status");
const selectionName = document.querySelector("#selection-name");
const selectionRole = document.querySelector("#selection-role");
const selectionSubject = document.querySelector("#selection-subject");
const referenceLinks = document.querySelector("#reference-links");

const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, preserveDrawingBuffer: false });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true;

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x080b0e);
const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 200);
camera.position.set(29, 18, -31);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.target.set(0, 0, 2.4);

scene.add(new THREE.HemisphereLight(0xd7e4ee, 0x101419, 2.5));
const key = new THREE.DirectionalLight(0xffe6bf, 3.5);
key.position.set(-12, -18, 25);
key.castShadow = true;
scene.add(key);
const rim = new THREE.DirectionalLight(0x7bc9df, 2.3);
rim.position.set(15, 14, 13);
scene.add(rim);

const railGroup = new THREE.Group();
scene.add(railGroup);
const railMaterial = new THREE.MeshStandardMaterial({ color: 0x58636b, metalness: 0.8, roughness: 0.3 });
const sleeperMaterial = new THREE.MeshStandardMaterial({ color: 0x4a2e1b, roughness: 0.8 });
for (const y of [-4.5, 4.5]) {
  for (const railY of [y - 0.72, y + 0.72]) {
    const rail = new THREE.Mesh(new THREE.BoxGeometry(34, 0.12, 0.18), railMaterial);
    rail.position.set(0, 0.15, railY);
    railGroup.add(rail);
  }
  for (let x = -16; x <= 16; x += 2) {
    const sleeper = new THREE.Mesh(new THREE.BoxGeometry(0.42, 0.16, 2.2), sleeperMaterial);
    sleeper.position.set(x, 0.02, y);
    railGroup.add(sleeper);
  }
}

const modelGroup = new THREE.Group();
scene.add(modelGroup);
const models = new Map();
const componentVisibility = new Map();
const manifestByName = new Map();
const referencesById = new Map();
const raycaster = new THREE.Raycaster();
const pointer = new THREE.Vector2();
let selectedMesh = null;
let pointerDown = null;
const categoryMatchers = [
  ["车体", /Body|Boiler|Cab|Frame|Deck|Nose|Tender|Skirt|Smoke_Box/i],
  ["轮组与转向架", /Wheel|Bogie|Axle|Running_Gear|Rod|Pilot/i],
  ["制动、底部与内饰", /Brake|Underframe|Interior/i],
  ["门窗与灯具", /Window|Door|Headlamp|Headlight|Glass/i],
  ["车顶与蒸汽设备", /Roof|Pantograph|Chimney|Dome|Pipe|Bus/i],
  ["连接与缓冲", /Coupler|Coupling|Buffer|Connection/i],
  ["轨道场景", /^Track_/i],
];

function categoryFor(name) {
  const match = categoryMatchers.find(([, pattern]) => pattern.test(name));
  return match ? match[0] : "其他部件";
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let quoted = false;
  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (char === '"' && quoted && next === '"') {
      field += '"';
      index += 1;
    } else if (char === '"') {
      quoted = !quoted;
    } else if (char === "," && !quoted) {
      row.push(field);
      field = "";
    } else if ((char === "\n" || char === "\r") && !quoted) {
      if (char === "\r" && next === "\n") index += 1;
      row.push(field);
      if (row.some((value) => value.trim() !== "")) rows.push(row);
      row = [];
      field = "";
    } else {
      field += char;
    }
  }
  if (field !== "" || row.length) {
    row.push(field);
    if (row.some((value) => value.trim() !== "")) rows.push(row);
  }
  const headers = rows.shift() || [];
  return rows.map((values) => Object.fromEntries(headers.map((header, index) => [header, values[index] || ""])));
}

function referenceIdForRow(row) {
  const file = (row.local_file || "").replaceAll("\\", "/");
  if (file.includes("qj-2655-side")) return "QJ-side";
  if (file.includes("qj-2655-three-quarter")) return "QJ-three-quarter";
  if (file.includes("qj-2655-front-detail")) return "QJ-front-detail";
  if (file.includes("cr400af-front")) return "CR400AF-front";
  if (file.includes("cr400af-side")) return "CR400AF-side";
  if (file.includes("cr400af-bogie")) return "CR400AF-bogie";
  if (file.includes("cr400af-line-scan")) return "CR400AF-line-scan";
  return "";
}

async function loadTraceability() {
  const [manifestResponse, referenceResponse] = await Promise.all([
    fetch("../models/model-manifest.json"),
    fetch("../references/reference-index.csv"),
  ]);
  if (!manifestResponse.ok || !referenceResponse.ok) throw new Error("traceability index unavailable");
  const manifest = await manifestResponse.json();
  for (const subject of Object.values(manifest.subjects || {})) {
    for (const object of subject.objects || []) {
      manifestByName.set(object.name, {
        ...object,
        subject: object.name.startsWith("QJ_") ? "QJ 2655" : "CR400AF",
      });
    }
  }
  for (const row of parseCsv(await referenceResponse.text())) {
    const referenceId = referenceIdForRow(row);
    if (referenceId) referencesById.set(referenceId, row);
  }
}

function materialsFor(mesh) {
  return Array.isArray(mesh.material) ? mesh.material : [mesh.material];
}

function clearSelection() {
  if (!selectedMesh) return;
  for (const material of materialsFor(selectedMesh)) {
    if (!material?.emissive || selectedMesh.userData.originalEmissive === undefined) continue;
    material.emissive.setHex(selectedMesh.userData.originalEmissive);
    material.emissiveIntensity = selectedMesh.userData.originalEmissiveIntensity;
  }
  selectedMesh = null;
}

function showSelection(mesh) {
  clearSelection();
  const metadata = manifestByName.get(mesh.name);
  if (!metadata) {
    selectionStatus.textContent = "无模型索引";
    selectionName.textContent = mesh.name || "未命名对象";
    selectionRole.textContent = "-";
    selectionSubject.textContent = "场景对象";
    referenceLinks.textContent = "该对象没有对应的模型清单记录";
    return;
  }
  selectedMesh = mesh;
  for (const material of materialsFor(mesh)) {
    if (!material?.emissive) continue;
    mesh.userData.originalEmissive = material.emissive.getHex();
    mesh.userData.originalEmissiveIntensity = material.emissiveIntensity;
    material.emissive.setHex(0xdca34e);
    material.emissiveIntensity = 0.8;
  }
  selectionStatus.textContent = "已选中";
  selectionName.textContent = metadata.name;
  selectionRole.textContent = metadata.role;
  selectionSubject.textContent = metadata.subject;
  referenceLinks.replaceChildren();
  const ids = (metadata.reference_ids || "").split(",").map((id) => id.trim()).filter(Boolean);
  for (const id of ids) {
    const reference = referencesById.get(id);
    const item = document.createElement("div");
    if (!reference) {
      item.textContent = `${id} · 索引缺失`;
    } else {
      const imageLink = document.createElement("a");
      imageLink.href = `../references/${reference.local_file.replaceAll("\\", "/")}`;
      imageLink.target = "_blank";
      imageLink.rel = "noreferrer";
      imageLink.textContent = `${id} · ${reference.view}`;
      const sourceLink = document.createElement("a");
      sourceLink.href = reference.source_page;
      sourceLink.target = "_blank";
      sourceLink.rel = "noreferrer";
      sourceLink.textContent = "来源";
      item.append(imageLink, document.createTextNode(" · "), sourceLink);
    }
    referenceLinks.append(item);
  }
}

function selectAtEvent(event) {
  const bounds = canvas.getBoundingClientRect();
  pointer.x = ((event.clientX - bounds.left) / bounds.width) * 2 - 1;
  pointer.y = -((event.clientY - bounds.top) / bounds.height) * 2 + 1;
  raycaster.setFromCamera(pointer, camera);
  const roots = [...models.values()].map((entry) => entry.root);
  const hit = raycaster.intersectObjects(roots, true).find((entry) => entry.object.isMesh);
  if (hit) showSelection(hit.object);
}

function resize() {
  const width = canvas.clientWidth || canvas.parentElement.clientWidth;
  const height = canvas.clientHeight || 560;
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}
window.addEventListener("resize", resize);

function fitCamera() {
  const box = new THREE.Box3().setFromObject(modelGroup);
  const center = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const radius = Math.max(size.x, size.z) * 0.98;
  controls.target.copy(center);
  camera.position.set(center.x + radius * 0.86, center.y + radius * 0.72, center.z - radius * 1.16);
  controls.update();
}

function applyMode(mode) {
  for (const [id, entry] of models) entry.root.visible = mode === "both" || mode === id;
  document.querySelectorAll("[data-mode]").forEach((button) => button.classList.toggle("active", button.dataset.mode === mode));
}

function applyVisibility() {
  modelGroup.traverse((object) => {
    if (!object.isMesh || !object.userData.category) return;
    const visible = componentVisibility.get(object.userData.category) ?? true;
    object.visible = visible;
  });
}

function applyExplode(value) {
  for (const [, entry] of models) {
    entry.root.traverse((object) => {
      if (!object.isMesh || !object.userData.basePosition) return;
      const base = object.userData.basePosition;
      const category = object.userData.category;
      const factor = category === "车顶与蒸汽设备" ? 1.4 : category === "轮组与转向架" ? -0.8 : category === "门窗与灯具" ? 0.55 : category === "连接与缓冲" ? 0.8 : 0.15;
      object.position.set(base.x, base.y + value * factor, base.z);
    });
  }
}

function buildToggles() {
  const categories = [...new Set([...categoryMatchers.map(([label]) => label), "其他部件"])];
  for (const category of categories) {
    componentVisibility.set(category, true);
    const label = document.createElement("label");
    label.className = "toggle";
    label.innerHTML = `<input type="checkbox" checked data-category="${category}" /> <span>${category}</span>`;
    label.querySelector("input").addEventListener("change", (event) => {
      componentVisibility.set(category, event.target.checked);
      applyVisibility();
    });
    toggleRoot.appendChild(label);
  }
}

async function loadModel(id, url) {
  const loader = new GLTFLoader();
  const gltf = await loader.loadAsync(url);
  const root = gltf.scene;
  root.traverse((object) => {
    if (!object.isMesh) return;
    object.castShadow = true;
    object.receiveShadow = true;
    object.userData.category = categoryFor(object.name);
    object.userData.basePosition = object.position.clone();
  });
  modelGroup.add(root);
  models.set(id, { root });
  return root;
}

canvas.addEventListener("pointerdown", (event) => {
  pointerDown = { x: event.clientX, y: event.clientY };
});
canvas.addEventListener("pointerup", (event) => {
  if (!pointerDown) return;
  const distance = Math.hypot(event.clientX - pointerDown.x, event.clientY - pointerDown.y);
  pointerDown = null;
  if (distance <= 6) selectAtEvent(event);
});

for (const [selector, mode] of [["[data-mode=both]", "both"], ["[data-mode=qj]", "qj"], ["[data-mode=cr400af]", "cr400af"]]) {
  document.querySelector(selector).addEventListener("click", () => applyMode(mode));
}
document.querySelector("#reset-camera").addEventListener("click", fitCamera);
explodeInput.addEventListener("input", (event) => applyExplode(Number(event.target.value)));

async function init() {
  buildToggles();
  resize();
  try {
    await loadTraceability();
    await Promise.all([
      loadModel("qj", "../models/QJ_steam_locomotive.glb"),
      loadModel("cr400af", "../models/CR400AF_emu.glb"),
    ]);
    applyVisibility();
    fitCamera();
    const meshes = [...modelGroup.children].reduce((count, root) => {
      let local = 0;
      root.traverse((object) => { if (object.isMesh) local += 1; });
      return count + local;
    }, 0);
    objectCount.textContent = `${meshes} 个可渲染部件`;
    status.textContent = "模型已加载 · 追溯索引已加载";
    status.style.color = "#8ed7b1";
  } catch (error) {
    console.error(error);
    status.textContent = "模型加载失败，请先运行构建脚本";
    status.style.color = "#ee907e";
  }
}

function animate() {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
}

init();
animate();
