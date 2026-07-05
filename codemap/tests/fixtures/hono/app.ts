// ABOUTME: Test fixture — Hono routes with inline and referenced handlers
// ABOUTME: Exercises the hono-routes rule: lowercase methods, route grouping

import { Hono } from "hono";

const app = new Hono();

app.get("/health", (c) => c.json({ ok: true }));
app.post("/webhooks/stripe", stripeHandler);
app.route("/api/v1", apiV1);

export default app;
