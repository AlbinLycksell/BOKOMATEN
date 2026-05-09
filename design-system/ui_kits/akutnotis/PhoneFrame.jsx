// PhoneFrame.jsx — minimal black bezel for showing iOS-style content.
const PhoneFrame = ({ children, time = "06:42" }) => (
  <div style={frameStyles.outer}>
    <div style={frameStyles.bezel}>
      <div style={frameStyles.notch}/>
      <div style={frameStyles.statusBar}>
        <span style={frameStyles.t}>{time}</span>
        <span style={frameStyles.icons}>
          <svg width="16" height="11" viewBox="0 0 16 11"><path d="M0 8h2v3H0zM4 6h2v5H4zM8 4h2v7H8zM12 1h2v10h-2z" fill="#fff"/></svg>
          <svg width="14" height="11" viewBox="0 0 14 11" fill="none"><path d="M1 4a8 8 0 0112 0M3 6.5a5 5 0 019 0M5.5 9a2.5 2.5 0 013 0" stroke="#fff" strokeWidth="1.4" strokeLinecap="round"/></svg>
          <svg width="24" height="11" viewBox="0 0 24 11"><rect x="0.5" y="0.5" width="20" height="10" rx="2.5" fill="none" stroke="#fff" opacity="0.8"/><rect x="2" y="2" width="14" height="7" rx="1" fill="#fff"/><rect x="21" y="3.5" width="2" height="4" rx="0.5" fill="#fff" opacity="0.8"/></svg>
        </span>
      </div>
      <div style={frameStyles.screen}>{children}</div>
    </div>
  </div>
);

const frameStyles = {
  outer: { display: "grid", placeItems: "center", padding: 28 },
  bezel: {
    width: 390, height: 800,
    background: "#000",
    borderRadius: 50,
    padding: "10px 8px 8px",
    
    position: "relative",
    overflow: "hidden",
  },
  notch: {
    position: "absolute", top: 12, left: "50%",
    transform: "translateX(-50%)",
    width: 110, height: 32,
    background: "#000", borderRadius: 20, zIndex: 2,
  },
  statusBar: {
    position: "absolute", top: 16, left: 0, right: 0,
    display: "flex", justifyContent: "space-between",
    padding: "0 28px",
    color: "#fff", zIndex: 3,
    fontFamily: "var(--font-body)",
    fontSize: 15, fontWeight: 500,
    fontFeatureSettings: '"tnum" 1',
  },
  t: { fontVariantNumeric: "tabular-nums" },
  icons: { display: "flex", gap: 5, alignItems: "center" },
  screen: {
    width: "100%", height: "100%",
    borderRadius: 42,
    overflow: "hidden",
    background: "#0A1F33",
    position: "relative",
  },
};

window.PhoneFrame = PhoneFrame;
