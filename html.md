# HTML & CSS — Senior-Level Interview Guide

---

## Part 1: HTML Best Practices

---

### Semantic HTML — Why It Matters

Semantic HTML is the #1 thing interviewers test. It signals you care about accessibility, SEO, and maintainability.

```html
<!-- ❌ Div soup -->
<div class="header">
  <div class="nav">
    <div class="nav-item">Home</div>
  </div>
</div>
<div class="main">
  <div class="article">
    <div class="title">Post Title</div>
  </div>
  <div class="sidebar">...</div>
</div>
<div class="footer">...</div>

<!-- ✅ Semantic -->
<header>
  <nav>
    <a href="/">Home</a>
  </nav>
</header>
<main>
  <article>
    <h1>Post Title</h1>
  </article>
  <aside>...</aside>
</main>
<footer>...</footer>
```

### Key Semantic Elements

| Element | Use for |
|---------|---------|
| `<header>` | Introductory content, navigation |
| `<nav>` | Navigation links |
| `<main>` | Primary content (one per page) |
| `<article>` | Self-contained content (blog post, card) |
| `<section>` | Thematic grouping with a heading |
| `<aside>` | Sidebar, tangential content |
| `<footer>` | Footer of a section or page |
| `<figure>` / `<figcaption>` | Images with captions |
| `<time>` | Dates/times (machine-readable) |
| `<mark>` | Highlighted/relevant text |
| `<details>` / `<summary>` | Native accordion/disclosure |
| `<dialog>` | Native modal (use with `.showModal()`) |

### Heading Hierarchy

```html
<!-- ❌ Skipping levels -->
<h1>Page Title</h1>
<h3>Subsection</h3>  <!-- skipped h2 -->

<!-- ✅ Sequential -->
<h1>Page Title</h1>
  <h2>Section</h2>
    <h3>Subsection</h3>
```

Only one `<h1>` per page. Screen readers and SEO crawlers rely on heading hierarchy.

### Forms — Senior-Level Knowledge

```html
<!-- ✅ Accessible form -->
<form novalidate>
  <fieldset>
    <legend>Shipping Address</legend>

    <label for="name">Full Name</label>
    <input id="name" name="name" type="text" required autocomplete="name" />

    <label for="email">Email</label>
    <input id="email" name="email" type="email" required autocomplete="email"
           inputmode="email" />

    <label for="phone">Phone</label>
    <input id="phone" name="phone" type="tel" autocomplete="tel"
           inputmode="tel" pattern="[0-9]{10}" />

    <button type="submit">Submit</button>
  </fieldset>
</form>
```

Key points:
- **Always** pair `<label>` with `for` matching `id`
- Use `inputmode` for mobile keyboard hints (`numeric`, `email`, `tel`, `url`)
- Use `autocomplete` attributes for autofill
- Use `novalidate` on form + JS validation (gives you control over UX)
- `<fieldset>` + `<legend>` for grouping related fields
- `<button type="submit">` not `<div onClick>` — keyboard accessible by default

### Images

```html
<!-- ❌ -->
<img src="photo.jpg" />

<!-- ✅ -->
<img
  src="photo.jpg"
  alt="Team celebrating product launch"
  width="800"
  height="600"
  loading="lazy"
  decoding="async"
/>
```

- **Always** provide `alt` (empty `alt=""` for decorative images)
- Set `width` and `height` to prevent layout shift (CLS)
- `loading="lazy"` for below-the-fold images
- Use `<picture>` for art direction / format fallbacks:

```html
<picture>
  <source srcset="photo.avif" type="image/avif" />
  <source srcset="photo.webp" type="image/webp" />
  <img src="photo.jpg" alt="Fallback" />
</picture>
```

### Accessibility (a11y) Essentials

```html
<!-- Skip link for keyboard users -->
<a href="#main-content" class="sr-only focus:not-sr-only">
  Skip to main content
</a>

<!-- ARIA only when native HTML can't do it -->
<button aria-expanded="false" aria-controls="menu">Menu</button>
<nav id="menu" aria-hidden="true">...</nav>

<!-- Live regions for dynamic content -->
<div aria-live="polite" role="status">3 results found</div>
```

