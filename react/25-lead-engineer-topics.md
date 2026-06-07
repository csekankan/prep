# Lead Engineer Topics

## Architecture Decision Records (ADRs)

An ADR is a short document that captures an important architectural decision, the context in which it was made, and the consequences. ADRs create a decision log that explains *why* the codebase looks the way it does.

### ADR Template

```markdown
# ADR-007: Use React Query for Server State Management

## Status
Accepted

## Context
Our application has 40+ API endpoints. Currently we manage server state with
Redux, which leads to boilerplate (action types, thunks, reducers, selectors)
and manual cache invalidation. Developers spend ~30% of feature development
time on data fetching plumbing.

## Decision
Adopt React Query (TanStack Query) for all server state. Redux will be retained
only for truly global client state (theme, auth session). Existing Redux-based
data fetching will be migrated incrementally, one feature area per sprint.

## Consequences
- Positive: Automatic caching, deduplication, background refetch, retry logic
  out of the box. Reduced boilerplate by ~60%.
- Positive: Devtools for inspecting cache state.
- Negative: Team must learn a new mental model (cache keys, stale time, query
  invalidation). Training session planned.
- Negative: Two state management patterns coexist during migration. We accept
  this cost for ~3 sprints.

## Alternatives Considered
- SWR: Similar to React Query but fewer features (no mutations API, less
  mature devtools). React Query's mutation support is critical for our use case.
- Keep Redux + RTK Query: RTK Query is tightly coupled to Redux. We want to
  reduce Redux surface area, not extend it.
```

**Why ADRs matter in interviews:** Lead engineers are expected to make decisions that outlast their tenure. ADRs show you value institutional knowledge and understand that code without context becomes legacy.

---

## Technical Debt Management

### Categorizing Technical Debt

| Type | Example | Impact | Priority |
|------|---------|--------|----------|
| Deliberate-prudent | "We know this is a shortcut, we will fix it next sprint" | Tracked, bounded | Medium |
| Deliberate-reckless | "We don't have time for tests" | Cascading failures | High |
| Inadvertent-prudent | "Now we know a better pattern exists" | Refactor opportunity | Low |
| Inadvertent-reckless | Poor design due to inexperience | Fundamental rework | Varies |

### Managing Debt as a Lead

1. **Make it visible:** Maintain a tech debt backlog separate from feature work. Tag debt items with impacted areas and estimated cost of delay.
2. **Quantify the cost:** "This legacy auth module causes 2 production incidents per quarter and adds 3 days to every feature that touches user sessions."
3. **Allocate capacity:** Reserve 15-20% of sprint capacity for debt reduction. This is not negotiable -- it is the cost of maintaining velocity.
4. **Pay it incrementally:** The Boy Scout Rule (leave the code better than you found it) works for small debts. Large debts need dedicated spikes.
5. **Prevent new debt:** Code review standards, linting rules, and architectural guardrails reduce the rate of new debt accumulation.

**Interview signal:** Interviewers want to see that you can balance product delivery with technical health. Saying "we should rewrite everything" is as bad as saying "we never address debt."

---

## Build Pipeline Optimization (CI/CD for Frontend)

### Typical Frontend CI Pipeline

```
Push -> Lint -> Type Check -> Unit Tests -> Build -> Integration Tests -> Deploy Preview -> Smoke Tests -> Production Deploy
```

### Optimization Strategies

**1. Parallelization**

Run lint, type-check, and unit tests in parallel rather than sequentially. In GitHub Actions:

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci --cache .npm
      - run: npm run lint

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci --cache .npm
      - run: npm run typecheck

  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci --cache .npm
      - run: npm test -- --coverage

  build:
    needs: [lint, typecheck, test]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci --cache .npm
      - run: npm run build
