# Repo Diff HTML Generator Architecture Design

## Objective
To completely resolve the UI layout breakdown, vertical alignment mismatches, and severe performance issues present in the previous HTML generator, delivering a VS Code-grade side-by-side diff viewer.

## Architectural Changes

### 1. The Death of the `<table>` (CSS Grid Adoption)
**Problem:** The previous `<table>` based approach caused lines to misalign severely when long code wrapped to the next line. The left and right `<td>` cells often disconnected visually from their line numbers.
**Solution:** We will adopt a modern CSS Grid architecture.
- The diff container will use `display: grid`.
- The track will be rigidly defined as 6 columns: `grid-template-columns: 50px 24px 1fr 50px 24px 1fr;`.
- Every "row" in the diff is simply 6 consecutive `<div>` elements appended to the grid container.
- **Benefit:** If code in the left column wraps to 3 lines, CSS Grid automatically forces the entire 6-element row to span the height of those 3 lines. The row numbers and right-side cells will perfectly expand to match, guaranteeing 100% vertical alignment natively in the browser without complex JS height recalculations.

### 2. Layout Stability (Flexbox Fixes)
**Problem:** The sidebar squished into a mess when too many files existed because of flex shrinking.
**Solution:** 
- The sidebar (`nav`) will be firmly locked: `width: 300px; flex-shrink: 0; overflow-y: auto;`.
- The main content area (`main`) will take the remaining space: `flex: 1; overflow: auto;`.
- This ensures the UI skeleton remains rigid regardless of content volume.

### 3. Typography & Styling Precision
- **Font:** The local `JetBrainsMono-Medium.ttf` will be securely loaded via `@font-face` with a fallback to `Consolas, monospace`.
- **Line Height:** Locked strictly to `1.5` (or exactly `20px`) with zero margins on `<pre>` or `<code>` tags to prevent arbitrary vertical spacing bloat.
- **Colors:** Precise hex codes matching VS Code's diff view:
  - Additions (New): Background `#e6ffec` (code), `#ccffd8` (line number), text `#1a7f37`.
  - Deletions (Old): Background `#ffebe9` (code), `#ffdce0` (line number), text `#cf222e`.
  - Context (Unchanged): Background `#ffffff`, line number `#6e7781`.

### 4. Performance (Lazy Highlighting)
**Problem:** Applying `highlight.js` or `pygments` to a massive 10,000-line diff file at load time freezes the browser.
**Solution:**
- The Python script outputs raw, unhighlighted code wrapped in `<pre><code>`.
- The HTML loads instantly.
- JavaScript attaches an `onclick` listener to the sidebar files.
- **Lazy Execution:** Only when a file panel becomes active (`display: grid`) does a `setTimeout` trigger `hljs.highlightElement()` specifically for the blocks within that panel.

## Implementation Steps
1. Rewrite the Python loop in `generate_html_diff` to output grid cells instead of `<tr>` and `<td>`.
2. Apply the CSS Grid styling and strict Flexbox rules for the structural layout.
3. Inject the lazy-loading JavaScript logic.
4. Verify local font linking works across different directory execution contexts.