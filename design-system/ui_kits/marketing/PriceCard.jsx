// PriceCard.jsx — Pleo-style price visible without three clicks.
// Magnus does not "request a demo" without seeing the price.
const PriceCard = ({ name, price, period = "/ mån", description, features, cta = "Kom igång", featured = false }) => {
  return (
    <div style={{
      ...priceCardStyles.card,
      ...(featured ? priceCardStyles.featured : {}),
    }}>
      {featured && <div style={priceCardStyles.badge}>Vanligast</div>}
      <div style={priceCardStyles.name}>{name}</div>
      <div style={priceCardStyles.priceRow}>
        <span style={priceCardStyles.price}>{price}</span>
        <span style={priceCardStyles.period}>{period}</span>
      </div>
      <div style={priceCardStyles.desc}>{description}</div>
      <ul style={priceCardStyles.list}>
        {features.map((f, i) => (
          <li key={i} style={priceCardStyles.feat}>
            <span style={{
              ...priceCardStyles.tick,
              color: featured ? "#E25822" : "#2F5233",
            }}>—</span>
            <span>{f}</span>
          </li>
        ))}
      </ul>
      <button className={featured ? "v-btn v-btn--primary v-btn--lg" : "v-btn v-btn--navy v-btn--lg"} style={{width:"100%"}}>{cta}</button>
    </div>
  );
};

const priceCardStyles = {
  card: {
    background: "#fff",
    border: "1px solid var(--border)",
    borderRadius: 14,
    padding: "28px 28px 28px",
    position: "relative",
    display: "flex",
    flexDirection: "column",
  },
  featured: {
    background: "var(--havsbla)",
    color: "var(--fg-on-dark)",
    border: "1px solid var(--havsbla)",
  },
  badge: {
    position: "absolute", top: -12, left: 24,
    background: "#E25822", color: "#fff",
    fontSize: 11, letterSpacing: "0.08em",
    textTransform: "uppercase",
    fontFamily: "var(--font-mono)",
    padding: "5px 10px", borderRadius: 9999,
  },
  name: {
    fontFamily: "var(--font-mono)",
    fontSize: 12, letterSpacing: "0.08em",
    textTransform: "uppercase",
    opacity: 0.7,
    marginBottom: 14,
  },
  priceRow: { display: "flex", alignItems: "baseline", gap: 6 },
  price: {
    fontFamily: "var(--font-display)",
    fontSize: 56,
    fontWeight: 600,
    letterSpacing: "-0.02em",
    fontFeatureSettings: '"tnum" 1',
    lineHeight: 1.0,
  },
  period: {
    fontSize: 16, opacity: 0.65,
  },
  desc: {
    marginTop: 16,
    fontSize: 15, lineHeight: 1.5,
    opacity: 0.85,
  },
  list: {
    margin: "24px 0 28px",
    padding: 0, listStyle: "none",
    flex: 1,
    display: "grid", gap: 10,
  },
  feat: {
    display: "flex", gap: 10,
    fontSize: 15, lineHeight: 1.5,
  },
  tick: {
    fontFamily: "var(--font-mono)",
    fontWeight: 600,
    flex: "0 0 auto",
    width: 16,
  },
};

window.PriceCard = PriceCard;