Golden rules:
1. **Use native HTML first** — `<button>`, `<a>`, `<input>` over `<div onClick>`
2. ARIA is a **last resort**, not a first choice
3. All interactive elements must be **keyboard accessible** (Tab, Enter, Escape)
4. Color should never be the **only** way to convey information
5. Minimum contrast ratio: **4.5:1** for normal text, **3:1** for large text

---

## Part 2: CSS — Core Concepts

---

### The Box Model

```
┌─────────────────────────────────────┐
│              margin                 │
│  ┌───────────────────────────────┐  │
│  │          border               │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │       padding           │  │  │
│  │  │  ┌───────────────────┐  │  │  │
│  │  │  │     content       │  │  │  │
│  │  │  └───────────────────┘  │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

**Always use this:**

```css
*, *::before, *::after {
  box-sizing: border-box;
}
```

`border-box` makes `width` include padding + border. Without it, a `width: 100px` element with `padding: 20px` becomes 140px wide.

### Specificity

Specificity is calculated as a **three-part score** (a, b, c):

| Selector | (a, b, c) | Score |
|----------|-----------|-------|
| `*` | (0, 0, 0) | 0 |
| `div` | (0, 0, 1) | 1 |
| `.card` | (0, 1, 0) | 10 |
| `#header` | (1, 0, 0) | 100 |
| `div.card` | (0, 1, 1) | 11 |
| `#header .nav a` | (1, 1, 1) | 111 |
| `style=""` (inline) | — | 1000 |
| `!important` | — | ∞ (overrides everything) |

Senior tip: **Never use `!important` in application code.** If you need it, your specificity architecture is broken.

### The Cascade (in order of priority)

1. `!important` user-agent styles
2. `!important` user styles
3. `!important` author styles
4. Author styles (your CSS)
5. User styles
6. User-agent (browser defaults)

Within the same origin, **specificity** breaks ties. Within the same specificity, **source order** (last wins).

### Stacking Context (`z-index`)

`z-index` only works on **positioned** elements (`relative`, `absolute`, `fixed`, `sticky`) or flex/grid children.

Things that create a **new stacking context** (common interview question):
- `position: fixed/sticky`
- `z-index` on a flex/grid child
- `opacity` less than 1
- `transform`, `filter`, `backdrop-filter`
- `will-change`
- `isolation: isolate` (use this intentionally to contain z-index)

```css
/* ✅ Contain z-index within a component */
.modal-wrapper {
  isolation: isolate;
}
```

### `position` Values

| Value | Relative to | In flow? | Creates stacking context? |
|-------|-------------|----------|---------------------------|
| `static` | Normal flow | Yes | No |
| `relative` | Its own normal position | Yes | If `z-index` set |
| `absolute` | Nearest positioned ancestor | No | If `z-index` set |
| `fixed` | Viewport | No | Always |
| `sticky` | Scroll container + threshold | Yes (until stuck) | Always |

### `display` Values That Matter

| Value | What it does |
|-------|-------------|
| `block` | Full width, new line |
| `inline` | Content width, same line, **ignores** width/height/vertical margin |
| `inline-block` | Content width, same line, **respects** width/height |
| `flex` | Flexbox container |
| `inline-flex` | Inline flexbox container |
| `grid` | Grid container |
| `none` | Removed from layout + accessibility tree |
| `contents` | Element disappears, children promoted (useful in flex/grid) |

---

## Part 3: Flexbox — Complete Reference

---

### Container Properties

```css
.container {
  display: flex;
  flex-direction: row;          /* row | row-reverse | column | column-reverse */
  flex-wrap: wrap;              /* nowrap | wrap | wrap-reverse */
  justify-content: center;     /* main axis alignment */
  align-items: center;         /* cross axis alignment */
  align-content: center;       /* multi-line cross axis (only with wrap) */
  gap: 16px;                   /* shorthand for row-gap + column-gap */
}
```

### `justify-content` (Main Axis)

```
flex-start:     |■ ■ ■         |
center:         |    ■ ■ ■     |
flex-end:       |         ■ ■ ■|
space-between:  |■     ■     ■ |
space-around:   | ■   ■   ■   |   (equal space around each)
space-evenly:   |  ■   ■   ■  |   (equal space between all)
```

