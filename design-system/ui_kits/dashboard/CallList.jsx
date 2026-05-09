// CallList.jsx — the night's calls in editorial form.
const calls = [
  { time: "23:14", who: "Eva Sundström", what: "Misstänkt gasläcka", where: "Kista", status: "akut", note: "Skickad till Alex · 8 sek till svar" },
  { time: "20:48", who: "Erik Ahlberg", what: "Offert badrumsrenovering", where: "Hökarängen", status: "info", note: "Sammanfattning till Magnus" },
  { time: "19:22", who: "Inger Lindqvist", what: "Vattenläcka under diskbänken", where: "Bromma", status: "bokad", note: "Bokad torsdag 16:00" },
  { time: "17:55", who: "Karin Holm", what: "Vill veta var Magnus är", where: "Mariefred", status: "info", note: "AI: Magnus kommer 14:00 i morgon" },
  { time: "14:32", who: "Olof Persson", what: "Toalett spolar inte", where: "Sundbyberg", status: "bokad", note: "Bokad fredag 09:00" },
];

const statusMeta = {
  akut:  { label: "AKUT",   color: "#E25822", bg: "rgba(226,88,34,0.12)" },
  bokad: { label: "BOKAD",  color: "#2F5233", bg: "rgba(47,82,51,0.12)" },
  info:  { label: "INFO",   color: "#7C7466", bg: "rgba(124,116,102,0.14)" },
};

const CallList = ({ onPick }) => {
  return (
    <section style={callStyles.section}>
      <div style={callStyles.head}>
        <h2 style={callStyles.h2}>I natt</h2>
        <a href="#" style={callStyles.see}>Se hela veckan →</a>
      </div>
      <ul style={callStyles.list}>
        {calls.map((c, i) => {
          const m = statusMeta[c.status];
          return (
            <li key={i} style={callStyles.item} onClick={() => onPick && onPick(c)}>
              <span style={callStyles.time}>{c.time}</span>
              <div style={callStyles.body}>
                <div style={callStyles.row}>
                  <span style={{...callStyles.pill, color: m.color, background: m.bg}}>{m.label}</span>
                  <span style={callStyles.who}>{c.who}</span>
                  <span style={callStyles.sep}>·</span>
                  <span style={callStyles.where}>{c.where}</span>
                </div>
                <div style={callStyles.what}>{c.what}</div>
                <div style={callStyles.note}>{c.note}</div>
              </div>
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#7C7466" strokeWidth="1.75" style={callStyles.chev}><path d="M9 6l6 6-6 6"/></svg>
            </li>
          );
        })}
      </ul>
    </section>
  );
};

const callStyles = {
  section: { padding: "32px 48px" },
  head: { display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 20 },
  h2: { fontFamily: "var(--font-display)", fontSize: 28, fontWeight: 600, letterSpacing: "-0.015em", color: "var(--fg-strong)", margin: 0 },
  see: { fontSize: 14, color: "var(--fg-muted)", textDecoration: "none" },
  list: { listStyle: "none", margin: 0, padding: 0 },
  item: {
    display: "grid", gridTemplateColumns: "60px 1fr 18px", gap: 18,
    padding: "18px 0", borderTop: "1px solid var(--border)",
    alignItems: "center", cursor: "pointer",
  },
  time: {
    fontFamily: "var(--font-mono)",
    fontSize: 13, color: "var(--fg-muted)",
    fontFeatureSettings: '"tnum" 1',
    letterSpacing: "0.02em",
  },
  body: {},
  row: { display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" },
  pill: {
    display: "inline-flex", alignItems: "center", height: 22,
    padding: "0 8px", borderRadius: 9999,
    fontSize: 11, letterSpacing: "0.06em", fontWeight: 500,
    fontFamily: "var(--font-mono)",
  },
  who: { fontFamily: "var(--font-display)", fontSize: 17, fontWeight: 500, color: "var(--fg-strong)", letterSpacing: "-0.005em" },
  sep: { color: "var(--border-strong)" },
  where: { fontSize: 14, color: "var(--fg-muted)" },
  what: { marginTop: 4, fontSize: 15, color: "var(--fg)" },
  note: { marginTop: 4, fontSize: 13, color: "var(--fg-muted)" },
  chev: { justifySelf: "end" },
};

window.CallList = CallList;
window.dashboardCalls = calls;
