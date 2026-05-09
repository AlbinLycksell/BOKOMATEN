interface PhotoFrameProps {
  meta: string;
  label: string;
  caption?: string;
  className?: string;
}

/**
 * Pleo-style still-life photo frame placeholder. The aspect-3/2 dark
 * "photograph" stands in until production photography ships. Honest
 * rectangle, no rounded corners.
 */
export function PhotoFrame({ meta, label, caption, className }: PhotoFrameProps) {
  return (
    <figure className={className} style={{ margin: 0 }}>
      <div
        className="relative w-full overflow-hidden bg-havsbla text-linne"
        style={{ aspectRatio: "16 / 9" }}
      >
        <div
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(135deg, #3D4D5C 0%, #1B2D40 50%, #14110B 100%)",
          }}
        />
        <div className="absolute left-8 bottom-7">
          <div className="font-mono text-[11px] tracking-[0.1em] uppercase opacity-70 mb-2">
            {meta}
          </div>
          <div className="font-display text-[22px] font-medium tracking-[-0.005em]">
            {label}
          </div>
        </div>
      </div>
      {caption ? (
        <figcaption className="mt-3.5 text-sm text-text-muted italic">
          {caption}
        </figcaption>
      ) : null}
    </figure>
  );
}
