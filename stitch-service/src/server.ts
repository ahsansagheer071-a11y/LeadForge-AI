import http from "node:http";

// ── Environment ────────────────────────────────────────────────────────────
// Railway sets PORT; STITCH_SERVICE_PORT is the fallback for local dev.
const PORT = parseInt(
  process.env.PORT || process.env.STITCH_SERVICE_PORT || "3100",
  10,
);
const SECRET = process.env.STITCH_SERVICE_SECRET || "";
const TIMEOUT_MS = parseInt(process.env.STITCH_TIMEOUT_MS || "300000", 10);

// ── Startup guard ──────────────────────────────────────────────────────────
// Fail immediately with a clear message if the API key is missing.
if (!process.env.STITCH_API_KEY) {
  console.error(
    "[stitch-service] FATAL: STITCH_API_KEY environment variable is not set. " +
      "The service cannot function without it. Exiting.",
  );
  process.exit(1);
}

// ── Types ──────────────────────────────────────────────────────────────────
interface GenerateRequest {
  brief_instruction: string;
  business_name: string;
  stitch_project_id?: string;
}

interface GenerateResponse {
  success: boolean;
  stitch_project_id?: string;
  stitch_screen_id?: string;
  html_content?: string;
  html_url?: string;
  screenshot_url?: string;
  provider_used: string;
  error?: string;
  attempts?: number;
}

// ── Helpers ────────────────────────────────────────────────────────────────
function unauthorized(res: http.ServerResponse) {
  res.writeHead(401, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ error: "Unauthorized" }));
}

function jsonResponse(res: http.ServerResponse, status: number, data: unknown) {
  res.writeHead(status, { "Content-Type": "application/json" });
  res.end(JSON.stringify(data));
}

async function readBody(req: http.IncomingMessage): Promise<string> {
  return new Promise((resolve, reject) => {
    const chunks: Buffer[] = [];
    req.on("data", (chunk: Buffer) => chunks.push(chunk));
    req.on("end", () => resolve(Buffer.concat(chunks).toString("utf-8")));
    req.on("error", reject);
  });
}

async function fetchUrlAsText(url: string, timeoutMs: number): Promise<string> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const resp = await fetch(url, { signal: controller.signal });
    if (!resp.ok) throw new Error(`HTTP ${resp.status} fetching ${url}`);
    return await resp.text();
  } finally {
    clearTimeout(timer);
  }
}

// ── POST /generate handler ────────────────────────────────────────────────
async function handleGenerate(
  body: GenerateRequest,
  res: http.ServerResponse,
): Promise<void> {
  // Dynamic import — the SDK reads STITCH_API_KEY at import time
  const { stitch } = await import("@google/stitch-sdk");

  let attempts = 0;
  const maxAttempts = 3;

  while (attempts < maxAttempts) {
    attempts++;
    try {
      const projectTitle = `${body.business_name} — LeadForge Redesign`;

      // Get or create project
      let project;
      if (body.stitch_project_id) {
        project = stitch.project(body.stitch_project_id);
      } else {
        project = await stitch.createProject(projectTitle);
      }

      const projectId = project.projectId;

      // Generate screen from brief instruction
      const screen = await project.generate(body.brief_instruction);
      const screenId = screen.screenId;

      // Retrieve HTML (may be a URL or inline)
      const htmlUrl = await screen.getHtml();
      let htmlContent: string;

      if (htmlUrl && htmlUrl.startsWith("http")) {
        htmlContent = await fetchUrlAsText(htmlUrl, TIMEOUT_MS);
      } else {
        htmlContent = htmlUrl as string;
      }

      // Screenshot is optional
      let screenshotUrl: string | undefined;
      try {
        screenshotUrl = await screen.getImage();
      } catch {
        // ignored
      }

      jsonResponse(res, 200, {
        success: true,
        stitch_project_id: projectId,
        stitch_screen_id: screenId,
        html_content: htmlContent,
        html_url: typeof htmlUrl === "string" ? htmlUrl : undefined,
        screenshot_url: screenshotUrl,
        provider_used: "stitch",
        attempts,
      } satisfies GenerateResponse);
      return;
    } catch (err: any) {
      const msg = String(err?.message || err);

      if (msg.includes("RATE_LIMITED") || msg.includes("429")) {
        if (attempts < maxAttempts) {
          const backoff = attempts * 5000;
          console.warn(
            `[stitch-service] Rate limited, retrying in ${backoff}ms (attempt ${attempts}/${maxAttempts})`,
          );
          await new Promise((r) => setTimeout(r, backoff));
          continue;
        }
      }

      jsonResponse(res, 502, {
        success: false,
        error: `Stitch generation failed: ${msg}`,
        provider_used: "stitch",
        attempts,
      } satisfies GenerateResponse);
      return;
    }
  }

  jsonResponse(res, 502, {
    success: false,
    error: "Max attempts exceeded",
    provider_used: "stitch",
    attempts,
  } satisfies GenerateResponse);
}

// ── HTTP server ────────────────────────────────────────────────────────────
const server = http.createServer(async (req, res) => {
  // GET /health — used by Railway probes and Python StitchDesignProvider
  if (req.method === "GET" && req.url === "/health") {
    jsonResponse(res, 200, {
      status: "ok",
      service: "leadforge-stitch-service",
      stitch_api_key_set: true, // always true — process exits if not set
    });
    return;
  }

  // 404 for unknown routes
  if (req.method !== "POST" || req.url !== "/generate") {
    jsonResponse(res, 404, { error: "Not found" });
    return;
  }

  // Internal shared-secret gate on /generate
  if (SECRET && req.headers["x-internal-secret"] !== SECRET) {
    unauthorized(res);
    return;
  }

  // Enforce a hard request-level timeout so a hung Stitch call never
  // blocks the worker forever.
  const requestTimer = setTimeout(() => {
    if (!res.headersSent) {
      jsonResponse(res, 504, {
        success: false,
        error: `Request timed out after ${Math.round(TIMEOUT_MS / 1000)}s`,
        provider_used: "stitch",
        attempts: 0,
      } satisfies GenerateResponse);
    }
  }, TIMEOUT_MS + 30_000);

  try {
    const raw = await readBody(req);
    const body: GenerateRequest = JSON.parse(raw);

    if (!body.brief_instruction || body.brief_instruction.length < 50) {
      jsonResponse(res, 400, {
        success: false,
        error: "brief_instruction is required and must be >= 50 chars",
        provider_used: "stitch",
      } satisfies GenerateResponse);
      return;
    }

    if (!body.business_name) {
      jsonResponse(res, 400, {
        success: false,
        error: "business_name is required",
        provider_used: "stitch",
      } satisfies GenerateResponse);
      return;
    }

    await handleGenerate(body, res);
  } catch (err: any) {
    // Log the error type, never the request body or secrets
    console.error(
      "[stitch-service] Unhandled error:",
      err?.name || String(err?.message || err),
    );
    if (!res.headersSent) {
      jsonResponse(res, 500, {
        success: false,
        error: "Internal service error",
        provider_used: "stitch",
      } satisfies GenerateResponse);
    }
  } finally {
    clearTimeout(requestTimer);
  }
});

// ── Start ──────────────────────────────────────────────────────────────────
server.listen(PORT, () => {
  console.log(`[stitch-service] Listening on port ${PORT}`);
});