### `align-items` (Cross Axis)

```
flex-start:   items at top
center:       items centered vertically
flex-end:     items at bottom
stretch:      items stretch to fill (default)
baseline:     items aligned by text baseline
```

### Item Properties

```css
.item {
  flex-grow: 1;        /* how much to grow (0 = don't grow) */
  flex-shrink: 1;      /* how much to shrink (0 = don't shrink) */
  flex-basis: 200px;   /* initial size before grow/shrink */
  align-self: center;  /* override align-items for this item */
  order: 2;            /* visual order (default 0) */
}
```

### `flex` Shorthand (Interview Favorite)

```css
flex: 1;           /* flex: 1 1 0%    — grow equally, basis 0 */
flex: auto;        /* flex: 1 1 auto  — grow equally, basis auto */
flex: none;        /* flex: 0 0 auto  — don't grow or shrink */
flex: 0 1 auto;   /* default — don't grow, can shrink */
```

**`flex: 1` vs `flex: auto`**: With `flex: 1` (basis 0), items share space equally regardless of content. With `flex: auto` (basis auto), items with more content get more space.

### Common Flexbox Patterns

```css
/* Center anything */
.center {
  display: flex;
  justify-content: center;
  align-items: center;
}

/* Push last item to the right (e.g., navbar logo left, menu right) */
.navbar {
  display: flex;
  align-items: center;
}
.navbar .spacer {
  flex: 1; /* or use margin-left: auto on the right item */
}

/* Equal-width columns */
.columns {
  display: flex;
  gap: 16px;
}
.columns > * {
  flex: 1;
}

/* Sticky footer */
body {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}
main {
  flex: 1;
}
```

---

## Part 4: CSS Grid — Complete Reference

---

### Container Properties

```css
.grid {
  display: grid;
  grid-template-columns: 1fr 2fr 1fr;       /* 3 columns */
  grid-template-rows: auto 1fr auto;         /* 3 rows */
  gap: 16px;
  grid-template-areas:
    "header header header"
    "sidebar main   aside"
    "footer footer footer";
}
```

### Sizing Functions

```css
/* Fixed */
grid-template-columns: 200px 400px 200px;

/* Fractional (proportional) */
grid-template-columns: 1fr 2fr 1fr;           /* 25% 50% 25% */

/* repeat() */
grid-template-columns: repeat(3, 1fr);         /* 3 equal columns */
grid-template-columns: repeat(4, 200px);       /* 4 fixed columns */

/* minmax() */
grid-template-columns: repeat(3, minmax(200px, 1fr));

/* auto-fill vs auto-fit */
grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));  /* keep empty tracks */
grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));   /* collapse empty tracks */
```

### `auto-fill` vs `auto-fit` (Common Interview Question)

```
Container: 1000px wide, minmax(200px, 1fr)

auto-fill: |■ 200px|■ 200px|■ 200px|  200px |  200px |
           (3 items + 2 empty tracks maintained)

auto-fit:  |■ 333px   |■ 333px   |■ 333px   |
           (3 items expand — empty tracks collapse to 0)
```

Use `auto-fit` for responsive grids that should stretch. Use `auto-fill` when you want consistent column widths.

### Grid Areas

```css
.layout {
  display: grid;
  grid-template-areas:
    "header  header"
    "sidebar main  "
    "footer  footer";
  grid-template-columns: 250px 1fr;
  grid-template-rows: auto 1fr auto;
}

.header  { grid-area: header; }
.sidebar { grid-area: sidebar; }
.main    { grid-area: main; }
.footer  { grid-area: footer; }
```

### Item Placement

```css
.item {
  grid-column: 1 / 3;         /* span from column line 1 to 3 */
  grid-column: span 2;        /* span 2 columns from auto position */
  grid-row: 2 / 4;            /* span from row line 2 to 4 */
  grid-area: 2 / 1 / 4 / 3;  /* row-start / col-start / row-end / col-end */
}
```

### Alignment in Grid

