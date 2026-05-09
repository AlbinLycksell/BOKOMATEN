// Footer.jsx — restrained navy footer, link columns + brand.
const Footer = () => (
  <footer style={footerStyles.bar}>
    <div style={footerStyles.inner}>
      <div style={footerStyles.brandCol}>
        <div style={footerStyles.word}>Switchboard<span style={footerStyles.dot}/></div>
        <div style={footerStyles.tag}>Svarstjänsten för hantverkare. Stockholm · Göteborg · Malmö · Skellefteå.</div>
      </div>
      <div style={footerStyles.cols}>
        <FCol title="Produkt" items={["Hur det funkar", "För VVS", "För el", "För snickeri", "Integrationer"]}/>
        <FCol title="Företag" items={["Om oss", "Karriär", "Press", "Kontakt"]}/>
        <FCol title="Hjälp" items={["Hjälpcenter", "Status", "Säkerhet", "Personuppgifter"]}/>
      </div>
    </div>
    <div style={footerStyles.legal}>
      <span>© 2026 Switchboard AB · Org.nr 559042-5566</span>
      <span style={footerStyles.lLinks}>
        <a href="#" style={footerStyles.lLink}>Villkor</a>
        <a href="#" style={footerStyles.lLink}>Sekretess</a>
        <a href="#" style={footerStyles.lLink}>Cookies</a>
      </span>
    </div>
  </footer>
);

const FCol = ({ title, items }) => (
  <div>
    <div style={footerStyles.colHead}>{title}</div>
    <ul style={footerStyles.colList}>
      {items.map(i => <li key={i}><a href="#" style={footerStyles.colLink}>{i}</a></li>)}
    </ul>
  </div>
);

const footerStyles = {
  bar: { background: "var(--havsbla)", color: "var(--fg-on-dark)", padding: "80px 6% 32px" },
  inner: {
    maxWidth: 1280, margin: "0 auto",
    display: "grid", gridTemplateColumns: "1.4fr 2fr", gap: 64,
    paddingBottom: 64,
    borderBottom: "1px solid rgba(244,239,230,0.12)",
  },
  brandCol: {},
  word: {
    fontFamily: "var(--font-display)",
    fontWeight: 600, letterSpacing: "-0.025em",
    fontSize: 28, color: "#F4EFE6",
  },
  dot: {
    display: "inline-block", width: "0.36em", height: "0.36em",
    background: "#E25822", borderRadius: "50%",
    marginLeft: "0.04em", verticalAlign: "baseline",
    transform: "translateY(0.04em)",
  },
  tag: {
    marginTop: 16, fontSize: 14,
    color: "rgba(244,239,230,0.65)",
    maxWidth: "32ch", lineHeight: 1.5,
  },
  cols: { display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 32 },
  colHead: {
    fontFamily: "var(--font-mono)",
    fontSize: 12, letterSpacing: "0.08em",
    textTransform: "uppercase",
    color: "rgba(244,239,230,0.55)",
    marginBottom: 14,
  },
  colList: { listStyle: "none", margin: 0, padding: 0, display: "grid", gap: 10 },
  colLink: {
    color: "rgba(244,239,230,0.85)",
    textDecoration: "none",
    fontSize: 14,
  },
  legal: {
    maxWidth: 1280, margin: "0 auto",
    paddingTop: 24,
    fontSize: 12, color: "rgba(244,239,230,0.5)",
    fontFeatureSettings: '"tnum" 1',
    display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 16,
  },
  lLinks: { display: "flex", gap: 18 },
  lLink: { color: "rgba(244,239,230,0.7)", textDecoration: "none" },
};

window.Footer = Footer;
