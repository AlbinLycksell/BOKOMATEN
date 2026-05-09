import { MarketingFooter } from "@/components/marketing/footer";
import { MarketingHero } from "@/components/marketing/hero";
import { PhotoFrame } from "@/components/marketing/photo-frame";
import { PriceCard } from "@/components/marketing/price-card";
import { MarketingQuote } from "@/components/marketing/quote-block";
import { MarketingTopNav } from "@/components/marketing/top-nav";
import { Eyebrow } from "@/components/ui/eyebrow";

const PRICING = [
  {
    name: "Starter",
    price: "995",
    description: "För enskilda hantverkare som börjar låta AI:n svara.",
    features: [
      "200 samtal / mån",
      "5 samtidiga samtal",
      "1 telefonnummer",
      "Mejl- & SMS-kvitton",
    ],
    cta: "Kom igång",
  },
  {
    name: "Professional",
    price: "1 495",
    description: "Vanligaste valet — passar tre till tjugo anställda.",
    features: [
      "600 samtal / mån",
      "25 samtidiga samtal",
      "3 telefonnummer",
      "Bokningsbekräftelser via Fortnox / Visma / Google Calendar",
      "Eskaleringskedja med jourtekniker",
    ],
    cta: "Boka demo",
    featured: true,
  },
  {
    name: "Premium",
    price: "3 495",
    description: "Större firmor som behöver multi-kontor och varumärke.",
    features: [
      "Obegränsade samtal",
      "Multi-kontor",
      "Egen varumärkesfärg & SMS-avsändarid",
      "Prioriterad support",
    ],
    cta: "Kontakta oss",
  },
];

const FEATURES = [
  {
    eyebrow: "Svar i två signaler",
    title: "AI:n hör som en människa.",
    body: "Svenska. Naturlig dialog. Förstår när det är akut. Magnus testar själv direkt i webbläsaren — du behöver inget kreditkort för att höra hur det låter.",
  },
  {
    eyebrow: "Inkommande sorterat",
    title: "Lena börjar dagen lugnt.",
    body: "Tre akutjobb i natt. Sju bokningar. Noll missat. Briefingen i din inkorg är redan ifylld klockan 06:42 — du häller upp kaffet, läser igenom, och alla samtal är redan hanterade.",
  },
  {
    eyebrow: "Akutläge",
    title: "Alex får ett ringsignal — inte en text.",
    body: "Misstänkt gasläcka i Kista, kund i hörlurarna, två val på låsskärmen: ta jobbet eller skicka tillbaka. Åtta sekunder, ett beslut.",
  },
];

export default function MarketingPage() {
  return (
    <div className="min-h-screen bg-linne text-text">
      <MarketingTopNav />
      <MarketingHero />

      <section className="px-[6%] pb-24">
        <div className="mx-auto max-w-[1280px]">
          <PhotoFrame
            meta="Photography · Placeholder"
            label="Magnus i panelbilen, 06:42, Bromma"
            caption="Phone i magnetisk dashboardhållare. Bahco-skiftnyckel på passagerarsätet. Frost på vindrutan."
          />
        </div>
      </section>

      <MarketingQuote />

      <section className="px-[6%] py-24">
        <div className="mx-auto max-w-[1280px] grid gap-16">
          {FEATURES.map((f, i) => (
            <article
              key={i}
              className="grid gap-8 md:grid-cols-[1fr_1fr] items-center"
            >
              <div className={i % 2 === 1 ? "md:order-2" : ""}>
                <Eyebrow className="mb-5">{f.eyebrow}</Eyebrow>
                <h2 className="font-display font-semibold tracking-[-0.02em] text-text-strong leading-[1.05] text-[clamp(36px,5vw,64px)] max-w-[18ch]">
                  {f.title}
                </h2>
                <p className="mt-5 max-w-[44ch] text-[18px] leading-[1.55] text-text">
                  {f.body}
                </p>
              </div>
              <PhotoFrame
                meta={`Photography · ${f.eyebrow}`}
                label={f.title.replace(/\.$/, "")}
              />
            </article>
          ))}
        </div>
      </section>

      <section id="priser" className="bg-linne-deep px-[6%] py-24">
        <div className="mx-auto max-w-[1280px]">
          <Eyebrow className="mb-5">Priser</Eyebrow>
          <h2 className="font-display font-semibold tracking-[-0.02em] text-text-strong leading-[1.05] text-[clamp(36px,5vw,64px)] max-w-[20ch]">
            Tre planer, ingen lock-in.
          </h2>
          <p className="mt-4 max-w-[50ch] text-[17px] leading-[1.5] text-text">
            Du kan byta plan, pausa, eller avsluta direkt i Switchboard. Inget
            kreditkort vid registrering. Första 30 dagarna är gratis.
          </p>

          <div className="mt-12 grid gap-5 lg:grid-cols-3">
            {PRICING.map((p) => (
              <PriceCard key={p.name} {...p} />
            ))}
          </div>
        </div>
      </section>

      <section className="bg-linne px-[6%] py-24">
        <div className="mx-auto max-w-[1080px] text-center">
          <Eyebrow className="mb-6 mx-auto">Boka demo</Eyebrow>
          <h2 className="font-display font-semibold tracking-[-0.02em] text-text-strong leading-[1.05] text-[clamp(36px,5vw,64px)] max-w-[24ch] mx-auto">
            Magnus svarar i två signaler. Du svarar i en.
          </h2>
          <p className="mt-5 max-w-[50ch] mx-auto text-[18px] leading-[1.55] text-text">
            Tjugo minuter. Du ser röstdemot, vi konfigurerar din firma live, och
            du kör ditt första riktiga test-samtal innan vi lägger på.
          </p>
          <div className="mt-8 inline-flex items-center justify-center gap-3">
            <a
              href="mailto:hej@switchboard.se"
              className="inline-flex h-14 px-8 items-center justify-center rounded-pill bg-signaloranje text-white text-base font-medium hover:bg-signaloranje-press transition-colors"
            >
              Boka demo
            </a>
          </div>
        </div>
      </section>

      <MarketingFooter />
    </div>
  );
}