```

**2. Caching**

- Cache `node_modules` or `.npm` between runs
- Cache build artifacts (Next.js `.next/cache`, Webpack cache)
- Cache test results for unchanged files (Vitest changed file detection, Jest `--changedSince`)

**3. Affected-only execution**

In monorepos, only run tasks for packages affected by the changeset. Nx and Turborepo compute the dependency graph and skip unchanged packages.

```bash
npx turbo run build test lint --filter=...[origin/main]
```

**4. Build time reduction**

- Use SWC or esbuild instead of Babel for transpilation (10-20x faster)
- Enable persistent caching in the bundler
- Use `tsconfig` project references for incremental type checking
- Consider Module Federation to split the build into independent chunks

**Metrics to track:** P50/P95 CI duration, cache hit rates, flaky test rate, deploy frequency.

---

## Monorepo vs Polyrepo

### Decision Matrix

| Factor | Monorepo | Polyrepo |
|--------|----------|----------|
| Code sharing | Trivial (same repo) | Requires publishing packages |
| Atomic changes | Single PR across packages | Coordinated PRs across repos |
| CI complexity | Needs smart task orchestration (Nx, Turborepo) | Simple per-repo CI |
| Tooling consistency | Enforced by shared config | Drifts over time |
| Onboarding | Clone one repo, see everything | Clone what you need |
| Scale concerns | Large repo = slow git operations | Many repos = many places to look |
| Team autonomy | Lower (shared CI, shared deps) | Higher (own repo, own rules) |
| Dependency versioning | Single version policy | Independent versioning |

### Monorepo Tooling

**Nx:**
- Full-featured build system with dependency graph analysis
- Computation caching (local and remote via Nx Cloud)
- Code generators for scaffolding new packages
- Plugin ecosystem (React, Next.js, Node, etc.)
- Enforces module boundaries via lint rules

**Turborepo:**
- Simpler, focused on task orchestration and caching
- Works with any package manager (npm, yarn, pnpm)
- Remote caching via Vercel
- Lower learning curve than Nx
- Less opinionated about project structure

**When to choose monorepo:** Shared component library across multiple apps, small-to-medium team, need for atomic cross-package changes, desire for consistent tooling.

**When to choose polyrepo:** Large organization with independent teams, strict deployment independence, different tech stacks across projects, regulatory isolation requirements.

---

## Micro-Frontends

### What Problem Do They Solve?

Large frontend applications developed by multiple teams encounter coordination bottlenecks: merge conflicts, release trains, shared CI queues, and forced framework alignment. Micro-frontends allow each team to own, develop, test, and deploy their piece of the UI independently.

### Implementation Approaches

**1. Module Federation (Webpack 5)**

```javascript
// Host application webpack config
new ModuleFederationPlugin({
  name: "shell",
  remotes: {
    dashboard: "dashboard@https://dashboard.cdn.example.com/remoteEntry.js",
    settings: "settings@https://settings.cdn.example.com/remoteEntry.js",
  },
  shared: {
    react: { singleton: true, requiredVersion: "^18.0.0" },
    "react-dom": { singleton: true, requiredVersion: "^18.0.0" },
  },
});

// Remote application webpack config
new ModuleFederationPlugin({
  name: "dashboard",
  filename: "remoteEntry.js",
  exposes: {
    "./DashboardApp": "./src/DashboardApp",
  },
  shared: {
    react: { singleton: true, requiredVersion: "^18.0.0" },
    "react-dom": { singleton: true, requiredVersion: "^18.0.0" },
  },
});
```

```tsx
// Loading a remote module in the host
const DashboardApp = React.lazy(() => import("dashboard/DashboardApp"));