```css
.grid {
  justify-items: center;    /* align items horizontally within their cell */
  align-items: center;      /* align items vertically within their cell */
  justify-content: center;  /* align the entire grid horizontally */
  align-content: center;    /* align the entire grid vertically */
  place-items: center;      /* shorthand: align-items + justify-items */
  place-content: center;    /* shorthand: align-content + justify-content */
}

.item {
  justify-self: end;        /* override for this item */
  align-self: start;
  place-self: start end;
}
```

### Flexbox vs Grid — When to Use Which

| Flexbox | Grid |
|---------|------|
| **One-dimensional** (row OR column) | **Two-dimensional** (rows AND columns) |
| Content dictates layout | Layout dictates content placement |
| Navigation bars, toolbars | Page layouts, dashboards |
| Centering things | Card grids with uniform sizing |
| When items should wrap naturally | When you need precise placement |

You can (and should) **nest them**: Grid for the page layout, Flexbox inside each component.

---

## Part 5: Critical CSS Properties

---

### Modern Reset (Use This)

```css
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html {
  -webkit-text-size-adjust: 100%;
  text-size-adjust: 100%;
}

body {
  min-height: 100vh;
  line-height: 1.5;
  -webkit-font-smoothing: antialiased;
}

img, picture, video, canvas, svg {
  display: block;
  max-width: 100%;
}

input, button, textarea, select {
  font: inherit;
}

p, h1, h2, h3, h4, h5, h6 {
  overflow-wrap: break-word;
}
```

### Responsive Design

```css
/* Mobile-first media queries */
.card {
  padding: 16px;
}

@media (min-width: 768px) {
  .card {
    padding: 24px;
  }
}

@media (min-width: 1024px) {
  .card {
    padding: 32px;
  }
}

/* Container queries (modern — scoped to parent, not viewport) */
.card-container {
  container-type: inline-size;
  container-name: card;
}

@container card (min-width: 400px) {
  .card {
    flex-direction: row;
  }
}
```

### `clamp()` for Fluid Typography

```css
/* No media queries needed */
h1 {
  font-size: clamp(1.5rem, 4vw, 3rem);
  /* min: 1.5rem, preferred: 4vw, max: 3rem */
}

.container {
  width: clamp(320px, 90%, 1200px);
  padding: clamp(1rem, 3vw, 3rem);
}
```

### `aspect-ratio`

```css
.video-embed {
  aspect-ratio: 16 / 9;
  width: 100%;
}

.avatar {
  aspect-ratio: 1;    /* square */
  width: 48px;
  border-radius: 50%;
  object-fit: cover;
}
```

### `object-fit` (for images/video)

```css
img {
  width: 100%;
  height: 300px;
  object-fit: cover;      /* crop to fill, maintain ratio */
  /* object-fit: contain   — fit inside, may have gaps */
  /* object-fit: fill      — stretch (distorts) */
  object-position: top;   /* which part to show when cropping */
}
```

### Scroll Behavior

```css
html {
  scroll-behavior: smooth;
}

.scrollable {
  overflow-y: auto;
  overscroll-behavior: contain;  /* prevent scroll chaining to parent */
  scroll-snap-type: y mandatory;
}

.scrollable > section {
  scroll-snap-align: start;
}
```

### `text-overflow` and Truncation

```css
/* Single line truncation */
.truncate {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Multi-line truncation (line clamp) */
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
```

### Custom Properties (CSS Variables)

```css
:root {
  --color-primary: #3b82f6;
  --color-primary-hover: #2563eb;
  --radius: 8px;
  --shadow-sm: 0 1px 2px rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px rgb(0 0 0 / 0.1);
}

.button {
  background: var(--color-primary);
  border-radius: var(--radius);
  box-shadow: var(--shadow-sm);
}

.button:hover {
  background: var(--color-primary-hover);
  box-shadow: var(--shadow-md);
}

/* Scoped overrides */
.dark-theme {
  --color-primary: #60a5fa;
}
```

### Transitions and Animations

```css
/* Transitions — for state changes (hover, focus, active) */
.button {
  transition: background-color 150ms ease, transform 150ms ease;
}
.button:hover {
  background-color: var(--color-primary-hover);
  transform: scale(1.02);
}
.button:active {
  transform: scale(0.98);
}

/* Respect reduced motion preference */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}

/* Keyframe animation */
@keyframes fade-in {
  from { opacity: 0; transform: translateY(8px); }
  to   { opacity: 1; transform: translateY(0); }
}

.card {
  animation: fade-in 300ms ease-out;
}
```

