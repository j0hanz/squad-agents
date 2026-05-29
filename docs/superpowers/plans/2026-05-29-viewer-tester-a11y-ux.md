# Viewer-Tester HTML — Accessibility & UX Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve 17 UI/UX and accessibility findings in `skills/skill-builder/eval-viewer/viewer-tester.html`, covering broken ARIA references, missing heading hierarchy, color-only status dots, touch targets below 44 px, XSS in XLSX rendering, lazy loading, and minor form/navigation UX issues.

**Architecture:** All changes are in a single self-contained HTML file with inline CSS and JavaScript. No build toolchain exists. Verification is manual in-browser. Changes are grouped into five logical commits: HTML structure → CSS → JS behaviour → Form/matrix UX → XLSX security.

**Tech Stack:** HTML5, Bootstrap 5.3 (local assets at `skills/skill-builder/assets/`), vanilla ES6 JS, SheetJS 0.20.3 (optional CDN, currently eager-loaded).

---

## File Map

| File | Role |
|------|------|
| `skills/skill-builder/eval-viewer/viewer-tester.html` | Single source of all changes — inline `<style>`, HTML structure, inline `<script>` |

No new files are created. All edits are within this one file.

---

## D1 Pre-Note — `aria-modal` is Already Handled by Bootstrap

Finding D1 (sidebar offcanvas missing `aria-modal`) does **not** require a code change. Bootstrap 5's `Offcanvas` component calls `element.setAttribute('aria-modal', 'true')` inside its `show()` method and removes it on `hide()`. Confirm this in Task 2's browser verification step.

---

## Task 1: HTML Structure — Heading Hierarchy and ARIA Labels (A1, A2, A3, A4)

**File:** `skills/skill-builder/eval-viewer/viewer-tester.html`

---

- [ ] **Step 1.1 — Add `h2#sidebar-title` so `#sidebar aria-labelledby` resolves (A1)**

The `<aside id="sidebar">` references `aria-labelledby="sidebar-title"` but no element with that id exists. Add a visually-hidden heading as the first child of the offcanvas body.

Replace:
```html
          <div id="eval-list" class="list-group list-group-flush"></div>
```
With:
```html
          <h2 id="sidebar-title" class="visually-hidden">Eval list</h2>
          <div id="eval-list" class="list-group list-group-flush"></div>
```

---

- [ ] **Step 1.2 — Fix `fb-rail-title` referencing a `d-xl-none` element on desktop (A2)**

The `<aside id="feedback-rail">` uses `aria-labelledby="fb-rail-title"`. The only element with that id is the `<h6>` inside `offcanvas-header d-xl-none`, which is `display:none` on ≥xl viewports. The fix: remove the `id` from the h6 and instead add a `visually-hidden` span with that id as the first child of `offcanvas-body` — it is always in the DOM at every viewport.

**Remove** `id="fb-rail-title"` from the offcanvas-header h6. Replace:
```html
            <h6 class="offcanvas-title" id="fb-rail-title">Your Review</h6>
```
With:
```html
            <h6 class="offcanvas-title">Your Review</h6>
```

**Add** the always-present label span as the first child of `offcanvas-body`. Replace:
```html
          <div class="offcanvas-body scroll-pane p-3 bg-body-tertiary">
            <div class="d-flex align-items-center justify-content-between mb-3 d-none d-xl-flex">
```
With:
```html
          <div class="offcanvas-body scroll-pane p-3 bg-body-tertiary">
            <span id="fb-rail-title" class="visually-hidden">Your Review</span>
            <div class="d-flex align-items-center justify-content-between mb-3 d-none d-xl-flex">
```

---

- [ ] **Step 1.3 — Complete the ARIA tab pattern: add `id`/`aria-controls` to buttons; add `role`/`aria-labelledby`/`tabindex` to panels (A3)**

Tab buttons currently have no `id`, so panels cannot reference them via `aria-labelledby`. Panels have no `role="tabpanel"` and no `tabindex="-1"` (needed for programmatic focus in Task 3).

Replace the Outputs tab button:
```html
        <button class="nav-link active" type="button" role="tab" data-bs-toggle="tab" data-bs-target="#panel-outputs" aria-selected="true" aria-label="Outputs">Outputs</button>
```
With:
```html
        <button id="tab-outputs" class="nav-link active" type="button" role="tab" data-bs-toggle="tab" data-bs-target="#panel-outputs" aria-selected="true" aria-controls="panel-outputs">Outputs</button>
```

