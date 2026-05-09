// SideNav.jsx — dashboard left rail. Lena's editorial calm starts here.
const SideNav = ({ active = "Briefing" }) => {
  const items = [
    { name: "Briefing", icon: "M3 6h18M3 12h18M3 18h12" },
    { name: "Samtal", icon: "M3 5l3-2 3 3-2 3a12 12 0 006 6l3-2 3 3-2 3A18 18 0 013 5z" },
    { name: "Kalender", icon: "M3 5h18v16H3zM3 9h18M8 3v4M16 3v4" },
    { name: "Kunder", icon: "M3 20a7 7 0 0114 0M10 11a4 4 0 100-8 4 4 0 000 8z" },
    { name: "Jourtekniker", icon: "M12 2l3 6 6 1-4.5 4.5L18 20l-6-3-6 3 1.5-6.5L3 9l6-1z" },
  ];
  return (
    <aside style={sideStyles.bar}>
      <a href="#" style={sideStyles.brand}>
        <span style={sideStyles.word}>Switchboard<span style={sideStyles.dot}/></span>
      </a>
      <nav style={sideStyles.nav}>
        {items.map(it => (
          <a key={it.name} href="#" style={{
            ...sideStyles.item,
            ...(it.name === active ? sideStyles.active : {})
          }}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round"><path d={it.icon}/></svg>
            <span>{it.name}</span>
          </a>
        ))}
      </nav>
      <div style={sideStyles.bottom}>
        <a href="#" style={sideStyles.item}>
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"><circle cx="12" cy="12" r="3"/><path d="M19 12a7 7 0 00-.1-1.2l2-1.5-2-3.4-2.4.9a7 7 0 00-2-1.2L14 3h-4l-.5 2.6a7 7 0 00-2 1.2l-2.4-.9-2 3.4 2 1.5A7 7 0 005 12c0 .4 0 .8.1 1.2l-2 1.5 2 3.4 2.4-.9c.6.5 1.3.9 2 1.2L10 21h4l.5-2.6c.7-.3 1.4-.7 2-1.2l2.4.9 2-3.4-2-1.5c0-.4.1-.8.1-1.2z"/></svg>
          <span>Inställningar</span>
        </a>
        <div style={sideStyles.account}>
          <div style={sideStyles.avatar}>L</div>
          <div>
            <div style={sideStyles.aName}>Lena Andersson</div>
            <div style={sideStyles.aSub}>Magnus VVS AB</div>
          </div>
        </div>
      </div>
    </aside>
  );
};

const sideStyles = {
  bar: {
    width: 240, flex: "0 0 240px",
    background: "var(--linne)",
    borderRight: "1px solid var(--border)",
    padding: "20px 14px 16px",
    display: "flex", flexDirection: "column",
    height: "100vh", position: "sticky", top: 0,
  },
  brand: { padding: "8px 10px 24px", textDecoration: "none" },
  word: {
    fontFamily: "var(--font-display)",
    fontWeight: 600, letterSpacing: "-0.025em",
    fontSize: 18, color: "var(--havsbla)",
  },
  dot: {
    display: "inline-block", width: "0.36em", height: "0.36em",
    background: "#E25822", borderRadius: "50%",
    marginLeft: "0.04em",
  },
  nav: { display: "flex", flexDirection: "column", gap: 2, flex: 1 },
  item: {
    display: "flex", alignItems: "center", gap: 10,
    padding: "9px 12px",
    borderRadius: 9999,
    color: "var(--fg)",
    fontSize: 14, fontWeight: 500,
    textDecoration: "none",
    transition: "background 120ms",
  },
  active: { background: "var(--havsbla)", color: "var(--fg-on-dark)" },
  bottom: { borderTop: "1px solid var(--border)", paddingTop: 12, marginTop: 12 },
  account: {
    display: "flex", alignItems: "center", gap: 10,
    padding: "10px 12px", marginTop: 4,
  },
  avatar: {
    width: 32, height: 32, borderRadius: "50%",
    background: "var(--havsbla)", color: "var(--fg-on-dark)",
    fontSize: 14, fontWeight: 500,
    display: "grid", placeItems: "center",
  },
  aName: { fontSize: 13, fontWeight: 500, color: "var(--fg-strong)" },
  aSub: { fontSize: 12, color: "var(--fg-muted)" },
};

window.SideNav = SideNav;
