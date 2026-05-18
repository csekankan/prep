# Monorepo Architecture — Deep Dive

> How Google manages 2 billion lines in one repo, why Meta and Uber agree,
> and how to set up your own. Every concept, tool, and pattern explained.

---

## Table of Contents

1. [What Is a Monorepo (And What It Is NOT)](#1-what-is-a-monorepo)
2. [Monorepo vs Polyrepo — The Real Trade-offs](#2-monorepo-vs-polyrepo)
3. [Who Uses Monorepos — Industry Map](#3-industry)
4. [How Google's Monorepo Works — 2 Billion Lines](#4-google)
5. [The Dependency Graph — The Core Concept](#5-dependency-graph)
6. [Monorepo Structure — How to Organize Files](#6-structure)
7. [Package Managers — npm vs Yarn vs pnpm](#7-package-managers)
8. [Workspace Protocol — Internal Dependencies](#8-workspace-protocol)
9. [Task Orchestration — Build, Test, Lint in Order](#9-task-orchestration)
10. [Affected Detection — Only Build What Changed](#10-affected)
11. [Caching — Local and Remote](#11-caching)
12. [Tools — Turborepo vs Nx vs Bazel vs Moon](#12-tools)
13. [Turborepo — Setup and Deep Dive](#13-turborepo)
14. [Nx — Setup and Deep Dive](#14-nx)
15. [Bazel — When and Why](#15-bazel)
16. [CI/CD for Monorepos](#16-cicd)
17. [Code Ownership — CODEOWNERS and Boundaries](#17-ownership)
18. [Versioning and Publishing — Changesets](#18-versioning)
19. [Shared Configuration — One Source of Truth](#19-shared-config)
20. [Deployment Strategies — Independent Deploys from One Repo](#20-deployment)
21. [Git Performance at Scale](#21-git-performance)
22. [Common Mistakes](#22-mistakes)
23. [Decision Framework — Should You Use a Monorepo?](#23-decision)
24. [Full Setup — From Zero to Production Monorepo](#24-full-setup)

---

## 1. What Is a Monorepo

### Definition

```
Monorepo = MULTIPLE projects in ONE repository.

What it IS:
  One git repo containing:
    - Frontend app
    - Backend API
    - Shared libraries
    - Infrastructure code
    - Mobile app
  All in one place. One git log. One CI pipeline. One set of tools.

What it is NOT:
  ✗ A monolith (code can be independently deployable)
  ✗ One big app (it's many apps that share a repo)
  ✗ Copy-pasting code (it's structured sharing with dependency graph)

Monorepo ≠ Monolith:
  Monolith:  one deployable unit, tightly coupled code
  Monorepo:  many deployable units, shared repo, explicit boundaries
```

### Visual

```
POLYREPO (separate repos):

  repo: frontend          repo: backend           repo: shared-utils
  ├── package.json        ├── package.json        ├── package.json
  ├── src/                ├── src/                ├── src/
  └── .github/            └── .github/            └── .github/

  3 repos, 3 CI configs, 3 sets of tooling
  Publishing shared-utils → npm → frontend installs → test → deploy
  Cross-repo change = 3 PRs, 3 reviews, 3 deploys

MONOREPO (single repo):

  repo: my-company
  ├── apps/
  │   ├── frontend/       (deployable)
  │   └── backend/        (deployable)
  ├── packages/
  │   ├── shared-utils/   (library)
  │   ├── ui-components/  (library)
  │   └── config/         (shared config)
  ├── package.json        (root workspace)
  ├── turbo.json          (task orchestration)
  └── .github/
      └── CODEOWNERS      (who owns what)

  1 repo, 1 CI config, 1 set of tooling
  Cross-project change = 1 PR, 1 review, atomic deploy
```

---

## 2. Monorepo vs Polyrepo

### The Trade-offs

```
                        MONOREPO                    POLYREPO
                        ────────                    ────────
Code sharing            Trivial (import directly)   Publish to registry, version, install
Cross-project changes   One PR, one commit          Multiple PRs, coordinate merges
Dependency management   Single lockfile, unified     Each repo has own versions
Tooling consistency     One config for all           Duplicated configs per repo
Refactoring at scale    Global find-and-replace      Repo by repo, hope nothing breaks
Onboarding              Clone once, see everything   Clone N repos, configure each
CI complexity           Need smart tooling           Simple per-repo CI
Git performance         Degrades at scale            Always fast (small repos)
Code ownership          Needs CODEOWNERS enforcement Natural (repo = team)
Access control          Complex (same repo)          Simple (repo-level permissions)
Autonomy                Teams share constraints      Teams pick own tools/versions
Deploy independence     Must be explicitly designed   Natural (separate repos)
```

### When Monorepo Wins

```
✓ Your projects share significant code (UI components, utils, types)
✓ You make frequent cross-project changes (API changes, schema updates)
✓ You want one source of truth for tooling (eslint, tsconfig, prettier)
✓ Team size < 100 engineers (above that, need custom tooling like Google)
✓ You want atomic refactoring ("rename this type everywhere, one PR")
✓ Your projects have the same tech stack (all TypeScript, or all Python)
```

### When Polyrepo Wins

```
✓ Teams are fully autonomous (different deploy cadences, different tools)
✓ Different tech stacks per project (Python backend, Swift iOS, Kotlin Android)
✓ Strict access control needed (open source + proprietary in same org)
✓ 100+ engineers without investment in custom build tooling
✓ Projects genuinely don't share code
✓ Compliance requires separate audit trails per project
```

---

## 3. Industry Map

### Who Uses What

```
MONOREPO:
  Google        2B+ lines of code, custom VCS (Piper), Bazel
  Meta          Mercurial fork (Sapling), Buck2, all platforms
  Microsoft     Windows + Office in one repo, custom tooling
  Uber          Go monorepo, custom Bazel rules
  Airbnb        Web + mobile, custom tooling
  Stripe        Ruby + JS monorepo
  Twitter/X     Pants build system
  Vercel        Turborepo (they built it)
  Nrwl          Nx (they built it)

POLYREPO:
  Amazon        "Two-pizza teams", each team owns their repos
  Netflix       Microservices in separate repos
  Spotify       Squad model, autonomous team repos

HYBRID (monorepo per domain):
  Many companies at 200+ engineers:
    monorepo: platform/          (infra team)
    monorepo: web/               (frontend team)
    monorepo: services/          (backend team)
    Each domain is a monorepo, domains are separate repos.
```

---

## 4. How Google's Monorepo Works

### The Numbers

```
Google's monorepo (as of published data):
  - 2 billion lines of code
  - 1 billion files
  - 35 million commits
  - 25,000+ developers
  - 40,000 commits per day
  - 86 TB of content
  - Single logical repo (not git — custom VCS called "Piper")

Every engineer can see every file in the company.
An engineer in Search can read Ads code, Maps code, YouTube code.
```

### How They Make It Work

```
1. CUSTOM VCS (Piper, built on Perforce concepts)
   Not git — git can't handle this scale.
   Virtual file system: only files you need are on your disk.
   Everything else is fetched on demand.

2. BAZEL (build tool)
   Hermetic builds: every build is reproducible.
   Knows the ENTIRE dependency graph.
   Builds ONLY what changed.
   Remote execution: build tasks run on a cluster, not your laptop.

3. TRUNK-BASED DEVELOPMENT
   One branch (main/trunk). No long-lived feature branches.
   Developers commit to trunk multiple times per day.
   Feature flags instead of feature branches.

4. CODE REVIEW (Critique)
   Every change is reviewed before merge.
   OWNERS files (like CODEOWNERS) per directory.
   Automated checks run before review.

5. LARGE-SCALE CHANGES (LSCs)
   Refactoring tool that modifies thousands of files at once.
   Example: "Rename this deprecated API across the entire codebase."
   Automated, reviewed in chunks, merged incrementally.

Key insight: Google doesn't use a monorepo because it's easy.
They invested YEARS in custom tooling to make it possible.
Without that investment, a monorepo at this scale would be unusable.
```

---

## 5. The Dependency Graph

### The Core Concept Everything Else Builds On

```
A dependency graph maps which projects depend on which.

  apps/frontend
    └── depends on: packages/ui-components
    └── depends on: packages/shared-utils

  apps/backend
    └── depends on: packages/shared-utils
    └── depends on: packages/database

  packages/ui-components
    └── depends on: packages/shared-utils

  As a graph:

  apps/frontend ──▶ packages/ui-components ──▶ packages/shared-utils
       │                                              ▲
       └──────────────────────────────────────────────┘
  
  apps/backend ──▶ packages/shared-utils
       │
       └──▶ packages/database

WHY THIS MATTERS:
  If you change packages/shared-utils:
    → must rebuild: ui-components, frontend, backend (all depend on it)
    → no need to rebuild: database (doesn't depend on it)

  The dependency graph tells the build tool:
    "Only rebuild what's affected by this change."
    "Build in the right order (shared-utils before ui-components before frontend)."
```

### Circular Dependencies = Disaster

```
BAD:
  package-A depends on package-B
  package-B depends on package-A
  
  → Can't determine build order
  → Can't determine affected projects
  → Everything breaks

Monorepo tools detect this and refuse to build.
Rule: dependency graph must be a DAG (Directed Acyclic Graph).
No cycles allowed.
```

---

## 6. Monorepo Structure

### Standard Layout

```
my-company/
├── apps/                          # Deployable applications
│   ├── web/                       # React frontend
│   │   ├── src/
│   │   ├── package.json           # depends on @company/ui, @company/utils
│   │   ├── tsconfig.json          # extends ../../packages/config/tsconfig.base.json
│   │   └── Dockerfile
│   ├── api/                       # Node.js backend
│   │   ├── src/
│   │   ├── package.json
│   │   └── Dockerfile
│   └── mobile/                    # React Native
│       ├── src/
│       └── package.json
│
├── packages/                      # Shared libraries (not deployed alone)
│   ├── ui/                        # Design system / component library
│   │   ├── src/
│   │   │   ├── Button.tsx
│   │   │   ├── Modal.tsx
│   │   │   └── index.ts
│   │   ├── package.json           # name: "@company/ui"
│   │   └── tsconfig.json
│   ├── utils/                     # Shared utilities
│   │   ├── src/
│   │   ├── package.json           # name: "@company/utils"
│   │   └── tsconfig.json
│   ├── types/                     # Shared TypeScript types
│   │   ├── src/
│   │   └── package.json           # name: "@company/types"
│   └── config/                    # Shared configs
│       ├── eslint/
│       ├── tsconfig/
│       │   ├── base.json
│       │   ├── react.json
│       │   └── node.json
│       └── prettier/
│
├── package.json                   # Root workspace config
├── pnpm-workspace.yaml            # Workspace packages definition
├── turbo.json                     # Task pipeline (Turborepo)
│   OR
├── nx.json                        # Nx configuration
├── .github/
│   ├── CODEOWNERS                 # Code ownership
│   └── workflows/
│       └── ci.yml                 # CI pipeline
├── .eslintrc.js                   # Root ESLint (extends packages/config)
├── .prettierrc                    # Prettier config
└── tsconfig.json                  # Root TypeScript config
```

### apps/ vs packages/

```
apps/   = things you DEPLOY (has a Dockerfile, has a start command)
          web app, API server, mobile app, CLI tool
          
packages/ = things you IMPORT (other projects use them)
            UI components, utilities, types, config
            Never deployed on their own

Rule: apps depend on packages. Packages depend on other packages.
      Apps should NEVER depend on other apps.

          apps/web ──▶ packages/ui ──▶ packages/utils
          apps/api ──▶ packages/utils
          apps/api ──▶ packages/types

          apps/web ──✗──▶ apps/api    ← NEVER
```

---

## 7. Package Managers

### npm vs Yarn vs pnpm

```
                npm (v7+)           Yarn (v3+)          pnpm
                ─────────           ──────────          ────
Speed           Slowest             Fast (PnP)          Fastest
Disk usage      High (hoisting)     Low (PnP)           Lowest (content-addressed)
Strictness      Loose               Strict (PnP)        Strictest
Phantom deps    YES (bug-prone)     No (PnP mode)       No
Workspace       ✓ (basic)           ✓ (good)            ✓ (best)
Lockfile        package-lock.json   yarn.lock           pnpm-lock.yaml

PHANTOM DEPENDENCY problem:
  npm hoists all deps to root node_modules.
  Your code can import packages you didn't declare in package.json.
  Works locally → breaks in production (where hoisting is different).
  
  pnpm prevents this by creating a strict node_modules structure.
  If you didn't declare it, you can't import it.

Industry recommendation: pnpm for monorepos (fastest, strictest, best workspace support).
```

### Setting Up Workspaces

```yaml
# pnpm-workspace.yaml
packages:
  - "apps/*"
  - "packages/*"
```

```json
// npm — package.json (root)
{
  "workspaces": ["apps/*", "packages/*"]
}
```

```yaml
# Yarn — package.json (root)
# Same as npm, plus .yarnrc.yml for PnP:
# nodeLinker: pnp
```

---

## 8. Workspace Protocol

### How Internal Packages Reference Each Other

```json
// apps/web/package.json
{
  "name": "@company/web",
  "dependencies": {
    "@company/ui": "workspace:*",        // always use local version
    "@company/utils": "workspace:^1.0.0", // local, semver-compatible
    "react": "^18.3.0"                    // external, from npm registry
  }
}
```

```
"workspace:*" means:
  Always use the local version from this monorepo.
  Never fetch from npm.
  Changes to @company/ui are immediately available in @company/web.
  No publishing step needed.

When you publish @company/web to npm:
  workspace:* → replaced with actual version (e.g., "1.2.3")
  So the published package works outside the monorepo too.
```

---

## 9. Task Orchestration

### The Problem

```
You run "build all" in a monorepo with 20 packages.

Without orchestration:
  Build all 20 in random order.
  package-A depends on package-B → A fails because B isn't built yet.
  Retry → maybe works, maybe not. Non-deterministic.

With orchestration:
  Tool reads the dependency graph:
    Level 0: packages/utils, packages/types  (no deps → build first)
    Level 1: packages/ui (depends on utils)  (build after level 0)
    Level 2: apps/web (depends on ui, utils) (build after level 1)
  
  Parallel execution: level 0 packages built simultaneously.
  Correct order guaranteed.
```

### Task Pipeline Definition

```json
// turbo.json (Turborepo)
{
  "tasks": {
    "build": {
      "dependsOn": ["^build"],    // build dependencies first
      "outputs": ["dist/**"]       // what to cache
    },
    "test": {
      "dependsOn": ["build"],     // test after build
      "outputs": []
    },
    "lint": {
      "outputs": []                // no dependencies, can run in parallel
    },
    "dev": {
      "cache": false,              // never cache dev server
      "persistent": true           // long-running
    }
  }
}
```

```
"dependsOn": ["^build"] 

The ^ means: build all DEPENDENCIES first, then build this package.

  pnpm turbo build

  Execution order:
    1. packages/utils    → build (no deps)     ┐
    2. packages/types    → build (no deps)     ├── parallel
    3. packages/config   → build (no deps)     ┘
    4. packages/ui       → build (depends on utils, types) → waits for 1,2
    5. apps/web          → build (depends on ui, utils)    → waits for 4,1
    6. apps/api          → build (depends on utils, types) → waits for 1,2
```

---

## 10. Affected Detection

### Only Build/Test What Changed

```
You have 20 packages. You changed ONE file in packages/utils.

Without affected detection:
  Build and test ALL 20 packages.
  CI time: 30 minutes.

With affected detection:
  Tool computes: "packages/utils changed"
  From dependency graph: "ui depends on utils, web depends on ui"
  Affected: utils, ui, web (3 packages)
  
  Build and test only 3 packages.
  CI time: 5 minutes.
```

### How It Works

```
1. Compare git diff between current branch and main:
   git diff main...HEAD --name-only
   → packages/utils/src/format.ts

2. Map changed files to packages:
   packages/utils/src/format.ts → belongs to packages/utils

3. Walk the dependency graph upward:
   packages/utils is depended on by:
     → packages/ui
     → apps/web (via ui)
     → apps/api (directly)

4. Run tasks only on affected set:
   npx nx affected --target=test
   # or
   npx turbo test --filter=...[main]
```

```bash
# Turborepo: run tests only for affected packages
pnpm turbo test --filter="...[origin/main]"

# Nx: run tests only for affected projects
npx nx affected -t test

# Both compare current branch to main and only run on affected.
```

---

## 11. Caching

### Local Cache

```
First run:
  pnpm turbo build
  packages/utils → building... (3s) → cached result stored
  packages/ui    → building... (5s) → cached result stored
  apps/web       → building... (10s) → cached result stored
  Total: 18s

Second run (nothing changed):
  pnpm turbo build
  packages/utils → cache HIT (0.1s)
  packages/ui    → cache HIT (0.1s)
  apps/web       → cache HIT (0.1s)
  Total: 0.3s

How it knows to use cache:
  Computes hash of:
    - source files
    - dependencies
    - environment variables
    - task configuration
  If hash matches → skip task, replay cached output
```

### Remote Cache

```
Problem: local cache only helps YOU.
  Developer A builds → cached locally.
  Developer B builds the same code → full rebuild (different machine).
  CI builds → full rebuild (fresh machine every time).

Solution: remote cache (shared across all machines).

  Developer A builds → uploads cache to cloud (Vercel, Nx Cloud, S3).
  Developer B builds → downloads cache from cloud → instant.
  CI builds → downloads cache → instant.

  ┌───────────────┐       ┌──────────────────┐
  │ Dev A laptop  │──────▶│  Remote Cache     │
  │ (builds)      │       │  (Vercel / Nx     │
  └───────────────┘       │   Cloud / S3)     │
                          │                    │
  ┌───────────────┐       │                    │
  │ Dev B laptop  │◀──────│  Cache hit!        │
  │ (instant)     │       │                    │
  └───────────────┘       │                    │
                          │                    │
  ┌───────────────┐       │                    │
  │ CI runner     │◀──────│  Cache hit!        │
  │ (instant)     │       │                    │
  └───────────────┘       └──────────────────┘

Impact:
  Without remote cache: CI takes 30 minutes
  With remote cache:    CI takes 3 minutes (most tasks cached)
  Cost savings: 50-70% reduction in CI compute
```

---

## 12. Tools Comparison

```
                Turborepo           Nx                  Bazel               Moon
                ─────────           ──                  ─────               ────
Made by         Vercel              Nrwl                Google              moonrepo
Language        Rust (v2)           TypeScript/Rust     Java/Starlark       Rust
Best for        JS/TS projects      JS/TS + plugins     Any language        Polyglot
                5-50 packages       10-200 projects     100-10,000+         10-100+

Setup           5 minutes           15 minutes          Days-weeks          30 minutes
Learning curve  Low                 Medium              Very high           Medium
Config          turbo.json          nx.json + project   BUILD files         .moon/ config

Caching         Task-based          Named Inputs        Action-based        Task-based
                (hash source files) (granular control)  (hermetic, exact)   (hash inputs)
Remote cache    Vercel (free)       Nx Cloud (free tier) Remote exec (BYO)  moonbase

Affected cmd    --filter=...[main]  nx affected         query //...         moon ci
Task ordering   Via dependsOn       Implicit from graph Via deps in BUILD   Via dependsOn
Code generation No                  Yes (nx generate)   No                  Yes
Plugins         No                  Rich ecosystem      Rules               Limited
Constraints     No                  Module boundaries   Visibility rules    Constraints

CI distribution Manual              Nx Agents (auto)    Remote execution    Manual

Choose:
  Turborepo → small-medium JS/TS, want simplicity
  Nx        → medium-large, want plugins, generators, boundaries
  Bazel     → massive, multi-language, need hermetic builds
  Moon      → polyglot, want Rust-like tooling
```

---

## 13. Turborepo Deep Dive

### Setup (5 Minutes)

```bash
# Create new monorepo
pnpm dlx create-turbo@latest my-monorepo
cd my-monorepo

# Or add to existing repo
pnpm add -D turbo -w
```

### Configuration

```json
// turbo.json
{
  "$schema": "https://turbo.build/schema.json",
  "tasks": {
    "build": {
      "dependsOn": ["^build"],
      "inputs": ["src/**", "tsconfig.json", "package.json"],
      "outputs": ["dist/**", ".next/**"]
    },
    "test": {
      "dependsOn": ["build"],
      "inputs": ["src/**", "test/**"],
      "outputs": [],
      "env": ["DATABASE_URL"]
    },
    "lint": {
      "inputs": ["src/**", ".eslintrc*"],
      "outputs": []
    },
    "dev": {
      "cache": false,
      "persistent": true
    },
    "typecheck": {
      "dependsOn": ["^build"],
      "inputs": ["src/**", "tsconfig.json"],
      "outputs": []
    }
  }
}
```

### Commands

```bash
# Build everything (in dependency order, with caching)
pnpm turbo build

# Build only the web app and its dependencies
pnpm turbo build --filter=@company/web

# Build only packages affected by changes since main
pnpm turbo build --filter="...[origin/main]"

# Run dev servers for web and api
pnpm turbo dev --filter=@company/web --filter=@company/api

# Run tests in parallel (no dependency between test tasks)
pnpm turbo test

# See the dependency graph
pnpm turbo build --graph
# Opens a visual graph in your browser

# Dry run (see what would execute)
pnpm turbo build --dry
```

---

## 14. Nx Deep Dive

### Setup

```bash
# Create new Nx workspace
npx create-nx-workspace@latest my-org --preset=ts

# Add Nx to existing monorepo
npx nx@latest init
```

### Configuration

```json
// nx.json
{
  "targetDefaults": {
    "build": {
      "dependsOn": ["^build"],
      "inputs": ["production", "^production"],
      "outputs": ["{projectRoot}/dist"],
      "cache": true
    },
    "test": {
      "inputs": ["default", "^production"],
      "cache": true
    },
    "lint": {
      "inputs": ["default", "{workspaceRoot}/.eslintrc.json"],
      "cache": true
    }
  },
  "namedInputs": {
    "default": ["{projectRoot}/**/*", "sharedGlobals"],
    "production": [
      "default",
      "!{projectRoot}/test/**",
      "!{projectRoot}/**/*.spec.ts"
    ],
    "sharedGlobals": ["{workspaceRoot}/tsconfig.base.json"]
  }
}
```

### Unique Nx Features

```bash
# Affected: only run on projects affected by your changes
npx nx affected -t build test lint

# Code generation
npx nx generate @nx/react:component Button --project=ui

# Dependency graph visualization (interactive)
npx nx graph

# Module boundary enforcement
# In project.json, set tags:
# { "tags": ["scope:frontend", "type:app"] }
# In .eslintrc.json, enforce:
# @nx/enforce-module-boundaries rules

# Distributed CI (Nx Agents)
# CI runs tasks across multiple machines automatically
# No manual sharding — Nx distributes based on task graph
```

### Module Boundaries (Nx Exclusive Feature)

```json
// apps/web/project.json
{
  "tags": ["scope:web", "type:app"]
}

// packages/ui/project.json
{
  "tags": ["scope:shared", "type:ui"]
}

// packages/backend-utils/project.json
{
  "tags": ["scope:backend", "type:util"]
}
```

```json
// .eslintrc.json (root)
{
  "rules": {
    "@nx/enforce-module-boundaries": [
      "error",
      {
        "depConstraints": [
          {
            "sourceTag": "scope:web",
            "onlyDependOnLibsWithTags": ["scope:shared"]
          },
          {
            "sourceTag": "scope:backend",
            "onlyDependOnLibsWithTags": ["scope:shared", "scope:backend"]
          },
          {
            "sourceTag": "type:app",
            "onlyDependOnLibsWithTags": ["type:ui", "type:util"]
          }
        ]
      }
    ]
  }
}
```

```
This PREVENTS:
  ✗ Frontend importing backend-only code
  ✗ Library A importing from App B
  ✗ Breaking architectural boundaries

Lint error: "A project tagged with 'scope:web' can only depend on
             projects tagged with 'scope:shared'."
```

---

## 15. Bazel

### When You Need Bazel

```
Use Bazel when:
  ✓ Multiple languages (Go + Python + Java + TypeScript)
  ✓ 1,000+ engineers
  ✓ Need hermetic, reproducible builds (same input → same output, always)
  ✓ Need remote execution (build on a cluster, not your laptop)
  ✓ Willing to invest months in setup

Don't use Bazel when:
  ✗ JS/TS only (Turborepo or Nx is far simpler)
  ✗ Small team (< 50 engineers)
  ✗ Can't invest in build engineering team
```

### BUILD Files

```python
# packages/utils/BUILD
load("@npm//:defs.bzl", "ts_project")

ts_project(
    name = "utils",
    srcs = glob(["src/**/*.ts"]),
    deps = [
        "@npm//lodash",
    ],
    visibility = ["//packages:__subpackages__", "//apps:__subpackages__"],
)

# apps/web/BUILD
load("@npm//:defs.bzl", "ts_project", "nodejs_binary")

ts_project(
    name = "web",
    srcs = glob(["src/**/*.ts", "src/**/*.tsx"]),
    deps = [
        "//packages/utils",
        "//packages/ui",
        "@npm//react",
        "@npm//react-dom",
    ],
)
```

---

## 16. CI/CD for Monorepos

### GitHub Actions — Turborepo Example

```yaml
# .github/workflows/ci.yml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0       # full history for affected detection

      - uses: pnpm/action-setup@v4
        with:
          version: 9

      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: "pnpm"

      - run: pnpm install --frozen-lockfile

      # Only build/test/lint what changed
      - run: pnpm turbo build test lint --filter="...[origin/main]"

  deploy-web:
    needs: build
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Only deploy if web app or its dependencies changed
      - name: Check if web changed
        id: changes
        run: |
          CHANGED=$(pnpm turbo build --filter=@company/web --dry=json | jq '.tasks | length')
          echo "should_deploy=$([[ $CHANGED -gt 0 ]] && echo true || echo false)" >> $GITHUB_OUTPUT

      - name: Deploy web
        if: steps.changes.outputs.should_deploy == 'true'
        run: pnpm turbo deploy --filter=@company/web
```

### Remote Cache in CI

```yaml
# With Turborepo + Vercel Remote Cache
env:
  TURBO_TOKEN: ${{ secrets.TURBO_TOKEN }}
  TURBO_TEAM: ${{ vars.TURBO_TEAM }}

# Now CI reuses cache from other CI runs AND developer machines
# First CI run: 20 minutes
# Subsequent CI runs (if only 1 package changed): 2 minutes
```

---

## 17. Code Ownership

### CODEOWNERS File

```
# .github/CODEOWNERS

# Default owners (review all PRs)
* @platform-team

# App-specific ownership
apps/web/                @frontend-team
apps/api/                @backend-team
apps/mobile/             @mobile-team

# Package ownership
packages/ui/             @design-system-team
packages/utils/          @platform-team
packages/database/       @backend-team
packages/config/         @platform-team

# CI/CD config
.github/                 @devops-team
turbo.json               @platform-team
```

```
What this does:
  PR that changes apps/web/ → @frontend-team must approve
  PR that changes packages/ui/ → @design-system-team must approve
  PR that changes both → both teams must approve

This gives per-team ownership without separate repos.
```

---

## 18. Versioning and Publishing

### Changesets (Most Popular)

```bash
# Install
pnpm add -D @changesets/cli -w
pnpm changeset init

# When you make a change that should be released:
pnpm changeset
# Interactive prompts:
#   Which packages changed? → @company/ui
#   Is this a major/minor/patch? → minor
#   Summary: "Added new Button variant"
# Creates: .changeset/cool-ducks-smile.md

# At release time (usually in CI):
pnpm changeset version
# Reads all changeset files
# Bumps versions in package.json
# Updates CHANGELOG.md
# Removes changeset files

pnpm changeset publish
# Publishes changed packages to npm
```

### Versioning Strategies

```
FIXED (locked):
  All packages share ONE version number.
  @company/ui@2.0.0, @company/utils@2.0.0, @company/types@2.0.0
  Change any package → all bump to 2.0.1
  
  Pros: simple, consumers know everything is compatible
  Cons: unnecessary version bumps
  Used by: Angular, Babel

INDEPENDENT:
  Each package has its own version.
  @company/ui@3.2.1, @company/utils@1.5.0, @company/types@2.0.0
  Change @company/ui → only ui bumps to 3.2.2
  
  Pros: accurate versioning, no noise
  Cons: more complex, dependency compatibility not guaranteed
  Used by: Babel (switched), most monorepos
```

---

## 19. Shared Configuration

### One Source of Truth

```
Problem without shared config:
  20 packages, each with its own:
    tsconfig.json (slightly different)
    .eslintrc.json (slightly different)
    jest.config.js (slightly different)
  
  Change ESLint rule → update 20 files. Miss one → inconsistency.

Solution: centralized config package.
```

```
packages/config/
├── eslint/
│   ├── base.js
│   ├── react.js
│   └── node.js
├── tsconfig/
│   ├── base.json
│   ├── react.json
│   └── node.json
├── prettier/
│   └── index.js
└── package.json
```

```json
// packages/config/tsconfig/base.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  }
}

// apps/web/tsconfig.json (just extends)
{
  "extends": "@company/config/tsconfig/react.json",
  "include": ["src"],
  "compilerOptions": {
    "outDir": "dist"
  }
}
```

---

## 20. Deployment Strategies

### Independent Deploys from One Repo

```
Key principle: monorepo does NOT mean mono-deploy.
Each app deploys INDEPENDENTLY.

  apps/web    → deploys to Vercel / CloudFront
  apps/api    → deploys to Kubernetes / ECS
  apps/mobile → deploys to App Store / Play Store

Deployment triggers:
  Option 1: Deploy only if the app's code (or its deps) changed
  Option 2: Deploy everything on every merge to main
  Option 3: Manual deploy per app (release button)

Best practice:
  Merge to main → CI detects affected apps → deploy only those

  Change packages/utils → affects web + api → deploy both
  Change apps/web only → deploy only web
  Change apps/api only → deploy only api
```

### Docker Build from Monorepo

```dockerfile
# apps/api/Dockerfile

# Build stage: install ALL workspace deps, build target app
FROM node:22-alpine AS builder
WORKDIR /app
COPY pnpm-lock.yaml pnpm-workspace.yaml package.json ./
COPY apps/api/package.json apps/api/
COPY packages/utils/package.json packages/utils/
COPY packages/types/package.json packages/types/
RUN corepack enable && pnpm install --frozen-lockfile

COPY packages/ packages/
COPY apps/api/ apps/api/
RUN pnpm turbo build --filter=@company/api

# Production: only the built output
FROM node:22-alpine
WORKDIR /app
COPY --from=builder /app/apps/api/dist ./dist
COPY --from=builder /app/apps/api/node_modules ./node_modules
CMD ["node", "dist/index.js"]
```

---

## 21. Git Performance at Scale

### The Problem

```
As your monorepo grows (50,000+ files):
  git status     → 2-5 seconds (walks entire tree)
  git log        → slow (massive history)
  git blame      → slow (many commits)
  git clone      → slow (large repo)

Solutions:
```

### Fixes

```bash
# 1. Shallow clone in CI (most impactful)
git clone --depth=1 https://github.com/company/monorepo.git
# Only fetches latest commit, not full history
# But: can't do affected detection without history
# Fix: fetch enough for comparison
git fetch --depth=50 origin main

# 2. Sparse checkout (only checkout what you need)
git sparse-checkout init --cone
git sparse-checkout set apps/web packages/ui packages/utils
# Your working directory only has these folders
# Everything else is in git but not on disk

# 3. File system monitor (fsmonitor)
git config core.fsmonitor true
# Uses OS file-watching instead of scanning entire tree
# git status: 5s → 0.1s

# 4. Git maintenance (auto-optimizes in background)
git maintenance start
# Auto-runs: gc, commit-graph, prefetch, incremental-repack

# 5. Partial clone (blob-less clone)
git clone --filter=blob:none https://github.com/company/monorepo.git
# Clones commits and trees but not file contents
# Blobs fetched on demand when you checkout/read files
# Clone: 30GB → 500MB, files fetched as needed
```

---

## 22. Common Mistakes

```
1. NO TASK ORCHESTRATION
   Using "npm run build" in each package manually.
   → Use Turborepo/Nx. It's the entire point of a monorepo.

2. NO CACHING
   Rebuilding everything on every CI run.
   → Enable remote cache. 30-min CI → 3-min CI.

3. CIRCULAR DEPENDENCIES
   Package A imports from B, B imports from A.
   → Restructure: extract shared code into package C.

4. apps/ DEPENDING ON apps/
   Web app importing from API server code.
   → Extract shared types/logic into packages/.

5. NO CODEOWNERS
   Anyone can change anything → no accountability.
   → Add CODEOWNERS file. Enforce reviews.

6. GLOBAL NODE_MODULES IMPORTS
   Importing packages you didn't declare as dependencies.
   → Use pnpm (strict mode prevents phantom deps).

7. ALL CONFIGS IN ROOT
   One tsconfig.json for 20 packages → config conflicts.
   → Each package extends from shared base in packages/config.

8. DEPLOYING EVERYTHING ON EVERY CHANGE
   Changed one package → rebuild and deploy all 10 apps.
   → Use affected detection → deploy only what changed.

9. ONE GIANT PACKAGE.JSON
   All dependencies in root → no visibility into who needs what.
   → Each package declares its own dependencies.

10. NO MODULE BOUNDARIES
    Frontend code importing database drivers.
    → Use Nx module boundaries or linting rules.
```

---

## 23. Decision Framework

```
┌─────────────────────────────────────────────────────────────────┐
│                    SHOULD YOU USE A MONOREPO?                     │
│                                                                  │
│  Do your projects share significant code?                       │
│    NO  → polyrepo is fine                                       │
│    YES ↓                                                        │
│                                                                  │
│  Do you make frequent cross-project changes?                    │
│    NO  → polyrepo with published packages                       │
│    YES ↓                                                        │
│                                                                  │
│  Is your team < 100 engineers?                                  │
│    NO  → monorepo BUT invest in custom tooling (Bazel-level)    │
│    YES ↓                                                        │
│                                                                  │
│  Mostly JavaScript/TypeScript?                                  │
│    YES → Turborepo (< 50 pkgs) or Nx (50+ pkgs)               │
│    NO  → Nx (multi-language) or Bazel (hermetic needs)          │
│                                                                  │
│  Need strict architectural boundaries?                          │
│    YES → Nx (module boundaries) or Bazel (visibility rules)    │
│    NO  → Turborepo (simpler)                                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 24. Full Setup — Zero to Production

### Turborepo + pnpm + TypeScript

```bash
# 1. Create monorepo
pnpm dlx create-turbo@latest my-company --package-manager pnpm

# 2. Structure
# my-company/
# ├── apps/
# │   ├── web/          (Next.js)
# │   └── api/          (Node.js)
# ├── packages/
# │   ├── ui/           (React components)
# │   ├── utils/        (Shared utilities)
# │   └── config/       (Shared configs: tsconfig, eslint)
# ├── turbo.json
# ├── pnpm-workspace.yaml
# └── package.json

# 3. Install everything
pnpm install

# 4. Build all (with caching)
pnpm turbo build

# 5. Run dev servers
pnpm turbo dev --filter=@company/web --filter=@company/api

# 6. Add remote cache (free via Vercel)
npx turbo login
npx turbo link

# 7. Run affected on PR
pnpm turbo build test lint --filter="...[origin/main]"

# 8. Add CODEOWNERS
cat > .github/CODEOWNERS << 'EOF'
apps/web/              @frontend-team
apps/api/              @backend-team
packages/ui/           @design-system-team
packages/              @platform-team
EOF

# 9. CI pipeline
# See Section 16 for full GitHub Actions config

# Done. You have:
#   ✓ Workspace-linked packages
#   ✓ Dependency-aware task orchestration
#   ✓ Local + remote caching
#   ✓ Affected detection (build only what changed)
#   ✓ Code ownership
#   ✓ Independent deploys
```

---

## Quick Reference

```
Term                    Meaning
─────────────────────── ─────────────────────────────────────────
Monorepo                Multiple projects in one git repo
Polyrepo                One project per git repo
Workspace               Package manager feature linking local packages
Dependency graph        Map of which project depends on which
Affected detection      Build/test only projects impacted by a change
Task orchestration      Run tasks in correct dependency order
Remote cache            Shared build cache across machines
CODEOWNERS              File defining who must review each directory
Changesets              Tool for versioning and publishing packages
Module boundaries       Rules preventing illegal cross-project imports
Phantom dependency      Importing an undeclared transitive dependency
Hermetic build          Same input always produces same output
```

```
Tool        Use when                                  Setup time
──────────  ────────────────────────────────────────  ──────────
Turborepo   JS/TS, < 50 packages, want simplicity     5 minutes
Nx          JS/TS, 50+ projects, need boundaries      15 minutes
Bazel       Multi-language, 1000+ engineers            Weeks-months
Moon        Polyglot, Rust-like tooling philosophy     30 minutes
Lerna       Legacy (use Nx or Turborepo instead)       —
```

---

*A monorepo is an architecture choice, not a tool choice.*
*The tool (Turborepo/Nx/Bazel) just makes the architecture viable.*
