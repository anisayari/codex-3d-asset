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
const ACTIVE_VIEWER_PORT = Number.parseInt(
  process.env.CODEX_3D_ASSET_ACTIVE_VIEWER_PORT || process.env.CODEX_3D_ASSET_VIEWER_PORT || "4174",
  10
);
const PLUGIN_VERSION = "0.5.2";
const TRIPO_API_BASE_URL = "https://api.tripo3d.ai/v2/openapi";
const WIDGET_URI = "ui://widget/asset-preview-v1.html";
const WIDGET_HTML = readFileSync(
  path.join(ROOT_DIR, "mcp-server", "public", "asset-preview-widget.html"),
  "utf8"
);

const LOCAL_VIEWER_ORIGINS = Array.from(
  new Set([
    `http://127.0.0.1:${ACTIVE_VIEWER_PORT}`,
    `http://localhost:${ACTIVE_VIEWER_PORT}`,
    "http://127.0.0.1:4173",
    "http://127.0.0.1:4174",
    "http://localhost:4173",
    "http://localhost:4174",
  ])
);

const server = new McpServer({
  name: "codex-3d-asset-widget",
  version: PLUGIN_VERSION,
});

function readNestedField(source, fieldPath) {
  return fieldPath.split(".").reduce((value, segment) => {
    if (value && typeof value === "object" && segment in value) {
      return value[segment];
    }
    return undefined;
  }, source);
}

function extractWalletBalance(payload) {
  const candidates = [
    "data.available_credits",
    "data.remaining_credits",
    "data.credit_balance",
    "data.credits",
    "data.balance",
  ];

  for (const candidate of candidates) {
    const value = readNestedField(payload, candidate);
    if (typeof value === "number") {
      return { field: candidate, value };
    }
  }

  return null;
}

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

registerAppTool(
  server,
  "get_tripo_wallet_balance",
  {
    title: "Get Tripo wallet balance",
    description:
      "Use this before a paid Tripo generation or conversion task to retrieve the current wallet credit balance when possible.",
    inputSchema: {
      apiKey: z
        .string()
        .optional()
        .describe(
          "Optional Tripo API key for the current request. If omitted, the tool uses TRIPO_API_KEY from the MCP server environment."
        ),
    },
    annotations: {
      readOnlyHint: true,
      destructiveHint: false,
      openWorldHint: true,
      idempotentHint: true,
    },
    _meta: {
      "openai/toolInvocation/invoking": "Checking Tripo wallet balance...",
      "openai/toolInvocation/invoked": "Tripo wallet balance checked.",
    },
  },
  async ({ apiKey }) => {
    const effectiveApiKey = apiKey || process.env.TRIPO_API_KEY || "";
    if (!effectiveApiKey) {
      return {
        content: [
          {
            type: "text",
            text: "TRIPO_API_KEY is missing, so the wallet balance could not be checked.",
          },
        ],
        structuredContent: {
          ok: false,
          verified: false,
          missingApiKey: true,
          walletPath: "/wallet",
        },
      };
    }

    try {
      const response = await fetch(`${TRIPO_API_BASE_URL}/wallet`, {
        headers: {
          Authorization: `Bearer ${effectiveApiKey}`,
        },
      });

      const rawText = await response.text();
      let payload = null;
      try {
        payload = JSON.parse(rawText);
      } catch {
        payload = { raw: rawText };
      }

      const balance = extractWalletBalance(payload);
      if (!response.ok) {
        return {
          content: [
            {
              type: "text",
              text: `Tripo wallet check failed with status ${response.status}.`,
            },
          ],
          structuredContent: {
            ok: false,
            verified: false,
            status: response.status,
            walletPath: "/wallet",
            response: payload,
          },
        };
      }

      if (!balance) {
        return {
          content: [
            {
              type: "text",
              text: "Tripo wallet responded, but the credit balance field could not be identified.",
            },
          ],
          structuredContent: {
            ok: true,
            verified: false,
            walletPath: "/wallet",
            response: payload,
          },
        };
      }

      return {
        content: [
          {
            type: "text",
            text: `Current Tripo wallet balance: ${balance.value} credits.`,
          },
        ],
        structuredContent: {
          ok: true,
          verified: true,
          walletPath: "/wallet",
          balanceCredits: balance.value,
          balanceField: balance.field,
          response: payload,
        },
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Tripo wallet check failed: ${error instanceof Error ? error.message : String(error)}`,
          },
        ],
        structuredContent: {
          ok: false,
          verified: false,
          walletPath: "/wallet",
          error: error instanceof Error ? error.message : String(error),
        },
      };
    }
  }
);

const transport = new StdioServerTransport();
await server.connect(transport);
