import { mkdirSync, rmSync, writeFileSync } from "node:fs";
import http from "node:http";
import net from "node:net";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, "..");

function isPortFree(port) {
  return new Promise((resolve) => {
    const server = net.createServer();
    server.unref();
    server.on("error", () => resolve(false));
    server.listen(port, "127.0.0.1", () => {
      server.close(() => resolve(true));
    });
  });
}

async function findFreePort(start = 4180, end = 4190) {
  for (let port = start; port <= end; port += 1) {
    if (await isPortFree(port)) {
      return port;
    }
  }

  throw new Error(`No free port found in the ${start}-${end} range`);
}

function readHealth(port) {
  return new Promise((resolve, reject) => {
    const request = http.get(
      {
        hostname: "127.0.0.1",
        port,
        path: "/__codex_3d_asset_health",
        timeout: 1500,
      },
      (response) => {
        let body = "";
        response.setEncoding("utf8");
        response.on("data", (chunk) => {
          body += chunk;
        });
        response.on("end", () => {
          try {
            resolve(JSON.parse(body));
          } catch (error) {
            reject(error);
          }
        });
      }
    );

    request.on("timeout", () => {
      request.destroy(new Error("viewer health request timed out"));
    });
    request.on("error", reject);
  });
}

function readGeneratedAssets(port) {
  return new Promise((resolve, reject) => {
    const request = http.get(
      {
        hostname: "127.0.0.1",
        port,
        path: "/__codex_3d_asset_assets",
        timeout: 1500,
      },
      (response) => {
        let body = "";
        response.setEncoding("utf8");
        response.on("data", (chunk) => {
          body += chunk;
        });
        response.on("end", () => {
          try {
            resolve(JSON.parse(body));
          } catch (error) {
            reject(error);
          }
        });
      }
    );

    request.on("timeout", () => {
      request.destroy(new Error("viewer asset request timed out"));
    });
    request.on("error", reject);
  });
}

const viewerPort = await findFreePort();
const smokeOutputDir = path.join(ROOT_DIR, "outputs", "smoke-test");
const smokeAssetPath = path.join(smokeOutputDir, "smoke-test-knight.glb");
mkdirSync(smokeOutputDir, { recursive: true });
writeFileSync(smokeAssetPath, "");

const transport = new StdioClientTransport({
  command: "node",
  args: ["./mcp-server/bootstrap.mjs"],
  cwd: ROOT_DIR,
  env: {
    ...process.env,
    CODEX_3D_ASSET_VIEWER_PORT: String(viewerPort),
  },
});

const client = new Client({
  name: "codex-3d-asset-widget-smoke-test",
  version: "0.1.0",
});

await client.connect(transport);

const tools = await client.listTools();
const tool = tools.tools.find((entry) => entry.name === "show_3d_asset_widget");
if (!tool) {
  throw new Error("show_3d_asset_widget tool not found");
}

if (tool?._meta?.ui?.resourceUri !== "ui://widget/asset-preview-v1.html") {
  throw new Error("Unexpected widget resource URI");
}

const health = await readHealth(viewerPort);
if (health?.entryPath !== "/viewer/index.html") {
  throw new Error("Viewer bootstrap did not expose the expected entry path");
}

try {
  const assetsPayload = await readGeneratedAssets(viewerPort);
  const smokeAsset = assetsPayload?.assets?.find((asset) => asset.modelPath === "/outputs/smoke-test/smoke-test-knight.glb");
  if (!smokeAsset) {
    throw new Error("Viewer asset browser did not expose the generated smoke-test asset");
  }

  const callResult = await client.callTool({
    name: "show_3d_asset_widget",
    arguments: {
      viewerUrl: `http://127.0.0.1:${viewerPort}/viewer/index.html?model=/outputs/smoke-test/smoke-test-knight.glb`,
      assetName: "Smoke Test Knight",
      format: "glb",
      autoFullscreen: true,
    },
  });

  if (callResult?.structuredContent?.assetName !== "Smoke Test Knight") {
    throw new Error("Tool call did not return the expected structured content");
  }

  console.log(
    JSON.stringify(
      {
        toolName: tool.name,
        resourceUri: tool?._meta?.ui?.resourceUri,
        viewerHealth: health,
        generatedAssetsCount: assetsPayload.count,
        smokeAsset,
        callStructuredContent: callResult.structuredContent,
      },
      null,
      2
    )
  );
} finally {
  await client.close();
  rmSync(smokeOutputDir, { recursive: true, force: true });
}