Replace the Benchmark tab button:
```html
        <button class="nav-link" type="button" role="tab" data-bs-toggle="tab" data-bs-target="#panel-benchmark" aria-selected="false">Benchmark</button>
```
With:
```html
        <button id="tab-benchmark" class="nav-link" type="button" role="tab" data-bs-toggle="tab" data-bs-target="#panel-benchmark" aria-selected="false" aria-controls="panel-benchmark">Benchmark</button>
```

Replace the Outputs panel opening tag:
```html
    <div class="tab-pane fade show active h-100" id="panel-outputs">
```
With:
```html
    <div class="tab-pane fade show active h-100" id="panel-outputs" role="tabpanel" aria-labelledby="tab-outputs" tabindex="-1">
```

Replace the Benchmark panel opening tag:
```html
    <div class="tab-pane fade h-100" id="panel-benchmark">
```
With:
```html
    <div class="tab-pane fade h-100" id="panel-benchmark" role="tabpanel" aria-labelledby="tab-benchmark" tabindex="-1">
```

---

- [ ] **Step 1.4 — Add `<h1>` to establish heading hierarchy (A4)**

The page has no `<h1>`. Accordion items use `<h2>` and the benchmark output generates `<h2>` — all orphaned. Make the skill name the page's `<h1>` using Bootstrap's `h6` visual size class to preserve the existing appearance.

Replace:
```html
        <span id="skill-name" class="fw-semibold text-body-emphasis text-truncate skill-name d-inline-block align-bottom" title=""></span>
```
With:
```html
        <h1 id="skill-name" class="fw-semibold text-body-emphasis text-truncate skill-name d-inline-block align-bottom h6 mb-0" title=""></h1>
```

---

- [ ] **Step 1.5 — Verify in browser**

Open `skills/skill-builder/eval-viewer/viewer-tester.html` in Chrome/Firefox.

1. **DevTools → Accessibility panel → inspect `#sidebar`**: accessible name should read "Eval list".
2. **Resize to ≥1200 px, inspect `#feedback-rail`**: accessible name should read "Your Review".
3. **Inspect `#tab-outputs`**: role=tab, aria-controls=panel-outputs visible.
4. **Inspect `#panel-outputs`**: role=tabpanel, aria-labelledby=tab-outputs visible.
5. **Accessibility tree (DevTools)**: page `<h1>` should be the skill name ("systematic-debugging"); accordion `<h2>`s appear below it.

---

- [ ] **Step 1.6 — Commit**

```bash
git add skills/skill-builder/eval-viewer/viewer-tester.html
git commit -m "fix(a11y): heading hierarchy, ARIA labels, and tab pattern in eval viewer

- Add visually-hidden h2#sidebar-title to satisfy aside aria-labelledby
- Add always-present span#fb-rail-title to fix desktop reference (was d-xl-none)
- Add id/aria-controls to tab buttons; role/aria-labelledby/tabindex to panels
- Change skill-name span to h1 with h6 visual class for semantic page structure

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 2: CSS — Touch Targets, Dot Shape, Font Size, Inline Style (A5, B1, B2, D2, E1)

**File:** `skills/skill-builder/eval-viewer/viewer-tester.html`

---

- [ ] **Step 2.1 — Raise `.eyebrow` font from `.7rem` (11.2 px) to `.75rem` (12 px) (E1)**

In the `<style>` block, replace:
```css
    .eyebrow { font-size: .7rem; letter-spacing: .08em; text-transform: uppercase; color: var(--bs-secondary-color); }
```
With:
```css
    .eyebrow { font-size: .75rem; letter-spacing: .08em; text-transform: uppercase; color: var(--bs-secondary-color); }
```

---

- [ ] **Step 2.2 — Add shape differentiation to `v-bad` dots for colorblind users (A5)**

`v-good` (round circle, green) and `v-bad` (round circle, red) are distinguishable only by hue. Giving `v-bad` a rounded-square shape (`border-radius: 2px`) provides a shape cue independent of color.

In the `<style>` block, replace:
```css
    .run-dot.v-bad  { background: var(--bs-danger); }
```
With:
```css
    .run-dot.v-bad  { background: var(--bs-danger); border-radius: 2px; }