function ShellLayout() {
  return (
    <Suspense fallback={<Spinner />}>
      <Routes>
        <Route path="/dashboard/*" element={<DashboardApp />} />
        <Route path="/settings/*" element={<SettingsApp />} />
      </Routes>
    </Suspense>
  );
}
```

**2. single-spa**

A meta-framework that orchestrates multiple SPAs on one page. Each micro-frontend registers itself with an activity function that determines when it should be active.

**3. iframe-based**

Strongest isolation (separate browsing context) but worst UX (no shared styles, awkward navigation, performance overhead). Use only when security isolation is paramount.

### Tradeoffs

- **Shared dependencies:** Must align on React version. Mismatches cause duplicate React runtimes and broken hooks.
- **Styling conflicts:** Each micro-frontend needs CSS isolation (CSS Modules, CSS-in-JS scoping, or Shadow DOM).
- **Communication:** Cross-micro-frontend communication via custom events, shared state (carefully scoped), or URL parameters.
- **Testing:** Integration testing across micro-frontends is harder. Need contract tests or end-to-end tests that span boundaries.
- **Performance:** Multiple bundles, multiple framework instances if not shared. Measure carefully.

---

## Design System Strategy

### Building vs Buying

| Factor | Build In-House | Use Open-Source (MUI, Chakra, Radix) |
|--------|---------------|--------------------------------------|
| Brand consistency | Full control | Requires theming/overriding |
| Cost | High (dedicated team, 6-12 months) | Low initial, higher customization cost |
| Maintenance | Ongoing team responsibility | Community-maintained |
| Accessibility | Must implement yourself | Often well-tested |
| Adoption | Forced by org mandate | Developers already familiar |

### Design System Architecture

```
Foundation Layer:   Design tokens (colors, spacing, typography, shadows)
Primitive Layer:    Unstyled accessible components (Radix-like headless)
Component Layer:    Styled components using tokens + primitives
Pattern Layer:      Composed patterns (forms, data tables, page layouts)
Documentation:      Storybook, usage guidelines, do/don't examples
```

### Token-Based Theming

```tsx
const tokens = {
  colors: {
    primary: { 50: "#eff6ff", 500: "#3b82f6", 900: "#1e3a5f" },
    semantic: {
      background: "var(--color-bg)",
      foreground: "var(--color-fg)",
      error: "var(--color-error)",
    },
  },
  spacing: { xs: "4px", sm: "8px", md: "16px", lg: "24px", xl: "32px" },
  radii: { sm: "4px", md: "8px", full: "9999px" },
};
```

**Versioning strategy:** Semantic versioning with a clear deprecation policy. Breaking changes require a major version bump with a migration guide. Support the previous major version for at least 6 months.

---

## Performance Budgets and Monitoring

### Setting Performance Budgets

```json
{
  "budgets": [
    { "metric": "JS bundle (gzipped)", "warning": "150 KB", "error": "200 KB" },
    { "metric": "LCP", "warning": "2.0s", "error": "2.5s" },
    { "metric": "FID / INP", "warning": "100ms", "error": "200ms" },
    { "metric": "CLS", "warning": "0.05", "error": "0.1" },
    { "metric": "Total page weight", "warning": "500 KB", "error": "750 KB" }
  ]
}
```

### Enforcement

- CI check: Run Lighthouse CI or `bundlesize` on every PR. Fail the build if budgets are exceeded.
- Runtime monitoring: Real User Monitoring (RUM) via web-vitals library, sent to Datadog/Grafana.
- Synthetic monitoring: Scheduled Lighthouse runs from multiple regions.

```tsx
import { onCLS, onINP, onLCP, onFCP, onTTFB } from "web-vitals";

function reportMetric(metric) {
  fetch("/api/metrics", {
    method: "POST",
    body: JSON.stringify({
      name: metric.name,
      value: metric.value,
      id: metric.id,
      navigationType: metric.navigationType,
    }),
    keepalive: true,
  });
}

onCLS(reportMetric);
onINP(reportMetric);
onLCP(reportMetric);
onFCP(reportMetric);
onTTFB(reportMetric);
```

---

## Feature Flags

### Architecture

```
Flag Service (LaunchDarkly, Unleash, or custom)
     |
     v
React SDK / Provider
     |
     v
