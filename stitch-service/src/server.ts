import http from "node:http";

const PORT = parseInt(process.env.STITCH_SERVICE_PORT || "3100", 10);
const SECRET = process.env.STITCH_SERVICE_SECRET || "";
const TIMEOUT = parseInt(process.env.STITCH_TIMEOUT_MS || "300000", 10);

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

async function handleGenerate(
  body: GenerateRequest,
  res: http.ServerResponse
): Promise<void> {
  const { stitch: stitchModule } = await import("@google/stitch-sdk");
  const stitch = stitchModule;

  if (!process.env.STITCH_API_KEY) {
    jsonResponse(res, 500, {
      success: false,
      error: "STITCH_API_KEY not configured",
      provider_used: "stitch",
    } satisfies GenerateResponse);
    return;
  }

  let attempts = 0;
  const maxAttempts = 3;

  while (attempts < maxAttempts) {
    attempts++;
    try {
      const projectTitle = `${body.business_name} — LeadForge Redesign`;
      let projectId = body.stitch_project_id;

      if (!projectId) {
        const project = await stitch.createProject(projectTitle);
        projectId = (project as any).projectId || (project as any).id;
        if (!projectId) {
          throw new Error("Failed to get project ID from Stitch response");
        }
      }

      const project = await stitch.getProject(projectId);

      const screen = await project.generate(body.brief_instruction);

      const screenId =
        (screen as any).screenId ||
        (screen as any).id ||
        "";

      const htmlUrl = await screen.getHtml();
      let htmlContent: string;

      if (htmlUrl && htmlUrl.startsWith("http")) {
        htmlContent = await fetchUrlAsText(htmlUrl, TIMEOUT);
      } else {
        htmlContent = htmlUrl as string;
      }

      let screenshotUrl: string | undefined;
      try {
        screenshotUrl = await screen.getImage();
      } catch {
        // Screenshot is optional
      }

      const result: GenerateResponse = {
        success: true,
        stitch_project_id: projectId,
        stitch_screen_id: screenId,
        html_content: htmlContent,
        html_url: typeof htmlUrl === "string" ? htmlUrl : undefined,
        screenshot_url: screenshotUrl,
        provider_used: "stitch",
        attempts,
      };

      jsonResponse(res, 200, result);
      return;
    } catch (err: any) {
      const msg = String(err?.message || err);

      if (msg.includes("RATE_LIMITED") || msg.includes("429")) {
        if (attempts < maxAttempts) {
          const backoff = attempts * 5000;
          console.warn(
            `[stitch-service] Rate limited, retrying in ${backoff}ms (attempt ${attempts}/${maxAttempts})`
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

const server = http.createServer(async (req, res) => {
  if (req.method === "GET" && req.url === "/health") {
    jsonResponse(res, 200, {
      status: "ok",
      service: "leadforge-stitch-service",
      stitch_api_key_set: !!process.env.STITCH_API_KEY,
    });
    return;
  }

  if (req.method !== "POST" || req.url !== "/generate") {
    jsonResponse(res, 404, { error: "Not found" });
    return;
  }

  if (SECRET && req.headers["x-internal-secret"] !== SECRET) {
    unauthorized(res);
    return;
  }

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
    console.error("[stitch-service] Unhandled error:", err);
    jsonResponse(res, 500, {
      success: false,
      error: `Internal error: ${String(err?.message || err)}`,
      provider_used: "stitch",
    } satisfies GenerateResponse);
  }
});

server.listen(PORT, () => {
  console.log(
    `[stitch-service] Listening on port ${PORT} (API key: ${process.env.STITCH_API_KEY ? "set" : "NOT SET"})`
  );
});