```

---

- [ ] **Step 2.3 — Add 44 px touch target minimums to nav buttons and sidebar items (B1, B2)**

Bootstrap `.btn` defaults to ~38 px height. Sidebar list items have ~32 px computed height. Both are used as primary navigation on mobile.

Add a new rule block after the existing `.run-dot` rules in `<style>`:
```css

    /* Touch target minimums — Apple HIG 44 pt / Material 48 dp */
    #prev-btn, #next-btn { min-height: 44px; min-width: 44px; }
    #eval-list .list-group-item-action { min-height: 44px; }
```

---

- [ ] **Step 2.4 — Move magic inline `min-height` on navbar container to CSS (D2)**

Add to the CSS block (after the touch target rules):
```css
    .navbar .container-fluid { min-height: 58px; }
```

In the HTML, replace:
```html
    <div class="container-fluid" style="min-height:58px">
```
With:
```html
    <div class="container-fluid">
```

---

- [ ] **Step 2.5 — Verify in browser**

1. **Eyebrow labels**: Section labels ("PROMPT", "OUTPUT", "VERDICT", "NOTES") should be visibly legible at 12 px.
2. **Dot shapes**: Select Eval 1 · without skill and set verdict to "Needs work". The dot in the sidebar should be a rounded square (red), not a circle. The "Looks good" dot on Eval 1 · with skill should be a circle.
3. **Touch targets**: DevTools → Elements → select `#prev-btn` → Computed → height: should show 44 px or greater.
4. **Sidebar items**: In mobile viewport (≤991 px), open sidebar offcanvas, inspect list items → min-height: 44px in computed styles.
5. **No inline style on container**: `div.container-fluid` inside `nav` should have no `style` attribute in DevTools Elements panel.
6. **D1 confirmation**: On mobile viewport, open the sidebar offcanvas. DevTools → Accessibility panel → inspect `#sidebar`: `aria-modal` should be `true` (set by Bootstrap JS automatically on open).

---

- [ ] **Step 2.6 — Commit**

```bash
git add skills/skill-builder/eval-viewer/viewer-tester.html
git commit -m "fix(css): touch targets, colorblind dot shape, eyebrow size, extract inline style

- .eyebrow raised from .7rem to .75rem (12 px minimum for legibility)
- v-bad run-dot gets border-radius: 2px — rounded-square vs circle shape cue
- 44px min-height on prev/next buttons and sidebar list items
- Navbar container min-height moved from inline style to CSS

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 3: JS — Screen Reader Announcer and Tab Focus Management (A6, G1)

**File:** `skills/skill-builder/eval-viewer/viewer-tester.html`

---

- [ ] **Step 3.1 — Add `#sr-announcer` element to HTML (A6)**

The copy success state changes button text visually but never reaches a screen reader. A `aria-live="polite"` region that receives a text update on copy will be announced.

Add the following line after the toast container `</div>` and before `<script src="../assets/bootstrap.bundle.min.js">`:
```html

  <div id="sr-announcer" class="visually-hidden" aria-live="polite" aria-atomic="true"></div>
```

---

- [ ] **Step 3.2 — Add `announceToSR()` helper in JS (A6)**

Find the `// ═══ COPY HELPER ═══` section comment. Add the helper function immediately before `function copyText`:
```js
    function announceToSR(msg) {
      const region = $("sr-announcer");
      region.textContent = "";
      requestAnimationFrame(() => { region.textContent = msg; });
    }
```

`requestAnimationFrame` clears then re-sets the text so repeat-click announcements re-trigger even when the message is identical.

---

- [ ] **Step 3.3 — Call `announceToSR` inside `copyText` on success (A6)**

Replace the success branch inside `copyText`:
```js
      navigator.clipboard.writeText(text).then(() => {
        const orig = btn.textContent;
        btn.textContent = "Copied!";
        btn.classList.replace("btn-outline-secondary", "btn-success");
        btn.classList.add("copied");
        setTimeout(() => {
```
With:
```js
      navigator.clipboard.writeText(text).then(() => {
        const orig = btn.textContent;
        btn.textContent = "Copied!";
        btn.classList.replace("btn-outline-secondary", "btn-success");
        btn.classList.add("copied");
        announceToSR("Copied to clipboard");
        setTimeout(() => {
```

---

- [ ] **Step 3.4 — Move focus to tabpanel on keyboard tab switch (G1)**

