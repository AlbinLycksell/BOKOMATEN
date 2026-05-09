// WatchFace.jsx — Apple Watch akutnotis on Magnus's wrist
const WatchFace = () => (
  <div style={wStyles.outer}>
    <div style={wStyles.bezel}>
      <div style={wStyles.screen}>
        <div style={wStyles.head}>
          <span style={wStyles.markBox}>S<span style={wStyles.dot}/></span>
          <span style={wStyles.brand}>SWITCHBOARD</span>
          <span style={wStyles.t}>nu</span>
        </div>
        <div style={wStyles.label}>AKUT</div>
        <div style={wStyles.title}>Eva S.<br/>Kista</div>
        <div style={wStyles.actions}>
          <div style={wStyles.btn}>Ta</div>
          <div style={{...wStyles.btn, ...wStyles.btnGhost}}>Skicka</div>
        </div>
      </div>
    </div>
    <div style={wStyles.cap}>Apple Watch · akutnotis</div>
  </div>
);

const wStyles = {
  outer: { display: "grid", placeItems: "center", gap: 16, padding: 20 },
  bezel: {
    width: 220, height: 264,
    background: "#1a1a1a",
    borderRadius: 48,
    padding: 12,
    boxShadow: "0 24px 48px -16px rgba(20,17,11,0.4)",
  },
  screen: {
    width: "100%", height: "100%",
    background: "#000", borderRadius: 38,
    color: "#fff", padding: "16px 14px",
    display: "flex", flexDirection: "column",
    border: "2px solid #E25822",
  },
  head: {
    display: "flex", alignItems: "center", gap: 6,
    fontFamily: "var(--font-mono)", fontSize: 9,
    letterSpacing: "0.08em", color: "rgba(255,255,255,0.7)",
  },
  markBox: {
    width: 14, height: 14, background: "#E25822", color: "#fff",
    borderRadius: 3, display: "grid", placeItems: "center",
    fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 9,
    position: "relative",
  },
  dot: { position: "absolute", right: -1, top: 4, width: 4, height: 4, background: "#fff", borderRadius: "50%" },
  brand: { flex: 1 },
  t: {},
  label: {
    fontFamily: "var(--font-mono)",
    fontSize: 10, letterSpacing: "0.1em",
    color: "#E25822", marginTop: 14,
  },
  title: {
    fontFamily: "var(--font-display)",
    fontSize: 26, fontWeight: 600,
    letterSpacing: "-0.02em",
    lineHeight: 1.05,
    marginTop: 4,
  },
  actions: { marginTop: "auto", display: "flex", gap: 6 },
  btn: {
    flex: 1, height: 32, borderRadius: 16,
    background: "#E25822", color: "#fff",
    display: "grid", placeItems: "center",
    fontSize: 13, fontWeight: 500,
  },
  btnGhost: {
    background: "transparent",
    border: "1px solid rgba(255,255,255,0.6)",
    color: "#fff",
  },
  cap: { fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.06em", color: "var(--fg-muted)" },
};

window.WatchFace = WatchFace;
