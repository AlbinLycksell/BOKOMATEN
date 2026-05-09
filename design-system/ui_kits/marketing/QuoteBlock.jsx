// QuoteBlock.jsx — pull-quote in Magnus's actual voice.
const QuoteBlock = () => (
  <section style={quoteStyles.section}>
    <div style={quoteStyles.inner}>
      <div style={quoteStyles.eyebrow}>FRÅN EN VVS-FÖRETAGARE I BROMMA</div>
      <blockquote style={quoteStyles.quote}>
        "Det här ser ut som något jag <em style={quoteStyles.em}>redan</em> använder."
      </blockquote>
      <div style={quoteStyles.who}>
        <span style={quoteStyles.name}>Magnus Lindgren</span>
        <span style={quoteStyles.sep}>·</span>
        <span style={quoteStyles.role}>Magnus VVS AB · 47 år · 9 anställda</span>
      </div>
    </div>
  </section>
);

const quoteStyles = {
  section: {
    background: "var(--linne-deep)",
    padding: "96px 12% 96px", // double-margin context
  },
  inner: { maxWidth: 1080, margin: "0 auto" },
  eyebrow: {
    fontFamily: "var(--font-mono)",
    fontSize: 12, letterSpacing: "0.1em",
    color: "var(--fg-muted)",
    marginBottom: 32,
  },
  quote: {
    fontFamily: "var(--font-display)",
    fontSize: "clamp(36px, 6vw, 76px)",
    lineHeight: 1.08,
    letterSpacing: "-0.02em",
    fontWeight: 500,
    color: "var(--fg-strong)",
    margin: 0,
    maxWidth: "20ch",
  },
  em: {
    fontStyle: "normal",
    color: "#E25822",
  },
  who: {
    marginTop: 36,
    display: "flex", alignItems: "center", gap: 12, flexWrap: "wrap",
    fontSize: 15,
  },
  name: { color: "var(--fg-strong)", fontWeight: 500 },
  role: { color: "var(--fg-muted)" },
  sep: { color: "var(--border-strong)" },
};

window.QuoteBlock = QuoteBlock;
