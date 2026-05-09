// CallDetail.jsx — when Lena clicks into a samtal. Density appears, but earned.
const CallDetail = ({ call, onClose }) => {
  if (!call) return null;
  return (
    <div style={detailStyles.scrim} onClick={onClose}>
      <aside style={detailStyles.sheet} onClick={e => e.stopPropagation()}>
        <header style={detailStyles.head}>
          <button onClick={onClose} style={detailStyles.close} aria-label="Stäng">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"><path d="M18 6L6 18M6 6l12 12"/></svg>
          </button>
          <div style={detailStyles.eye}>22 MAJ · {call.time} · 4 MIN 12 SEK</div>
          <h2 style={detailStyles.h}>{call.who}</h2>
          <div style={detailStyles.subline}>
            <span>070-512 44 19</span>
            <span style={detailStyles.sep}>·</span>
            <span>{call.where}</span>
          </div>
          <div style={detailStyles.actions}>
            <button className="v-btn v-btn--navy v-btn--sm">Ring tillbaka</button>
            <button className="v-btn v-btn--secondary v-btn--sm">Skicka SMS</button>
            <button className="v-btn v-btn--ghost v-btn--sm">Boka om</button>
          </div>
        </header>

        <section style={detailStyles.section}>
          <div style={detailStyles.label}>SAMMANFATTNING</div>
          <p style={detailStyles.summary}>
            Inger Lindqvist, 71, ringer från Bromma. Vatten droppar under diskbänken sedan i går kväll, hon har ställt en hink under. Inget tryck, inget akut. AI:n bokade in ett besök torsdag 16:00 hos Magnus och bekräftade adressen via SMS.
          </p>
        </section>

        <section style={detailStyles.section}>
          <div style={detailStyles.label}>EXTRAHERAT</div>
          <dl style={detailStyles.kv}>
            <dt>Adress</dt><dd>Riddarsporrevägen 14, 168 47 Bromma</dd>
            <dt>Akutgrad</dt><dd>Låg · droppande, ingen översvämning</dd>
            <tr></tr>
            <dt>Bokad tid</dt><dd>Torsdag 23 maj · 16:00 · Magnus</dd>
            <dt>Kund sedan</dt><dd>2019 · 11 tidigare jobb</dd>
            <dt>Nyckelord</dt><dd>vattenläcka · diskbänk · droppande</dd>
          </dl>
        </section>

        <section style={detailStyles.section}>
          <div style={detailStyles.label}>UTSKRIFT</div>
          <div style={detailStyles.transcript}>
            <Line who="AI" t="00:02">Magnus VVS, det här är Sara. Hur kan jag hjälpa dig?</Line>
            <Line who="Inger" t="00:05">Ja hej, det är Inger Lindqvist. Det droppar under min diskbänk.</Line>
            <Line who="AI" t="00:14">Okej, då hjälper vi dig med det. Är det mycket vatten? Står det och rinner, eller droppar det?</Line>
            <Line who="Inger" t="00:21">Det droppar. Jag har en hink under. Men jag vill ju ha det fixat.</Line>
            <Line who="AI" t="00:30">Då bokar jag in Magnus i morgon — torsdag — kl 16:00 hos dig. Adressen är fortfarande Riddarsporrevägen 14?</Line>
            <Line who="Inger" t="00:42">Ja det stämmer.</Line>
            <Line who="AI" t="00:45">Kanon, då bokar jag in det. Du får ett SMS med bekräftelsen.</Line>
          </div>
        </section>
      </aside>
    </div>
  );
};

const Line = ({ who, t, children }) => (
  <div style={detailStyles.line}>
    <span style={detailStyles.lineT}>{t}</span>
    <span style={{...detailStyles.lineWho, color: who === "AI" ? "#E25822" : "var(--fg-strong)"}}>{who}</span>
    <span style={detailStyles.lineText}>{children}</span>
  </div>
);

const detailStyles = {
  scrim: {
    position: "fixed", inset: 0,
    background: "rgba(20,17,11,0.45)",
    display: "flex", justifyContent: "flex-end",
    zIndex: 100,
    animation: "v-fade 120ms",
  },
  sheet: {
    width: 560, maxWidth: "100%",
    background: "var(--linne)",
    overflowY: "auto",
    boxShadow: "0 24px 48px -16px rgba(20,17,11,0.4)",
  },
  head: { padding: "28px 36px 24px", borderBottom: "1px solid var(--border)", position: "relative" },
  close: {
    position: "absolute", right: 18, top: 18,
    width: 36, height: 36, borderRadius: "50%",
    background: "transparent", border: "none",
    cursor: "pointer", color: "var(--fg-muted)",
    display: "grid", placeItems: "center",
  },
  eye: {
    fontFamily: "var(--font-mono)", fontSize: 11,
    letterSpacing: "0.08em", color: "var(--fg-muted)",
    fontFeatureSettings: '"tnum" 1',
  },
  h: {
    fontFamily: "var(--font-display)", fontSize: 32,
    fontWeight: 600, letterSpacing: "-0.015em",
    color: "var(--fg-strong)", margin: "8px 0 6px",
  },
  subline: { fontSize: 14, color: "var(--fg-muted)", display: "flex", gap: 10 },
  sep: { color: "var(--border-strong)" },
  actions: { marginTop: 18, display: "flex", gap: 8, flexWrap: "wrap" },
  section: { padding: "24px 36px", borderBottom: "1px solid var(--border)" },
  label: {
    fontFamily: "var(--font-mono)", fontSize: 11,
    letterSpacing: "0.08em", color: "var(--fg-muted)",
    marginBottom: 10,
  },
  summary: { fontSize: 16, lineHeight: 1.55, color: "var(--fg)", margin: 0 },
  kv: {
    display: "grid", gridTemplateColumns: "140px 1fr",
    rowGap: 10, columnGap: 16, margin: 0, fontSize: 14,
  },
  transcript: { display: "grid", gap: 8 },
  line: {
    display: "grid",
    gridTemplateColumns: "44px 56px 1fr",
    gap: 10,
    fontSize: 14, lineHeight: 1.5,
  },
  lineT: { fontFamily: "var(--font-mono)", fontSize: 12, color: "var(--fg-muted)", fontFeatureSettings: '"tnum" 1' },
  lineWho: { fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 500, letterSpacing: "0.04em" },
  lineText: { color: "var(--fg)" },
};

window.CallDetail = CallDetail;
