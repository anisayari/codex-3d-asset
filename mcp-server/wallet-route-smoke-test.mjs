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

async function findFreePort(start = 4290, end = 4310) {
  for (let port = start; port <= end; port += 1) {
    if (await isPortFree(port)) {
      return port;
    }
  }

  throw new Error(`No free port found in the ${start}-${end} range`);
}

const apiPort = await findFreePort();

const apiServer = http.createServer((request, response) => {
  if (request.url === "/v2/openapi/wallet") {
    response.writeHead(404, { "Content-Type": "application/json; charset=utf-8" });
    response.end(JSON.stringify({ code: 404, message: "Not found" }));
    return;
  }

  if (request.url === "/v2/openapi/wallet/balance") {
    response.writeHead(200, { "Content-Type": "application/json; charset=utf-8" });
    response.end(
      JSON.stringify({
        data: {
          available_credits: 321,
        },
      })
    );
    return;
  }

  response.writeHead(404, { "Content-Type": "application/json; charset=utf-8" });
  response.end(JSON.stringify({ code: 404, message: "Unknown route" }));
});

await new Promise((resolve) => apiServer.listen(apiPort, "127.0.0.1", resolve));

const transport = new StdioClientTransport({
  command: "node",
  args: ["./mcp-server/server.mjs"],
  cwd: ROOT_DIR,
  env: {
    ...process.env,
    CODEX_3D_ASSET_TRIPO_API_BASE_URL: `http://127.0.0.1:${apiPort}/v2/openapi`,
    CODEX_3D_ASSET_TRIPO_WALLET_PATHS: "/wallet,/wallet/balance",
  },
});

const client = new Client({
  name: "codex-3d-asset-wallet-route-smoke-test",
  version: "0.1.0",
});

try {
  await client.connect(transport);
  const walletResult = await client.callTool({
    name: "get_tripo_wallet_balance",
    arguments: {
      apiKey: "tsk_test_wallet_route",
    },
  });

  if (walletResult?.structuredContent?.ok !== true) {
    throw new Error("Wallet route fallback did not return an OK result");
  }

  if (walletResult?.structuredContent?.verified !== true) {
    throw new Error("Wallet route fallback did not return a verified balance");
  }

  if (walletResult?.structuredContent?.walletPath !== "/wallet/balance") {
    throw new Error(
      `Unexpected wallet path: ${walletResult?.structuredContent?.walletPath || "missing"}`
    );
  }

  if (walletResult?.structuredContent?.balanceCredits !== 321) {
    throw new Error(
      `Unexpected wallet balance: ${walletResult?.structuredContent?.balanceCredits || "missing"}`
    );
  }

  const attemptedPaths = walletResult?.structuredContent?.attemptedPaths || [];
  if (!Array.isArray(attemptedPaths) || attemptedPaths.join(",") !== "/wallet,/wallet/balance") {
    throw new Error(`Unexpected attempted paths: ${JSON.stringify(attemptedPaths)}`);
  }

  console.log(
    JSON.stringify(
      {
        ok: true,
        walletPath: walletResult.structuredContent.walletPath,
        balanceCredits: walletResult.structuredContent.balanceCredits,
        attemptedPaths,
      },
      null,
      2
    )
  );
} finally {
  await client.close().catch(() => {});
  await new Promise((resolve, reject) => apiServer.close((error) => (error ? reject(error) : resolve())));
}