useFeatureFlag("new-checkout-flow")
     |
     v
Conditionally render feature
```

### Implementation

```tsx
const FeatureFlagContext = createContext<Record<string, boolean>>({});

function FeatureFlagProvider({ children }) {
  const [flags, setFlags] = useState<Record<string, boolean>>({});
  const { userId } = useAuth();

  useEffect(() => {
    fetchFlags(userId).then(setFlags);

    const sse = new EventSource(`/api/flags/stream?userId=${userId}`);
    sse.onmessage = (event) => {
      setFlags((prev) => ({ ...prev, ...JSON.parse(event.data) }));
    };
    return () => sse.close();
  }, [userId]);

  return (
    <FeatureFlagContext.Provider value={flags}>
      {children}
    </FeatureFlagContext.Provider>
  );
}

function useFeatureFlag(flagName: string): boolean {
  const flags = useContext(FeatureFlagContext);
  return flags[flagName] ?? false;
}

// Usage
function CheckoutPage() {
  const useNewFlow = useFeatureFlag("new-checkout-flow");
  return useNewFlow ? <NewCheckout /> : <LegacyCheckout />;
}
```

### Pitfalls

- **Flag debt:** Flags that are 100% rolled out but never removed become dead code. Establish a cleanup process: once a flag is fully on for 2 weeks with no issues, create a ticket to remove it.
- **Testing combinatorial explosion:** With N flags, there are 2^N possible states. Test critical paths with flags on and off; do not try to cover every combination.
- **SSR flicker:** If flags load asynchronously, the UI may flash the wrong variant. Fetch flags server-side for SSR pages or use a loading state.

---

## A/B Testing Infrastructure

### How It Differs from Feature Flags

Feature flags are binary (on/off). A/B tests assign users to variants with statistical rigor to measure the impact of a change.

### Architecture

```
Experiment Service
  - Assigns user to variant (deterministic hash of userId + experimentId)
  - Records assignment for analysis
  - Tracks conversion events
     |
     v
React SDK
  useExperiment("checkout-v2") -> { variant: "B", payload: { ... } }
     |
     v
Analytics Pipeline
  - Collects events per variant
  - Computes statistical significance
  - Provides dashboards
```

### Implementation Considerations

- **Sample size:** Calculate required sample size before starting. Running tests on too few users produces noise, not signal.
- **Interaction effects:** Running multiple experiments simultaneously can create confounding. Use experiment layers (Google's Overlapping Experiment Infrastructure pattern) to prevent interactions.
- **Guardrail metrics:** Every experiment should monitor guardrail metrics (crash rate, latency, error rate) in addition to the target metric. An experiment that improves conversion but doubles error rate should be rolled back.

---

## Code Review Best Practices

### As a Lead Reviewing Code

1. **Focus on architecture, not style.** Automate style enforcement with ESLint + Prettier.
2. **Ask questions instead of dictating.** "Have you considered what happens when the user is offline?" is better than "Add offline support."
3. **Approve with suggestions.** Do not block PRs on nitpicks. Use "nit:" prefix for suggestions that are optional.
4. **Review the tests.** Tests reveal whether the author understood the requirements.
5. **Check for missing things:** error handling, accessibility, edge cases, security (XSS, CSRF).
6. **Keep reviews small.** If a PR is > 400 lines, ask the author to split it.

### Fostering a Healthy Review Culture

- Set a review SLA (e.g., first review within 4 hours during business hours)
- Rotate reviewers to spread knowledge and avoid bottlenecks
- Review your own PR first before requesting others (self-review catches obvious issues)
- Use PR templates to ensure consistent context (what, why, how to test)

---

## Mentoring Strategies

### The 70-20-10 Model

- **70% on-the-job learning:** Stretch assignments, owning a feature end-to-end, debugging production issues.
- **20% social learning:** Pair programming, code reviews, architecture discussions, tech talks.
- **10% formal learning:** Courses, books, conferences.

### Practical Mentoring Techniques

- **Pairing with decreasing scaffolding:** Start by driving while the mentee observes. Then co-drive. Then they drive while you observe. Then they work independently with async review.
- **Design review before code review:** Have the mentee propose their approach in a short document before coding. This catches misunderstandings early and teaches design thinking.
- **Celebrate the learning, not just the outcome:** "You figured out a great approach to this race condition" reinforces growth more than "the feature works."

---

## Cross-Team Collaboration

### Common Challenges

- **Shared component ownership:** Who fixes a bug in the shared Button component? Establish a clear ownership model: either a dedicated design system team or a rotating on-call across consumer teams.
- **API contracts:** Frontend and backend teams must agree on API shape before implementation. Use OpenAPI specs as contracts, with mock servers for parallel development.
- **Priority conflicts:** Your team depends on another team's API that is not their priority. Escalate through the technical roadmap, not through personal pressure. Propose alternatives (can we use an existing endpoint? can we build a BFF?).

### Communication Patterns

- **RFCs for cross-cutting changes:** If a change affects multiple teams, write an RFC and circulate it for feedback before starting.
- **Demo days:** Regular cross-team demos build shared understanding and surface integration issues early.
- **Shared Slack channels for dependencies:** A `#frontend-platform` channel where teams can ask questions about shared tooling.

