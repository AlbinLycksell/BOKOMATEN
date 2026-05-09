// LockScreen.jsx — Alex's lock screen at 19:47, evening, kids in bed.
// The akutnotis arrives. Eight seconds, one decision.
const LockScreen = ({ akut = false, expanded = false, onTap }) => (
  <div style={lockStyles.bg}>
    {/* Wallpaper — subtle photo placeholder */}
    <div style={lockStyles.wallpaper}/>

    {/* Big lock-screen clock */}
    <div style={lockStyles.clock}>
      <div style={lockStyles.date}>onsdag, 21 maj</div>
      <div style={lockStyles.time}>19:47</div>
    </div>

    {/* Notification(s) */}
    <div style={lockStyles.notifStack}>
      {akut && (
        <div style={{
          ...lockStyles.notif,
          ...lockStyles.akut,
          ...(expanded ? lockStyles.expanded : {}),
        }} className="v-akut-pulse" onClick={onTap}>
          <div style={lockStyles.akutHead}>
            <div style={lockStyles.akutBrand}>
              <span style={lockStyles.akutMark}>S<span style={lockStyles.akutDot}/></span>
              <span>SWITCHBOARD</span>
            </div>
            <span style={lockStyles.akutMeta}>nu</span>
          </div>
          <div style={lockStyles.akutLabel}>AKUT · MISSTÄNKT GASLÄCKA</div>
          <div style={lockStyles.akutTitle}>Eva Sundström · Kista</div>
          <div style={lockStyles.akutWho}>Ringde 19:47 · 2 min sedan</div>
          {expanded && (
            <div style={lockStyles.actions}>
              <button style={{...lockStyles.act, ...lockStyles.actPrimary}}>Ta jobbet</button>
              <button style={lockStyles.act}>Skicka tillbaka</button>
            </div>
          )}
        </div>
      )}
      {!akut && (
        <div style={lockStyles.normalNotif}>
          <div style={lockStyles.normalHead}>SWITCHBOARD · 14:32</div>
          <div style={lockStyles.normalTitle}>Inger Lindqvist bokade torsdag 16:00</div>
          <div style={lockStyles.normalSub}>Vattenläcka under diskbänken · Bromma</div>
        </div>
      )}
    </div>
  </div>
);

const lockStyles = {
  bg: {
    width: "100%", height: "100%",
    background: "linear-gradient(180deg, #0A1F33 0%, #14110B 100%)",
    position: "relative",
    color: "#F4EFE6",
    paddingTop: 72,
    overflow: "hidden",
  },
  wallpaper: {
    position: "absolute", inset: 0,
    background: "radial-gradient(circle at 30% 20%, rgba(226,88,34,0.12), transparent 50%), radial-gradient(circle at 80% 80%, rgba(244,239,230,0.06), transparent 50%)",
  },
  clock: {
    position: "relative",
    textAlign: "center",
    padding: "12px 20px 24px",
  },
  date: {
    fontSize: 15, fontWeight: 500,
    opacity: 0.9, marginBottom: 2,
  },
  time: {
    fontFamily: "var(--font-display)",
    fontSize: 92, fontWeight: 300,
    letterSpacing: "-0.04em",
    fontFeatureSettings: '"tnum" 1',
    lineHeight: 1.0,
  },
  notifStack: {
    position: "absolute",
    left: 14, right: 14, bottom: 100,
    display: "grid", gap: 10,
  },
  notif: {
    background: "rgba(255,255,255,0.10)",
    backdropFilter: "blur(20px)",
    WebkitBackdropFilter: "blur(20px)",
    borderRadius: 18,
    padding: "14px 16px",
    cursor: "pointer",
  },
  akut: {
    background: "#E25822",
    backdropFilter: "none", WebkitBackdropFilter: "none",
    color: "#fff",
    boxShadow: "0 0 0 4px rgba(226,88,34,0.18), 0 12px 32px -8px rgba(226,88,34,0.45)",
  },
  expanded: { padding: "16px 18px 18px" },
  akutHead: { display: "flex", justifyContent: "space-between", fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.08em", opacity: 0.9 },
  akutBrand: { display: "flex", alignItems: "center", gap: 8 },
  akutMark: {
    width: 16, height: 16,
    background: "rgba(255,255,255,0.18)",
    borderRadius: 4,
    display: "grid", placeItems: "center",
    fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 11,
    position: "relative",
  },
  akutDot: { position: "absolute", right: -1, top: 5, width: 5, height: 5, background: "#fff", borderRadius: "50%" },
  akutMeta: { opacity: 0.8 },
  akutLabel: {
    fontFamily: "var(--font-mono)", fontSize: 11,
    letterSpacing: "0.08em", marginTop: 14, marginBottom: 6,
    opacity: 0.85,
  },
  akutTitle: {
    fontFamily: "var(--font-display)",
    fontSize: 22, fontWeight: 600, letterSpacing: "-0.012em",
    lineHeight: 1.2,
  },
  akutWho: { marginTop: 4, fontSize: 13, opacity: 0.85, fontFeatureSettings: '"tnum" 1' },
  actions: { display: "flex", gap: 8, marginTop: 14 },
  act: {
    flex: 1, height: 40,
    border: "1px solid rgba(255,255,255,0.6)",
    borderRadius: 9999,
    background: "transparent", color: "#fff",
    fontWeight: 500, fontSize: 14,
    fontFamily: "var(--font-body)",
    cursor: "pointer",
  },
  actPrimary: { background: "#fff", color: "#C84612", borderColor: "#fff" },

  normalNotif: {
    background: "rgba(255,255,255,0.10)",
    backdropFilter: "blur(20px)", WebkitBackdropFilter: "blur(20px)",
    borderRadius: 18, padding: "14px 16px",
  },
  normalHead: { fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.08em", opacity: 0.7 },
  normalTitle: { fontFamily: "var(--font-display)", fontSize: 16, fontWeight: 500, marginTop: 8, lineHeight: 1.3 },
  normalSub: { fontSize: 13, opacity: 0.75, marginTop: 4 },
};

window.LockScreen = LockScreen;
