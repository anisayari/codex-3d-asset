import { readFileSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import {
  registerAppResource,
  registerAppTool,
  RESOURCE_MIME_TYPE,
} from "@modelcontextprotocol/ext-apps/server";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(__dirname, "..");
const WIDGET_URI = "ui://widget/asset-preview-v1.html";
const WIDGET_HTML = readFileSync(
  path.join(ROOT_DIR, "mcp-server", "public", "asset-preview-widget.html"),
  "utf8"
);

const LOCAL_VIEWER_ORIGINS = [
  "http://127.0.0.1:4173",
  "http://127.0.0.1:4174",
  "http://localhost:4173",
  "http://localhost:4174",
];

const server = new McpServer({
  name: "codex-3d-asset-widget",
  version: "0.4.0",
});

registerAppResource(
  server,
  "asset-preview-widget",
  WIDGET_URI,
  {},
  async () => ({
    contents: [
      {
        uri: WIDGET_URI,
        mimeType: RESOURCE_MIME_TYPE,
        text: WIDGET_HTML,
        _meta: {
          ui: {
            prefersBorder: false,
            csp: {
              connectDomains: LOCAL_VIEWER_ORIGINS,
              resourceDomains: [],
              frameDomains: LOCAL_VIEWER_ORIGINS,
            },
          },
          "openai/widgetDescription":
            "Interactive Codex 3D asset preview widget for locally generated Tripo outputs.",
        },
      },
    ],
  })
);

registerAppTool(
  server,
  "show_3d_asset_widget",
  {
    title: "Show 3D asset widget",
    description:
      "Use this when the user wants Codex to open a local 3D asset preview widget for a generated model and request fullscreen automatically.",
    inputSchema: {
      viewerUrl: z
        .string()
        .describe("Absolute local viewer URL, for example http://127.0.0.1:4174/..."),
      assetName: z.string().optional().describe("User-facing asset label."),
      format: z.string().optional().describe("Asset format such as glb or obj."),
      notes: z.string().optional().describe("Optional preview notes or fallback guidance."),
      autoFullscreen: z
        .boolean()
        .optional()
        .describe("Whether the widget should request fullscreen on mount."),
    },
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      openWorldHint: false,
      idempotentHint: true,
    },
    _meta: {
      ui: { resourceUri: WIDGET_URI },
      "openai/toolInvocation/invoking": "Opening 3D preview widget...",
      "openai/toolInvocation/invoked": "3D preview widget ready.",
    },
  },
  async ({ viewerUrl, assetName, format, notes, autoFullscreen }) => ({
    content: [
      {
        type: "text",
        text: `Opened the 3D preview widget for ${assetName || "the generated asset"}.`,
      },
    ],
    structuredContent: {
      viewerUrl,
      assetName: assetName || "Generated 3D asset",
      format: format || "glb",
      notes:
        notes ||
        "If the embedded preview does not render, use the in-app target to open the local viewer directly.",
      autoFullscreen: autoFullscreen !== false,
    },
    _meta: {
      "openai/outputTemplate": WIDGET_URI,
    },
  })
);

const transport = new StdioServerTransport();
await server.connect(transport);