---

## Migration Strategies

### Class Components to Hooks

**Incremental approach:** Never rewrite everything at once.

1. Start with leaf components (no children that depend on lifecycle methods)
2. Extract class logic into custom hooks
3. Convert the component to a function component using those hooks
4. Keep class-based error boundaries (no hook equivalent for `componentDidCatch`)

```tsx
// Before: Class component
class UserProfile extends React.Component {
  state = { user: null, loading: true };

  componentDidMount() {
    fetchUser(this.props.userId).then((user) =>
      this.setState({ user, loading: false })
    );
  }

  componentDidUpdate(prevProps) {
    if (prevProps.userId !== this.props.userId) {
      this.setState({ loading: true });
      fetchUser(this.props.userId).then((user) =>
        this.setState({ user, loading: false })
      );
    }
  }

  render() {
    if (this.state.loading) return <Spinner />;
    return <ProfileCard user={this.state.user} />;
  }
}

// After: Function component with hooks
function UserProfile({ userId }) {
  const { data: user, isLoading } = useQuery({
    queryKey: ["user", userId],
    queryFn: () => fetchUser(userId),
  });

  if (isLoading) return <Spinner />;
  return <ProfileCard user={user} />;
}
```

### CRA to Next.js

1. **Audit:** Identify routing patterns, data fetching, and environment variables.
2. **Set up Next.js alongside CRA:** Run both in parallel during migration.
3. **Migrate pages incrementally:** Start with static pages (easiest), then pages with client-side data fetching, then pages that benefit from SSR/SSG.
4. **Handle routing:** Replace `react-router` with Next.js file-based routing. Create a compatibility layer if needed.
5. **API routes:** Move BFF logic into Next.js API routes or keep external API server.
6. **Test:** Compare Lighthouse scores, bundle sizes, and functionality between old and new.

### Redux to Modern Alternatives

| From | To | Strategy |
|------|----|----------|
| Redux (all state) | React Query + Zustand | Separate server state (React Query) from client state (Zustand). Migrate one slice at a time. |
| Redux + Redux Saga | React Query + simple hooks | Replace sagas with React Query's built-in retry, polling, and mutation lifecycle. |
| Redux + Redux Thunk | RTK Query (if staying Redux) | RTK Query reduces boilerplate while staying in the Redux ecosystem. |

---

## Observability

### Error Tracking

