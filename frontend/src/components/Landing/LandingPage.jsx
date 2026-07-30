import Logo from "../Logo";

const FEATURES = [
  {
    title: "Sprint Progress",
    detail: "Live Jira sprint status, blocked issues, and backlog health.",
  },
  {
    title: "Code Activity",
    detail: "Recent commits and pull requests straight from GitHub.",
  },
  {
    title: "Build & Deploy",
    detail: "CI/CD pipeline runs and deployment status at a glance.",
  },
  {
    title: "Uptime & Incidents",
    detail: "Service health, outages, and incident history.",
  },
  {
    title: "Log Search",
    detail: "Semantic search over CI/CD and application logs.",
  },
  {
    title: "AI Correlation",
    detail: "One agent connects signals across every system into a single story.",
  },
];

export default function LandingPage({ onLogin }) {
  return (
    <div className="landing-page">
      <div className="landing-topbar">
        <button className="landing-login-btn" onClick={onLogin}>
          Log in
        </button>
      </div>

      <div className="landing-hero">
        <div className="landing-hero__logo">
          <Logo size={40} />
        </div>
        <h1>AI Engineering Command Center</h1>
        <p className="landing-hero__tagline">
          One conversational interface for everything happening across your engineering org.
        </p>
        <p className="landing-hero__body">
          Ask a question and an agentic assistant investigates your sprints, code activity,
          builds, uptime, incidents, and logs — correlating signals across systems to return
          executive-ready summaries with recommended actions, instead of you tabbing between five
          dashboards.
        </p>
        <button className="landing-cta" onClick={onLogin}>
          Get Started
        </button>
      </div>

      <div className="landing-features">
        {FEATURES.map((feature) => (
          <div className="landing-feature-card" key={feature.title}>
            <h3>{feature.title}</h3>
            <p>{feature.detail}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
