import { createReadStream, existsSync, readdirSync, statSync } from "node:fs";
import { mkdir } from "node:fs/promises";
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(process.env.CODEX_3D_ASSET_VIEWER_ROOT || path.resolve(__dirname, ".."));
const HOST = process.env.CODEX_3D_ASSET_VIEWER_HOST || "127.0.0.1";
const PORT = Number.parseInt(process.env.CODEX_3D_ASSET_VIEWER_PORT || "4174", 10);
const OUTPUT_DIR = path.join(ROOT_DIR, "outputs");
const PREVIEWABLE_EXTENSIONS = new Set([".glb", ".gltf", ".fbx", ".obj", ".stl", ".usdz"]);

const MIME_TYPES = new Map([
  [".css", "text/css; charset=utf-8"],
  [".fbx", "application/octet-stream"],
  [".gif", "image/gif"],
  [".glb", "model/gltf-binary"],
  [".gltf", "model/gltf+json"],
  [".html", "text/html; charset=utf-8"],
  [".ico", "image/x-icon"],
  [".jpeg", "image/jpeg"],
  [".jpg", "image/jpeg"],
  [".js", "text/javascript; charset=utf-8"],
  [".json", "application/json; charset=utf-8"],
  [".obj", "text/plain; charset=utf-8"],
  [".png", "image/png"],
  [".stl", "model/stl"],
  [".svg", "image/svg+xml"],
  [".txt", "text/plain; charset=utf-8"],
  [".usdz", "model/vnd.usdz+zip"],
  [".webp", "image/webp"],
  [".zip", "application/zip"],
  [".bin", "application/octet-stream"],
]);

function log(message) {
  process.stderr.write(`[codex-3d-asset viewer] ${message}\n`);
}

function getMimeType(filePath) {
  return MIME_TYPES.get(path.extname(filePath).toLowerCase()) || "application/octet-stream";
}

function toSafePathname(rawPathname) {
  try {
    return decodeURIComponent(rawPathname);
  } catch {
    return rawPathname;
  }
}

function resolveFilePath(rawPathname) {
  const pathname = toSafePathname(rawPathname);
  const candidate = path.resolve(ROOT_DIR, `.${pathname}`);
  const relative = path.relative(ROOT_DIR, candidate);
  if (relative.startsWith("..") || path.isAbsolute(relative)) {
    return null;
  }
  if (!existsSync(candidate)) {
    return null;
  }
  if (statSync(candidate).isDirectory()) {
    const indexPath = path.join(candidate, "index.html");
    if (!existsSync(indexPath)) {
      return null;
    }
    return indexPath;
  }
  return candidate;
}

function toAssetLabel(filePath) {
  const baseName = path.basename(filePath, path.extname(filePath));
  return baseName
    .replace(/[-_]+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function listGeneratedAssets() {
  const assets = [];

  function walk(currentDir) {
    for (const entry of readdirSync(currentDir, { withFileTypes: true })) {
      const entryPath = path.join(currentDir, entry.name);
      if (entry.isDirectory()) {
        walk(entryPath);
        continue;
      }

      const ext = path.extname(entry.name).toLowerCase();
      if (!PREVIEWABLE_EXTENSIONS.has(ext)) {
        continue;
      }

      const stat = statSync(entryPath);
      const relativePath = path.relative(ROOT_DIR, entryPath).split(path.sep).join("/");
      const modelPath = `/${relativePath}`;

      assets.push({
        id: relativePath,
        name: toAssetLabel(entryPath),
        fileName: path.basename(entryPath),
        format: ext.slice(1),
        modelPath,
        relativePath,
        modifiedAt: stat.mtime.toISOString(),
        sizeBytes: stat.size,
      });
    }
  }

  if (existsSync(OUTPUT_DIR)) {
    walk(OUTPUT_DIR);
  }

  assets.sort((left, right) => {
    const dateDiff = new Date(right.modifiedAt).getTime() - new Date(left.modifiedAt).getTime();
    if (dateDiff !== 0) {
      return dateDiff;
    }
    return left.fileName.localeCompare(right.fileName);
  });

  return assets;
}

await mkdir(OUTPUT_DIR, { recursive: true });

const server = http.createServer(async (request, response) => {
  const url = new URL(request.url || "/", `http://${request.headers.host || `${HOST}:${PORT}`}`);

  if (url.pathname === "/__codex_3d_asset_health") {
    response.writeHead(200, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
    response.end(
      JSON.stringify({
        ok: true,
        host: HOST,
        port: PORT,
        rootDir: ROOT_DIR,
        outputDir: OUTPUT_DIR,
        entryPath: "/viewer/index.html",
      })
    );
    return;
  }

  if (url.pathname === "/__codex_3d_asset_assets") {
    const assets = listGeneratedAssets();
    response.writeHead(200, { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" });
    response.end(
      JSON.stringify({
        ok: true,
        count: assets.length,
        assets,
      })
    );
    return;
  }

  const targetPath = resolveFilePath(url.pathname === "/" ? "/viewer/index.html" : url.pathname);
  if (!targetPath) {
    response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" });
    response.end("Not found");
    return;
  }

  const fileStat = statSync(targetPath);
  response.writeHead(200, {
    "Content-Type": getMimeType(targetPath),
    "Content-Length": fileStat.size,
    "Cache-Control": "no-store",
    "Access-Control-Allow-Origin": "*",
  });

  if (request.method === "HEAD") {
    response.end();
    return;
  }

  createReadStream(targetPath).pipe(response);
});

server.on("error", (error) => {
  log(`server error: ${error instanceof Error ? error.message : String(error)}`);
  process.exit(1);
});

server.listen(PORT, HOST, () => {
  log(`serving ${ROOT_DIR} on http://${HOST}:${PORT}/viewer/index.html`);
});