```tsx
// Sentry integration
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "https://examplePublicKey@o0.ingest.sentry.io/0",
  integrations: [
    Sentry.browserTracingIntegration(),
    Sentry.replayIntegration(),
  ],
  tracesSampleRate: 0.1,        // 10% of transactions
  replaysSessionSampleRate: 0.01, // 1% of sessions
  replaysOnErrorSampleRate: 1.0,  // 100% of error sessions
  environment: process.env.NODE_ENV,
  release: process.env.COMMIT_SHA,
});

// Error boundary integration
const SentryErrorBoundary = Sentry.withErrorBoundary(App, {
  fallback: <ErrorFallback />,
  showDialog: false,
});
```

### Performance Monitoring

- **Core Web Vitals in production:** Collect LCP, INP, CLS from real users using `web-vitals` library.
- **Custom performance marks:** Use `performance.mark()` and `performance.measure()` for business-critical user flows (time from "Add to Cart" click to confirmation).
- **Bundle analysis:** Run `next build --analyze` or `webpack-bundle-analyzer` in CI. Track bundle size over time.

### Logging

```tsx
const logger = {
  info: (msg: string, context?: Record<string, unknown>) => {
    if (process.env.NODE_ENV === "production") {
      sendToLogService({ level: "info", msg, ...context });
    } else {
      console.log(`[INFO] ${msg}`, context);
    }
  },
  warn: (msg: string, context?: Record<string, unknown>) => {
    console.warn(`[WARN] ${msg}`, context);
    sendToLogService({ level: "warn", msg, ...context });
  },
  error: (msg: string, error?: Error, context?: Record<string, unknown>) => {
    console.error(`[ERROR] ${msg}`, error);
    Sentry.captureException(error, { extra: context });
  },
};
```

---

## Interview Questions

### Q1: You inherit a frontend codebase with no tests, inconsistent patterns, and a 12-minute CI pipeline. How do you prioritize improvements?

**Answer:** First, establish a baseline: measure CI time, catalog the types of inconsistencies, and identify the highest-incident areas. Then prioritize by impact-to-effort ratio:

1. **Immediate (Week 1-2):** Add ESLint + Prettier with auto-fix on save. This addresses inconsistency with zero ongoing effort. Add a pre-commit hook to prevent new violations.
2. **Short-term (Month 1):** Parallelize CI (lint, typecheck, test in parallel). Add caching. This alone typically cuts CI time by 40-60%.
3. **Medium-term (Month 1-3):** Add tests strategically. Do not aim for 100% coverage. Write integration tests for the 10 most critical user flows (login, checkout, etc.). These catch the most regressions per test written.
4. **Ongoing:** Establish a "campsite rule" -- every PR must leave the code better than it found it. This gradually improves the codebase without dedicated refactoring sprints.
5. **Track and communicate:** Set up a dashboard showing CI time trends, test coverage trends, and incident counts. Share weekly with the team.

### Q2: Your team is debating monorepo vs polyrepo for 3 React apps that share a component library. What do you recommend?

**Answer:** For 3 apps with a shared component library, I would recommend a monorepo with Turborepo (or Nx if you need more advanced features like module boundary enforcement).

**Reasoning:**
- The shared component library is the deciding factor. In a polyrepo, you would need to publish the library as an npm package, version it, and coordinate updates across 3 repos. With 3 consuming apps, this creates significant friction.
- In a monorepo, changing the component library and all consuming apps is a single PR. You can run affected-only tests to keep CI fast.
- Three apps is small enough that git performance is not a concern.
- Single CI pipeline can be parallelized and cached effectively.

**Caveats:** If the apps are owned by different organizations with different release cycles and security requirements, polyrepo with published packages provides better isolation. But for a single team or closely collaborating teams, monorepo is more productive.

### Q3: How would you implement a migration from REST to GraphQL without disrupting ongoing feature development?

**Answer:** A strangler fig migration pattern:

