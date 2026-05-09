// BriefingHeader.jsx — Lena's morning. Editorial, not dashboardy.
const BriefingHeader = ({ name = "Lena", date = "torsdag 22 maj" }) => {
  const greeting = "God morgon, " + name;
  return (
    <header style={briefingStyles.bar}>
      <div>
        <div style={briefingStyles.eye}>{date.toUpperCase()} · 06:42</div>
        <h1 style={briefingStyles.h}>{greeting}.</h1>
        <p style={briefingStyles.sub}>
          Du fångade <strong style={briefingStyles.strong}>tre akutjobb</strong> i natt — kosta dig själv en till kopp kaffe på det.
        </p>
      </div>
      <div style={briefingStyles.actions}>
        <button className="v-btn v-btn--ghost v-btn--sm">Skicka sammanfattning till Magnus</button>
        <button className="v-btn v-btn--secondary v-btn--sm">Ny bokning</button>
      </div>
    </header>
  );
};

const briefingStyles = {
  bar: {
    display: "flex", justifyContent: "space-between",
    alignItems: "flex-end", gap: 24,
    padding: "48px 48px 32px",
    borderBottom: "1px solid var(--border)",
    background: "var(--linne)",
  },
  eye: {
    fontFamily: "var(--font-mono)",
    fontSize: 12, letterSpacing: "0.08em",
    color: "var(--fg-muted)",
    fontFeatureSettings: '"tnum" 1',
    marginBottom: 12,
  },
  h: {
    fontFamily: "var(--font-display)",
    fontSize: 48, fontWeight: 600,
    letterSpacing: "-0.02em",
    color: "var(--fg-strong)",
    margin: 0, lineHeight: 1.05,
  },
  sub: {
    marginTop: 12, fontSize: 17,
    color: "var(--fg)",
    maxWidth: "60ch", lineHeight: 1.5,
  },
  strong: { fontWeight: 500, color: "var(--fg-strong)" },
  actions: { display: "flex", gap: 8, flexShrink: 0 },
};

window.BriefingHeader = BriefingHeader;
