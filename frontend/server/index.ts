import "dotenv/config";
import express from "express";
import cors from "cors";
import { handleDemo } from "./routes/demo";

// Import busboy for multipart form data handling
import busboy from "busboy";

export function createServer() {
  const app = express();

  // Get Flask backend URL from environment or default to localhost:5000
  const FLASK_BACKEND_URL = process.env.FLASK_BACKEND_URL || "http://localhost:5000";

  // Middleware
  app.use(cors());
  app.use(express.json());
  app.use(express.urlencoded({ extended: true }));

  // Example API routes
  app.get("/api/ping", (_req, res) => {
    const ping = process.env.PING_MESSAGE ?? "ping";
    res.json({ message: ping });
  });

  app.get("/api/demo", handleDemo);

  // Proxy API calls to Flask backend
  // NOTE: This is a convenience route used by the signup flow.
  // It maps to the real backend endpoint: POST /api/blockchain/token/generate
  app.post("/api/token/generate", async (req, res) => {
    try {
      const response = await fetch(`${FLASK_BACKEND_URL}/api/blockchain/token/generate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(req.headers.authorization && { Authorization: req.headers.authorization }),
        },
        body: JSON.stringify(req.body),
      });
      const data = await response.json();
      res.status(response.status).json(data);
    } catch (error) {
      console.error("Error proxying token generation:", error);
      res.status(500).json({ error: "Failed to generate token" });
    }
  });

  // Special handling for file uploads (multipart form data)
  // Maps to backend: POST /api/documents/upload
  app.post("/api/user/documents/upload", async (req, res) => {
    try {
      // Forward multipart form data directly to Flask backend
      const bb = busboy({ headers: req.headers });
      const formData = new FormData();
      
      let fileProcessed = false;

      bb.on("file", (fieldname: string, file, info) => {
        // Read file into buffer
        const chunks: Buffer[] = [];
        file.on("data", (chunk) => {
          chunks.push(Buffer.from(chunk));
        });
        file.on("end", () => {
          const buffer = Buffer.concat(chunks);
          const blob = new Blob([buffer], { type: info.mimeType });
          formData.append(fieldname, blob, info.filename);
          fileProcessed = true;
        });
      });

      bb.on("field", (fieldname: string, value) => {
        formData.append(fieldname, value);
      });

      bb.on("close", async () => {
        try {
          const response = await fetch(`${FLASK_BACKEND_URL}/api/documents/upload`, {
            method: "POST",
            headers: {
              ...(req.headers.authorization && { Authorization: req.headers.authorization }),
            },
            body: formData,
          });

          const data = await response.json();
          res.status(response.status).json(data);
        } catch (error) {
          console.error("Error proxying document upload:", error);
          res.status(500).json({ error: "Failed to upload document" });
        }
      });

      req.pipe(bb);
    } catch (error) {
      console.error("Error in document upload handler:", error);
      res.status(500).json({ error: "Failed to process upload" });
    }
  });

  // Proxy other API endpoints to Flask backend using middleware
  // The Flask backend is mounted under /api, so we forward /api/* -> {FLASK_BACKEND_URL}/api/*.
  app.use("/api", async (req, res) => {
    try {
      // Skip proxying for already handled routes
      if (
        req.path === "/ping" ||
        req.path === "/demo" ||
        req.path === "/token/generate" ||
        req.path === "/user/documents/upload"
      ) {
        return;
      }

      // Preserve query string by using originalUrl.
      // Example: /api/auth/login -> {FLASK_BACKEND_URL}/api/auth/login
      const url = `${FLASK_BACKEND_URL}${req.originalUrl}`;
      
      const requestInit: RequestInit = {
        method: req.method,
        headers: {
          ...(req.headers.authorization && { Authorization: req.headers.authorization }),
          // Only set JSON content-type for non-multipart requests.
          ...(!req.headers["content-type"]?.includes("multipart") && {
            "Content-Type": "application/json",
          }),
        },
      };

      // Add body for non-GET/HEAD requests
      if (req.method !== "GET" && req.method !== "HEAD") {
        requestInit.body = JSON.stringify(req.body);
      }

      const response = await fetch(url, requestInit);
      const data = await response.json().catch(() => ({}));
      
      res.status(response.status).json(data);
    } catch (error) {
      console.error("Error proxying API request:", error);
      res.status(500).json({ error: "API request failed" });
    }
  });

  return app;
}
