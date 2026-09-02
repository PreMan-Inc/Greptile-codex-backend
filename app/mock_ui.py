from fastapi.responses import HTMLResponse

MOCK_TEST_UI_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>Mock API Workbench</title>
  <style>
    :root {
      --bg: #f4f6fa;
      --panel: #ffffff;
      --panel-soft: #f8fafc;
      --ink: #172033;
      --muted: #667085;
      --line: #dfe4ec;
      --line-strong: #c8d0dc;
      --brand: #635bff;
      --brand-dark: #4c45d6;
      --success: #087e5b;
      --danger: #c43245;
      --warning: #a15c00;
      --shadow: 0 18px 48px rgba(20, 29, 52, 0.09);
      --radius-lg: 20px;
      --radius-md: 14px;
      --radius-sm: 10px;
    }

    * { box-sizing: border-box; }

    html { scroll-behavior: smooth; }

    body {
      margin: 0;
      background:
        radial-gradient(circle at 12% 0%, rgba(99, 91, 255, 0.10), transparent 28rem),
        var(--bg);
      color: var(--ink);
      font-family:
        Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
        sans-serif;
      font-size: 15px;
      line-height: 1.5;
    }

    button, input, textarea { font: inherit; }

    button { cursor: pointer; }

    button:focus-visible,
    input:focus-visible,
    textarea:focus-visible,
    summary:focus-visible,
    a:focus-visible {
      outline: 3px solid rgba(99, 91, 255, 0.28);
      outline-offset: 2px;
    }

    .hero {
      position: relative;
      overflow: hidden;
      background: #11172a;
      color: #fff;
      padding: 54px 24px 82px;
    }

    .hero::before,
    .hero::after {
      position: absolute;
      width: 360px;
      height: 360px;
      border-radius: 999px;
      content: "";
      filter: blur(2px);
      opacity: 0.5;
      pointer-events: none;
    }

    .hero::before {
      top: -250px;
      right: -40px;
      background: radial-gradient(circle, #786fff, transparent 68%);
    }

    .hero::after {
      bottom: -330px;
      left: 20%;
      background: radial-gradient(circle, #21c7a8, transparent 66%);
    }

    .hero-inner,
    .page {
      position: relative;
      width: min(1480px, 100%);
      margin: 0 auto;
    }

    .eyebrow {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      margin: 0 0 14px;
      color: #b9c1ff;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.14em;
      text-transform: uppercase;
    }

    .eyebrow-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      background: #51ddb7;
      box-shadow: 0 0 0 5px rgba(81, 221, 183, 0.14);
    }

    h1 {
      max-width: 800px;
      margin: 0;
      font-size: clamp(2.2rem, 5vw, 4.4rem);
      line-height: 1.02;
      letter-spacing: -0.055em;
    }

    .hero-copy {
      max-width: 760px;
      margin: 20px 0 0;
      color: #c8cedc;
      font-size: clamp(1rem, 2vw, 1.16rem);
    }

    .hero-badges {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-top: 27px;
    }

    .hero-badge {
      display: inline-flex;
      align-items: center;
      min-height: 34px;
      padding: 7px 12px;
      border: 1px solid rgba(255, 255, 255, 0.14);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.06);
      color: #e7e9ef;
      font-size: 13px;
      font-weight: 700;
      text-decoration: none;
    }

    a.hero-badge:hover {
      border-color: rgba(185, 193, 255, 0.7);
      background: rgba(255, 255, 255, 0.11);
    }

    .page {
      z-index: 2;
      padding: 0 24px 72px;
    }

    .control-shell {
      margin-top: -42px;
      border: 1px solid rgba(223, 228, 236, 0.8);
      border-radius: var(--radius-lg);
      background: rgba(255, 255, 255, 0.97);
      box-shadow: var(--shadow);
      backdrop-filter: blur(16px);
    }

    .controls {
      display: grid;
      grid-template-columns: minmax(260px, 1fr) auto auto;
      gap: 14px;
      align-items: end;
      padding: 20px;
    }

    .field-label {
      display: block;
      margin: 0 0 7px;
      color: #344054;
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0.025em;
    }

    .base-input,
    .id-input,
    .body-editor {
      width: 100%;
      border: 1px solid var(--line-strong);
      border-radius: var(--radius-sm);
      background: #fff;
      color: var(--ink);
      transition: border-color 120ms ease, box-shadow 120ms ease;
    }

    .base-input,
    .id-input {
      height: 44px;
      padding: 0 12px;
    }

    .base-input:focus,
    .id-input:focus,
    .body-editor:focus {
      border-color: var(--brand);
      box-shadow: 0 0 0 4px rgba(99, 91, 255, 0.10);
      outline: none;
    }

    .button {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 8px;
      min-height: 44px;
      padding: 10px 16px;
      border: 1px solid transparent;
      border-radius: var(--radius-sm);
      font-weight: 800;
      white-space: nowrap;
      transition: transform 120ms ease, background 120ms ease, border-color 120ms ease;
    }

    .button:hover:not(:disabled) { transform: translateY(-1px); }

    .button:disabled { cursor: wait; opacity: 0.6; }

    .button-primary {
      background: var(--brand);
      color: #fff;
      box-shadow: 0 8px 18px rgba(99, 91, 255, 0.22);
    }

    .button-primary:hover:not(:disabled) { background: var(--brand-dark); }

    .button-danger {
      border-color: #efbdc5;
      background: #fff7f8;
      color: #a61b32;
    }

    .button-danger:hover:not(:disabled) {
      border-color: #df8796;
      background: #fff0f2;
    }

    .button-secondary {
      border-color: var(--line-strong);
      background: #fff;
      color: #344054;
    }

    .button-secondary:hover:not(:disabled) { background: #f5f7fb; }

    .state-note {
      display: grid;
      grid-template-columns: auto 1fr;
      gap: 12px;
      align-items: start;
      padding: 14px 20px;
      border-top: 1px solid var(--line);
      border-radius: 0 0 var(--radius-lg) var(--radius-lg);
      background: #fffaeb;
      color: #765300;
      font-size: 13px;
    }

    .state-note strong { color: #5d4200; }

    .note-icon {
      display: grid;
      width: 24px;
      height: 24px;
      place-items: center;
      border-radius: 50%;
      background: #ffe7a3;
      font-weight: 900;
    }

    .resource-nav {
      display: flex;
      gap: 8px;
      margin: 22px 0;
      padding: 4px 0;
      overflow-x: auto;
      scrollbar-width: thin;
    }

    .resource-nav a {
      flex: 0 0 auto;
      padding: 9px 13px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: rgba(255, 255, 255, 0.8);
      color: #475467;
      font-size: 13px;
      font-weight: 800;
      text-decoration: none;
    }

    .resource-nav a:hover {
      border-color: #b8b3ff;
      color: var(--brand-dark);
    }

    .resource-nav code {
      margin-left: 5px;
      color: #7b8495;
      font-size: 11px;
    }

    .runner {
      margin-bottom: 24px;
      border: 1px solid var(--line);
      border-radius: var(--radius-lg);
      background: var(--panel);
      box-shadow: 0 8px 24px rgba(20, 29, 52, 0.05);
    }

    .runner-header {
      display: flex;
      gap: 20px;
      align-items: center;
      justify-content: space-between;
      padding: 19px 20px;
    }

    .runner h2,
    .resource-heading h2 {
      margin: 0;
      font-size: 20px;
      letter-spacing: -0.025em;
    }

    .runner-copy,
    .resource-heading p {
      margin: 4px 0 0;
      color: var(--muted);
      font-size: 13px;
    }

    .runner-status {
      display: inline-flex;
      align-items: center;
      gap: 8px;
      padding: 6px 10px;
      border-radius: 999px;
      background: #f1f3f8;
      color: #475467;
      font-size: 12px;
      font-weight: 800;
      white-space: nowrap;
    }

    .runner-status[data-tone="success"] {
      background: #e9f9f3;
      color: var(--success);
    }

    .runner-status[data-tone="danger"] {
      background: #fff0f2;
      color: var(--danger);
    }

    .progress-track {
      height: 4px;
      overflow: hidden;
      background: #edf0f5;
    }

    .progress-bar {
      width: 0;
      height: 100%;
      background: linear-gradient(90deg, var(--brand), #22bda1);
      transition: width 180ms ease;
    }

    .run-log {
      display: grid;
      gap: 8px;
      max-height: 380px;
      padding: 14px 20px 20px;
      overflow: auto;
    }

    .empty-log {
      padding: 18px;
      border: 1px dashed var(--line-strong);
      border-radius: var(--radius-sm);
      background: var(--panel-soft);
      color: var(--muted);
      text-align: center;
    }

    .log-entry {
      border: 1px solid var(--line);
      border-radius: var(--radius-sm);
      background: var(--panel-soft);
    }

    .log-entry summary {
      display: grid;
      grid-template-columns: 30px 64px minmax(160px, 1fr) auto auto;
      gap: 9px;
      align-items: center;
      padding: 10px 12px;
      cursor: pointer;
      list-style: none;
    }

    .log-entry summary::-webkit-details-marker { display: none; }

    .log-step,
    .operation-number {
      display: grid;
      width: 28px;
      height: 28px;
      place-items: center;
      border-radius: 8px;
      background: #eceffd;
      color: #4943bd;
      font-size: 11px;
      font-weight: 900;
    }

    .log-path {
      overflow: hidden;
      color: #344054;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .log-time { color: var(--muted); font-size: 12px; }

    .log-output,
    .response-output,
    .reset-output {
      margin: 0;
      overflow: auto;
      color: #d8deed;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
      line-height: 1.55;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
    }

    .log-output {
      max-height: 230px;
      padding: 13px;
      border-radius: 0 0 var(--radius-sm) var(--radius-sm);
      background: #171d2c;
    }

    .reset-result {
      display: none;
      grid-template-columns: auto 1fr;
      gap: 10px;
      margin: 0 20px 18px;
      padding: 12px;
      border: 1px solid var(--line);
      border-radius: var(--radius-sm);
      background: var(--panel-soft);
    }

    .reset-result.is-visible { display: grid; }

    .reset-output { color: #344054; }

    .resource-section {
      margin-top: 24px;
      scroll-margin-top: 18px;
    }

    .resource-heading {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 18px;
      margin-bottom: 12px;
    }

    .resource-title {
      display: flex;
      gap: 12px;
      align-items: center;
    }

    .resource-mark {
      display: grid;
      width: 42px;
      height: 42px;
      place-items: center;
      border-radius: 12px;
      color: #fff;
      font-size: 13px;
      font-weight: 900;
      letter-spacing: 0.03em;
      box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.22);
    }

    .operation-count {
      padding: 6px 10px;
      border: 1px solid var(--line);
      border-radius: 999px;
      background: #fff;
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      white-space: nowrap;
    }

    .operation-grid {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 14px;
    }

    .operation-card {
      display: flex;
      min-width: 0;
      min-height: 100%;
      flex-direction: column;
      overflow: hidden;
      border: 1px solid var(--line);
      border-radius: var(--radius-md);
      background: var(--panel);
      box-shadow: 0 5px 16px rgba(20, 29, 52, 0.04);
      transition: border-color 140ms ease, box-shadow 140ms ease, transform 140ms ease;
    }

    .operation-card:hover {
      border-color: #c9c6f5;
      box-shadow: 0 10px 24px rgba(20, 29, 52, 0.08);
      transform: translateY(-1px);
    }

    .card-main {
      display: flex;
      flex: 1;
      flex-direction: column;
      padding: 16px;
    }

    .card-topline {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
    }

    .method {
      display: inline-flex;
      min-width: 58px;
      justify-content: center;
      padding: 5px 8px;
      border-radius: 7px;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 11px;
      font-weight: 900;
      letter-spacing: 0.045em;
    }

    .method-get { background: #e8f2ff; color: #155ab6; }
    .method-post { background: #e5f8f1; color: #087759; }
    .method-put { background: #fff3d9; color: #8a5700; }
    .method-patch { background: #f1ebff; color: #7040b2; }
    .method-delete { background: #ffe9ed; color: #b4233b; }

    .card-title {
      margin: 15px 0 5px;
      font-size: 17px;
      letter-spacing: -0.018em;
    }

    .card-description {
      min-height: 40px;
      margin: 0;
      color: var(--muted);
      font-size: 13px;
    }

    .path {
      margin: 13px 0;
      padding: 9px 10px;
      overflow: auto;
      border: 1px solid #e7eaf0;
      border-radius: 8px;
      background: #f7f8fb;
      color: #3e4759;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 11px;
      white-space: nowrap;
    }

    .body-group { margin-top: 12px; }

    .body-label-row {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 7px;
    }

    .body-label-row .field-label { margin: 0; }

    .text-button {
      padding: 0;
      border: 0;
      background: transparent;
      color: var(--brand-dark);
      font-size: 11px;
      font-weight: 800;
    }

    .body-editor {
      min-height: 150px;
      padding: 11px;
      resize: vertical;
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 12px;
      line-height: 1.5;
      tab-size: 2;
    }

    .card-action {
      display: flex;
      gap: 10px;
      align-items: center;
      margin-top: auto;
      padding-top: 14px;
    }

    .run-button { width: 100%; }

    .response-panel {
      border-top: 1px solid var(--line);
      background: #151b29;
    }

    .response-meta {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      min-height: 38px;
      padding: 8px 12px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
      color: #9ea7b9;
      font-size: 11px;
    }

    .response-status {
      font-weight: 900;
      letter-spacing: 0.025em;
    }

    .response-status[data-tone="success"] { color: #62dfb7; }
    .response-status[data-tone="danger"] { color: #ff899b; }
    .response-status[data-tone="warning"] { color: #ffd172; }

    .response-output {
      min-height: 92px;
      max-height: 230px;
      padding: 12px;
    }

    .footer {
      margin-top: 42px;
      padding-top: 20px;
      border-top: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
      text-align: center;
    }

    .toast-region {
      position: fixed;
      z-index: 20;
      right: 20px;
      bottom: 20px;
      display: grid;
      gap: 8px;
      width: min(380px, calc(100vw - 40px));
      pointer-events: none;
    }

    .toast {
      padding: 12px 14px;
      border: 1px solid #cad1dd;
      border-radius: 11px;
      background: #fff;
      color: #344054;
      box-shadow: 0 14px 36px rgba(20, 29, 52, 0.18);
      font-size: 13px;
      font-weight: 700;
      animation: toast-in 180ms ease-out;
    }

    .toast[data-tone="success"] { border-color: #93ddc6; }
    .toast[data-tone="danger"] { border-color: #efa7b2; }

    @keyframes toast-in {
      from { opacity: 0; transform: translateY(8px); }
      to { opacity: 1; transform: translateY(0); }
    }

    @media (max-width: 1080px) {
      .operation-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
      .controls { grid-template-columns: 1fr 1fr; }
      .base-field { grid-column: 1 / -1; }
    }

    @media (max-width: 680px) {
      .hero { padding: 42px 18px 72px; }
      .page { padding: 0 14px 54px; }
      .controls { grid-template-columns: 1fr; padding: 16px; }
      .base-field { grid-column: auto; }
      .button { width: 100%; }
      .state-note { padding: 13px 16px; }
      .runner-header { align-items: flex-start; flex-direction: column; }
      .runner-status { white-space: normal; }
      .run-log { padding: 12px; }
      .log-entry summary {
        grid-template-columns: 28px 58px 1fr;
      }
      .log-time,
      .log-entry summary > .response-status { grid-column: 3; }
      .operation-grid { grid-template-columns: 1fr; }
      .resource-heading { align-items: flex-start; }
      .resource-heading p { max-width: 230px; }
      .toast-region { right: 12px; bottom: 12px; width: calc(100vw - 24px); }
    }

    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after {
        scroll-behavior: auto !important;
        transition-duration: 0.01ms !important;
        animation-duration: 0.01ms !important;
      }
    }
  </style>
</head>
<body>
  <header class="hero">
    <div class="hero-inner">
      <p class="eyebrow"><span class="eyebrow-dot"></span>Interactive REST test console</p>
      <h1>Mock API Workbench</h1>
      <p class="hero-copy">
        Explore, edit, and run every CRUD operation from one place. Test individual requests
        or launch a disposable end-to-end lifecycle across the complete mock catalog.
      </p>
      <div class="hero-badges" aria-label="API summary">
        <span class="hero-badge">30 CRUD operations</span>
        <span class="hero-badge">5 resources</span>
        <span class="hero-badge">No client dependencies</span>
        <a class="hero-badge" href="/mock-openapi.json">View mock OpenAPI JSON ↗</a>
        <a class="hero-badge" href="/mock-schemas.json">View test schemas + fixtures ↗</a>
      </div>
    </div>
  </header>

  <main class="page">
    <section class="control-shell" aria-label="Workbench controls">
      <div class="controls">
        <label class="base-field">
          <span class="field-label">API base URL</span>
          <input
            class="base-input"
            id="base-url"
            inputmode="url"
            type="url"
            autocomplete="url"
            aria-describedby="base-help"
          >
        </label>
        <button class="button button-primary" id="run-all" type="button">
          <span aria-hidden="true">▶</span> Run all 30 operations
        </button>
        <button class="button button-danger" id="reset-data" type="button">
          <span aria-hidden="true">↺</span> Reset mock data
        </button>
      </div>
      <div class="state-note" id="base-help">
        <span class="note-icon" aria-hidden="true">!</span>
        <span>
          <strong>Hosted state is shared and resettable.</strong>
          Use disposable records for testing. Reset restores the JSON-backed seed dataset;
          hosted changes persist across service restarts but can be changed by any tester.
        </span>
      </div>
      <div class="reset-result" id="reset-result" aria-live="polite">
        <span class="response-status" id="reset-status">Not run</span>
        <pre class="reset-output" id="reset-output"></pre>
      </div>
    </section>

    <nav class="resource-nav" aria-label="Jump to resource">
      <a href="#customers">Customers <code>/api/v1/mock/customers</code></a>
      <a href="#products">Products <code>/api/v1/mock/products</code></a>
      <a href="#orders">Orders <code>/api/v1/mock/orders</code></a>
      <a href="#tickets">Tickets <code>/api/v1/mock/tickets</code></a>
      <a href="#reviews">Reviews <code>/api/v1/mock/reviews</code></a>
    </nav>

    <section class="runner" aria-labelledby="runner-title">
      <div class="runner-header">
        <div>
          <h2 id="runner-title">Automated 30-operation lifecycle</h2>
          <p class="runner-copy">
            Creates disposable records, lists and reads them, replaces and patches them,
            then deletes them in dependency-safe order.
          </p>
        </div>
        <span class="runner-status" id="runner-status" aria-live="polite">Ready to run</span>
      </div>
      <div class="progress-track" aria-hidden="true">
        <div class="progress-bar" id="progress-bar"></div>
      </div>
      <div class="run-log" id="run-log" aria-live="polite">
        <div class="empty-log">Run the lifecycle to see status, timing, and output for all 30 calls.</div>
      </div>
    </section>

    <div id="resource-sections"></div>

    <footer class="footer">
      Mock API Workbench · Requests are sent directly from your browser to the selected base URL.
    </footer>
  </main>

  <div class="toast-region" id="toast-region" aria-live="polite"></div>
  <noscript>This test UI requires JavaScript to send API requests.</noscript>

  <script>
    "use strict";

    const API_PREFIX = "/api/v1/mock";
    const REQUEST_TIMEOUT_MS = 20000;

    const resources = [
      {
        key: "customers",
        singular: "customer",
        label: "Customers",
        idParam: "customer_id",
        seedId: "cus_seed_001",
        // Customers are region-partitioned and the listing has no cross-region
        // form, so the card has to name one or the request is a 422.
        listQuery: "region=emea",
        mark: "CU",
        color: "#5365d8",
        description: "Customer profiles, contact details, companies, and account status.",
        examples: {
          create: {
            name: "Avery Stone",
            email: "avery.stone@example.com",
            phone: "+1-555-0100",
            company: "Northstar Labs",
            status: "active"
          },
          put: {
            name: "Avery Stone",
            email: "avery.stone@example.com",
            phone: "+1-555-0101",
            company: "Northstar Labs",
            status: "active"
          },
          patch: { company: "Northstar Labs West", status: "inactive" }
        }
      },
      {
        key: "products",
        singular: "product",
        label: "Products",
        idParam: "product_id",
        seedId: "prd_seed_001",
        mark: "PR",
        color: "#087e6b",
        description: "Product catalog records, inventory levels, pricing, and availability.",
        examples: {
          create: {
            sku: "KB-1000",
            name: "Wireless Keyboard",
            description: "Compact keyboard",
            category: "Accessories",
            price_cents: 7999,
            stock_quantity: 25,
            active: true
          },
          put: {
            sku: "KB-1000",
            name: "Wireless Keyboard Pro",
            description: "Compact low-profile keyboard",
            category: "Accessories",
            price_cents: 8999,
            stock_quantity: 18,
            active: true
          },
          patch: { price_cents: 7499, stock_quantity: 30 }
        }
      },
      {
        key: "orders",
        singular: "order",
        label: "Orders",
        idParam: "order_id",
        seedId: "ord_seed_001",
        mark: "OR",
        color: "#b55c08",
        description: "Purchases connecting customers and products with computed totals.",
        examples: {
          create: {
            customer_id: "cus_seed_001",
            items: [{ product_id: "prd_seed_001", quantity: 2 }],
            status: "pending",
            shipping_address: "123 Market St, San Francisco, CA",
            notes: "Leave at reception"
          },
          put: {
            customer_id: "cus_seed_001",
            items: [{ product_id: "prd_seed_001", quantity: 1 }],
            status: "paid",
            shipping_address: "123 Market St, San Francisco, CA",
            notes: "Updated delivery instructions"
          },
          patch: { status: "shipped", notes: "Tracking sent to customer" }
        }
      },
      {
        key: "tickets",
        singular: "ticket",
        label: "Tickets",
        idParam: "ticket_id",
        seedId: "tkt_seed_001",
        mark: "TI",
        color: "#a03c79",
        description: "Support requests with priority, ownership, and resolution status.",
        examples: {
          create: {
            customer_id: "cus_seed_001",
            subject: "Cannot update billing address",
            description: "Save returns an error",
            status: "open",
            priority: "high",
            assignee: "Support Team"
          },
          put: {
            customer_id: "cus_seed_001",
            subject: "Billing address update fails",
            description: "The save action returns an error",
            status: "in_progress",
            priority: "high",
            assignee: "Support Team"
          },
          patch: { status: "resolved", priority: "medium" }
        }
      },
      {
        key: "reviews",
        singular: "review",
        label: "Reviews",
        idParam: "review_id",
        seedId: "rev_seed_001",
        mark: "RE",
        color: "#6f4cc3",
        description: "Customer product ratings and written feedback.",
        examples: {
          create: {
            customer_id: "cus_seed_001",
            product_id: "prd_seed_001",
            rating: 5,
            title: "Excellent keyboard",
            body: "Comfortable and responsive."
          },
          put: {
            customer_id: "cus_seed_001",
            product_id: "prd_seed_001",
            rating: 4,
            title: "A strong keyboard",
            body: "Responsive keys and a compact layout."
          },
          patch: { rating: 5, body: "Even better after a week of daily use." }
        }
      }
    ];

    const operations = [
      {
        key: "list",
        method: "GET",
        title: resource => `List ${resource.label.toLowerCase()}`,
        description: resource => `Return the complete ${resource.singular} collection.`,
        hasId: false,
        bodyKey: null
      },
      {
        key: "create",
        method: "POST",
        title: resource => `Create ${resource.singular}`,
        description: resource => `Add a new ${resource.singular} and capture its generated ID.`,
        hasId: false,
        bodyKey: "create"
      },
      {
        key: "get",
        method: "GET",
        title: resource => `Get ${resource.singular}`,
        description: resource => `Read one ${resource.singular} by its stable identifier.`,
        hasId: true,
        bodyKey: null
      },
      {
        key: "put",
        method: "PUT",
        title: resource => `Replace ${resource.singular}`,
        description: resource => `Completely replace every writable ${resource.singular} field.`,
        hasId: true,
        bodyKey: "put"
      },
      {
        key: "patch",
        method: "PATCH",
        title: resource => `Update ${resource.singular}`,
        description: resource => `Partially update selected ${resource.singular} fields.`,
        hasId: true,
        bodyKey: "patch"
      },
      {
        key: "delete",
        method: "DELETE",
        title: resource => `Delete ${resource.singular}`,
        description: resource => `Permanently remove one disposable ${resource.singular}.`,
        hasId: true,
        bodyKey: null
      }
    ];

    const cards = new Map();
    const resourceInputs = new Map();
    const baseInput = document.getElementById("base-url");
    const runAllButton = document.getElementById("run-all");
    const resetButton = document.getElementById("reset-data");
    const runnerStatus = document.getElementById("runner-status");
    const progressBar = document.getElementById("progress-bar");
    const runLog = document.getElementById("run-log");
    const resetResult = document.getElementById("reset-result");
    const resetStatus = document.getElementById("reset-status");
    const resetOutput = document.getElementById("reset-output");
    const toastRegion = document.getElementById("toast-region");
    let lifecycleRunning = false;

    function defaultBaseUrl() {
      if (window.location.protocol === "http:" || window.location.protocol === "https:") {
        return window.location.origin;
      }
      return "http://127.0.0.1:8000";
    }

    function loadBaseUrl() {
      try {
        return window.localStorage.getItem("mock-api-base-url") || defaultBaseUrl();
      } catch (error) {
        return defaultBaseUrl();
      }
    }

    function saveBaseUrl() {
      try {
        window.localStorage.setItem("mock-api-base-url", baseInput.value.trim());
      } catch (error) {
        // Storage can be blocked by browser privacy settings; requests still work.
      }
    }

    function normalizedBaseUrl() {
      const raw = baseInput.value.trim().replace(/\/+$/, "");
      let parsed;
      try {
        parsed = new URL(raw);
      } catch (error) {
        throw new Error("Enter a valid API base URL, such as https://api.example.com");
      }
      if (!(["http:", "https:"].includes(parsed.protocol))) {
        throw new Error("The API base URL must use HTTP or HTTPS");
      }
      return raw;
    }

    function cardKey(resourceKey, operationKey) {
      return `${resourceKey}:${operationKey}`;
    }

    function prettyJson(value) {
      return JSON.stringify(value, null, 2);
    }

    function formatOutput(result) {
      const body = result.body === null || result.body === undefined
        ? "(empty response body)"
        : typeof result.body === "string"
          ? result.body
          : prettyJson(result.body);
      return result.location ? `Location: ${result.location}\n\n${body}` : body;
    }

    function toneForResult(result) {
      if (result.ok) return "success";
      if (result.status === 0 || result.status === "INPUT") return "danger";
      return result.status >= 500 ? "danger" : "warning";
    }

    function pathFor(resource, operation, id) {
      const collection = `${API_PREFIX}/${resource.key}`;
      if (!operation.hasId) {
        if (operation.key === "list" && resource.listQuery) {
          return `${collection}?${resource.listQuery}`;
        }
        return collection;
      }
      const value = id || `{${resource.idParam}}`;
      return `${collection}/${encodeURIComponent(value)}`;
    }

    function setResourceId(resourceKey, value, source) {
      const inputs = resourceInputs.get(resourceKey) || [];
      inputs.forEach(input => {
        if (input !== source) input.value = value;
      });
      const resource = resources.find(item => item.key === resourceKey);
      operations.filter(operation => operation.hasId).forEach(operation => {
        const card = cards.get(cardKey(resourceKey, operation.key));
        if (card) card.path.textContent = pathFor(resource, operation, value);
      });
    }

    function createMethodBadge(method) {
      const badge = document.createElement("span");
      badge.className = `method method-${method.toLowerCase()}`;
      badge.textContent = method;
      return badge;
    }

    function renderResourceSections() {
      const container = document.getElementById("resource-sections");
      let operationNumber = 0;

      resources.forEach(resource => {
        resourceInputs.set(resource.key, []);
        const section = document.createElement("section");
        section.className = "resource-section";
        section.id = resource.key;

        const heading = document.createElement("div");
        heading.className = "resource-heading";
        const title = document.createElement("div");
        title.className = "resource-title";
        const mark = document.createElement("span");
        mark.className = "resource-mark";
        mark.style.background = resource.color;
        mark.textContent = resource.mark;
        const text = document.createElement("div");
        const h2 = document.createElement("h2");
        h2.textContent = resource.label;
        const description = document.createElement("p");
        description.textContent = resource.description;
        text.append(h2, description);
        title.append(mark, text);
        const count = document.createElement("span");
        count.className = "operation-count";
        count.textContent = "6 CRUD operations";
        heading.append(title, count);

        const grid = document.createElement("div");
        grid.className = "operation-grid";

        operations.forEach(operation => {
          operationNumber += 1;
          const card = renderOperationCard(resource, operation, operationNumber);
          grid.append(card.node);
          cards.set(cardKey(resource.key, operation.key), card);
        });

        section.append(heading, grid);
        container.append(section);
      });
    }

    function renderOperationCard(resource, operation, operationNumber) {
      const article = document.createElement("article");
      article.className = "operation-card";
      article.dataset.operation = cardKey(resource.key, operation.key);

      const main = document.createElement("div");
      main.className = "card-main";
      const topline = document.createElement("div");
      topline.className = "card-topline";
      topline.append(createMethodBadge(operation.method));
      const number = document.createElement("span");
      number.className = "operation-number";
      number.textContent = String(operationNumber).padStart(2, "0");
      topline.append(number);

      const title = document.createElement("h3");
      title.className = "card-title";
      title.textContent = operation.title(resource);
      const description = document.createElement("p");
      description.className = "card-description";
      description.textContent = operation.description(resource);
      const path = document.createElement("div");
      path.className = "path";
      path.textContent = pathFor(resource, operation, resource.seedId);
      main.append(topline, title, description, path);

      let idInput = null;
      if (operation.hasId) {
        const label = document.createElement("label");
        const labelText = document.createElement("span");
        labelText.className = "field-label";
        labelText.textContent = resource.idParam;
        idInput = document.createElement("input");
        idInput.className = "id-input";
        idInput.type = "text";
        idInput.value = resource.seedId;
        idInput.autocomplete = "off";
        idInput.setAttribute("aria-label", `${resource.label} identifier`);
        idInput.addEventListener("input", () => {
          setResourceId(resource.key, idInput.value.trim(), idInput);
        });
        resourceInputs.get(resource.key).push(idInput);
        label.append(labelText, idInput);
        main.append(label);
      }

      let editor = null;
      if (operation.bodyKey) {
        const group = document.createElement("div");
        group.className = "body-group";
        const labelRow = document.createElement("div");
        labelRow.className = "body-label-row";
        const label = document.createElement("label");
        label.className = "field-label";
        label.textContent = "JSON request body";
        const resetExample = document.createElement("button");
        resetExample.className = "text-button";
        resetExample.type = "button";
        resetExample.textContent = "Restore example";
        editor = document.createElement("textarea");
        editor.className = "body-editor";
        editor.spellcheck = false;
        editor.value = prettyJson(resource.examples[operation.bodyKey]);
        editor.setAttribute("aria-label", `${operation.title(resource)} JSON request body`);
        label.htmlFor = `body-${resource.key}-${operation.key}`;
        editor.id = label.htmlFor;
        resetExample.addEventListener("click", () => {
          editor.value = prettyJson(resource.examples[operation.bodyKey]);
        });
        labelRow.append(label, resetExample);
        group.append(labelRow, editor);
        main.append(group);
      }

      const action = document.createElement("div");
      action.className = "card-action";
      const run = document.createElement("button");
      run.className = "button button-secondary run-button";
      run.type = "button";
      run.textContent = `Send ${operation.method}`;
      action.append(run);
      main.append(action);

      const responsePanel = document.createElement("div");
      responsePanel.className = "response-panel";
      const responseMeta = document.createElement("div");
      responseMeta.className = "response-meta";
      const status = document.createElement("span");
      status.className = "response-status";
      status.textContent = "Not run";
      const timing = document.createElement("span");
      timing.textContent = "—";
      responseMeta.append(status, timing);
      const output = document.createElement("pre");
      output.className = "response-output";
      output.textContent = "Response output will appear here.";
      responsePanel.append(responseMeta, output);
      article.append(main, responsePanel);

      const card = { node: article, idInput, editor, run, path, status, timing, output };
      run.addEventListener("click", () => executeOperation(resource, operation));
      return card;
    }

    async function requestApi(method, path, body) {
      const started = performance.now();
      let timeout;
      try {
        const controller = new AbortController();
        timeout = window.setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
        const headers = { Accept: "application/json" };
        const options = { method, headers, signal: controller.signal };
        if (body !== undefined && body !== null) {
          headers["Content-Type"] = "application/json";
          options.body = JSON.stringify(body);
        }
        const response = await fetch(`${normalizedBaseUrl()}${path}`, options);
        const raw = await response.text();
        let parsed = null;
        if (raw) {
          try {
            parsed = JSON.parse(raw);
          } catch (error) {
            parsed = raw;
          }
        }
        return {
          ok: response.ok,
          status: response.status,
          statusText: response.statusText,
          elapsed: performance.now() - started,
          body: parsed,
          location: response.headers.get("Location")
        };
      } catch (error) {
        const message = error.name === "AbortError"
          ? `Request timed out after ${REQUEST_TIMEOUT_MS / 1000} seconds`
          : error.message;
        return {
          ok: false,
          status: 0,
          statusText: "Network error",
          elapsed: performance.now() - started,
          body: { error: message },
          location: null
        };
      } finally {
        window.clearTimeout(timeout);
      }
    }

    function renderCardResult(card, result) {
      const tone = toneForResult(result);
      const label = result.status === 0
        ? result.statusText
        : result.status === "INPUT"
          ? "Invalid JSON"
          : `${result.status} ${result.statusText || ""}`.trim();
      card.status.textContent = label;
      card.status.dataset.tone = tone;
      card.timing.textContent = Number.isFinite(result.elapsed)
        ? `${Math.round(result.elapsed)} ms`
        : "Client-side";
      card.output.textContent = formatOutput(result);
    }

    function extractId(body) {
      if (!body || typeof body !== "object") return null;
      if (typeof body.id === "string") return body.id;
      if (body.data && typeof body.data.id === "string") return body.data.id;
      return null;
    }

    async function executeOperation(resource, operation, overrides = {}) {
      const card = cards.get(cardKey(resource.key, operation.key));
      let id = overrides.id;
      let body = overrides.body;

      if (operation.hasId) {
        id = id || (card.idInput ? card.idInput.value.trim() : "");
        if (!id) {
          const result = {
            ok: false,
            status: "INPUT",
            statusText: "Missing ID",
            elapsed: NaN,
            body: { error: `Enter a ${resource.idParam} before sending this request.` }
          };
          renderCardResult(card, result);
          return result;
        }
        if (overrides.id && card.idInput) {
          card.idInput.value = overrides.id;
          setResourceId(resource.key, overrides.id, card.idInput);
        }
      }

      if (operation.bodyKey && body === undefined) {
        try {
          body = JSON.parse(card.editor.value);
        } catch (error) {
          const result = {
            ok: false,
            status: "INPUT",
            statusText: "Invalid JSON",
            elapsed: NaN,
            body: { error: error.message }
          };
          renderCardResult(card, result);
          return result;
        }
      } else if (operation.bodyKey && body !== undefined) {
        card.editor.value = prettyJson(body);
      }

      card.run.disabled = true;
      card.run.textContent = "Sending…";
      card.status.textContent = "In flight";
      card.status.dataset.tone = "";
      card.timing.textContent = "—";

      const path = pathFor(resource, operation, id);
      card.path.textContent = path;
      const result = await requestApi(operation.method, path, body);
      renderCardResult(card, result);
      card.run.disabled = lifecycleRunning;
      card.run.textContent = `Send ${operation.method}`;

      if (operation.key === "create" && result.ok) {
        const createdId = extractId(result.body);
        if (createdId) setResourceId(resource.key, createdId, null);
      }
      return result;
    }

    function operationByKey(key) {
      return operations.find(operation => operation.key === key);
    }

    function lifecyclePayloads(resourceKey, nonce, refs) {
      const customerId = refs.customers || "cus_seed_001";
      const productId = refs.products || "prd_seed_001";
      const payloads = {
        customers: {
          create: {
            name: `Lifecycle Customer ${nonce}`,
            email: `lifecycle.${nonce}@example.com`,
            phone: "+1-555-0199",
            company: "Lifecycle Labs",
            status: "active"
          },
          put: {
            name: `Updated Customer ${nonce}`,
            email: `lifecycle.${nonce}@example.com`,
            phone: "+1-555-0188",
            company: "Lifecycle Labs West",
            status: "active"
          },
          patch: { company: "Lifecycle Labs Complete", status: "inactive" }
        },
        products: {
          create: {
            sku: `LIFE-${nonce}`,
            name: "Lifecycle Keyboard",
            description: "Disposable product created by the test UI",
            category: "Test Fixtures",
            price_cents: 8199,
            stock_quantity: 12,
            active: true
          },
          put: {
            sku: `LIFE-${nonce}`,
            name: "Lifecycle Keyboard Pro",
            description: "Completely replaced by the test UI",
            category: "Test Fixtures",
            price_cents: 9099,
            stock_quantity: 17,
            active: true
          },
          patch: { price_cents: 8799, stock_quantity: 21 }
        },
        orders: {
          create: {
            customer_id: customerId,
            items: [{ product_id: productId, quantity: 2 }],
            status: "pending",
            shipping_address: "500 Test Avenue, San Francisco, CA",
            notes: "Disposable lifecycle order"
          },
          put: {
            customer_id: customerId,
            items: [{ product_id: productId, quantity: 1 }],
            status: "paid",
            shipping_address: "501 Test Avenue, San Francisco, CA",
            notes: "Replaced by lifecycle runner"
          },
          patch: { status: "shipped", notes: "Lifecycle shipment complete" }
        },
        tickets: {
          create: {
            customer_id: customerId,
            subject: `Lifecycle ticket ${nonce}`,
            description: "Disposable ticket created by the test UI",
            status: "open",
            priority: "high",
            assignee: "Support Team"
          },
          put: {
            customer_id: customerId,
            subject: `Updated lifecycle ticket ${nonce}`,
            description: "Completely replaced by the lifecycle runner",
            status: "in_progress",
            priority: "medium",
            assignee: "API Support"
          },
          patch: { status: "resolved", assignee: "Lifecycle Bot" }
        },
        reviews: {
          create: {
            customer_id: customerId,
            product_id: productId,
            rating: 5,
            title: "Lifecycle test review",
            body: "Created by the automated test UI."
          },
          put: {
            customer_id: customerId,
            product_id: productId,
            rating: 4,
            title: "Updated lifecycle review",
            body: "Completely replaced by the automated test UI."
          },
          patch: { rating: 5, body: "Lifecycle verification complete." }
        }
      };
      return payloads[resourceKey];
    }

    function setRunnerStatus(message, tone = "") {
      runnerStatus.textContent = message;
      runnerStatus.dataset.tone = tone;
    }

    function setProgress(step) {
      progressBar.style.width = `${Math.min(100, (step / 30) * 100)}%`;
    }

    function addLogEntry(step, resource, operation, id, result) {
      const details = document.createElement("details");
      details.className = "log-entry";
      const summary = document.createElement("summary");
      const number = document.createElement("span");
      number.className = "log-step";
      number.textContent = String(step).padStart(2, "0");
      const method = createMethodBadge(operation.method);
      const path = document.createElement("span");
      path.className = "log-path";
      path.textContent = pathFor(resource, operation, id);
      const status = document.createElement("span");
      status.className = "response-status";
      status.dataset.tone = toneForResult(result);
      status.textContent = result.status === 0 ? "Network error" : String(result.status);
      const timing = document.createElement("span");
      timing.className = "log-time";
      timing.textContent = Number.isFinite(result.elapsed)
        ? `${Math.round(result.elapsed)} ms`
        : "Client-side";
      summary.append(number, method, path, status, timing);
      const output = document.createElement("pre");
      output.className = "log-output";
      output.textContent = formatOutput(result);
      details.append(summary, output);
      runLog.append(details);
    }

    function disableCardButtons(disabled) {
      cards.forEach(card => {
        card.run.disabled = disabled;
      });
    }

    function restoreSeedExamples() {
      resources.forEach(resource => {
        setResourceId(resource.key, resource.seedId, null);
        operations.forEach(operation => {
          const card = cards.get(cardKey(resource.key, operation.key));
          if (!card) return;
          if (operation.bodyKey && card.editor) {
            card.editor.value = prettyJson(resource.examples[operation.bodyKey]);
          }
          card.status.textContent = "Not run";
          card.status.dataset.tone = "";
          card.timing.textContent = "—";
          card.output.textContent = "Response output will appear here.";
        });
      });
    }

    async function runLifecycle() {
      if (lifecycleRunning) return;
      lifecycleRunning = true;
      runAllButton.disabled = true;
      resetButton.disabled = true;
      disableCardButtons(true);
      runLog.replaceChildren();
      setProgress(0);
      setRunnerStatus("Starting lifecycle…");

      const nonce = `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
      const refs = {};
      let step = 0;

      async function runStep(resource, operationKey, options = {}) {
        step += 1;
        setRunnerStatus(`Running ${step} of 30 · ${resource.label}`);
        const operation = operationByKey(operationKey);
        const result = await executeOperation(resource, operation, options);
        addLogEntry(step, resource, operation, options.id, result);
        setProgress(step);
        if (!result.ok) {
          const error = new Error(
            `${operation.method} ${pathFor(resource, operation, options.id)} returned ${result.status}`
          );
          error.result = result;
          throw error;
        }
        return result;
      }

      try {
        for (const resource of resources) {
          const payload = lifecyclePayloads(resource.key, nonce, refs).create;
          const result = await runStep(resource, "create", { body: payload });
          const id = extractId(result.body);
          if (!id) throw new Error(`Create ${resource.singular} response did not include an id`);
          refs[resource.key] = id;
          setResourceId(resource.key, id, null);
        }

        for (const resource of resources) {
          await runStep(resource, "list");
        }
        for (const resource of resources) {
          await runStep(resource, "get", { id: refs[resource.key] });
        }
        for (const resource of resources) {
          const payload = lifecyclePayloads(resource.key, nonce, refs).put;
          await runStep(resource, "put", { id: refs[resource.key], body: payload });
        }
        for (const resource of resources) {
          const payload = lifecyclePayloads(resource.key, nonce, refs).patch;
          await runStep(resource, "patch", { id: refs[resource.key], body: payload });
        }
        for (const resource of [...resources].reverse()) {
          await runStep(resource, "delete", { id: refs[resource.key] });
        }

        restoreSeedExamples();
        setRunnerStatus(`All 30 operations passed · run ${nonce}`, "success");
        showToast(
          "All 30 CRUD operations passed. Request cards were restored to valid seed examples.",
          "success"
        );
      } catch (error) {
        setRunnerStatus(`Stopped at operation ${step} · ${error.message}`, "danger");
        showToast(`Lifecycle stopped: ${error.message}`, "danger");
      } finally {
        lifecycleRunning = false;
        runAllButton.disabled = false;
        resetButton.disabled = false;
        disableCardButtons(false);
      }
    }

    async function resetMockData() {
      if (lifecycleRunning) return;
      const confirmed = window.confirm(
        "Reset the hosted mock state to the JSON seed data? Shared test changes will be removed."
      );
      if (!confirmed) return;

      resetButton.disabled = true;
      resetButton.textContent = "Resetting…";
      resetResult.classList.add("is-visible");
      resetStatus.textContent = "In flight";
      resetStatus.dataset.tone = "";
      resetOutput.textContent = "POST /api/v1/mock/reset";

      const result = await requestApi("POST", `${API_PREFIX}/reset`, null);
      resetStatus.textContent = result.status === 0
        ? "Network error"
        : `${result.status} ${result.statusText || ""}`.trim();
      resetStatus.dataset.tone = toneForResult(result);
      resetOutput.textContent = `${Math.round(result.elapsed)} ms\n${formatOutput(result)}`;

      if (result.ok) {
        restoreSeedExamples();
        showToast("Mock data restored from the JSON seed.", "success");
      } else {
        showToast("Mock data reset failed. Inspect the response for details.", "danger");
      }
      resetButton.disabled = false;
      resetButton.innerHTML = '<span aria-hidden="true">↺</span> Reset mock data';
    }

    function showToast(message, tone = "") {
      const toast = document.createElement("div");
      toast.className = "toast";
      toast.dataset.tone = tone;
      toast.textContent = message;
      toastRegion.append(toast);
      window.setTimeout(() => toast.remove(), 5000);
    }

    baseInput.value = loadBaseUrl();
    baseInput.addEventListener("change", saveBaseUrl);
    renderResourceSections();
    runAllButton.addEventListener("click", runLifecycle);
    resetButton.addEventListener("click", resetMockData);
  </script>
</body>
</html>
"""


def mock_test_ui() -> HTMLResponse:
    """Return the dependency-free browser workbench for the mock CRUD API."""

    return HTMLResponse(
        content=MOCK_TEST_UI_HTML,
        headers={
            "Cache-Control": "no-store",
            "Content-Security-Policy": (
                "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; "
                "connect-src http: https:; img-src data:; base-uri 'none'; form-action 'none'"
            ),
            "Referrer-Policy": "no-referrer",
            "X-Content-Type-Options": "nosniff",
        },
    )


__all__ = ["mock_test_ui"]
