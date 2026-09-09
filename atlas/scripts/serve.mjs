import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const project = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const root = path.resolve(process.argv[2] || path.join(project, 'dist'));
let port = Number(process.env.ATLAS_PORT || 4173);
if (!fs.existsSync(path.join(root,'index.html'))) throw new Error(`Missing build: ${root}. Run npm run build first.`);
const types={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.glb':'model/gltf-binary','.png':'image/png','.json':'application/json; charset=utf-8','.txt':'text/plain; charset=utf-8'};
const server=http.createServer((request,response)=>{
  if(!['GET','HEAD'].includes(request.method)) {response.writeHead(405,{'Allow':'GET, HEAD'});response.end();return;}
  let pathname;
  try {pathname=decodeURIComponent(new URL(request.url,'http://localhost').pathname);} catch {response.writeHead(400);response.end('Bad request');return;}
  const candidate=path.resolve(root,`.${pathname.endsWith('/') ? pathname+'index.html' : pathname}`);
  if(candidate!==root && !candidate.startsWith(root+path.sep)) {response.writeHead(403);response.end('Forbidden');return;}
  fs.stat(candidate,(error,stat)=>{
    if(error || !stat.isFile()) {response.writeHead(404);response.end('Not found');return;}
    response.writeHead(200,{'Content-Type':types[path.extname(candidate)] || 'application/octet-stream','Content-Length':stat.size,'X-Content-Type-Options':'nosniff','Cache-Control':path.extname(candidate)==='.html' ? 'no-cache' : 'public, max-age=3600'});
    if(request.method==='HEAD') {response.end();return;}
    const stream=fs.createReadStream(candidate);stream.on('error',()=>response.destroy());stream.pipe(response);
  });
});
server.on('error',error=>{
  if(error.code==='EADDRINUSE' && port<4190) {port++;server.listen(port,'0.0.0.0');}
  else throw error;
});
server.listen(port,'0.0.0.0',()=>console.log(`ASTRA ATLAS: http://localhost:${port}/`));