1. **Set up a GraphQL gateway** that initially proxies to existing REST endpoints. This means frontend can start using GraphQL immediately, and the backend migration can happen independently.
2. **Create a data fetching abstraction layer** on the frontend (e.g., custom hooks like `useUser(id)` that internally call either REST or GraphQL). This decouples feature code from the transport layer.
3. **Migrate one entity at a time.** Start with a read-heavy, low-risk entity. Move its queries to native GraphQL resolvers.
4. **Use feature flags** to toggle between REST and GraphQL per entity. This allows safe rollback.
5. **Monitor performance:** Compare response times, error rates, and payload sizes between REST and GraphQL for each migrated entity.
6. **Remove the REST proxy** only after all consumers have migrated and the direct GraphQL resolvers are proven stable.

### Q4: A new team member consistently writes PRs with 1000+ lines of changes. How do you address this?

**Answer:** This is a mentoring opportunity, not a disciplinary issue.

1. **Private conversation first.** Explain why small PRs matter: faster reviews, easier reverts, lower merge conflict risk, better git bisect accuracy.
2. **Teach decomposition.** Show them how to split work into vertical slices (each PR delivers a thin but complete piece of functionality) rather than horizontal layers (all models, then all controllers, then all views).
3. **Set a soft limit** (e.g., 300 lines). PRs exceeding this require a brief justification in the description.
4. **Lead by example.** When you create PRs, demonstrate small, well-scoped changes with clear descriptions.
5. **Tooling support.** Set up stacked PRs (using tools like Graphite or ghstack) so they can split work without waiting for each PR to merge.

### Q5: You need to introduce micro-frontends to a monolithic React app. Walk through your approach.

**Answer:**

**Assessment phase:**
- Identify natural team boundaries and corresponding UI boundaries
- Map the component dependency graph to find low-coupling boundaries
- Evaluate whether the benefits (independent deployment, team autonomy) outweigh the costs (infrastructure complexity, shared dependency management)

**Technical approach:**
1. Start with Module Federation (Webpack 5) or native ESM + import maps if using Vite.
2. Extract the shell (layout, navigation, authentication) as the host application.
3. Pick the most independent section of the app for the first extraction (e.g., a settings page that has few shared components).
4. Establish shared dependency contracts (React version, design system version).
5. Set up a shared event bus for cross-micro-frontend communication.
6. Implement health checks and fallback UI for each remote module (if the settings micro-frontend fails to load, show a graceful error, not a blank page).

**Rollout:**
- Deploy behind a feature flag: serve the monolith by default, micro-frontend to a percentage of users.
- Monitor bundle sizes, load times, and error rates for the micro-frontend vs monolith.
- Expand extraction to the next boundary only after the first is stable.

### Q6: How do you establish and maintain a performance culture in a frontend team?

**Answer:**

**1. Make performance visible:**
- Set up a performance dashboard with Core Web Vitals from production (LCP, INP, CLS).
- Show the dashboard in the team area or link it in the sprint board.
- Include performance metrics in sprint reviews alongside feature demos.

**2. Establish budgets with teeth:**
- Define performance budgets (JS bundle < 200KB gzipped, LCP < 2.5s).
- Enforce budgets in CI: fail the build if a PR exceeds the budget.
- When a budget is exceeded, the PR author must optimize or justify the regression.

**3. Embed performance in the development process:**
- Add Lighthouse scores to PR checks (using Lighthouse CI).
- Include "Performance Impact" as a section in the PR template.
- During design reviews, discuss performance implications upfront (e.g., "This carousel will load 20 high-res images -- what is our lazy loading strategy?").

**4. Build expertise:**
- Run quarterly performance workshops (profiling with Chrome DevTools, reading flame charts, optimizing React renders).
- Assign a "performance champion" rotation so everyone develops the skill.
- Celebrate wins: "This optimization reduced LCP by 400ms, improving conversion by 2%."

**5. Measure what matters:**
- Lab metrics (Lighthouse) for development feedback.
- Field metrics (RUM) for real-user experience.
- Business metrics tied to performance (conversion rate vs LCP, bounce rate vs FCP).
