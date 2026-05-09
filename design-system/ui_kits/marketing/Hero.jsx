// Hero.jsx — type-led hero. Klarna principle: scale aggressively.
// One headline, one decision. The headline IS the design.
const Hero = () => {
  return (
    <section style={heroStyles.section}>
      <div style={heroStyles.inner}>
        <div style={heroStyles.eyebrow}>SWITCHBOARD <span style={{color:"#E25822"}}>·</span> SVARSTJÄNSTEN FÖR HANTVERKARE</div>
        <h1 style={heroStyles.headline}>
          Magnus missar inga<br/>
          <span style={{color:"#E25822"}}>akutsamtal</span>.
        </h1>
        <p style={heroStyles.lede}>
          När en kund ringer svarar Switchboard inom två signaler, frågar artigt vad det gäller, och bokar in tiden direkt i din kalender. Du behöver inte stanna mitt i jobbet för att svara i telefon.
        </p>
        <div style={heroStyles.ctas}>
          <button className="v-btn v-btn--primary v-btn--lg">Boka demo</button>
          <button className="v-btn v-btn--secondary v-btn--lg">Se hur det funkar</button>
        </div>
        <div style={heroStyles.proof}>
          <span>1 495 SEK / mån</span>
          <span style={heroStyles.sep}>·</span>
          <span>30 dagar gratis</span>
          <span style={heroStyles.sep}>·</span>
          <span>Inget kreditkort</span>
        </div>
      </div>

      {/* Photo block — Pleo-still-life sensibility. Placeholder. */}
      <figure style={heroStyles.photo}>
        <div style={heroStyles.photoFrame}>
          <div style={heroStyles.photoCaption}>
            <div style={heroStyles.photoMeta}>PHOTOGRAPHY · PLACEHOLDER</div>
            <div style={heroStyles.photoLabel}>Magnus i panelbilen, 06:42, Bromma</div>
          </div>
        </div>
        <figcaption style={heroStyles.figcap}>
          Phone i magnetisk dashboardhållare. Bahco-skiftnyckel på passagerarsätet. Frost på vindrutan.
        </figcaption>
      </figure>
    </section>
  );
};

const heroStyles = {
  section: {
    background: "var(--linne)",
    padding: "80px 6% 64px",
  },
  inner: { maxWidth: 1280, margin: "0 auto", paddingBottom: 56 },
  eyebrow: {
    fontFamily: "var(--font-mono)",
    fontSize: 12, letterSpacing: "0.1em",
    color: "var(--fg-muted)",
    marginBottom: 32,
  },
  headline: {
    fontFamily: "var(--font-display)",
    fontSize: "clamp(56px, 9vw, 128px)",
    lineHeight: 1.0,
    letterSpacing: "-0.03em",
    fontWeight: 600,
    color: "var(--fg-strong)",
    margin: 0,
    maxWidth: "16ch",
    textWrap: "pretty",
  },
  lede: {
    marginTop: 32,
    maxWidth: "44ch",
    fontSize: 20,
    lineHeight: 1.5,
    color: "var(--fg)",
  },
  ctas: { display: "flex", gap: 12, marginTop: 36, flexWrap: "wrap" },
  proof: {
    marginTop: 24,
    fontSize: 14,
    color: "var(--fg-muted)",
    fontFeatureSettings: '"tnum" 1',
    display: "flex", gap: 10, flexWrap: "wrap", alignItems: "center",
  },
  sep: { color: "var(--border-strong)" },
  photo: { margin: 0, maxWidth: 1280, marginInline: "auto" },
  photoFrame: {
    aspectRatio: "16 / 9",
    background: "linear-gradient(135deg, #3D4D5C 0%, #1B2D40 50%, #14110B 100%)",
    borderRadius: 0, // Photographs are honest rectangles
    position: "relative",
    overflow: "hidden",
  },
  photoCaption: {
    position: "absolute",
    left: 32, bottom: 28,
    color: "#F4EFE6",
  },
  photoMeta: {
    fontFamily: "var(--font-mono)",
    fontSize: 11, letterSpacing: "0.1em",
    opacity: 0.65, marginBottom: 8,
  },
  photoLabel: {
    fontFamily: "var(--font-display)",
    fontSize: 22, fontWeight: 500,
    letterSpacing: "-0.01em",
  },
  figcap: {
    fontSize: 14, color: "var(--fg-muted)",
    marginTop: 14, fontStyle: "italic",
  },
};

window.Hero = Hero;
