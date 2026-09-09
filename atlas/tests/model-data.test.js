import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { SYSTEMS, MODEL_METADATA, getSystemId, getPartLabel, getPartDescription, getExplodeDirection } from '../src/model-data.js';

const bytes = fs.readFileSync(new URL('../public/models/leopard2.glb',import.meta.url));
const gltf = JSON.parse(bytes.subarray(20,20+bytes.readUInt32LE(12)));
const sourceParts = gltf.nodes.filter(node=>node.mesh!==undefined);

test('every source part belongs to a known system and has Chinese metadata',()=>{
  assert.equal(sourceParts.length,MODEL_METADATA.logicalParts);
  for(const part of sourceParts) {
    assert.ok(SYSTEMS.some(s=>s.id===getSystemId(part.name)),part.name);
    assert.match(getPartLabel(part.name),/[\u3400-\u9fff]/,part.name);
    assert.ok(getPartDescription(part.name).length>10,part.name);
  }
});
test('track links preserve the 85-per-side logical part count',()=>{
  for(const id of ['track-left','track-right']) {
    const parts=sourceParts.filter(p=>getSystemId(p.name)===id);
    assert.equal(parts.length,85);
    for(const part of parts) assert.equal(gltf.meshes[part.mesh].primitives.length,3);
  }
});
test('explode vectors follow GLB Y-up, left -Z coordinates without shared mutable state',()=>{
  assert.ok(getExplodeDirection('track-left')[2]<0);
  assert.ok(getExplodeDirection('track-right')[2]>0);
  assert.ok(getExplodeDirection('turret')[1]>0);
  const changed=getExplodeDirection('gun'); changed[0]=999;
  assert.ok(getExplodeDirection('gun')[0]<0);
});