When a user presses a tab button via keyboard, Bootstrap activates the panel but focus stays on the button. Screen reader users won't know the main content changed. `tabindex="-1"` was added to both panels in Task 1 Step 1.3, enabling programmatic focus.

In `init()`, find:
```js
      if (DATA.benchmark) { $("view-tabs").classList.remove("d-none"); renderBenchmark(); }
```
Replace with:
```js
      if (DATA.benchmark) {
        $("view-tabs").classList.remove("d-none");
        renderBenchmark();
        $("view-tabs").addEventListener("shown.bs.tab", (e) => {
          const targetId = e.target.getAttribute("data-bs-target");
          const panel = document.querySelector(targetId);
          if (panel) panel.focus();
        });
      }
```

---

- [ ] **Step 3.5 — Verify**

1. Open the file in a browser with Windows Narrator, VoiceOver, or NVDA active (or use axe DevTools browser extension).
2. **Copy button**: Tab to any "Copy" button in an output pane. Press Space/Enter. Verify the screen reader announces "Copied to clipboard".
3. **Repeat copy**: Press copy again — should announce again (not silently skip due to duplicate text).
4. **Tab focus**: Keyboard-navigate to the "Benchmark" tab and activate it. DevTools console: `document.activeElement` should be `#panel-benchmark`.

If no screen reader is available, verify step 2 by watching DevTools → Accessibility → Live Regions panel as you click Copy.

---

- [ ] **Step 3.6 — Commit**

```bash
git add skills/skill-builder/eval-viewer/viewer-tester.html
git commit -m "fix(a11y): announce copy success to screen readers; move focus on tab switch

- Add #sr-announcer aria-live region; announceToSR() uses rAF for repeat triggers
- copyText() calls announceToSR('Copied to clipboard') on success
- shown.bs.tab listener moves focus into the activated tabpanel

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 4: JS Behaviour — Form UX and Benchmark Matrix (F1, F2, E2)

**File:** `skills/skill-builder/eval-viewer/viewer-tester.html`

---

- [ ] **Step 4.1 — Make code block expand/collapse toggleable (F1)**

The current "Show all N lines" button removes itself from the DOM on click. There is no way to re-collapse. Replace the one-shot remove with a toggle.

Find the `expandBtn` creation inside `buildFileContentInto`:
```js
          const expandBtn = el("button", {
            class: "btn btn-link small d-block w-100 text-center py-1 mt-1",
            type: "button",
            text: `▼ Show all ${lines} lines`,
            "aria-expanded": "false",
            onclick: (e) => { pre.classList.remove("output-collapsed"); e.currentTarget.remove(); },
          });
```
Replace with:
```js
          const expandBtn = el("button", {
            class: "btn btn-link small d-block w-100 text-center py-1 mt-1",
            type: "button",
            text: `▼ Show all ${lines} lines`,
            "aria-expanded": "false",
            onclick: (e) => {
              const btn = e.currentTarget;
              const isCollapsed = pre.classList.toggle("output-collapsed");
              btn.textContent = isCollapsed ? `▼ Show all ${lines} lines` : "▲ Collapse";
              btn.setAttribute("aria-expanded", String(!isCollapsed));
            },
          });
```

---

- [ ] **Step 4.2 — Increase toast auto-dismiss delay from 1 500 ms to 3 000 ms (F2)**

The UX guideline is 3–5 s. At 1.5 s the "Saved" toast closes before many users finish reading it.

Replace:
```js
      bootstrap.Toast.getOrCreateInstance(t, { delay: 1500 }).show();
```
With:
```js
      bootstrap.Toast.getOrCreateInstance(t, { delay: 3000 }).show();
```

---

- [ ] **Step 4.3 — Add `table-warning` for mixed pass/fail assertion cells (E2)**

When a configuration has multiple runs per eval (future use), an assertion might pass in some runs and fail in others. Currently that mixed cell renders as `table-danger` (looks like a full failure). Introduce `table-warning` for the mixed case.

In `buildAssertionMatrix`, replace:
```js
          const allPass = results.every((r) => r.passed);
          const anyFail = results.some((r) => !r.passed);
          const cellCls = allPass ? "table-success text-center" : anyFail ? "table-danger text-center" : "text-center";
```
With:
```js
          const allPass = results.every((r) => r.passed);
          const anyFail = results.some((r) => !r.passed);
          const anyPass = results.some((r) => r.passed);
          const cellCls = allPass ? "table-success text-center"
            : (anyFail && anyPass) ? "table-warning text-center"
            : anyFail ? "table-danger text-center"
            : "text-center";
