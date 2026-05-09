import { Button } from "@/components/ui/button";
import { Eyebrow } from "@/components/ui/eyebrow";

export function MarketingHero() {
  return (
    <section className="bg-linne px-[6%] pt-20 pb-16">
      <div className="mx-auto max-w-[1280px]">
        <Eyebrow className="mb-8">
          Switchboard <span className="text-signaloranje not-italic">·</span> Svarstjänsten för hantverkare
        </Eyebrow>

        <h1 className="font-display font-semibold tracking-[-0.03em] text-text-strong leading-[1.0] text-[clamp(56px,9vw,128px)] max-w-[16ch]">
          Magnus missar inga{" "}
          <span className="text-signaloranje">akutsamtal</span>
          <span className="inline-block w-[0.18em] h-[0.18em] align-baseline ml-[0.04em] bg-havsbla rounded-[2px]" />
        </h1>

        <p className="mt-8 max-w-[44ch] text-[20px] leading-[1.5] text-text">
          När en kund ringer svarar Switchboard inom två signaler, frågar artigt
          vad det gäller, och bokar in tiden direkt i din kalender. Du behöver
          inte stanna mitt i jobbet för att svara i telefon.
        </p>

        <div className="flex flex-wrap gap-3 mt-9">
          <Button variant="primary" size="lg">
            Boka demo
          </Button>
          <Button variant="secondary" size="lg">
            Se hur det funkar
          </Button>
        </div>

        <div className="mt-6 flex flex-wrap items-center gap-2.5 text-sm text-text-muted v-tnum">
          <span>1 495 SEK / mån</span>
          <span className="text-border-strong">·</span>
          <span>30 dagar gratis</span>
          <span className="text-border-strong">·</span>
          <span>Inget kreditkort</span>
        </div>
      </div>
    </section>
  );
}
