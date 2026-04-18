import { spawn, spawnSync } from "node:child_process";
import { existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import http from "node:http";
import net from "node:net";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, "..");
const PACKAGE_JSON_PATH = path.join(ROOT_DIR, "package.json");
const PACKAGE_JSON = JSON.parse(readFileSync(PACKAGE_JSON_PATH, "utf8"));
const NODE_MODULES_DIR = path.join(ROOT_DIR, "node_modules");
const DEFAULT_PORT = Number.parseInt(process.env.CODEX_3D_ASSET_VIEWER_PORT || "4174", 10);
const VIEWER_HOST = process.env.CODEX_3D_ASSET_VIEWER_HOST || "127.0.0.1";
const VIEWER_ROOT = ROOT_DIR;
const OUTPUT_DIR = path.join(ROOT_DIR, "outputs");
const RUNTIME_DIR = path.join(ROOT_DIR, ".codex-runtime");
const VIEWER_RUNTIME_PATH = path.join(RUNTIME_DIR, "viewer.json");
const VIEWER_SERVER_PATH = path.join(ROOT_DIR, "mcp-server", "local-viewer-server.mjs");
const SERVER_ENTRY_PATH = path.join(ROOT_DIR, "mcp-server", "server.mjs");
const PORT_SCAN_LIMIT = 10;

function log(message) {
  process.stderr.write(`[codex-3d-asset bootstrap] ${message}\n`);
}

function ensureDir(dirPath) {
  mkdirSync(dirPath, { recursive: true });
}

function hasInstalledDependencies() {
  if (!existsSync(NODE_MODULES_DIR)) {
    return false;
  }

  return Object.keys(PACKAGE_JSON.dependencies || {}).every((dependencyName) =>
    existsSync(path.join(NODE_MODULES_DIR, dependencyName))
  );
}

function installDependencies() {
  const npmCommand = process.platform === "win32" ? "npm.cmd" : "npm";
  const npmArgs = existsSync(path.join(ROOT_DIR, "package-lock.json"))
    ? ["ci", "--no-fund", "--no-audit"]
    : ["install", "--no-fund", "--no-audit"];

  log(`installing local MCP dependencies with "${npmCommand} ${npmArgs.join(" ")}"`);
  const result = spawnSync(npmCommand, npmArgs, {
    cwd: ROOT_DIR,
    encoding: "utf8",
    stdio: "pipe",
  });

  if (result.stdout) {
    process.stderr.write(result.stdout);
  }
  if (result.stderr) {
    process.stderr.write(result.stderr);
  }

  if (result.error) {
    throw result.error;
  }
  if (result.status !== 0) {
    throw new Error(`Dependency installation failed with exit code ${result.status}`);
  }
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function readHealth(port) {
  return new Promise((resolve) => {
    const request = http.get(
      {
        hostname: VIEWER_HOST,
        port,
        path: "/__codex_3d_asset_health",
        timeout: 1200,
      },
      (response) => {
        let body = "";
        response.setEncoding("utf8");
        response.on("data", (chunk) => {
          body += chunk;
        });
        response.on("end", () => {
          if (response.statusCode !== 200) {
            resolve(null);
            return;
          }

          try {
            resolve(JSON.parse(body));
          } catch {
            resolve(null);
          }
        });
      }
    );

    request.on("timeout", () => {
      request.destroy();
      resolve(null);
    });
    request.on("error", () => resolve(null));
  });
}

function isPortFree(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.unref();
    server.on("error", () => resolve(false));
    server.listen(port, VIEWER_HOST, () => {
      server.close(() => resolve(true));
    });
  });
}

async function resolveViewerPort() {
  for (let offset = 0; offset <= PORT_SCAN_LIMIT; offset += 1) {
    const candidate = DEFAULT_PORT + offset;
    const health = await readHealth(candidate);
    if (health?.ok && health.rootDir === VIEWER_ROOT) {
      return { port: candidate, alreadyRunning: true };
    }
    if (await isPortFree(candidate)) {
      return { port: candidate, alreadyRunning: false };
    }
  }

  throw new Error(
    `Could not find a free preview port in the ${DEFAULT_PORT}-${DEFAULT_PORT + PORT_SCAN_LIMIT} range`
  );
}

function writeRuntimeFile(port) {
  ensureDir(RUNTIME_DIR);
  writeFileSync(
    VIEWER_RUNTIME_PATH,
    JSON.stringify(
      {
        generatedAt: new Date().toISOString(),
        viewerUrlBase: `http://${VIEWER_HOST}:${port}`,
        host: VIEWER_HOST,
        activePort: port,
        rootDir: VIEWER_ROOT,
        outputDir: OUTPUT_DIR,
        entryPath: "/viewer/index.html",
        modelQueryParameter: "model",
        previewOutputPrefix: "/outputs/",
      },
      null,
      2
    )
  );
}

function spawnViewerServer(port) {
  log(`starting local viewer server on ${VIEWER_HOST}:${port}`);
  const child = spawn(process.execPath, [VIEWER_SERVER_PATH], {
    cwd: ROOT_DIR,
    env: {
      ...process.env,
      CODEX_3D_ASSET_VIEWER_ROOT: VIEWER_ROOT,
      CODEX_3D_ASSET_VIEWER_HOST: VIEWER_HOST,
      CODEX_3D_ASSET_VIEWER_PORT: String(port),
    },
    detached: true,
    stdio: "ignore",
  });
  child.unref();
}

async function ensureViewerServer() {
  ensureDir(OUTPUT_DIR);

  const { port, alreadyRunning } = await resolveViewerPort();
  if (!alreadyRunning) {
    spawnViewerServer(port);
    for (let attempt = 0; attempt < 30; attempt += 1) {
      const health = await readHealth(port);
      if (health?.ok && health.rootDir === VIEWER_ROOT) {
        writeRuntimeFile(port);
        return port;
      }
      await wait(200);
    }
    throw new Error(`Viewer server did not become healthy on port ${port}`);
  }

  writeRuntimeFile(port);
  return port;
}

async function main() {
  ensureDir(OUTPUT_DIR);

  if (!hasInstalledDependencies()) {
    installDependencies();
  }

  const activePort = await ensureViewerServer();
  process.env.CODEX_3D_ASSET_ACTIVE_VIEWER_PORT = String(activePort);
  process.env.CODEX_3D_ASSET_VIEWER_ROOT = VIEWER_ROOT;
  process.env.CODEX_3D_ASSET_OUTPUT_DIR = OUTPUT_DIR;

  if (process.env.CODEX_3D_ASSET_BOOTSTRAP_ONLY === "1") {
    log(`bootstrap-only check complete on port ${activePort}`);
    return;
  }

  await import(pathToFileURL(SERVER_ENTRY_PATH).href);
}

await main();