### Logical Properties (for RTL/i18n support)

```css
/* ❌ Physical — breaks in RTL */
.card {
  margin-left: 16px;
  padding-right: 24px;
  border-bottom: 1px solid gray;
  text-align: left;
}

/* ✅ Logical — works in any direction */
.card {
  margin-inline-start: 16px;
  padding-inline-end: 24px;
  border-block-end: 1px solid gray;
  text-align: start;
}
```

| Physical | Logical |
|----------|---------|
| `left` / `right` | `inline-start` / `inline-end` |
| `top` / `bottom` | `block-start` / `block-end` |
| `margin-left` | `margin-inline-start` |
| `width` | `inline-size` |
| `height` | `block-size` |

### `has()` Selector (Game Changer)

```css
/* Style a form group when its input is focused */
.form-group:has(input:focus) {
  border-color: var(--color-primary);
}

/* Style a card differently if it contains an image */
.card:has(img) {
  grid-template-rows: 200px auto;
}

/* Disable submit button if required fields are empty */
form:has(:required:invalid) button[type="submit"] {
  opacity: 0.5;
  pointer-events: none;
}
```

### Other Modern Selectors

```css
/* :is() — reduces repetition, takes highest specificity in list */
:is(h1, h2, h3, h4) {
  font-weight: 700;
  line-height: 1.2;
}

/* :where() — same as :is() but zero specificity */
:where(h1, h2, h3, h4) {
  margin-block: 0.5em;
}

/* :not() */
.nav a:not(.active) {
  opacity: 0.7;
}

/* :focus-visible — only show focus ring for keyboard navigation */
button:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

---

## Part 6: Tailwind CSS Best Practices

---

### Class Ordering Convention

Follow the **"outside-in"** order — layout → spacing → sizing → visual → typography → state:

```html
<!-- ✅ Consistent ordering -->
<div class="
  flex items-center justify-between    <!-- 1. Layout -->
  gap-4 p-6 mx-auto                    <!-- 2. Spacing -->
  w-full max-w-2xl                     <!-- 3. Sizing -->
  bg-white rounded-lg shadow-md        <!-- 4. Visual/Box -->
  text-sm text-gray-700 font-medium    <!-- 5. Typography -->
  hover:shadow-lg transition-shadow    <!-- 6. States/Transitions -->
">
```

Tailwind's Prettier plugin (`prettier-plugin-tailwindcss`) auto-sorts for you — **always use it**.

### Component Extraction (When Classes Get Long)

**Don't** extract too early. **Do** extract when you repeat the same combination 3+ times.

```tsx
// ❌ Creating .btn in CSS defeats Tailwind's purpose
// ❌ @apply in a CSS file is an anti-pattern in most cases

// ✅ Extract to a component
function Button({ children, variant = "primary", ...props }) {
  const base = "inline-flex items-center justify-center rounded-lg px-4 py-2 text-sm font-medium transition-colors focus-visible:outline-2 focus-visible:outline-offset-2";

  const variants = {
    primary: "bg-blue-600 text-white hover:bg-blue-700 focus-visible:outline-blue-600",
    secondary: "bg-gray-100 text-gray-700 hover:bg-gray-200 focus-visible:outline-gray-500",
    danger: "bg-red-600 text-white hover:bg-red-700 focus-visible:outline-red-600",
  };

  return (
    <button className={`${base} ${variants[variant]}`} {...props}>
      {children}
    </button>
  );
}
```

### `cn()` / `clsx` + `tailwind-merge` (Industry Standard)

```tsx
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Usage — handles conditional classes + resolves Tailwind conflicts
<div className={cn(
  "rounded-lg p-4 text-sm",
  isPrimary && "bg-blue-600 text-white",
  isDisabled && "opacity-50 cursor-not-allowed",
  className  // allow parent overrides
)} />
```

Why `tailwind-merge`? Without it:
```tsx
// ❌ Both bg classes are in the DOM — which wins depends on CSS source order
<div className="bg-red-500 bg-blue-500" />

