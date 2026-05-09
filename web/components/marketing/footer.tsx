import { Wordmark } from "@/components/brand/wordmark";

const COLUMNS = [
  {
    title: "Produkt",
    items: ["Hur det funkar", "För VVS", "För el", "För snickeri", "Integrationer"],
  },
  {
    title: "Företag",
    items: ["Om oss", "Karriär", "Press", "Kontakt"],
  },
  {
    title: "Hjälp",
    items: ["Hjälpcenter", "Status", "Säkerhet", "Personuppgifter"],
  },
];

export function MarketingFooter() {
  return (
    <footer className="bg-havsbla text-linne px-[6%] pt-20 pb-8">
      <div className="mx-auto max-w-[1280px] grid grid-cols-1 lg:grid-cols-[1.4fr_2fr] gap-16 pb-16 border-b border-border-on-dark">
        <div>
          <Wordmark tone="linne" size="xl" />
          <p className="mt-4 max-w-[32ch] text-sm leading-[1.5] text-linne/65">
            Svarstjänsten för hantverkare. Stockholm · Göteborg · Malmö ·
            Skellefteå.
          </p>
        </div>
        <div className="grid grid-cols-3 gap-8">
          {COLUMNS.map((col) => (
            <div key={col.title}>
              <div className="font-mono text-[12px] uppercase tracking-[0.08em] text-linne/55 mb-3.5">
                {col.title}
              </div>
              <ul className="list-none m-0 p-0 grid gap-2.5">
                {col.items.map((item) => (
                  <li key={item}>
                    <a
                      href="#"
                      className="text-sm text-linne/85 hover:text-linne transition-colors"
                    >
                      {item}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </div>
      <div className="mx-auto max-w-[1280px] pt-6 flex flex-wrap justify-between gap-4 text-xs text-linne/50 v-tnum">
        <span>© 2026 Switchboard AB · Org.nr 559042-5566</span>
        <span className="flex gap-4">
          <a href="#" className="text-linne/70 hover:text-linne">Villkor</a>
          <a href="#" className="text-linne/70 hover:text-linne">Sekretess</a>
          <a href="#" className="text-linne/70 hover:text-linne">Cookies</a>
        </span>
      </div>
    </footer>
  );
}
