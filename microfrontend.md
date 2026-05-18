# Micro Frontend — Complete Industry Mastery Guide

> **Project**: E-Commerce Platform (ShopZone) built with Micro Frontends
> Covers Module Federation, Single-SPA, Web Components, shared state, independent deployments, and production patterns used at companies like Spotify, IKEA, Zalando, and Amazon.

---

## Table of Contents

1. [What Are Micro Frontends?](#1-what-are-micro-frontends)
2. [Why Micro Frontends? — Real Problems They Solve](#2-why-micro-frontends)
3. [Architecture Patterns](#3-architecture-patterns)
4. [Integration Approaches — Deep Dive](#4-integration-approaches)
5. [Module Federation (Webpack 5) — The Industry Standard](#5-module-federation)
6. [Single-SPA — Framework-Agnostic Orchestration](#6-single-spa)
7. [Web Components Approach](#7-web-components)
8. [Routing Across Micro Frontends](#8-routing)
9. [Shared State & Communication](#9-shared-state-and-communication)
10. [Shared Dependencies & Design Systems](#10-shared-dependencies)
11. [Authentication & Authorization](#11-auth)
12. [Error Boundaries & Resilience](#12-error-boundaries)
13. [Testing Strategies](#13-testing)
14. [CI/CD & Independent Deployments](#14-cicd)
15. [Performance Optimization](#15-performance)
16. [Monitoring & Observability](#16-monitoring)
17. [Migration Strategy — Monolith to Micro Frontends](#17-migration)
18. [Project: ShopZone E-Commerce Platform](#18-project)
19. [Interview Questions](#19-interview-questions)

---

## 1. What Are Micro Frontends?

Micro frontends extend the microservices philosophy to the frontend world. Instead of a single monolithic frontend application, the UI is composed of **independently developed, tested, and deployed** features owned by autonomous teams.

```
┌─────────────────────────────────────────────────────────┐
│                    MONOLITH FRONTEND                     │
│  ┌──────────┬──────────┬──────────┬──────────┐          │
│  │  Catalog  │  Cart    │  Checkout │  Profile │          │
│  │          │          │          │          │          │
│  │  ALL COUPLED — ONE REPO, ONE BUILD, ONE DEPLOY       │
│  └──────────┴──────────┴──────────┴──────────┘          │
└─────────────────────────────────────────────────────────┘

                        ▼ BECOMES ▼

┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Team      │  │ Team      │  │ Team      │  │ Team      │
│ Catalog   │  │ Cart      │  │ Checkout  │  │ Profile   │
│           │  │           │  │           │  │           │
│ React     │  │ Vue       │  │ React     │  │ Svelte    │
│ Webpack   │  │ Vite      │  │ Webpack   │  │ Rollup    │
│ Own CI/CD │  │ Own CI/CD │  │ Own CI/CD │  │ Own CI/CD │
│ Own DB    │  │ Own API   │  │ Own API   │  │ Own API   │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
      │              │              │              │
      └──────────────┴──────┬───────┴──────────────┘
                            │
                   ┌────────▼────────┐
                   │  Shell / Host   │
                   │  Application    │
                   │  (Orchestrator) │
                   └─────────────────┘
```

### Core Principles

| Principle | Description |
|-----------|-------------|
| **Team Autonomy** | Each team owns a vertical slice — UI, API, data, deploy pipeline |
| **Technology Agnostic** | Teams pick their own framework, build tool, test runner |
| **Independent Deployability** | Ship one micro frontend without touching others |
| **Isolated Runtime** | CSS, JS, and state don't leak between micro frontends |
| **Resilient** | One micro frontend failing doesn't crash the entire page |

---

## 2. Why Micro Frontends? — Real Problems They Solve

### Problems in Monolithic Frontends

```
REAL SCENARIO: 50-developer team, single React app

Problem 1: MERGE HELL
  → 200+ PRs/week, constant conflicts in shared files
  → package.json, router config, global state — everyone touches them

Problem 2: DEPLOY FEAR
  → One team's broken test blocks ALL teams from deploying
  → "Who broke the build?" — daily standup nightmare

Problem 3: SCALING TEAMS
  → New team joins → onboarding takes 3 weeks to understand the codebase
  → Cross-team dependencies create invisible coupling

Problem 4: TECH DEBT PRISON
  → Stuck on React 16 because upgrading means touching everything
  → Can't adopt new tools without full team consensus

Problem 5: BUILD TIME
  → 15-minute build times, 30-minute CI pipelines
  → Developer productivity tanks
```

### When to Use Micro Frontends

```
USE MICRO FRONTENDS WHEN:
  ✅ Multiple teams (3+) work on the same application
  ✅ Teams need independent release cycles
  ✅ Application is large (50k+ LOC frontend)
  ✅ Different parts have different scaling/performance needs
  ✅ Migrating incrementally from legacy to modern framework

DON'T USE WHEN:
  ❌ Small team (< 5 developers)
  ❌ Simple application with few features
  ❌ Team is comfortable with monorepo tooling (Nx, Turborepo)
  ❌ No organizational need for team autonomy
  ❌ Tight budget — micro frontends add operational complexity
```

### Industry Examples

```
SPOTIFY:
  → Each "squad" owns a UI section (playlists, search, player)
  → iframes initially, moved to Web Components
  → ~100 autonomous squads

IKEA:
  → Product pages, cart, checkout — separate micro frontends
  → Module Federation with Webpack 5
  → Teams in 5+ countries deploy independently

ZALANDO:
  → "Project Mosaic" — server-side composed micro frontends
  → Tailor (layout service) + Fragment (micro frontend units)
  → 200+ micro frontends in production

AMAZON:
  → Every widget on a product page is a separate micro frontend
  → Teams own "Buy Box", "Reviews", "Recommendations" independently
  → Server-side includes (SSI) + client-side hydration
```

---

## 3. Architecture Patterns

### Pattern 1: Build-Time Integration (NPM Packages)

```
┌─────────────────────────────────────┐
│           Host Application          │
│                                     │
│  import Catalog from '@shop/catalog'│
│  import Cart from '@shop/cart'      │
│                                     │
│  // These are NPM packages          │
│  // Built and published separately  │
│  // But bundled together at build   │
└─────────────────────────────────────┘

PROS:
  + Simple to understand
  + Type safety via published types
  + Tree-shaking works naturally

CONS:
  - NOT truly independent deploys (host must rebuild)
  - Version coordination required
  - Lock-step releases
```

```typescript
// package.json of host
{
  "dependencies": {
    "@shopzone/catalog": "^2.1.0",
    "@shopzone/cart": "^1.5.0",
    "@shopzone/checkout": "^3.0.0"
  }
}

// Host App
import { ProductGrid } from '@shopzone/catalog';
import { MiniCart } from '@shopzone/cart';
import { CheckoutFlow } from '@shopzone/checkout';

function App() {
  return (
    <Layout>
      <Header><MiniCart /></Header>
      <Main><ProductGrid /></Main>
    </Layout>
  );
}
```

### Pattern 2: Run-Time Integration via JavaScript

```
┌─────────────────────────────────────────┐
│           Host Application              │
│                                         │
│  // Loads micro frontends at runtime    │
│  // from different CDN URLs             │
│                                         │
│  <script src="https://catalog.cdn/app.js">
│  <script src="https://cart.cdn/app.js">  │
│                                         │
│  // Each script registers itself        │
│  // Host renders them into DOM slots    │
└─────────────────────────────────────────┘
```

```typescript
// catalog micro frontend — self-registers
(function() {
  window.__MFE_REGISTRY__ = window.__MFE_REGISTRY__ || {};
  
  window.__MFE_REGISTRY__['catalog'] = {
    mount(container: HTMLElement, props: any) {
      const root = ReactDOM.createRoot(container);
      root.render(<CatalogApp {...props} />);
      return {
        unmount() {
          root.unmount();
        },
        update(newProps: any) {
          root.render(<CatalogApp {...newProps} />);
        }
      };
    }
  };
})();

// Host application — loads and mounts
class MicroFrontendLoader {
  private instances = new Map<string, any>();

  async load(name: string, url: string, container: HTMLElement) {
    // Load the script
    await this.loadScript(url);
    
    // Get the registered micro frontend
    const mfe = window.__MFE_REGISTRY__[name];
    if (!mfe) throw new Error(`MFE ${name} not found`);
    
    // Mount it
    const instance = mfe.mount(container, { user: this.getUser() });
    this.instances.set(name, instance);
  }

  private loadScript(url: string): Promise<void> {
    return new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = url;
      script.onload = () => resolve();
      script.onerror = reject;
      document.head.appendChild(script);
    });
  }
}
```

### Pattern 3: Run-Time Integration via iframes

```
┌──────────────────────────────────────────┐
│  Host Application                        │
│  ┌────────────────────────────────────┐  │
│  │ <iframe src="catalog.shopzone.com">│  │
│  │  ┌──────────────────────────────┐  │  │
│  │  │  Complete isolated app       │  │  │
│  │  │  Own DOM, CSS, JS context    │  │  │
│  │  └──────────────────────────────┘  │  │
│  └────────────────────────────────────┘  │
│  ┌────────────────────────────────────┐  │
│  │ <iframe src="cart.shopzone.com">   │  │
│  │  ┌──────────────────────────────┐  │  │
│  │  │  Complete isolated app       │  │  │
│  │  └──────────────────────────────┘  │  │
│  └────────────────────────────────────┘  │
└──────────────────────────────────────────┘

PROS:
  + Perfect isolation (CSS, JS, global state)
  + True crash isolation
  + Works with any technology

CONS:
  - Performance overhead (each iframe = full browser context)
  - Communication via postMessage only (slow, complex)
  - SEO nightmare — search engines can't index iframe content
  - Responsive design is painful
  - Deep linking is complex
```

```typescript
// Host — iframe-based micro frontend container
class IframeMicroFrontend {
  private iframe: HTMLIFrameElement;
  private messageHandlers = new Map<string, Function>();

  constructor(
    private name: string,
    private url: string,
    private container: HTMLElement
  ) {}

  mount() {
    this.iframe = document.createElement('iframe');
    this.iframe.src = this.url;
    this.iframe.style.cssText = 'width:100%;border:none;';
    
    // Auto-resize iframe based on content
    window.addEventListener('message', (event) => {
      if (event.origin !== new URL(this.url).origin) return;
      
      const { type, payload } = event.data;
      
      if (type === 'RESIZE') {
        this.iframe.style.height = `${payload.height}px`;
      }
      
      const handler = this.messageHandlers.get(type);
      if (handler) handler(payload);
    });
    
    this.container.appendChild(this.iframe);
  }

  sendMessage(type: string, payload: any) {
    this.iframe.contentWindow?.postMessage(
      { type, payload },
      new URL(this.url).origin
    );
  }

  onMessage(type: string, handler: Function) {
    this.messageHandlers.set(type, handler);
  }
}

// Inside iframe micro frontend — notify parent of height changes
const resizeObserver = new ResizeObserver((entries) => {
  for (const entry of entries) {
    window.parent.postMessage({
      type: 'RESIZE',
      payload: { height: entry.contentRect.height }
    }, '*');
  }
});
resizeObserver.observe(document.body);
```

### Pattern 4: Server-Side Composition

```
┌─────────────────────────────────────────────────────────┐
│                    REVERSE PROXY / EDGE                  │
│                    (Nginx / CDN Edge Worker)              │
│                                                          │
│  GET /products → Team Catalog's server → HTML fragment   │
│  GET /cart     → Team Cart's server    → HTML fragment   │
│                                                          │
│  ┌────────────────────────────────────────────────────┐  │
│  │              COMPOSED HTML RESPONSE                 │  │
│  │                                                    │  │
│  │  <html>                                            │  │
│  │    <head><!-- shared styles --></head>              │  │
│  │    <body>                                          │  │
│  │      <header><!-- from shell service --></header>  │  │
│  │      <main>                                        │  │
│  │        <!-- SSI: catalog fragment -->               │  │
│  │        <!-- SSI: recommendations fragment -->       │  │
│  │      </main>                                       │  │
│  │      <footer><!-- from shell service --></footer>  │  │
│  │    </body>                                          │  │
│  │  </html>                                            │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

```nginx
# Nginx Server-Side Includes (SSI) configuration
server {
    listen 80;
    ssi on;
    
    location / {
        # Shell app serves the layout
        proxy_pass http://shell-service:3000;
    }
    
    location /fragments/catalog {
        proxy_pass http://catalog-service:3001;
    }
    
    location /fragments/cart {
        proxy_pass http://cart-service:3002;
    }
    
    location /fragments/checkout {
        proxy_pass http://checkout-service:3003;
    }
}
```

```html
<!-- Shell service template with SSI directives -->
<!DOCTYPE html>
<html>
<head>
  <title>ShopZone</title>
  <!--#include virtual="/fragments/shared-styles" -->
</head>
<body>
  <!--#include virtual="/fragments/header" -->
  
  <main>
    <!--#include virtual="/fragments/catalog?category=electronics" -->
  </main>

  <!--#include virtual="/fragments/footer" -->
  
  <!-- Client-side hydration scripts -->
  <script src="/fragments/catalog/hydrate.js" async></script>
</body>
</html>
```

### Pattern 5: Edge-Side Composition (Modern)

```typescript
// Cloudflare Worker — edge-side composition
export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    
    // Determine which fragments to load based on route
    const layout = await getLayout(url.pathname);
    
    // Fetch all fragments in parallel
    const fragments = await Promise.all(
      layout.fragments.map(async (fragment) => {
        try {
          const response = await fetch(fragment.url, {
            headers: { 'x-fragment': 'true' },
            cf: { cacheTtl: fragment.cacheTtl }
          });
          return { name: fragment.name, html: await response.text() };
        } catch (error) {
          return { name: fragment.name, html: fragment.fallback };
        }
      })
    );
    
    // Compose the final HTML
    let html = layout.template;
    for (const fragment of fragments) {
      html = html.replace(`<!--fragment:${fragment.name}-->`, fragment.html);
    }
    
    return new Response(html, {
      headers: { 'content-type': 'text/html' }
    });
  }
};
```

---

## 4. Integration Approaches — Deep Dive

### Comparison Matrix

```
┌─────────────────────┬───────────┬───────────┬───────────┬───────────┬───────────┐
│ Criteria            │ Build-Time│ Runtime JS│ iframes   │ Server    │ Module    │
│                     │ (NPM)     │           │           │ Side      │ Federation│
├─────────────────────┼───────────┼───────────┼───────────┼───────────┼───────────┤
│ Independent Deploy  │    ❌     │    ✅     │    ✅     │    ✅     │    ✅     │
│ Isolation           │    ❌     │    ⚠️     │    ✅     │    ✅     │    ⚠️     │
│ Performance         │    ✅     │    ⚠️     │    ❌     │    ✅     │    ✅     │
│ SEO                 │    ✅     │    ⚠️     │    ❌     │    ✅     │    ⚠️     │
│ Developer Experience│    ✅     │    ⚠️     │    ✅     │    ⚠️     │    ✅     │
│ Framework Agnostic  │    ❌     │    ✅     │    ✅     │    ✅     │    ✅     │
│ Shared State        │    ✅     │    ⚠️     │    ❌     │    ❌     │    ✅     │
│ Complexity          │    Low    │   Medium  │    Low    │   High    │   Medium  │
│ Industry Adoption   │   Medium  │   Medium  │    Low    │   Medium  │   High    │
└─────────────────────┴───────────┴───────────┴───────────┴───────────┴───────────┘
```

---

## 5. Module Federation (Webpack 5) — The Industry Standard

Module Federation allows a JavaScript application to dynamically load code from another application at runtime, sharing dependencies and eliminating duplication.

### Mental Model

```
┌──────────────────────────────────────────────────────────────┐
│                    MODULE FEDERATION                          │
│                                                              │
│  HOST (Shell App)                                            │
│  ┌─────────────────────────────────────────────────────┐     │
│  │                                                     │     │
│  │  "I need <ProductCard /> from the catalog remote"   │     │
│  │                                                     │     │
│  │  1. Check: Do I already have React loaded?  → YES   │     │
│  │  2. Don't download React again (SHARED)             │     │
│  │  3. Fetch only ProductCard chunk from catalog CDN   │     │
│  │  4. Execute and render ProductCard                  │     │
│  │                                                     │     │
│  └─────────────────────────────────────────────────────┘     │
│                          ▲                                   │
│                          │ remoteEntry.js                    │
│                          │ (manifest of exposed modules)     │
│  REMOTE (Catalog App)    │                                   │
│  ┌───────────────────────┴─────────────────────────────┐     │
│  │                                                     │     │
│  │  exposes: {                                         │     │
│  │    './ProductCard': './src/components/ProductCard',  │     │
│  │    './ProductGrid': './src/components/ProductGrid',  │     │
│  │  }                                                  │     │
│  │                                                     │     │
│  │  shared: { react: { singleton: true } }             │     │
│  │                                                     │     │
│  └─────────────────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

### Host Application (Shell) — Webpack Config

```typescript
// shell-app/webpack.config.ts
import { ModuleFederationPlugin } from 'webpack/container/ModuleFederationPlugin';
import HtmlWebpackPlugin from 'html-webpack-plugin';
import path from 'path';

const config = {
  entry: './src/index.tsx',
  mode: 'development',
  devServer: {
    port: 3000,
    historyApiFallback: true,
    headers: {
      'Access-Control-Allow-Origin': '*',
    },
  },
  output: {
    publicPath: 'auto',
    uniqueName: 'shell',
    clean: true,
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js', '.jsx'],
  },
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: 'ts-loader',
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: ['style-loader', 'css-loader', 'postcss-loader'],
      },
    ],
  },
  plugins: [
    new ModuleFederationPlugin({
      name: 'shell',
      
      // Remotes — where to find other micro frontends
      remotes: {
        catalog: 'catalog@http://localhost:3001/remoteEntry.js',
        cart: 'cart@http://localhost:3002/remoteEntry.js',
        checkout: 'checkout@http://localhost:3003/remoteEntry.js',
        profile: 'profile@http://localhost:3004/remoteEntry.js',
      },
      
      // Shared dependencies — loaded once, used by all
      shared: {
        react: { 
          singleton: true,        // only one instance
          requiredVersion: '^18.0.0',
          eager: true,            // load immediately in host
        },
        'react-dom': { 
          singleton: true, 
          requiredVersion: '^18.0.0',
          eager: true,
        },
        'react-router-dom': { 
          singleton: true, 
          requiredVersion: '^6.0.0',
        },
        // Shared design system
        '@shopzone/ui-kit': {
          singleton: true,
          requiredVersion: '^1.0.0',
        },
        // Shared state library
        zustand: {
          singleton: true,
          requiredVersion: '^4.0.0',
        },
      },
    }),
    new HtmlWebpackPlugin({
      template: './public/index.html',
    }),
  ],
};

export default config;
```

### Remote Application (Catalog) — Webpack Config

```typescript
// catalog-app/webpack.config.ts
import { ModuleFederationPlugin } from 'webpack/container/ModuleFederationPlugin';

const config = {
  entry: './src/index.tsx',
  mode: 'development',
  devServer: {
    port: 3001,
    headers: { 'Access-Control-Allow-Origin': '*' },
  },
  output: {
    publicPath: 'auto',
    uniqueName: 'catalog',
    clean: true,
  },
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
  },
  module: {
    rules: [
      { test: /\.tsx?$/, use: 'ts-loader', exclude: /node_modules/ },
      { test: /\.css$/, use: ['style-loader', 'css-loader', 'postcss-loader'] },
    ],
  },
  plugins: [
    new ModuleFederationPlugin({
      name: 'catalog',
      filename: 'remoteEntry.js',  // the manifest file
      
      // What this micro frontend exposes to others
      exposes: {
        './ProductCard': './src/components/ProductCard',
        './ProductGrid': './src/components/ProductGrid',
        './ProductDetail': './src/pages/ProductDetail',
        './SearchBar': './src/components/SearchBar',
        './CategoryNav': './src/components/CategoryNav',
      },
      
      shared: {
        react: { singleton: true, requiredVersion: '^18.0.0' },
        'react-dom': { singleton: true, requiredVersion: '^18.0.0' },
        'react-router-dom': { singleton: true, requiredVersion: '^6.0.0' },
        '@shopzone/ui-kit': { singleton: true, requiredVersion: '^1.0.0' },
        zustand: { singleton: true, requiredVersion: '^4.0.0' },
      },
    }),
  ],
};

export default config;
```

### Dynamic Remote Loading (Production Pattern)

```typescript
// shell-app/src/utils/loadRemote.ts

interface RemoteConfig {
  url: string;
  scope: string;
  module: string;
}

// Registry of micro frontend URLs — fetched from config service
const remoteRegistry: Record<string, RemoteConfig> = {};

async function fetchRemoteRegistry(): Promise<void> {
  const response = await fetch('/api/mfe-registry');
  const registry = await response.json();
  Object.assign(remoteRegistry, registry);
}

// Dynamically load a remote module at runtime
async function loadRemoteModule<T = any>(
  remoteName: string,
  moduleName: string
): Promise<T> {
  const config = remoteRegistry[remoteName];
  if (!config) {
    throw new Error(`Remote "${remoteName}" not found in registry`);
  }

  // Step 1: Load the remoteEntry.js script
  await loadScript(`${config.url}/remoteEntry.js`);

  // Step 2: Initialize the remote container
  const container = (window as any)[config.scope];
  if (!container) {
    throw new Error(`Container "${config.scope}" not initialized`);
  }
  
  await container.init(__webpack_share_scopes__.default);

  // Step 3: Get the module factory
  const factory = await container.get(moduleName);
  const module = factory();
  
  return module;
}

function loadScript(url: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const existing = document.querySelector(`script[src="${url}"]`);
    if (existing) { resolve(); return; }
    
    const script = document.createElement('script');
    script.src = url;
    script.type = 'text/javascript';
    script.async = true;
    script.onload = () => resolve();
    script.onerror = () => reject(new Error(`Failed to load script: ${url}`));
    document.head.appendChild(script);
  });
}

export { loadRemoteModule, fetchRemoteRegistry };
```

### Using Remote Components in Host

```tsx
// shell-app/src/App.tsx
import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ErrorBoundary } from './components/ErrorBoundary';
import { AppShell } from './components/AppShell';
import { LoadingSpinner } from '@shopzone/ui-kit';

// Static remote imports (resolved at build time via webpack config)
const CatalogPage = lazy(() => import('catalog/ProductGrid'));
const ProductDetail = lazy(() => import('catalog/ProductDetail'));
const CartPage = lazy(() => import('cart/CartPage'));
const CheckoutPage = lazy(() => import('checkout/CheckoutFlow'));
const ProfilePage = lazy(() => import('profile/ProfilePage'));

// Type declarations for remote modules
declare module 'catalog/ProductGrid' {
  const ProductGrid: React.ComponentType<{ category?: string }>;
  export default ProductGrid;
}

declare module 'catalog/ProductDetail' {
  const ProductDetail: React.ComponentType<{ productId: string }>;
  export default ProductDetail;
}

function App() {
  return (
    <BrowserRouter>
      <AppShell>
        <ErrorBoundary fallback={<div>Something went wrong</div>}>
          <Suspense fallback={<LoadingSpinner />}>
            <Routes>
              <Route path="/" element={<CatalogPage />} />
              <Route path="/product/:id" element={<ProductDetail />} />
              <Route path="/cart" element={<CartPage />} />
              <Route path="/checkout/*" element={<CheckoutPage />} />
              <Route path="/profile/*" element={<ProfilePage />} />
            </Routes>
          </Suspense>
        </ErrorBoundary>
      </AppShell>
    </BrowserRouter>
  );
}

export default App;
```

### Version Management with Module Federation

```typescript
// Dynamic version negotiation
// shell-app/webpack.config.ts — production pattern

const shared = {
  react: {
    singleton: true,
    requiredVersion: '^18.0.0',
    // strictVersion: true would CRASH if versions don't match
    // Instead, use requiredVersion for warnings
    version: '18.2.0',
  },
  'react-dom': {
    singleton: true,
    requiredVersion: '^18.0.0',
    version: '18.2.0',
  },
  // Eagerly load in host to prevent waterfall
  '@shopzone/ui-kit': {
    singleton: true,
    eager: true,
    requiredVersion: '^1.0.0',
  },
};

/*
VERSION RESOLUTION FLOW:
1. Host declares react@18.2.0 as eager singleton
2. Catalog remote declares react@18.2.0 as singleton
3. Cart remote declares react@18.3.0 as singleton

Resolution:
  → Host loads first, provides react@18.2.0
  → Catalog: "18.2.0 satisfies ^18.0.0" → uses host's React ✅
  → Cart: "18.2.0 satisfies ^18.0.0" → uses host's React ✅
  → Only ONE copy of React loaded

If Cart declared requiredVersion: '^19.0.0':
  → "18.2.0 does NOT satisfy ^19.0.0" → loads own React
  → TWO copies of React (but singleton prevents crashes)
  → Console warning about multiple instances
*/
```

---

## 6. Single-SPA — Framework-Agnostic Orchestration

Single-SPA is a meta-framework for combining multiple JavaScript micro frontends into a single page application.

### Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    SINGLE-SPA ROOT CONFIG                   │
│                                                            │
│  registerApplication({                                     │
│    name: 'catalog',                                        │
│    app: () => System.import('catalog'),                    │
│    activeWhen: '/products'                                 │
│  });                                                       │
│                                                            │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │
│  │ Navbar  │  │ Catalog │  │  Cart   │  │Checkout │      │
│  │(React)  │  │(React)  │  │ (Vue)   │  │(Angular)│      │
│  │         │  │         │  │         │  │         │      │
│  │ ALWAYS  │  │ /prod*  │  │ /cart   │  │/check*  │      │
│  │ ACTIVE  │  │         │  │         │  │         │      │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │
│                                                            │
│  LIFECYCLE:  bootstrap → mount → unmount (→ unload)        │
└────────────────────────────────────────────────────────────┘
```

### Root Config

```typescript
// root-config/src/index.ts
import { registerApplication, start, LifeCycles } from 'single-spa';

// Layout engine for defining page layouts
import { constructApplications, constructRoutes, constructLayoutEngine } from 'single-spa-layout';

// Define the layout via HTML template
const routes = constructRoutes(document.querySelector('#single-spa-layout')!);

const applications = constructApplications({
  routes,
  loadApp({ name }) {
    return System.import(name) as Promise<LifeCycles>;
  },
});

// Register all applications from layout
applications.forEach(registerApplication);

// Construct layout engine
const layoutEngine = constructLayoutEngine({ routes, applications });

// Start single-spa
start({
  urlRerouteOnly: true, // don't trigger re-routes on hash changes
});
```

```html
<!-- root-config/src/index.html -->
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>ShopZone</title>
  
  <!-- Import map — tells SystemJS where each micro frontend lives -->
  <script type="systemjs-importmap">
    {
      "imports": {
        "@shopzone/root-config": "//localhost:9000/shopzone-root-config.js",
        "@shopzone/navbar": "//localhost:9001/shopzone-navbar.js",
        "@shopzone/catalog": "//localhost:9002/shopzone-catalog.js",
        "@shopzone/cart": "//localhost:9003/shopzone-cart.js",
        "@shopzone/checkout": "//localhost:9004/shopzone-checkout.js",
        "react": "https://cdn.jsdelivr.net/npm/react@18/umd/react.production.min.js",
        "react-dom": "https://cdn.jsdelivr.net/npm/react-dom@18/umd/react-dom.production.min.js"
      }
    }
  </script>
  <script src="https://cdn.jsdelivr.net/npm/systemjs/dist/system.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/systemjs/dist/extras/amd.min.js"></script>
  
  <!-- Layout definition -->
  <template id="single-spa-layout">
    <single-spa-router>
      <!-- Navbar is always visible -->
      <application name="@shopzone/navbar"></application>
      
      <main>
        <route path="products">
          <application name="@shopzone/catalog"></application>
        </route>
        
        <route path="cart">
          <application name="@shopzone/cart"></application>
        </route>
        
        <route path="checkout">
          <application name="@shopzone/checkout"></application>
        </route>
        
        <!-- Default route -->
        <route default>
          <application name="@shopzone/catalog"></application>
        </route>
      </main>
    </single-spa-router>
  </template>
</head>
<body>
  <script>
    System.import('@shopzone/root-config');
  </script>
</body>
</html>
```

### Single-SPA React Micro Frontend

```tsx
// catalog/src/shopzone-catalog.tsx
import React from 'react';
import ReactDOM from 'react-dom';
import singleSpaReact from 'single-spa-react';
import { CatalogApp } from './CatalogApp';

// single-spa lifecycle functions
const lifecycles = singleSpaReact({
  React,
  ReactDOM,
  rootComponent: CatalogApp,
  
  // Custom DOM element to mount into
  domElementGetter: () => {
    let el = document.getElementById('catalog-container');
    if (!el) {
      el = document.createElement('div');
      el.id = 'catalog-container';
      document.body.appendChild(el);
    }
    return el;
  },
  
  errorBoundary(err: Error, info: React.ErrorInfo, props: any) {
    console.error('Catalog MFE error:', err);
    return <div className="mfe-error">Catalog is temporarily unavailable</div>;
  },
});

export const bootstrap = lifecycles.bootstrap;
export const mount = lifecycles.mount;
export const unmount = lifecycles.unmount;

// CatalogApp.tsx
function CatalogApp(props: { name: string; singleSpa: any }) {
  return (
    <div className="catalog-mfe">
      <h2>Product Catalog</h2>
      <ProductGrid />
    </div>
  );
}
```

### Single-SPA Vue Micro Frontend

```typescript
// cart/src/main.ts — Vue micro frontend
import { h, createApp } from 'vue';
import singleSpaVue from 'single-spa-vue';
import CartApp from './CartApp.vue';
import { createPinia } from 'pinia';

const vueLifecycles = singleSpaVue({
  createApp,
  appOptions: {
    render() {
      return h(CartApp, {
        name: (this as any).name,
      });
    },
  },
  handleInstance(app) {
    app.use(createPinia());
  },
});

export const bootstrap = vueLifecycles.bootstrap;
export const mount = vueLifecycles.mount;
export const unmount = vueLifecycles.unmount;
```

---

## 7. Web Components Approach

Web Components provide native browser encapsulation — Shadow DOM for style isolation, Custom Elements for framework-agnostic components.

```typescript
// catalog/src/ProductCardElement.ts — Framework-agnostic Web Component
class ProductCardElement extends HTMLElement {
  private shadow: ShadowRoot;
  private _product: any = null;

  static get observedAttributes() {
    return ['product-id'];
  }

  constructor() {
    super();
    this.shadow = this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
    this.render();
    this.fetchProduct();
  }

  attributeChangedCallback(name: string, oldVal: string, newVal: string) {
    if (name === 'product-id' && oldVal !== newVal) {
      this.fetchProduct();
    }
  }

  set product(value: any) {
    this._product = value;
    this.render();
  }

  private async fetchProduct() {
    const id = this.getAttribute('product-id');
    if (!id) return;
    
    const response = await fetch(`/api/products/${id}`);
    this._product = await response.json();
    this.render();
  }

  private render() {
    if (!this._product) {
      this.shadow.innerHTML = `<div class="skeleton">Loading...</div>`;
      return;
    }

    this.shadow.innerHTML = `
      <style>
        /* Styles are SCOPED — no leaks! */
        :host {
          display: block;
          font-family: system-ui, sans-serif;
        }
        .card {
          border: 1px solid #e2e8f0;
          border-radius: 12px;
          overflow: hidden;
          transition: box-shadow 0.2s;
        }
        .card:hover {
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .card img {
          width: 100%;
          aspect-ratio: 1;
          object-fit: cover;
        }
        .card-body {
          padding: 16px;
        }
        .price {
          font-size: 1.25rem;
          font-weight: 700;
          color: #1a1a2e;
        }
        .add-to-cart {
          width: 100%;
          padding: 10px;
          background: #2563eb;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-size: 0.95rem;
        }
        .add-to-cart:hover { background: #1d4ed8; }
      </style>
      
      <div class="card">
        <img src="${this._product.image}" alt="${this._product.name}" />
        <div class="card-body">
          <h3>${this._product.name}</h3>
          <p class="price">$${this._product.price.toFixed(2)}</p>
          <button class="add-to-cart">Add to Cart</button>
        </div>
      </div>
    `;

    this.shadow.querySelector('.add-to-cart')?.addEventListener('click', () => {
      this.dispatchEvent(new CustomEvent('add-to-cart', {
        bubbles: true,
        composed: true, // crosses shadow DOM boundary
        detail: { product: this._product },
      }));
    });
  }

  disconnectedCallback() {
    // Cleanup
  }
}

customElements.define('shopzone-product-card', ProductCardElement);
```

### Wrapping React Inside a Web Component

```tsx
// Wrap a React component as a Web Component for cross-framework use
import React from 'react';
import ReactDOM from 'react-dom/client';

class ReactWebComponentWrapper extends HTMLElement {
  private root: ReactDOM.Root | null = null;
  private mountPoint: HTMLDivElement | null = null;

  connectedCallback() {
    const shadow = this.attachShadow({ mode: 'open' });
    this.mountPoint = document.createElement('div');
    shadow.appendChild(this.mountPoint);
    
    // Inject shared styles
    const styleLink = document.createElement('link');
    styleLink.rel = 'stylesheet';
    styleLink.href = '/shared-styles.css';
    shadow.appendChild(styleLink);

    this.root = ReactDOM.createRoot(this.mountPoint);
    this.renderReactComponent();
  }

  static get observedAttributes() {
    return ['data-props'];
  }

  attributeChangedCallback() {
    this.renderReactComponent();
  }

  private renderReactComponent() {
    if (!this.root) return;
    
    const props = JSON.parse(this.getAttribute('data-props') || '{}');
    
    // Import the actual React component
    import('./components/MiniCart').then(({ MiniCart }) => {
      this.root!.render(
        <React.StrictMode>
          <MiniCart {...props} />
        </React.StrictMode>
      );
    });
  }

  disconnectedCallback() {
    this.root?.unmount();
  }
}

customElements.define('shopzone-mini-cart', ReactWebComponentWrapper);
```

---

## 8. Routing Across Micro Frontends

### The Routing Challenge

```
PROBLEM:
  Shell owns the top-level routes: /products, /cart, /checkout
  Each micro frontend has internal routes:
    Catalog: /products/:id, /products?category=shoes
    Checkout: /checkout/shipping, /checkout/payment, /checkout/confirm
  
  WHO CONTROLS THE ROUTER?
  
SOLUTION: Two-level routing
  Shell: Top-level route matching → loads the right micro frontend
  MFE:   Internal routing within its own namespace
```

### Shell Router

```tsx
// shell-app/src/AppRouter.tsx
import React, { Suspense, lazy, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';

const CatalogMFE = lazy(() => import('catalog/CatalogApp'));
const CartMFE = lazy(() => import('cart/CartApp'));
const CheckoutMFE = lazy(() => import('checkout/CheckoutApp'));

function AppRouter() {
  return (
    <BrowserRouter>
      <NavigationListener />
      <Routes>
        {/* Shell owns top-level routes */}
        <Route path="/products/*" element={
          <MFEBoundary name="catalog">
            <Suspense fallback={<PageSkeleton />}>
              <CatalogMFE basePath="/products" />
            </Suspense>
          </MFEBoundary>
        } />
        
        <Route path="/cart" element={
          <MFEBoundary name="cart">
            <Suspense fallback={<PageSkeleton />}>
              <CartMFE />
            </Suspense>
          </MFEBoundary>
        } />
        
        <Route path="/checkout/*" element={
          <ProtectedRoute>
            <MFEBoundary name="checkout">
              <Suspense fallback={<PageSkeleton />}>
                <CheckoutMFE basePath="/checkout" />
              </Suspense>
            </MFEBoundary>
          </ProtectedRoute>
        } />
        
        <Route path="/" element={<Navigate to="/products" />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}

// Listen for navigation events from micro frontends
function NavigationListener() {
  const navigate = useNavigate();
  
  useEffect(() => {
    const handler = (event: CustomEvent) => {
      navigate(event.detail.path, event.detail.options);
    };
    
    window.addEventListener('mfe:navigate', handler as EventListener);
    return () => window.removeEventListener('mfe:navigate', handler as EventListener);
  }, [navigate]);
  
  return null;
}
```

### Micro Frontend Internal Router

```tsx
// catalog-app/src/CatalogApp.tsx
import React from 'react';
import { Routes, Route, useNavigate } from 'react-router-dom';
import { MemoryRouter } from 'react-router-dom';

interface CatalogAppProps {
  basePath: string;
  // When running standalone, use BrowserRouter
  // When running inside shell, use MemoryRouter synced with shell
}

function CatalogApp({ basePath }: CatalogAppProps) {
  const isStandalone = !window.__SHELL__;
  
  const Router = isStandalone ? BrowserRouter : MemoryRouterSynced;
  
  return (
    <Router basePath={basePath}>
      <Routes>
        <Route index element={<ProductGrid />} />
        <Route path=":productId" element={<ProductDetail />} />
        <Route path="category/:categoryId" element={<CategoryPage />} />
        <Route path="search" element={<SearchResults />} />
      </Routes>
    </Router>
  );
}

// Synced MemoryRouter — keeps MFE internal routing in sync with browser URL
function MemoryRouterSynced({ basePath, children }: { basePath: string; children: React.ReactNode }) {
  const [initialEntry] = React.useState(() => {
    // Strip the basePath from current URL to get internal route
    const path = window.location.pathname.replace(basePath, '') || '/';
    return path;
  });

  return (
    <MemoryRouter initialEntries={[initialEntry]}>
      <URLSync basePath={basePath} />
      {children}
    </MemoryRouter>
  );
}

// Sync internal navigation back to shell
function URLSync({ basePath }: { basePath: string }) {
  const location = useLocation();
  
  React.useEffect(() => {
    const fullPath = `${basePath}${location.pathname}`;
    if (window.location.pathname !== fullPath) {
      window.dispatchEvent(new CustomEvent('mfe:navigate', {
        detail: { path: fullPath, options: { replace: true } }
      }));
    }
  }, [location.pathname, basePath]);
  
  return null;
}

// Navigation helper for cross-MFE navigation
function navigateToMFE(path: string) {
  window.dispatchEvent(new CustomEvent('mfe:navigate', {
    detail: { path }
  }));
}

export { CatalogApp, navigateToMFE };
```

---

## 9. Shared State & Communication

### Pattern 1: Custom Events (Loosely Coupled)

```typescript
// shared/src/events.ts — Event bus via Custom Events

type EventMap = {
  'cart:item-added': { productId: string; quantity: number; price: number };
  'cart:item-removed': { productId: string };
  'cart:updated': { items: CartItem[]; total: number };
  'auth:login': { user: User; token: string };
  'auth:logout': {};
  'notification:show': { message: string; type: 'success' | 'error' | 'info' };
  'mfe:navigate': { path: string; options?: { replace?: boolean } };
};

class MicroFrontendEventBus {
  private listeners = new Map<string, Set<Function>>();

  emit<K extends keyof EventMap>(event: K, payload: EventMap[K]) {
    window.dispatchEvent(
      new CustomEvent(event, { 
        detail: payload,
        bubbles: true,
      })
    );
  }

  on<K extends keyof EventMap>(event: K, handler: (payload: EventMap[K]) => void): () => void {
    const wrappedHandler = (e: CustomEvent) => handler(e.detail);
    
    window.addEventListener(event, wrappedHandler as EventListener);
    
    // Track for cleanup
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(wrappedHandler);
    
    // Return cleanup function
    return () => {
      window.removeEventListener(event, wrappedHandler as EventListener);
      this.listeners.get(event)?.delete(wrappedHandler);
    };
  }

  // Cleanup all listeners for a micro frontend
  destroyScope(prefix: string) {
    for (const [event, handlers] of this.listeners) {
      if (event.startsWith(prefix)) {
        handlers.forEach(h => window.removeEventListener(event, h as EventListener));
        this.listeners.delete(event);
      }
    }
  }
}

// Singleton shared across all micro frontends
export const eventBus = (window as any).__MFE_EVENT_BUS__ ??= new MicroFrontendEventBus();
```

### Pattern 2: Shared Zustand Store

```typescript
// shared/src/stores/cartStore.ts
import { createStore, StoreApi } from 'zustand/vanilla';
import { useStore } from 'zustand';

interface CartItem {
  productId: string;
  name: string;
  price: number;
  quantity: number;
  image: string;
}

interface CartState {
  items: CartItem[];
  total: number;
  itemCount: number;
  isOpen: boolean;
  
  addItem: (item: Omit<CartItem, 'quantity'>) => void;
  removeItem: (productId: string) => void;
  updateQuantity: (productId: string, quantity: number) => void;
  clearCart: () => void;
  toggleCart: () => void;
}

function createCartStore(): StoreApi<CartState> {
  return createStore<CartState>((set, get) => ({
    items: [],
    total: 0,
    itemCount: 0,
    isOpen: false,

    addItem: (item) => {
      set((state) => {
        const existing = state.items.find(i => i.productId === item.productId);
        
        let newItems: CartItem[];
        if (existing) {
          newItems = state.items.map(i =>
            i.productId === item.productId
              ? { ...i, quantity: i.quantity + 1 }
              : i
          );
        } else {
          newItems = [...state.items, { ...item, quantity: 1 }];
        }
        
        const total = newItems.reduce((sum, i) => sum + i.price * i.quantity, 0);
        const itemCount = newItems.reduce((sum, i) => sum + i.quantity, 0);
        
        // Persist to localStorage for cross-tab sync
        localStorage.setItem('shopzone:cart', JSON.stringify(newItems));
        
        // Emit event for other MFEs
        window.dispatchEvent(new CustomEvent('cart:updated', {
          detail: { items: newItems, total, itemCount }
        }));
        
        return { items: newItems, total, itemCount };
      });
    },

    removeItem: (productId) => {
      set((state) => {
        const newItems = state.items.filter(i => i.productId !== productId);
        const total = newItems.reduce((sum, i) => sum + i.price * i.quantity, 0);
        const itemCount = newItems.reduce((sum, i) => sum + i.quantity, 0);
        
        localStorage.setItem('shopzone:cart', JSON.stringify(newItems));
        
        return { items: newItems, total, itemCount };
      });
    },

    updateQuantity: (productId, quantity) => {
      if (quantity <= 0) {
        get().removeItem(productId);
        return;
      }
      
      set((state) => {
        const newItems = state.items.map(i =>
          i.productId === productId ? { ...i, quantity } : i
        );
        const total = newItems.reduce((sum, i) => sum + i.price * i.quantity, 0);
        const itemCount = newItems.reduce((sum, i) => sum + i.quantity, 0);
        
        localStorage.setItem('shopzone:cart', JSON.stringify(newItems));
        
        return { items: newItems, total, itemCount };
      });
    },

    clearCart: () => {
      localStorage.removeItem('shopzone:cart');
      set({ items: [], total: 0, itemCount: 0 });
    },

    toggleCart: () => set((state) => ({ isOpen: !state.isOpen })),
  }));
}

// Singleton store — same instance across all micro frontends
const CART_STORE_KEY = '__SHOPZONE_CART_STORE__';

function getCartStore(): StoreApi<CartState> {
  if (!(window as any)[CART_STORE_KEY]) {
    const store = createCartStore();
    
    // Hydrate from localStorage
    const saved = localStorage.getItem('shopzone:cart');
    if (saved) {
      const items = JSON.parse(saved);
      const total = items.reduce((sum: number, i: CartItem) => sum + i.price * i.quantity, 0);
      const itemCount = items.reduce((sum: number, i: CartItem) => sum + i.quantity, 0);
      store.setState({ items, total, itemCount });
    }
    
    (window as any)[CART_STORE_KEY] = store;
  }
  
  return (window as any)[CART_STORE_KEY];
}

// React hook for use in any micro frontend
function useCartStore<T>(selector: (state: CartState) => T): T {
  return useStore(getCartStore(), selector);
}

export { getCartStore, useCartStore, CartState, CartItem };
```

### Pattern 3: Pub/Sub with Message Broker

```typescript
// shared/src/messageBroker.ts — Production-grade message broker

interface Message<T = any> {
  id: string;
  type: string;
  source: string;  // which MFE sent it
  payload: T;
  timestamp: number;
  correlationId?: string;  // for request-response patterns
}

type Subscription = { unsubscribe: () => void };

class MessageBroker {
  private subscriptions = new Map<string, Map<string, (msg: Message) => void>>();
  private history: Message[] = [];
  private maxHistory = 100;

  publish<T>(type: string, payload: T, source: string): string {
    const message: Message<T> = {
      id: crypto.randomUUID(),
      type,
      source,
      payload,
      timestamp: Date.now(),
    };

    // Store in history for late subscribers
    this.history.push(message);
    if (this.history.length > this.maxHistory) {
      this.history.shift();
    }

    // Deliver to all subscribers
    const subs = this.subscriptions.get(type);
    if (subs) {
      subs.forEach(handler => {
        try {
          handler(message);
        } catch (error) {
          console.error(`Message handler error for ${type}:`, error);
        }
      });
    }

    return message.id;
  }

  subscribe(type: string, handler: (msg: Message) => void, subscriberId?: string): Subscription {
    const id = subscriberId || crypto.randomUUID();
    
    if (!this.subscriptions.has(type)) {
      this.subscriptions.set(type, new Map());
    }
    
    this.subscriptions.get(type)!.set(id, handler);
    
    return {
      unsubscribe: () => {
        this.subscriptions.get(type)?.delete(id);
      }
    };
  }

  // Get messages that happened before this subscriber joined
  getHistory(type?: string): Message[] {
    if (type) {
      return this.history.filter(m => m.type === type);
    }
    return [...this.history];
  }

  // Request-response pattern across MFEs
  async request<TReq, TRes>(
    type: string, 
    payload: TReq, 
    source: string, 
    timeoutMs = 5000
  ): Promise<TRes> {
    return new Promise((resolve, reject) => {
      const correlationId = crypto.randomUUID();
      const responseType = `${type}:response`;
      
      const timer = setTimeout(() => {
        sub.unsubscribe();
        reject(new Error(`Request ${type} timed out after ${timeoutMs}ms`));
      }, timeoutMs);
      
      const sub = this.subscribe(responseType, (msg) => {
        if (msg.correlationId === correlationId) {
          clearTimeout(timer);
          sub.unsubscribe();
          resolve(msg.payload as TRes);
        }
      });
      
      this.publish(type, { ...payload as any, correlationId }, source);
    });
  }
}

// Singleton
export const broker = (window as any).__MFE_BROKER__ ??= new MessageBroker();
```

### Using Shared State in Components

```tsx
// In Catalog MFE — "Add to Cart" button
import { useCartStore } from '@shopzone/shared/stores/cartStore';

function AddToCartButton({ product }: { product: Product }) {
  const addItem = useCartStore(state => state.addItem);
  const items = useCartStore(state => state.items);
  
  const inCart = items.find(i => i.productId === product.id);
  
  return (
    <button 
      onClick={() => addItem({
        productId: product.id,
        name: product.name,
        price: product.price,
        image: product.image,
      })}
      className={inCart ? 'btn-in-cart' : 'btn-add-cart'}
    >
      {inCart ? `In Cart (${inCart.quantity})` : 'Add to Cart'}
    </button>
  );
}

// In Shell — MiniCart badge in header
import { useCartStore } from '@shopzone/shared/stores/cartStore';

function MiniCartBadge() {
  const itemCount = useCartStore(state => state.itemCount);
  const toggleCart = useCartStore(state => state.toggleCart);
  
  return (
    <button onClick={toggleCart} className="mini-cart-badge">
      🛒 {itemCount > 0 && <span className="badge">{itemCount}</span>}
    </button>
  );
}
```

---

## 10. Shared Dependencies & Design Systems

### Shared UI Kit (Design System)

```
┌──────────────────────────────────────────────────────────┐
│                @shopzone/ui-kit                           │
│                                                          │
│  PUBLISHED AS NPM PACKAGE + SHARED VIA MODULE FEDERATION │
│                                                          │
│  Components:                                             │
│  ├── Button, Input, Select, Checkbox                     │
│  ├── Modal, Drawer, Toast                                │
│  ├── Card, Table, Pagination                             │
│  ├── LoadingSpinner, Skeleton                            │
│  └── Typography, Grid, Stack                             │
│                                                          │
│  Design Tokens:                                          │
│  ├── colors, spacing, typography                         │
│  ├── breakpoints, shadows, borders                       │
│  └── CSS custom properties + Tailwind config             │
│                                                          │
│  RULES:                                                  │
│  1. NO business logic — pure presentational              │
│  2. Semantic versioning — breaking changes = major bump  │
│  3. Backward compatible for at least 2 major versions    │
│  4. Storybook for visual testing                         │
└──────────────────────────────────────────────────────────┘
```

```typescript
// @shopzone/ui-kit/src/components/Button.tsx
import React from 'react';
import styles from './Button.module.css';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}

function Button({ 
  variant = 'primary', 
  size = 'md', 
  loading, 
  icon, 
  children, 
  disabled, 
  className,
  ...rest 
}: ButtonProps) {
  return (
    <button
      className={`${styles.button} ${styles[variant]} ${styles[size]} ${className || ''}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && <span className={styles.spinner} />}
      {icon && !loading && <span className={styles.icon}>{icon}</span>}
      {children}
    </button>
  );
}

export { Button, ButtonProps };
```

### CSS Isolation Strategies

```typescript
// Strategy 1: CSS Modules (recommended for most cases)
// Each MFE uses CSS Modules — class names are automatically scoped
// catalog/src/ProductCard.module.css → .card_abc123

// Strategy 2: CSS-in-JS with namespace
// Emotion/styled-components with container-based scoping
import { CacheProvider } from '@emotion/react';
import createCache from '@emotion/cache';

function createMFEEmotionCache(mfeName: string) {
  return createCache({
    key: `mfe-${mfeName}`,  // prefixes all generated class names
    prepend: true,
  });
}

function CatalogMFE() {
  const cache = useMemo(() => createMFEEmotionCache('catalog'), []);
  
  return (
    <CacheProvider value={cache}>
      <CatalogApp />
    </CacheProvider>
  );
}

// Strategy 3: Shadow DOM (strongest isolation)
// Already covered in Web Components section

// Strategy 4: CSS Custom Properties for theming
// :root defines tokens, each MFE reads them
:root {
  --sz-color-primary: #2563eb;
  --sz-color-surface: #ffffff;
  --sz-spacing-md: 16px;
  --sz-radius-md: 8px;
  --sz-font-body: 'Inter', system-ui, sans-serif;
}

// MFE uses the tokens
.product-card {
  background: var(--sz-color-surface);
  padding: var(--sz-spacing-md);
  border-radius: var(--sz-radius-md);
  font-family: var(--sz-font-body);
}
```

---

## 11. Authentication & Authorization

```
┌────────────────────────────────────────────────────────────┐
│                   AUTH FLOW IN MICRO FRONTENDS              │
│                                                            │
│  1. User logs in via Auth MFE (or Auth Service)            │
│  2. JWT token stored in HttpOnly cookie (NOT localStorage) │
│  3. Shell reads token, provides auth context               │
│  4. Each MFE receives auth context via:                    │
│     - Props (Module Federation)                            │
│     - Custom Events (event bus)                            │
│     - Shared Store (Zustand/Redux)                         │
│     - window.__AUTH__ global (last resort)                 │
│                                                            │
│  CRITICAL: Token refresh handled by Shell ONLY             │
│  MFEs never directly manage tokens                         │
└────────────────────────────────────────────────────────────┘
```

```typescript
// shared/src/auth/authProvider.ts

interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  permissions: string[];
  token: string | null;
  
  login: (credentials: Credentials) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
}

// Shell creates and manages the auth store
const createAuthStore = () => createStore<AuthState>((set, get) => ({
  user: null,
  isAuthenticated: false,
  permissions: [],
  token: null,

  login: async (credentials) => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials),
      credentials: 'include', // HttpOnly cookie
    });
    
    const { user, token, permissions } = await response.json();
    
    set({ user, token, permissions, isAuthenticated: true });
    
    // Notify all MFEs
    window.dispatchEvent(new CustomEvent('auth:login', {
      detail: { user, permissions }
    }));
  },

  logout: () => {
    fetch('/api/auth/logout', { method: 'POST', credentials: 'include' });
    set({ user: null, token: null, permissions: [], isAuthenticated: false });
    window.dispatchEvent(new CustomEvent('auth:logout', { detail: {} }));
  },

  refreshToken: async () => {
    const response = await fetch('/api/auth/refresh', {
      method: 'POST',
      credentials: 'include',
    });
    
    if (!response.ok) {
      get().logout();
      return;
    }
    
    const { token } = await response.json();
    set({ token });
  },

  hasPermission: (permission: string) => {
    return get().permissions.includes(permission);
  },
}));

// Shared auth hook for MFEs
function useAuth() {
  const store = (window as any).__AUTH_STORE__;
  if (!store) throw new Error('Auth store not initialized. Is Shell running?');
  return useStore(store);
}

// Protected route wrapper
function ProtectedRoute({ children, permission }: { children: React.ReactNode; permission?: string }) {
  const { isAuthenticated, hasPermission } = useAuth();
  
  if (!isAuthenticated) {
    window.dispatchEvent(new CustomEvent('mfe:navigate', {
      detail: { path: '/login', options: { replace: true } }
    }));
    return null;
  }
  
  if (permission && !hasPermission(permission)) {
    return <div>You don't have permission to access this page.</div>;
  }
  
  return <>{children}</>;
}

export { createAuthStore, useAuth, ProtectedRoute };
```

### API Gateway Pattern for MFE Auth

```typescript
// Each MFE's API calls go through a shared HTTP client
// that auto-attaches auth headers

class MFEHttpClient {
  private baseURL: string;
  private mfeName: string;

  constructor(baseURL: string, mfeName: string) {
    this.baseURL = baseURL;
    this.mfeName = mfeName;
  }

  private getAuthHeaders(): Record<string, string> {
    const authStore = (window as any).__AUTH_STORE__;
    const token = authStore?.getState()?.token;
    
    return {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      'X-MFE-Source': this.mfeName,
      'X-Request-ID': crypto.randomUUID(),
    };
  }

  async fetch<T>(path: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(`${this.baseURL}${path}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...this.getAuthHeaders(),
        ...options.headers,
      },
      credentials: 'include',
    });

    if (response.status === 401) {
      // Try token refresh
      const authStore = (window as any).__AUTH_STORE__;
      await authStore?.getState()?.refreshToken();
      
      // Retry once
      const retryResponse = await fetch(`${this.baseURL}${path}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          ...this.getAuthHeaders(),
          ...options.headers,
        },
        credentials: 'include',
      });
      
      if (!retryResponse.ok) throw new HttpError(retryResponse);
      return retryResponse.json();
    }

    if (!response.ok) throw new HttpError(response);
    return response.json();
  }
}

// Usage in Catalog MFE
const catalogApi = new MFEHttpClient('/api/catalog', 'catalog');
const products = await catalogApi.fetch<Product[]>('/products?category=shoes');
```

---

## 12. Error Boundaries & Resilience

```tsx
// shared/src/components/MFEErrorBoundary.tsx

interface MFEErrorBoundaryProps {
  name: string;
  children: React.ReactNode;
  fallback?: React.ReactNode;
  onError?: (error: Error, mfeName: string) => void;
}

interface MFEErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorCount: number;
}

class MFEErrorBoundary extends React.Component<MFEErrorBoundaryProps, MFEErrorBoundaryState> {
  private retryTimeout: ReturnType<typeof setTimeout> | null = null;

  state: MFEErrorBoundaryState = {
    hasError: false,
    error: null,
    errorCount: 0,
  };

  static getDerivedStateFromError(error: Error): Partial<MFEErrorBoundaryState> {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    const { name, onError } = this.props;
    
    console.error(`[MFE:${name}] Error:`, error, errorInfo);
    
    // Report to monitoring
    window.dispatchEvent(new CustomEvent('mfe:error', {
      detail: {
        mfeName: name,
        error: error.message,
        stack: error.stack,
        componentStack: errorInfo.componentStack,
        timestamp: Date.now(),
      }
    }));
    
    onError?.(error, name);
    
    this.setState(prev => ({ errorCount: prev.errorCount + 1 }));
  }

  handleRetry = () => {
    this.setState({ hasError: false, error: null });
  };

  componentWillUnmount() {
    if (this.retryTimeout) clearTimeout(this.retryTimeout);
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="mfe-error-container" role="alert">
          <div className="mfe-error-content">
            <h3>This section is temporarily unavailable</h3>
            <p>The {this.props.name} module encountered an issue.</p>
            {this.state.errorCount < 3 && (
              <button onClick={this.handleRetry} className="mfe-retry-btn">
                Try Again
              </button>
            )}
            {this.state.errorCount >= 3 && (
              <p>Please refresh the page or try again later.</p>
            )}
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

// Timeout wrapper — don't wait forever for a MFE to load
function withLoadingTimeout(
  importFn: () => Promise<any>,
  timeoutMs: number = 10000,
  mfeName: string
): Promise<any> {
  return Promise.race([
    importFn(),
    new Promise((_, reject) => 
      setTimeout(
        () => reject(new Error(`MFE "${mfeName}" failed to load within ${timeoutMs}ms`)),
        timeoutMs
      )
    ),
  ]);
}

// Circuit breaker for MFE loading
class MFECircuitBreaker {
  private failures = new Map<string, { count: number; lastFailure: number }>();
  private threshold = 3;
  private resetTimeout = 60000; // 1 minute

  canLoad(mfeName: string): boolean {
    const record = this.failures.get(mfeName);
    if (!record) return true;
    
    if (record.count >= this.threshold) {
      if (Date.now() - record.lastFailure > this.resetTimeout) {
        this.failures.delete(mfeName);
        return true;
      }
      return false; // circuit is OPEN — don't even try
    }
    
    return true;
  }

  recordFailure(mfeName: string) {
    const record = this.failures.get(mfeName) || { count: 0, lastFailure: 0 };
    record.count++;
    record.lastFailure = Date.now();
    this.failures.set(mfeName, record);
  }

  recordSuccess(mfeName: string) {
    this.failures.delete(mfeName);
  }
}

export { MFEErrorBoundary, withLoadingTimeout, MFECircuitBreaker };
```

---

## 13. Testing Strategies

```
┌────────────────────────────────────────────────────────────┐
│                TESTING PYRAMID FOR MICRO FRONTENDS          │
│                                                            │
│                      ╱╲                                    │
│                     ╱  ╲         E2E Tests                 │
│                    ╱ E2E╲        (Cypress/Playwright)      │
│                   ╱──────╲       Test full user flows      │
│                  ╱        ╲      across multiple MFEs      │
│                 ╱ Contract ╲                               │
│                ╱   Tests    ╲    Contract Tests (Pact)     │
│               ╱──────────────╲   Verify MFE interfaces    │
│              ╱                ╲                            │
│             ╱  Integration     ╲  Integration Tests        │
│            ╱    Tests           ╲ Test MFE in isolation    │
│           ╱──────────────────────╲with mocked neighbors    │
│          ╱                        ╲                        │
│         ╱       Unit Tests         ╲ Unit Tests (Jest)     │
│        ╱────────────────────────────╲Component-level tests │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### Unit Testing a MFE Component

```tsx
// catalog/src/components/__tests__/ProductCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ProductCard } from '../ProductCard';
import { useCartStore } from '@shopzone/shared/stores/cartStore';

// Mock the shared store
jest.mock('@shopzone/shared/stores/cartStore');

const mockProduct = {
  id: 'prod-1',
  name: 'Wireless Headphones',
  price: 79.99,
  image: '/headphones.jpg',
  rating: 4.5,
};

describe('ProductCard', () => {
  beforeEach(() => {
    (useCartStore as jest.Mock).mockImplementation((selector) => {
      const state = { items: [], addItem: jest.fn() };
      return selector(state);
    });
  });

  it('renders product information correctly', () => {
    render(<ProductCard product={mockProduct} />);
    
    expect(screen.getByText('Wireless Headphones')).toBeInTheDocument();
    expect(screen.getByText('$79.99')).toBeInTheDocument();
    expect(screen.getByRole('img')).toHaveAttribute('alt', 'Wireless Headphones');
  });

  it('dispatches add-to-cart event when button clicked', () => {
    const addItem = jest.fn();
    (useCartStore as jest.Mock).mockImplementation((selector) => {
      return selector({ items: [], addItem });
    });

    render(<ProductCard product={mockProduct} />);
    
    fireEvent.click(screen.getByText('Add to Cart'));
    
    expect(addItem).toHaveBeenCalledWith({
      productId: 'prod-1',
      name: 'Wireless Headphones',
      price: 79.99,
      image: '/headphones.jpg',
    });
  });

  it('shows "In Cart" when product is already in cart', () => {
    (useCartStore as jest.Mock).mockImplementation((selector) => {
      return selector({
        items: [{ productId: 'prod-1', quantity: 2 }],
        addItem: jest.fn(),
      });
    });

    render(<ProductCard product={mockProduct} />);
    
    expect(screen.getByText(/In Cart \(2\)/)).toBeInTheDocument();
  });
});
```

### Contract Testing Between MFEs

```typescript
// catalog/src/__contracts__/ProductCard.contract.test.ts
// Ensures the Catalog MFE's exposed interface doesn't break

import { Pact } from '@pact-foundation/pact';

describe('Catalog MFE Contract', () => {
  // What the Catalog MFE exposes
  const exposedInterface = {
    ProductCard: {
      props: {
        product: {
          id: 'string',
          name: 'string',
          price: 'number',
          image: 'string',
        },
        onAddToCart: '(product: Product) => void',
      },
      events: {
        'add-to-cart': {
          productId: 'string',
          quantity: 'number',
          price: 'number',
        },
      },
    },
    ProductGrid: {
      props: {
        category: 'string?',
        searchQuery: 'string?',
        onProductClick: '(productId: string) => void',
      },
    },
  };

  it('ProductCard accepts required props', async () => {
    const { ProductCard } = await import('../components/ProductCard');
    
    // Verify the component renders without errors with the contract props
    const { container } = render(
      <ProductCard 
        product={{ 
          id: 'test-1', 
          name: 'Test Product', 
          price: 29.99, 
          image: '/test.jpg' 
        }} 
      />
    );
    
    expect(container.firstChild).toBeTruthy();
  });

  it('emits correct event shape on add-to-cart', async () => {
    const eventPayload = await new Promise((resolve) => {
      window.addEventListener('cart:item-added', ((e: CustomEvent) => {
        resolve(e.detail);
      }) as EventListener, { once: true });
      
      const { ProductCard } = require('../components/ProductCard');
      const { container } = render(
        <ProductCard product={{ id: 'p1', name: 'X', price: 10, image: '/x.jpg' }} />
      );
      fireEvent.click(screen.getByText('Add to Cart'));
    });
    
    // Verify the event shape matches the contract
    expect(eventPayload).toMatchObject({
      productId: expect.any(String),
      quantity: expect.any(Number),
      price: expect.any(Number),
    });
  });
});
```

### E2E Testing Across MFEs

```typescript
// e2e/tests/checkout-flow.spec.ts (Playwright)
import { test, expect } from '@playwright/test';

test.describe('Complete Checkout Flow', () => {
  test('user can browse, add to cart, and checkout', async ({ page }) => {
    // Step 1: Browse catalog (Catalog MFE)
    await page.goto('/products');
    await expect(page.locator('[data-testid="product-grid"]')).toBeVisible();
    
    // Step 2: Add item to cart (crosses MFE boundary)
    await page.click('[data-testid="product-card"]:first-child [data-testid="add-to-cart"]');
    
    // Verify cart badge updated (Shell MFE)
    await expect(page.locator('[data-testid="cart-badge"]')).toHaveText('1');
    
    // Step 3: Go to cart (Cart MFE)
    await page.click('[data-testid="cart-icon"]');
    await expect(page).toHaveURL('/cart');
    await expect(page.locator('[data-testid="cart-item"]')).toHaveCount(1);
    
    // Step 4: Proceed to checkout (Checkout MFE)
    await page.click('[data-testid="checkout-btn"]');
    await expect(page).toHaveURL('/checkout/shipping');
    
    // Fill shipping form
    await page.fill('[data-testid="shipping-name"]', 'John Doe');
    await page.fill('[data-testid="shipping-address"]', '123 Main St');
    await page.fill('[data-testid="shipping-city"]', 'New York');
    await page.click('[data-testid="continue-to-payment"]');
    
    // Step 5: Payment (still Checkout MFE, different internal route)
    await expect(page).toHaveURL('/checkout/payment');
    await page.fill('[data-testid="card-number"]', '4242424242424242');
    await page.click('[data-testid="place-order"]');
    
    // Step 6: Confirmation
    await expect(page).toHaveURL('/checkout/confirmation');
    await expect(page.locator('[data-testid="order-success"]')).toBeVisible();
  });
});
```

---

## 14. CI/CD & Independent Deployments

### Pipeline Architecture

```
┌────────────────────────────────────────────────────────────────┐
│              INDEPENDENT DEPLOYMENT PIPELINE                    │
│                                                                │
│  Team Catalog pushes to main                                   │
│       │                                                        │
│       ▼                                                        │
│  ┌──────────────────┐                                          │
│  │ 1. Lint + Types  │ ← eslint, tsc --noEmit                  │
│  └────────┬─────────┘                                          │
│           ▼                                                    │
│  ┌──────────────────┐                                          │
│  │ 2. Unit Tests    │ ← jest --coverage (>80%)                 │
│  └────────┬─────────┘                                          │
│           ▼                                                    │
│  ┌──────────────────┐                                          │
│  │ 3. Contract Tests│ ← verify exposed interface unchanged     │
│  └────────┬─────────┘                                          │
│           ▼                                                    │
│  ┌──────────────────┐                                          │
│  │ 4. Build         │ ← webpack build, outputs remoteEntry.js  │
│  └────────┬─────────┘                                          │
│           ▼                                                    │
│  ┌──────────────────┐                                          │
│  │ 5. Deploy to CDN │ ← S3 + CloudFront / Vercel              │
│  │    (Canary)      │    10% traffic                           │
│  └────────┬─────────┘                                          │
│           ▼                                                    │
│  ┌──────────────────┐                                          │
│  │ 6. Smoke Tests   │ ← Playwright against canary              │
│  └────────┬─────────┘                                          │
│           ▼                                                    │
│  ┌──────────────────┐                                          │
│  │ 7. Full Rollout  │ ← 100% traffic                           │
│  └──────────────────┘                                          │
│                                                                │
│  ROLLBACK: Repoint CDN to previous version (< 30 seconds)     │
└────────────────────────────────────────────────────────────────┘
```

### GitHub Actions Pipeline

```yaml
# catalog-app/.github/workflows/deploy.yml
name: Deploy Catalog MFE

on:
  push:
    branches: [main]
    paths:
      - 'catalog-app/**'

env:
  MFE_NAME: catalog
  AWS_REGION: us-east-1
  S3_BUCKET: shopzone-mfe-assets
  CLOUDFRONT_ID: E1234ABCDEF

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
          cache: 'npm'
          cache-dependency-path: catalog-app/package-lock.json
      
      - name: Install dependencies
        working-directory: catalog-app
        run: npm ci
      
      - name: Type check
        working-directory: catalog-app
        run: npx tsc --noEmit
      
      - name: Lint
        working-directory: catalog-app
        run: npx eslint src/ --max-warnings 0
      
      - name: Unit tests
        working-directory: catalog-app
        run: npm test -- --coverage --watchAll=false
      
      - name: Contract tests
        working-directory: catalog-app
        run: npm run test:contracts

  build:
    needs: test
    runs-on: ubuntu-latest
    outputs:
      version: ${{ steps.version.outputs.version }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      
      - run: npm ci
        working-directory: catalog-app
      
      - name: Generate version
        id: version
        run: echo "version=$(git rev-parse --short HEAD)-$(date +%s)" >> $GITHUB_OUTPUT
      
      - name: Build
        working-directory: catalog-app
        run: npm run build
        env:
          PUBLIC_PATH: https://cdn.shopzone.com/mfe/catalog/${{ steps.version.outputs.version }}/
      
      - uses: actions/upload-artifact@v4
        with:
          name: catalog-build
          path: catalog-app/dist/

  deploy-canary:
    needs: build
    runs-on: ubuntu-latest
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/mfe-deploy
          aws-region: ${{ env.AWS_REGION }}
      
      - uses: actions/download-artifact@v4
        with:
          name: catalog-build
          path: dist/
      
      - name: Upload to S3
        run: |
          aws s3 sync dist/ s3://${{ env.S3_BUCKET }}/catalog/${{ needs.build.outputs.version }}/ \
            --cache-control "public, max-age=31536000, immutable"
      
      - name: Update canary config
        run: |
          # Update the MFE registry to point canary to new version
          aws ssm put-parameter \
            --name "/shopzone/mfe/catalog/canary-version" \
            --value "${{ needs.build.outputs.version }}" \
            --type String \
            --overwrite

  smoke-test:
    needs: deploy-canary
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Run smoke tests
        run: |
          npx playwright test e2e/smoke/catalog.spec.ts
        env:
          BASE_URL: https://canary.shopzone.com

  deploy-production:
    needs: [smoke-test, build]
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789:role/mfe-deploy
          aws-region: ${{ env.AWS_REGION }}
      
      - name: Update production config
        run: |
          aws ssm put-parameter \
            --name "/shopzone/mfe/catalog/production-version" \
            --value "${{ needs.build.outputs.version }}" \
            --type String \
            --overwrite
      
      - name: Invalidate CloudFront
        run: |
          aws cloudfront create-invalidation \
            --distribution-id ${{ env.CLOUDFRONT_ID }} \
            --paths "/mfe/catalog/remoteEntry.js"
```

### Dynamic MFE Registry Service

```typescript
// infra/mfe-registry/src/registry.ts
// API that tells the Shell where each MFE version lives

interface MFEVersion {
  name: string;
  version: string;
  url: string;
  integrity: string; // SRI hash for security
  deployedAt: string;
}

interface RegistryResponse {
  remotes: Record<string, {
    url: string;
    integrity: string;
  }>;
}

// GET /api/mfe-registry
async function getRegistry(request: Request): Promise<Response> {
  const isCanary = request.headers.get('x-canary') === 'true' 
    || Math.random() < 0.1; // 10% canary traffic
  
  const versionSuffix = isCanary ? 'canary-version' : 'production-version';
  
  const mfes = ['catalog', 'cart', 'checkout', 'profile'];
  const registry: RegistryResponse = { remotes: {} };
  
  for (const mfe of mfes) {
    const version = await getParameter(`/shopzone/mfe/${mfe}/${versionSuffix}`);
    
    registry.remotes[mfe] = {
      url: `https://cdn.shopzone.com/mfe/${mfe}/${version}/remoteEntry.js`,
      integrity: await getParameter(`/shopzone/mfe/${mfe}/${version}/integrity`),
    };
  }
  
  return new Response(JSON.stringify(registry), {
    headers: {
      'Content-Type': 'application/json',
      'Cache-Control': 'public, max-age=60', // short TTL for fast rollbacks
    },
  });
}
```

---

## 15. Performance Optimization

### Loading Strategy

```
┌─────────────────────────────────────────────────────────────┐
│              MFE LOADING OPTIMIZATION                        │
│                                                              │
│  PROBLEM: Loading 5 MFEs = 5 remoteEntry.js + their chunks  │
│  → Waterfall of network requests                             │
│  → Slow initial page load                                    │
│                                                              │
│  SOLUTIONS:                                                  │
│                                                              │
│  1. PRELOAD critical MFEs                                    │
│     <link rel="preload" href="catalog/remoteEntry.js" />     │
│                                                              │
│  2. PREFETCH likely-next MFEs                                │
│     User on /products → prefetch /cart remoteEntry            │
│                                                              │
│  3. SHARED CHUNKS                                            │
│     React, React-DOM, design system → loaded once             │
│     eager: true in host                                       │
│                                                              │
│  4. SKELETON UI                                              │
│     Show layout skeleton while MFE loads                     │
│                                                              │
│  5. SERVICE WORKER CACHING                                   │
│     Cache remoteEntry.js with network-first strategy          │
│     Cache chunks with cache-first (immutable URLs)            │
└─────────────────────────────────────────────────────────────┘
```

```typescript
// shell-app/src/utils/prefetch.ts

const prefetchCache = new Set<string>();

function prefetchMFE(mfeName: string) {
  const registry = (window as any).__MFE_REGISTRY__;
  const config = registry?.remotes?.[mfeName];
  
  if (!config || prefetchCache.has(mfeName)) return;
  
  const link = document.createElement('link');
  link.rel = 'prefetch';
  link.href = config.url;
  link.as = 'script';
  document.head.appendChild(link);
  
  prefetchCache.add(mfeName);
}

// Predictive prefetching based on user behavior
function setupPredictivePrefetch() {
  const prefetchMap: Record<string, string[]> = {
    '/products': ['cart'],          // browsing → likely to add to cart
    '/cart': ['checkout'],          // in cart → likely to checkout
    '/products/:id': ['cart'],     // viewing product → likely to add to cart
  };
  
  // Prefetch on route change
  window.addEventListener('popstate', () => {
    const path = window.location.pathname;
    
    for (const [pattern, mfes] of Object.entries(prefetchMap)) {
      if (matchPath(path, pattern)) {
        mfes.forEach(prefetchMFE);
      }
    }
  });
  
  // Prefetch on hover over navigation links
  document.addEventListener('mouseover', (e) => {
    const link = (e.target as HTMLElement).closest('a[data-prefetch-mfe]');
    if (link) {
      const mfeName = link.getAttribute('data-prefetch-mfe')!;
      prefetchMFE(mfeName);
    }
  }, { passive: true });
}

// Service Worker for MFE caching
// sw.js
self.addEventListener('fetch', (event: FetchEvent) => {
  const url = new URL(event.request.url);
  
  // remoteEntry.js — network-first (always get latest)
  if (url.pathname.endsWith('remoteEntry.js')) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const cache = await caches.open('mfe-entries');
          cache.put(event.request, response.clone());
          return response;
        })
        .catch(() => caches.match(event.request))
    );
    return;
  }
  
  // Versioned chunks — cache-first (immutable)
  if (url.pathname.includes('/mfe/') && url.pathname.match(/\.[a-f0-9]{8}\./)) {
    event.respondWith(
      caches.match(event.request)
        .then(cached => cached || fetch(event.request).then(response => {
          const cache = await caches.open('mfe-chunks');
          cache.put(event.request, response.clone());
          return response;
        }))
    );
  }
});
```

---

## 16. Monitoring & Observability

```typescript
// shared/src/monitoring/mfeTracker.ts

interface MFEMetrics {
  loadTime: number;
  renderTime: number;
  errors: number;
  mfeName: string;
  version: string;
}

class MFEPerformanceTracker {
  private metrics = new Map<string, MFEMetrics>();

  trackLoad(mfeName: string, startTime: number) {
    const loadTime = performance.now() - startTime;
    
    this.updateMetrics(mfeName, { loadTime });
    
    // Send to analytics
    this.report('mfe.load', {
      mfe: mfeName,
      duration_ms: loadTime,
      connection: (navigator as any).connection?.effectiveType,
    });
  }

  trackRender(mfeName: string, renderTime: number) {
    this.updateMetrics(mfeName, { renderTime });
    
    this.report('mfe.render', {
      mfe: mfeName,
      duration_ms: renderTime,
    });
  }

  trackError(mfeName: string, error: Error) {
    this.report('mfe.error', {
      mfe: mfeName,
      error: error.message,
      stack: error.stack?.slice(0, 500),
    });
  }

  // Web Vitals per MFE
  trackWebVitals(mfeName: string) {
    if (!('PerformanceObserver' in window)) return;
    
    // Largest Contentful Paint
    new PerformanceObserver((entryList) => {
      const entries = entryList.getEntries();
      const lastEntry = entries[entries.length - 1] as any;
      
      this.report('mfe.lcp', {
        mfe: mfeName,
        value_ms: lastEntry.startTime,
      });
    }).observe({ type: 'largest-contentful-paint', buffered: true });
    
    // Cumulative Layout Shift
    let clsValue = 0;
    new PerformanceObserver((entryList) => {
      for (const entry of entryList.getEntries() as any[]) {
        if (!entry.hadRecentInput) {
          clsValue += entry.value;
        }
      }
      this.report('mfe.cls', { mfe: mfeName, value: clsValue });
    }).observe({ type: 'layout-shift', buffered: true });
  }

  private report(event: string, data: Record<string, any>) {
    // Send to your analytics service (DataDog, New Relic, etc.)
    if ((window as any).__ANALYTICS__) {
      (window as any).__ANALYTICS__.track(event, data);
    }
    
    // Also available via Performance API
    performance.mark(`${event}:${data.mfe}`, { detail: data });
  }

  private updateMetrics(mfeName: string, partial: Partial<MFEMetrics>) {
    const existing = this.metrics.get(mfeName) || {
      loadTime: 0, renderTime: 0, errors: 0, mfeName, version: '',
    };
    this.metrics.set(mfeName, { ...existing, ...partial });
  }
}

export const mfeTracker = new MFEPerformanceTracker();
```

---

## 17. Migration Strategy — Monolith to Micro Frontends

```
┌────────────────────────────────────────────────────────────────────┐
│            STRANGLER FIG PATTERN — INCREMENTAL MIGRATION          │
│                                                                    │
│  Phase 1: SHELL WRAPPER (Week 1-2)                                │
│  ┌──────────────────────────────────────────────────────┐          │
│  │  New Shell App                                       │          │
│  │  ┌────────────────────────────────────────────────┐  │          │
│  │  │  iframe: OLD MONOLITH (entire legacy app)      │  │          │
│  │  └────────────────────────────────────────────────┘  │          │
│  └──────────────────────────────────────────────────────┘          │
│                                                                    │
│  Phase 2: EXTRACT FIRST MFE (Week 3-6)                            │
│  ┌──────────────────────────────────────────────────────┐          │
│  │  Shell App                                           │          │
│  │  ┌─────────────┐  ┌──────────────────────────────┐  │          │
│  │  │ New Header  │  │ iframe: MONOLITH (minus      │  │          │
│  │  │ MFE (React) │  │ header)                      │  │          │
│  │  └─────────────┘  └──────────────────────────────┘  │          │
│  └──────────────────────────────────────────────────────┘          │
│                                                                    │
│  Phase 3: EXTRACT MORE (Week 7-16)                                │
│  ┌──────────────────────────────────────────────────────┐          │
│  │  Shell App                                           │          │
│  │  ┌─────────┐                                        │          │
│  │  │ Header  │                                        │          │
│  │  ├─────────┤  ┌──────────┐  ┌────────────────────┐  │          │
│  │  │ Catalog │  │   Cart   │  │ iframe: MONOLITH   │  │          │
│  │  │ MFE     │  │   MFE    │  │ (checkout + profile│  │          │
│  │  │         │  │          │  │  still in legacy)  │  │          │
│  │  └─────────┘  └──────────┘  └────────────────────┘  │          │
│  └──────────────────────────────────────────────────────┘          │
│                                                                    │
│  Phase 4: COMPLETE (Week 17-24)                                   │
│  ┌──────────────────────────────────────────────────────┐          │
│  │  Shell App                                           │          │
│  │  ┌────────┬─────────┬────────┬──────────┬────────┐  │          │
│  │  │Header  │ Catalog │  Cart  │ Checkout │Profile │  │          │
│  │  │ MFE    │  MFE    │  MFE   │   MFE    │  MFE   │  │          │
│  │  └────────┴─────────┴────────┴──────────┴────────┘  │          │
│  │                                                      │          │
│  │  ⚰️  MONOLITH DECOMMISSIONED                         │          │
│  └──────────────────────────────────────────────────────┘          │
└────────────────────────────────────────────────────────────────────┘
```

### Migration Decision Framework

```
FOR EACH MODULE IN MONOLITH, ASK:

1. TEAM OWNERSHIP
   → Does a distinct team own this feature?
   → Will they benefit from independent deployment?

2. CHANGE FREQUENCY
   → How often does this part change?
   → High change = good MFE candidate (reduces deploy risk)

3. COUPLING
   → How tightly coupled is this to other modules?
   → LOW coupling = easy to extract
   → HIGH coupling = extract LAST (or refactor first)

4. COMPLEXITY
   → How complex is the module?
   → SIMPLE modules = extract first (build confidence)
   → COMPLEX modules = extract after team has experience

RECOMMENDED EXTRACTION ORDER:
  1. Header/Navigation (simple, owned by platform team)
  2. Catalog/Search (high change frequency, clear boundaries)
  3. Cart (moderate coupling, distinct domain)
  4. Checkout (complex but high business value for independence)
  5. Profile/Account (low change frequency, extract last)
```

---

## 18. Project: ShopZone E-Commerce Platform

### Full Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                     SHOPZONE — PRODUCTION ARCHITECTURE                 │
│                                                                        │
│  ┌──────────────────────────────────────────────────────────┐          │
│  │                      CDN (CloudFront)                     │          │
│  │   Serves all static assets: JS bundles, CSS, images       │          │
│  └──────────────┬───────────────────────────────┬───────────┘          │
│                 │                               │                      │
│  ┌──────────────▼───────────────┐  ┌───────────▼───────────┐          │
│  │   MFE Registry Service       │  │  Feature Flag Service  │          │
│  │   (which version of each MFE) │  │  (LaunchDarkly/Split)  │          │
│  └──────────────┬───────────────┘  └───────────┬───────────┘          │
│                 │                               │                      │
│  ┌──────────────▼───────────────────────────────▼───────────┐          │
│  │                    SHELL APPLICATION                      │          │
│  │                                                           │          │
│  │  ┌─────────┐  ┌──────────┐  ┌──────┐  ┌──────────────┐  │          │
│  │  │ Navbar  │  │ Auth     │  │ Toast│  │ Feature      │  │          │
│  │  │ + Search│  │ Provider │  │ Queue│  │ Flags        │  │          │
│  │  └─────────┘  └──────────┘  └──────┘  └──────────────┘  │          │
│  │                                                           │          │
│  │  ┌─────────────────────────────────────────────────────┐  │          │
│  │  │                   ROUTER                             │  │          │
│  │  │                                                     │  │          │
│  │  │  /products/*  → Catalog MFE (React, Team Alpha)     │  │          │
│  │  │  /cart        → Cart MFE (React, Team Beta)         │  │          │
│  │  │  /checkout/*  → Checkout MFE (React, Team Gamma)    │  │          │
│  │  │  /profile/*   → Profile MFE (React, Team Delta)     │  │          │
│  │  │  /admin/*     → Admin MFE (React, Team Platform)    │  │          │
│  │  └─────────────────────────────────────────────────────┘  │          │
│  └───────────────────────────────────────────────────────────┘          │
│                                                                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │
│  │  Catalog API │  │  Cart API   │  │ Checkout API│                    │
│  │  (Node.js)   │  │  (Go)       │  │ (Node.js)   │                    │
│  │  PostgreSQL  │  │  Redis      │  │ Stripe      │                    │
│  └─────────────┘  └─────────────┘  └─────────────┘                    │
└────────────────────────────────────────────────────────────────────────┘
```

### Project File Structure

```
shopzone/
├── shell-app/                    # Host application
│   ├── src/
│   │   ├── index.tsx             # Entry point (bootstrap)
│   │   ├── App.tsx               # Main app with router
│   │   ├── bootstrap.tsx         # Async bootstrap for Module Federation
│   │   ├── components/
│   │   │   ├── AppShell.tsx      # Layout: header, sidebar, main
│   │   │   ├── Navbar.tsx        # Navigation with MiniCart
│   │   │   ├── ErrorBoundary.tsx # MFE error boundary
│   │   │   └── PageSkeleton.tsx  # Loading skeleton
│   │   └── utils/
│   │       ├── loadRemote.ts     # Dynamic remote loader
│   │       ├── prefetch.ts       # Predictive prefetching
│   │       └── mfeRegistry.ts    # Registry client
│   ├── webpack.config.ts
│   ├── package.json
│   └── tsconfig.json
│
├── catalog-app/                  # Team Alpha
│   ├── src/
│   │   ├── index.tsx
│   │   ├── CatalogApp.tsx
│   │   ├── components/
│   │   │   ├── ProductCard.tsx
│   │   │   ├── ProductGrid.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   └── CategoryNav.tsx
│   │   ├── pages/
│   │   │   ├── ProductDetail.tsx
│   │   │   └── SearchResults.tsx
│   │   └── api/
│   │       └── catalogApi.ts
│   ├── webpack.config.ts
│   └── package.json
│
├── cart-app/                     # Team Beta
│   ├── src/
│   │   ├── CartApp.tsx
│   │   ├── components/
│   │   │   ├── CartItem.tsx
│   │   │   ├── CartSummary.tsx
│   │   │   └── MiniCart.tsx
│   │   └── stores/
│   │       └── cartStore.ts
│   ├── webpack.config.ts
│   └── package.json
│
├── checkout-app/                 # Team Gamma
│   ├── src/
│   │   ├── CheckoutApp.tsx
│   │   ├── steps/
│   │   │   ├── ShippingStep.tsx
│   │   │   ├── PaymentStep.tsx
│   │   │   └── ConfirmationStep.tsx
│   │   └── api/
│   │       └── checkoutApi.ts
│   ├── webpack.config.ts
│   └── package.json
│
├── shared/                       # Shared packages
│   ├── ui-kit/                   # @shopzone/ui-kit
│   │   ├── src/
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── index.ts
│   │   └── package.json
│   ├── events/                   # @shopzone/events
│   │   ├── src/
│   │   │   ├── eventBus.ts
│   │   │   └── types.ts
│   │   └── package.json
│   └── auth/                     # @shopzone/auth
│       ├── src/
│       │   ├── authStore.ts
│       │   ├── ProtectedRoute.tsx
│       │   └── useAuth.ts
│       └── package.json
│
├── e2e/                          # Cross-MFE E2E tests
│   ├── tests/
│   │   ├── checkout-flow.spec.ts
│   │   ├── search-and-browse.spec.ts
│   │   └── auth-flow.spec.ts
│   └── playwright.config.ts
│
├── infra/                        # Infrastructure
│   ├── docker-compose.yml        # Local development
│   ├── mfe-registry/             # Registry service
│   └── nginx/                    # Local reverse proxy
│       └── nginx.conf
│
└── docs/
    ├── architecture.md
    ├── adding-new-mfe.md
    └── deployment.md
```

See the project files in this folder for complete, runnable implementations of each component.

---

## 19. Interview Questions

### Conceptual Questions

**Q1: What is the difference between micro frontends and component libraries?**

```
Component Library:
  → Shared, reusable UI components (Button, Modal, Card)
  → Published as NPM package
  → No business logic, no data fetching
  → Used BY micro frontends, not a micro frontend itself

Micro Frontend:
  → Complete, autonomous feature slice (Catalog, Cart, Checkout)
  → Has its own API calls, state, routing
  → Independently deployed
  → Owned by a specific team

ANALOGY:
  Component Library = bricks and windows (building materials)
  Micro Frontend = a room in a house (complete functional unit)
```

**Q2: How do you handle CSS conflicts between micro frontends?**

```
STRATEGIES (ranked by isolation strength):

1. Shadow DOM (Web Components)
   → Strongest isolation
   → Styles truly encapsulated
   → Cannot use global theme easily

2. CSS Modules
   → Class names auto-scoped: .button → .button_abc123
   → Works with most frameworks
   → No runtime overhead

3. CSS-in-JS with prefix
   → Emotion/styled-components with key prefix
   → Scoped at runtime
   → Slight performance cost

4. BEM + MFE prefix convention
   → .catalog__product-card, .cart__item-row
   → No tooling needed
   → Relies on developer discipline

5. Tailwind with prefix
   → prefix: 'catalog-' in tailwind.config
   → Utility classes are naturally isolated
   → May increase bundle size

RECOMMENDATION:
  CSS Modules for most teams.
  Shadow DOM if you need framework-agnostic components.
  CSS Custom Properties for shared theming across all approaches.
```

**Q3: How do you prevent a single MFE failure from crashing the whole app?**

```
1. ERROR BOUNDARIES — React ErrorBoundary around each MFE
2. LOADING TIMEOUT — Don't wait forever; show fallback after 10s
3. CIRCUIT BREAKER — After 3 failures, stop trying for 60s
4. FALLBACK UI — Show degraded experience, not a blank page
5. INDEPENDENT BUNDLES — MFE code is in separate chunks
6. GRACEFUL DEGRADATION — If cart MFE fails, catalog still works
7. MONITORING — Track MFE health, alert on error spikes
```

**Q4: Module Federation vs Single-SPA — when to use which?**

```
MODULE FEDERATION:
  ✅ Same framework across teams (React + React)
  ✅ Fine-grained sharing (share individual components)
  ✅ Webpack ecosystem
  ✅ Better DX with TypeScript
  ✅ Performance (shared chunks, no duplication)
  ❌ Webpack-specific (though Vite/Rspack now support it)

SINGLE-SPA:
  ✅ Different frameworks (React + Vue + Angular)
  ✅ Framework-agnostic lifecycle management
  ✅ Mature ecosystem with layout engine
  ✅ Import maps for dependency management
  ❌ Coarser granularity (whole app, not individual components)
  ❌ More boilerplate per MFE

COMBINE BOTH:
  → Single-SPA for orchestration (lifecycle, routing)
  → Module Federation for code sharing within same-framework MFEs
```

**Q5: How do you handle shared state across micro frontends?**

```
OPTIONS (from loosely to tightly coupled):

1. URL STATE (query params, path params)
   → Zero coupling
   → Works: /products?category=shoes
   → Best for: navigation state, filters

2. CUSTOM EVENTS (pub/sub)
   → Loose coupling
   → window.dispatchEvent / addEventListener
   → Best for: notifications, "something happened" signals

3. SHARED STORE (Zustand/Redux singleton on window)
   → Medium coupling
   → Shared via Module Federation
   → Best for: cart state, auth state

4. SHARED API/BFF (Backend for Frontend)
   → Backend-mediated
   → Each MFE reads from same API
   → Best for: user data, product data

ANTI-PATTERNS:
  ❌ localStorage for cross-MFE communication (no reactivity)
  ❌ Direct imports between MFEs (creates coupling)
  ❌ Global Redux store shared by all MFEs (monolith in disguise)
```

**Q6: Design a micro frontend architecture for a banking dashboard.**

```
TEAMS AND MFEs:

1. Shell (Platform Team)
   → Authentication, routing, nav, notifications
   → Security headers, CSP policy

2. Accounts MFE (Accounts Team)
   → Account list, balances, transactions
   → /accounts, /accounts/:id

3. Payments MFE (Payments Team)
   → Send money, pay bills, scheduled payments
   → /payments/*

4. Cards MFE (Cards Team)
   → Credit/debit card management, limits, statements
   → /cards/*

5. Investments MFE (Wealth Team)
   → Portfolio, stocks, mutual funds
   → /investments/*

SECURITY CONSIDERATIONS:
  → HttpOnly cookies for auth (never localStorage)
  → Content Security Policy headers
  → Subresource Integrity (SRI) on all MFE scripts
  → Sandboxed iframes for third-party widgets
  → CORS locked to specific origins
  → No cross-MFE data sharing for PII

ARCHITECTURE:
  → Module Federation for same-framework MFEs
  → BFF per team (no direct DB access from frontend)
  → Server-side rendering for initial load (SEO not critical but security is)
  → Feature flags per MFE (gradual rollout)
```

**Q7: How do you handle versioning and backward compatibility?**

```
RULES:

1. SEMVER for exposed interfaces
   → Breaking change to component props = MAJOR bump
   → New optional prop = MINOR bump
   → Bug fix = PATCH

2. CONSUMER-DRIVEN CONTRACTS
   → Each consuming MFE defines what it expects
   → Provider MFE runs contract tests before deploy
   → Deploy blocked if contracts break

3. DEPRECATION POLICY
   → Deprecated APIs supported for 2 major versions
   → Console warnings on deprecated usage
   → Migration guide published

4. BACKWARD COMPATIBLE EVENTS
   → New fields are additive only
   → Old fields never removed, only deprecated
   → Event versioning: cart:item-added:v2

5. SHARED DEPENDENCY VERSIONS
   → Host controls singleton version (React, Router)
   → requiredVersion uses caret (^18.0.0) for flexibility
   → strictVersion: false to prevent crashes
```

**Q8: What metrics do you track for micro frontend health?**

```
PERFORMANCE METRICS:
  → MFE Load Time (time to download + execute remoteEntry.js)
  → MFE Render Time (time from mount to first paint)
  → Web Vitals per MFE (LCP, CLS, INP)
  → Bundle Size per MFE
  → Shared Dependency Cache Hit Rate

RELIABILITY METRICS:
  → MFE Load Failure Rate
  → Error Boundary Trigger Rate
  → Circuit Breaker Open Count
  → Fallback Render Rate

DEPLOYMENT METRICS:
  → Deploy Frequency per Team
  → Lead Time (commit to production)
  → Change Failure Rate
  → Mean Time to Recovery (rollback speed)

DEVELOPER EXPERIENCE:
  → Local Dev Startup Time
  → Build Time per MFE
  → Test Execution Time
  → Time to Onboard New Developer
```

---

## Quick Reference Cheat Sheet

```
┌────────────────────────────────────────────────────────────────────┐
│                    MICRO FRONTEND CHEAT SHEET                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  MODULE FEDERATION:                                                │
│    Host:   remotes: { cart: 'cart@url/remoteEntry.js' }            │
│    Remote: exposes: { './CartPage': './src/CartPage' }             │
│    Shared: { react: { singleton: true, eager: true } }            │
│                                                                    │
│  COMMUNICATION:                                                    │
│    Events:  window.dispatchEvent(new CustomEvent('x', {detail}))  │
│    Store:   Zustand singleton on window.__STORE__                  │
│    Props:   Pass directly via Module Federation                    │
│                                                                    │
│  CSS ISOLATION:                                                    │
│    CSS Modules > CSS-in-JS prefix > Shadow DOM > BEM convention   │
│                                                                    │
│  ROUTING:                                                          │
│    Shell: BrowserRouter → top-level routes                         │
│    MFE:   MemoryRouter → internal routes, synced via events       │
│                                                                    │
│  DEPLOYMENT:                                                       │
│    Each MFE → own CI/CD → own S3/CDN path → own version           │
│    Shell loads remoteEntry.js URLs from registry service           │
│    Rollback = update registry to point to previous version         │
│                                                                    │
│  TESTING:                                                          │
│    Unit: Jest + RTL per MFE                                        │
│    Contract: Pact — verify exposed interface stability             │
│    E2E: Playwright — test cross-MFE flows                          │
│                                                                    │
│  GOLDEN RULES:                                                     │
│    1. Each MFE = one team = one deploy pipeline                    │
│    2. Share UI kit, NEVER share business logic                     │
│    3. Communicate via events/store, NEVER import directly          │
│    4. Every MFE must work standalone (dev + test)                  │
│    5. One MFE crashing must NOT crash others                       │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```
