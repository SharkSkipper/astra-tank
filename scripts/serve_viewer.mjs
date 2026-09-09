import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const port = Number(process.env.ASTRA_TRAIN_PORT || 41738);
const mime = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".glb": "model/gltf-binary",
  ".png": "image/png",
  ".jpg": "image/jpeg",
};

const server = http.createServer((request, response) => {
  const requestPath = decodeURIComponent((request.url || "/").split("?")[0]);
  const relative = requestPath === "/" ? "/viewer/" : requestPath;
  const candidate = path.resolve(root, `.${relative}`);
  if (!candidate.startsWith(root)) {
    response.writeHead(403);
    response.end("Forbidden");
    return;
  }
  fs.stat(candidate, (statError, stat) => {
    const filePath = !statError && stat.isDirectory() ? path.join(candidate, "index.html") : candidate;
    fs.readFile(filePath, (error, data) => {
      if (error) {
        response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
        response.end("Not found");
        return;
      }
      response.writeHead(200, { "Content-Type": mime[path.extname(filePath).toLowerCase()] || "application/octet-stream" });
      response.end(data);
    });
  });
});

server.listen(port, "127.0.0.1", () => {
  console.log(`Viewer running at http://localhost:${port}/viewer/`);
});

