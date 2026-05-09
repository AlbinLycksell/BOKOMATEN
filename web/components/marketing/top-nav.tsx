import Link from "next/link";

import { Wordmark } from "@/components/brand/wordmark";
import { Button } from "@/components/ui/button";

const LINKS = [
  { href: "#produkt", label: "Produkt" },
  { href: "#priser", label: "Priser" },
  { href: "#kunder", label: "Kunder" },
  { href: "#jourtekniker", label: "För jourtekniker" },
];

interface TopNavProps {
  active?: string;
}

export function MarketingTopNav({ active = "Produkt" }: TopNavProps) {
  return (
    <nav className="sticky top-0 z-50 bg-havsbla border-b border-border-on-dark">
      <div className="mx-auto max-w-[1280px] px-[6%] py-3.5 flex items-center gap-8">
        <Link href="/marketing" className="inline-flex items-center">
          <Wordmark tone="linne" size="md" />
        </Link>
        <ul className="hidden md:flex flex-1 gap-7 list-none m-0 p-0">
          {LINKS.map((l) => (
            <li key={l.label}>
              <a
                href={l.href}
                className={`text-sm font-medium transition-colors ${
                  l.label === active ? "text-linne" : "text-linne/70 hover:text-linne"
                }`}
              >
                {l.label}
              </a>
            </li>
          ))}
        </ul>
        <div className="flex items-center gap-4 md:gap-6 ml-auto">
          <Link
            href="/login"
            className="text-sm font-medium text-linne/70 hover:text-linne transition-colors"
          >
            Logga in
          </Link>
          <Button variant="primary" size="sm">
            Boka demo
          </Button>
        </div>
      </div>
    </nav>
  );
}
