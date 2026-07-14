import { describe, it, expect, beforeAll, afterAll } from "vitest";
import http from "node:http";
import { spawn, ChildProcess } from "node:child_process";
import path from "node:path";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function httpGet(
  url: string,
  headers: Record<string, string> = {},
): Promise<{ status: number; data: any }> {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const req = http.request(
      {
        hostname: u.hostname,
        port: u.port,
        path: u.pathname,
        method: "GET",
        headers,
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (c: Buffer) => chunks.push(c));
        res.on("end", () => {
          const raw = Buffer.concat(chunks).toString("utf-8");
          let data: any;
          try {
            data = JSON.parse(raw);
          } catch {
            data = raw;
          }
          resolve({ status: res.statusCode || 0, data });
        });
      },
    );
    req.on("error", reject);
    req.end();
  });
}

function httpPost(
  url: string,
  body: unknown,
  headers: Record<string, string> = {},
): Promise<{ status: number; data: any }> {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const payload = JSON.stringify(body);
    const req = http.request(
      {
        hostname: u.hostname,
        port: u.port,
        path: u.pathname,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(payload).toString(),
          ...headers,
        },
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (c: Buffer) => chunks.push(c));
        res.on("end", () => {
          const raw = Buffer.concat(chunks).toString("utf-8");
          let data: any;
          try {
            data = JSON.parse(raw);
          } catch {
            data = raw;
          }
          resolve({ status: res.statusCode || 0, data });
        });
      },
    );
    req.on("error", reject);
    req.write(payload);
    req.end();
  });
}

function httpPostRaw(
  url: string,
  rawBody: string,
  headers: Record<string, string> = {},
): Promise<{ status: number; data: any }> {
  return new Promise((resolve, reject) => {
    const u = new URL(url);
    const req = http.request(
      {
        hostname: u.hostname,
        port: u.port,
        path: u.pathname,
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(rawBody).toString(),
          ...headers,
        },
      },
      (res) => {
        const chunks: Buffer[] = [];
        res.on("data", (c: Buffer) => chunks.push(c));
        res.on("end", () => {
          const raw = Buffer.concat(chunks).toString("utf-8");
          let data: any;
          try {
            data = JSON.parse(raw);
          } catch {
            data = raw;
          }
          resolve({ status: res.statusCode || 0, data });
        });
      },
    );
    req.on("error", reject);
    req.write(rawBody);
    req.end();
  });
}

function waitForPort(
  port: number,
  timeoutMs = 10000,
): Promise<void> {
  const start = Date.now();
  return new Promise((resolve, reject) => {
    const tryConnect = () => {
      const req = http.get(`http://127.0.0.1:${port}/health`, (res) => {
        res.resume();
        resolve();
      });
      req.on("error", () => {
        if (Date.now() - start > timeoutMs) {
          reject(new Error(`Port ${port} not ready after ${timeoutMs}ms`));
          return;
        }
        setTimeout(tryConnect, 200);
      });
      req.end();
    };
    tryConnect();
  });
}

// ---------------------------------------------------------------------------
// Start the real server as a child process
// ---------------------------------------------------------------------------

const PORT = 13200 + Math.floor(Math.random() * 800);
const BASE = `http://127.0.0.1:${PORT}`;
let serverProcess: ChildProcess;

beforeAll(async () => {
  serverProcess = spawn("node", ["dist/server.js"], {
    cwd: path.resolve(__dirname, ".."),
    env: {
      ...process.env,
      STITCH_API_KEY: "test-api-key-for-contract-tests",
      STITCH_SERVICE_PORT: String(PORT),
      STITCH_SERVICE_SECRET: "test-shared-secret",
      STITCH_TIMEOUT_MS: "5000",
    },
    stdio: "pipe",
  });
  serverProcess.stderr?.pipe(process.stderr);
  serverProcess.stdout?.pipe(process.stdout);

  await waitForPort(PORT, 15000);
});

afterAll(async () => {
  if (serverProcess && !serverProcess.killed) {
    serverProcess.kill("SIGTERM");
    await new Promise<void>((resolve) => {
      serverProcess.on("exit", () => resolve());
      setTimeout(() => resolve(), 3000);
    });
  }
});

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("GET /health", () => {
  it("returns 200 with status ok", async () => {
    const { status, data } = await httpGet(`${BASE}/health`);
    expect(status).toBe(200);
    expect(data.status).toBe("ok");
    expect(data.service).toBe("leadforge-stitch-service");
    expect(data.stitch_api_key_set).toBe(true);
  });
});

describe("POST /generate — auth", () => {
  it("rejects requests without the shared secret", async () => {
    const { status, data } = await httpPost(`${BASE}/generate`, {
      brief_instruction: "x".repeat(60),
      business_name: "Test Biz",
    });
    expect(status).toBe(401);
    expect(data.error).toBe("Unauthorized");
  });

  it(
    "accepts requests with the correct shared secret",
    async () => {
      // The Stitch SDK will fail with a fake key, but we verify that
      // the request passes auth and reaches the handler (502 = auth passed).
      const { status, data } = await httpPost(
        `${BASE}/generate`,
        {
          brief_instruction: "x".repeat(60),
          business_name: "Test Biz",
        },
        { "X-Internal-Secret": "test-shared-secret" },
      );
      expect(status).toBe(502);
      expect(data.success).toBe(false);
      expect(data.error).toContain("Stitch generation failed");
    },
    30_000,
  );
});

describe("POST /generate — input validation", () => {
  it("rejects missing brief_instruction", async () => {
    const { status, data } = await httpPost(
      `${BASE}/generate`,
      { business_name: "Test Biz" },
      { "X-Internal-Secret": "test-shared-secret" },
    );
    expect(status).toBe(400);
    expect(data.error).toContain("brief_instruction");
    expect(data.success).toBe(false);
  });

  it("rejects short brief_instruction", async () => {
    const { status, data } = await httpPost(
      `${BASE}/generate`,
      { brief_instruction: "short", business_name: "Test Biz" },
      { "X-Internal-Secret": "test-shared-secret" },
    );
    expect(status).toBe(400);
    expect(data.success).toBe(false);
  });

  it("rejects missing business_name", async () => {
    const { status, data } = await httpPost(
      `${BASE}/generate`,
      { brief_instruction: "x".repeat(60) },
      { "X-Internal-Secret": "test-shared-secret" },
    );
    expect(status).toBe(400);
    expect(data.error).toContain("business_name");
    expect(data.success).toBe(false);
  });

  it("rejects invalid JSON body", async () => {
    const { status, data } = await httpPostRaw(
      `${BASE}/generate`,
      "this is not valid json {{{",
      { "X-Internal-Secret": "test-shared-secret" },
    );
    expect(status).toBe(500);
    expect(data.success).toBe(false);
  });
});

describe("Route handling", () => {
  it("GET /unknown returns 404", async () => {
    const { status, data } = await httpGet(`${BASE}/unknown`);
    expect(status).toBe(404);
    expect(data.error).toBe("Not found");
  });

  it("POST /unknown returns 404", async () => {
    const { status, data } = await httpPost(`${BASE}/unknown`, {}, {});
    expect(status).toBe(404);
  });
});

describe("Response structure", () => {
  it("error responses have provider_used field", async () => {
    const { data } = await httpPost(
      `${BASE}/generate`,
      { brief_instruction: "x".repeat(60), business_name: "Biz" },
      { "X-Internal-Secret": "test-shared-secret" },
    );
    expect(data).toHaveProperty("provider_used");
    expect(data.provider_used).toBe("stitch");
    expect(data).toHaveProperty("success");
    expect(data).toHaveProperty("attempts");
  });
});
