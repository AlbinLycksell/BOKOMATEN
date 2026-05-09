// TopNav.jsx — Verkstad marketing nav. Sticky, navy, restrained.
const TopNav = ({ active = "Produkt" }) => {
  const links = ["Produkt", "Priser", "Kunder", "För jourtekniker"];
  return (
    <nav style={topNavStyles.bar}>
      <div style={topNavStyles.inner}>
        <a href="#" style={topNavStyles.brand}>
          <span style={topNavStyles.word}>Switchboard<span style={topNavStyles.dot}/></span>
        </a>
        <ul style={topNavStyles.links}>
          {links.map(l => (
            <li key={l}>
              <a href="#" style={{
                ...topNavStyles.link,
                ...(l === active ? topNavStyles.linkActive : {})
              }}>{l}</a>
            </li>
          ))}
        </ul>
        <div style={topNavStyles.right}>
          <a href="#" style={topNavStyles.login}>Logga in</a>
          <button className="v-btn v-btn--primary v-btn--sm">Boka demo</button>
        </div>
      </div>
    </nav>
  );
};

const topNavStyles = {
  bar: {
    position: "sticky", top: 0, zIndex: 50,
    background: "rgba(10,31,51,0.96)",
    borderBottom: "1px solid rgba(244,239,230,0.08)",
  },
  inner: {
    maxWidth: 1280, margin: "0 auto",
    padding: "14px 6%",
    display: "flex", alignItems: "center", gap: 32,
  },
  brand: { textDecoration: "none", display: "inline-flex", alignItems: "center" },
  word: {
    fontFamily: "var(--font-display)",
    fontWeight: 600, letterSpacing: "-0.025em",
    fontSize: 20, color: "#F4EFE6",
  },
  dot: {
    display: "inline-block", width: "0.36em", height: "0.36em",
    background: "#E25822", borderRadius: "50%",
    marginLeft: "0.04em", verticalAlign: "baseline",
    transform: "translateY(0.04em)",
  },
  links: {
    display: "flex", gap: 28, listStyle: "none",
    margin: 0, padding: 0, flex: 1,
  },
  link: {
    color: "rgba(244,239,230,0.72)",
    textDecoration: "none",
    fontSize: 14, fontWeight: 500,
    fontFamily: "var(--font-body)",
  },
  linkActive: { color: "#F4EFE6" },
  right: { display: "flex", gap: 16, alignItems: "center" },
  login: {
    color: "rgba(244,239,230,0.72)",
    textDecoration: "none",
    fontSize: 14, fontWeight: 500,
  },
};

window.TopNav = TopNav;
