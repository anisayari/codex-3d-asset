import path from "node:path";
import { fileURLToPath } from "node:url";

import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, "..");

const transport = new StdioClientTransport({
  command: "node",
  args: ["./mcp-server/server.mjs"],
  cwd: ROOT_DIR,
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

const callResult = await client.callTool({
  name: "show_3d_asset_widget",
  arguments: {
    viewerUrl:
      "http://127.0.0.1:4174/codex-3d-asset/viewer/index.html?model=/codex-3d-asset-api-test/c84d9ea6-ea7f-43f5-b8e2-5170f22bd808-pbr-model.glb",
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
      callStructuredContent: callResult.structuredContent,
    },
    null,
    2
  )
);

await client.close();