// ✅ tailwind-merge resolves: keeps only bg-blue-500
cn("bg-red-500", "bg-blue-500")  // → "bg-blue-500"
```

### Responsive Design in Tailwind

Tailwind is **mobile-first**. Unprefixed = mobile. Prefixed = that breakpoint and up.

```html
<div class="
  flex flex-col         <!-- mobile: stack vertically -->
  md:flex-row           <!-- 768px+: side by side -->
  lg:gap-8              <!-- 1024px+: bigger gap -->
">
  <div class="w-full md:w-1/3">Sidebar</div>
  <div class="w-full md:w-2/3">Content</div>
</div>
```

Default breakpoints:
| Prefix | Min-width |
|--------|-----------|
| `sm` | 640px |
| `md` | 768px |
| `lg` | 1024px |
| `xl` | 1280px |
| `2xl` | 1536px |

### Dark Mode

```html
<!-- Class strategy (most common with Next.js / theme toggles) -->
<div class="bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100">
  <p class="text-gray-600 dark:text-gray-400">Subtitle</p>
</div>
```

```js
// tailwind.config.js
module.exports = {
  darkMode: 'class',  // or 'media' for OS preference only
}
```

### Design Token Pattern (Consistent Spacing/Colors)

```js
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        brand: {
          50:  '#eff6ff',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
      },
      spacing: {
        18: '4.5rem',
        88: '22rem',
      },
      fontSize: {
        'display': ['3.5rem', { lineHeight: '1.1', fontWeight: '700' }],
      },
      borderRadius: {
        '4xl': '2rem',
      },
    },
  },
}
```

Usage: `bg-brand-500`, `text-brand-700`, `p-18`, `text-display`

### Animation Utilities

```html
<!-- Built-in -->
<div class="animate-spin" />
<div class="animate-pulse" />
<div class="animate-bounce" />

<!-- Custom in config -->
<!-- tailwind.config.js -->
<!--
keyframes: {
  'fade-in': {
    '0%':   { opacity: '0', transform: 'translateY(8px)' },
    '100%': { opacity: '1', transform: 'translateY(0)' },
  },
},
animation: {
  'fade-in': 'fade-in 300ms ease-out',
},
-->
<div class="animate-fade-in" />
```

### Common Patterns

```html
<!-- Sticky header -->
<header class="sticky top-0 z-50 bg-white/80 backdrop-blur-sm border-b">

<!-- Truncate text -->
<p class="truncate">...</p>                        <!-- single line -->
<p class="line-clamp-3">...</p>                    <!-- multi-line -->

<!-- Aspect ratio -->
<div class="aspect-video">                          <!-- 16:9 -->
<div class="aspect-square">                         <!-- 1:1 -->

<!-- Gradient text -->
<h1 class="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">

<!-- Glass effect -->
<div class="bg-white/10 backdrop-blur-lg rounded-xl border border-white/20">

<!-- Responsive grid -->
<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">

<!-- Center on page -->
<div class="min-h-screen flex items-center justify-center">

<!-- Container with auto margins -->
<div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">

<!-- Visually hidden but accessible -->
<span class="sr-only">Close menu</span>
```

### Tailwind Anti-Patterns

```html
<!-- ❌ Using arbitrary values for things that should be design tokens -->
<div class="p-[13px] text-[#1a2b3c] mt-[7px]">

<!-- ✅ Use the scale — round to nearest token or extend config -->
<div class="p-3 text-gray-800 mt-2">

<!-- ❌ @apply in CSS files (defeats utility-first purpose) -->
.btn {
  @apply px-4 py-2 bg-blue-600 text-white rounded-lg;
}

<!-- ✅ Extract a component instead -->
<!-- <Button variant="primary">Click</Button> -->

<!-- ❌ Overriding Tailwind with custom CSS -->
.card {
  padding: 20px !important;
}

<!-- ✅ Use Tailwind classes or extend the config -->
<div class="p-5">
```

### Tailwind v4 (Latest) Key Changes

```css
/* v4 uses CSS-first config instead of JS */
@import "tailwindcss";