```

---

- [ ] **Step 4.4 — Verify**

1. **Code toggle**: Open the file, select "Eval 1 · with skill". The `fix.py` output has 57 lines and should show "▼ Show all 57 lines". Click it → code expands, button reads "▲ Collapse". Click again → code re-collapses, button returns to "▼ Show all 57 lines". `aria-expanded` toggles between `"true"` and `"false"` in DevTools.
2. **Toast delay**: Type any character in the Notes textarea and stop. After ~800 ms the "Saved" toast appears. Verify it remains visible for ~3 s before fading (count silently or use DevTools Performance recording).
3. **Matrix**: Switch to Benchmark tab. All cells in the assertion matrices show ✓/✗ correctly. No visual regressions (all single-run data, so mixed cells won't appear with this fixture — verify no JS errors in console).

---

- [ ] **Step 4.5 — Commit**

```bash
git add skills/skill-builder/eval-viewer/viewer-tester.html
git commit -m "fix(ux): toggleable code collapse, longer toast delay, mixed assertion color

- Code blocks now toggle expand/collapse; aria-expanded tracks state
- Toast delay raised from 1.5 s to 3 s per 3-5 s UX guideline
- Assertion matrix uses table-warning for mixed pass/fail cells

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Task 5: XLSX Security — Sanitize `innerHTML` and Lazy-Load SheetJS (C1, C2)

**File:** `skills/skill-builder/eval-viewer/viewer-tester.html`

---

- [ ] **Step 5.1 — Remove eager `<script>` tag for SheetJS from `<head>` (C2)**

Remove the following three lines from `<head>` (the comment and the script tag):
```html
  <!-- SheetJS is optional: if it fails to load (e.g. offline), xlsx outputs fall back to a download link. -->
  <script src="https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js"
          integrity="sha384-EnyY0/GSHQGSxSgMwaIPzSESbqoOLSexfnSMN2AP+39Ckmn92stwABZynq1JyzdT"
          crossorigin="anonymous"></script>
```

---

- [ ] **Step 5.2 — Add `loadXlsx()` lazy-loader before `renderXlsx` (C2)**

Locate `function renderXlsx(container, file) {` inside the `// ═══ FILE RENDERING ═══` section. Insert the following constants and function **immediately before** that line:

```js
    // SheetJS — load on demand (only when an xlsx file type is encountered)
    const XLSX_CDN = "https://cdn.sheetjs.com/xlsx-0.20.3/package/dist/xlsx.full.min.js";
    const XLSX_SRI = "sha384-EnyY0/GSHQGSxSgMwaIPzSESbqoOLSexfnSMN2AP+39Ckmn92stwABZynq1JyzdT";
    let _xlsxPromise = null;

    function loadXlsx() {
      if (typeof XLSX !== "undefined") return Promise.resolve(XLSX);
      if (_xlsxPromise) return _xlsxPromise;
      _xlsxPromise = new Promise((resolve, reject) => {
        const s = document.createElement("script");
        s.src = XLSX_CDN;
        s.integrity = XLSX_SRI;
        s.crossOrigin = "anonymous";
        s.onload = () => resolve(XLSX);
        s.onerror = () => { _xlsxPromise = null; reject(new Error("SheetJS load failed")); };
        document.head.appendChild(s);
      });
      return _xlsxPromise;
    }

```

---

- [ ] **Step 5.3 — Rewrite `renderXlsx` to use async lazy loader and sanitize `innerHTML` (C1, C2)**

Replace the entire `function renderXlsx(container, file) { … }` block (from the opening `function` line to its closing `}`) with:

