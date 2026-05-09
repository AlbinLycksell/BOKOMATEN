// StatPanel.jsx — small numerical summary, tabular numerals.
const StatPanel = () => (
  <section style={statStyles.section}>
    <Stat label="Samtal i natt" value="11" delta="+2 mot snitt" pos />
    <Stat label="Akutjobb" value="3" delta="alla bemannade" pos />
    <Stat label="Bokningar" value="7" delta="2 till v. 22" />
    <Stat label="Missat av AI" value="0" delta="senaste 14 dagar" />
  </section>
);

const Stat = ({ label, value, delta, pos }) => (
  <div style={statStyles.cell}>
    <div style={statStyles.lbl}>{label.toUpperCase()}</div>
    <div style={statStyles.val}>{value}</div>
    <div style={{...statStyles.delta, color: pos ? "#2F5233" : "var(--fg-muted)"}}>{delta}</div>
  </div>
);

const statStyles = {
  section: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    background: "var(--linne)",
    margin: "0 48px",
    border: "1px solid var(--border)",
    borderRadius: 14,
    background: "#fff",
    overflow: "hidden",
  },
  cell: {
    padding: "20px 22px",
    borderRight: "1px solid var(--border)",
  },
  lbl: {
    fontFamily: "var(--font-mono)",
    fontSize: 11, letterSpacing: "0.08em",
    color: "var(--fg-muted)",
    marginBottom: 8,
  },
  val: {
    fontFamily: "var(--font-display)",
    fontSize: 40, fontWeight: 600,
    letterSpacing: "-0.02em",
    color: "var(--fg-strong)",
    fontFeatureSettings: '"tnum" 1',
    lineHeight: 1.0,
  },
  delta: { marginTop: 8, fontSize: 13 },
};

window.StatPanel = StatPanel;
