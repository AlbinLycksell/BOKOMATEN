import { Eyebrow } from "@/components/ui/eyebrow";

export function MarketingQuote() {
  return (
    <section className="bg-linne-deep px-[12%] py-24">
      <div className="mx-auto max-w-[1080px]">
        <Eyebrow className="mb-8">Från en VVS-företagare i Bromma</Eyebrow>
        <blockquote className="font-display font-medium text-text-strong leading-[1.08] tracking-[-0.02em] text-[clamp(36px,6vw,76px)] max-w-[20ch] m-0">
          &ldquo;Det här ser ut som något jag{" "}
          <em className="not-italic text-signaloranje">redan</em> använder.&rdquo;
        </blockquote>
        <div className="mt-9 flex flex-wrap items-center gap-3 text-[15px]">
          <span className="text-text-strong font-medium">Magnus Lindgren</span>
          <span className="text-border-strong">·</span>
          <span className="text-text-muted">Magnus VVS AB · 47 år · 9 anställda</span>
        </div>
      </div>
    </section>
  );
}