```js
    function sanitizeXlsxWrap(wrap) {
      wrap.querySelectorAll("*").forEach((node) => {
        [...node.attributes].forEach((attr) => {
          if (/^on/i.test(attr.name)) node.removeAttribute(attr.name);
          if (attr.name === "href" && /^javascript:/i.test(attr.value)) node.removeAttribute(attr.name);
        });
        if (node.tagName === "SCRIPT") node.remove();
      });
    }

    function renderXlsx(container, file) {
      const placeholder = el("div", { class: "text-secondary small p-2 fst-italic", text: "Loading spreadsheet…" });
      container.append(placeholder);

      loadXlsx().then((XLSXLib) => {
        placeholder.remove();
        try {
          const raw = Uint8Array.from(atob(file.data_b64), (c) => c.charCodeAt(0));
          const wb = XLSXLib.read(raw, { type: "array" });
          const theme = document.documentElement.getAttribute("data-bs-theme");
          const theadClass = theme === "dark" ? "table-dark" : "table-light";

          wb.SheetNames.forEach((name) => {
            if (wb.SheetNames.length > 1) {
              container.append(el("div", { class: "fw-semibold small text-secondary mt-2", text: "Sheet: " + name }));
            }
            const html = XLSXLib.utils.sheet_to_html(wb.Sheets[name]);
            const wrap = el("div", { class: "table-responsive" });
            wrap.innerHTML = html;
            sanitizeXlsxWrap(wrap);
            wrap.querySelectorAll("table").forEach((t) => {
              t.classList.add("table", "table-hover", "table-sm", "table-striped", "table-bordered", "align-middle");
              const thead = t.querySelector("thead");
              if (thead) thead.classList.add(theadClass);
            });
            container.append(wrap);
          });
        } catch (err) {
          container.append(el("div", { class: "text-danger", text: "Error rendering spreadsheet: " + err.message }));
        }
      }).catch(() => {
        placeholder.remove();
        container.append(el("a", {
          class: "btn btn-outline-secondary",
          href: downloadUri(file), download: file.name,
          text: "Download " + file.name + " (spreadsheet preview unavailable offline)",
        }));
      });
    }
```

---

- [ ] **Step 5.4 — Verify lazy loading and non-xlsx pages unaffected**

1. Open the file in browser with DevTools → Network tab, filter by "JS".
2. **Initial load**: SheetJS (`xlsx.full.min.js`) must NOT appear in the network log. The page uses text/html/image outputs only in the test fixture.
3. **All six test evals render correctly**: cycle through all six sidebar entries, confirming prompt text, output files, grades accordion, and benchmark panel display without errors.
4. **No JS errors**: DevTools → Console must be clean (no errors or warnings from the lazy-loader change).
5. **xlsx code path** (optional, if a real xlsx file is available): Drop an xlsx eval into `EMBEDDED_DATA.runs` temporarily. Confirm the "Loading spreadsheet…" placeholder appears and then is replaced by the table. Remove the temp eval afterward.

---

- [ ] **Step 5.5 — Commit**

```bash
git add skills/skill-builder/eval-viewer/viewer-tester.html
git commit -m "fix(security): sanitize XLSX innerHTML; lazy-load SheetJS on demand

- Remove eager <script> tag — SheetJS now loads only when xlsx output is rendered
- _xlsxPromise singleton prevents duplicate script injection on multiple renders
- sanitizeXlsxWrap() strips on* event handlers and javascript: hrefs post-inject
- Async load shows placeholder while script fetches; falls back to download link

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

---

## Coverage Check

| Finding | Severity | Task / Step | Status |
|---------|----------|-------------|--------|
| A1 — Broken sidebar aria-labelledby | Critical | 1.1 | ✓ |
| A2 — fb-rail-title hidden on desktop | Critical | 1.2 | ✓ |
| A3 — Tab ARIA pattern incomplete | Critical | 1.3 | ✓ |
| A4 — No `<h1>` on page | High | 1.4 | ✓ |
| A5 — Color-only verdict dots | High | 2.2 | ✓ |
| A6 — Copy success not announced | Medium | 3.1–3.3 | ✓ |
| B1 — Prev/Next buttons ~38 px | High | 2.3 | ✓ |
| B2 — Sidebar items ~32 px | High | 2.3 | ✓ |
| C1 — XLSX innerHTML XSS | High | 5.3 | ✓ |
| C2 — SheetJS eager-loaded | Medium | 5.1–5.3 | ✓ |
| D1 — aria-modal | Medium | Pre-note (Bootstrap handles) | ✓ |
| D2 — Inline min-height style | Low | 2.4 | ✓ |
| E1 — .eyebrow 11.2 px | Medium | 2.1 | ✓ |
| E2 — Mixed matrix cells no color | Low | 4.3 | ✓ |
| F1 — No re-collapse on code blocks | Low | 4.1 | ✓ |
| F2 — Toast 1.5 s too fast | Low | 4.2 | ✓ |
| G1 — Focus not moved on tab switch | Medium | 3.4 | ✓ |