@theme {
  --color-brand-500: #3b82f6;
  --font-display: "Inter", sans-serif;
  --breakpoint-3xl: 1920px;
}
```

- No more `tailwind.config.js` — configured in CSS with `@theme`
- Automatic content detection (no `content` array needed)
- Built-in `@starting-style` for entry animations
- Native CSS cascade layers

---

## Part 7: Performance & Layout Shift

---

### Core Web Vitals You Should Know

| Metric | What it measures | Target |
|--------|-----------------|--------|
| **LCP** (Largest Contentful Paint) | Loading performance | < 2.5s |
| **INP** (Interaction to Next Paint) | Responsiveness | < 200ms |
| **CLS** (Cumulative Layout Shift) | Visual stability | < 0.1 |

### Preventing CLS

```css
/* Always set dimensions on media */
img, video { width: 100%; height: auto; aspect-ratio: 16/9; }

/* Reserve space for dynamic content */
.ad-slot { min-height: 250px; }

/* Use transform for animations, not layout properties */
/* ❌ */ .animate { top: 0; left: 0; }
/* ✅ */ .animate { transform: translate(0, 0); }
```

### CSS Properties That Trigger Layout vs Paint vs Composite

| Trigger | Properties (avoid animating these) |
|---------|-----------------------------------|
| **Layout** (expensive) | `width`, `height`, `margin`, `padding`, `top`, `left`, `font-size` |
| **Paint** (moderate) | `color`, `background`, `box-shadow`, `border` |
| **Composite** (cheap ✅) | `transform`, `opacity`, `filter` |

**Always animate `transform` and `opacity`** — they're GPU-accelerated and don't trigger layout/paint.

```css
/* ❌ Triggers layout on every frame */
.slide { left: 0; transition: left 300ms; }
.slide.active { left: 100px; }

/* ✅ Composite only — smooth 60fps */
.slide { transform: translateX(0); transition: transform 300ms; }
.slide.active { transform: translateX(100px); }
```

### `will-change` and `contain`

```css
/* Tell browser to optimize for upcoming transform changes */
.animated-element {
  will-change: transform;
}

/* Contain layout/paint to this element (limits browser recalculations) */
.card {
  contain: layout paint;
}
```

---

## Part 8: Quick Interview Answers

---

**Q: `em` vs `rem` vs `px`?**
- `px` — absolute, doesn't scale with user preferences
- `em` — relative to parent's font-size (compounds — dangerous for nesting)
- `rem` — relative to root (`<html>`) font-size (consistent, preferred for spacing/typography)

**Q: How do you center a div?**
```css
/* Flexbox */  display: flex; justify-content: center; align-items: center;
/* Grid */     display: grid; place-items: center;
/* Position */ position: absolute; top: 50%; left: 50%; translate: -50% -50%;
/* Margin */   margin: auto; /* works in flex/grid containers */
```

**Q: What is BEM?**
Block-Element-Modifier naming: `.block__element--modifier`
```css
.card { }
.card__title { }
.card__title--highlighted { }
```
Less relevant with Tailwind/CSS-in-JS, but still asked.

**Q: Pseudo-elements vs pseudo-classes?**
- Pseudo-class = state (`:hover`, `:focus`, `:first-child`, `:nth-child(2n)`)
- Pseudo-element = virtual element (`::before`, `::after`, `::placeholder`, `::selection`)

**Q: What's the difference between `visibility: hidden` and `display: none`?**
- `display: none` — removed from layout, no space taken, invisible to screen readers
- `visibility: hidden` — invisible but **still takes up space**, still in accessibility tree
- `opacity: 0` — invisible, takes space, still interactive (receives clicks)

**Q: CSS selector performance?**
Selectors are read **right to left**. `.nav > a` first finds all `<a>`, then checks parent. Performance rarely matters in practice, but avoid universal selectors in large DOMs (`.wrapper * { }`).

**Q: `@layer` — what and why?**
```css
@layer base, components, utilities;

@layer base { h1 { font-size: 2rem; } }
@layer components { .btn { padding: 8px 16px; } }
@layer utilities { .mt-4 { margin-top: 1rem; } }
```
Later layers always win regardless of specificity. This is how Tailwind v4 ensures utilities override components.
