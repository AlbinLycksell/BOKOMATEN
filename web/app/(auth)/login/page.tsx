"use client";

import { signIn } from "next-auth/react";

import { Wordmark } from "@/components/brand/wordmark";
import { Button } from "@/components/ui/button";

export default function LoginPage() {
  return (
    <div className="min-h-screen grid place-items-center bg-linne px-6">
      <div className="w-full max-w-md flex flex-col items-center text-center gap-8">
        <Wordmark size="xl" />

        <div className="flex flex-col gap-4">
          <h1 className="font-display text-[40px] leading-[1.05] tracking-[-0.02em] font-semibold text-text-strong">
            Logga in.
          </h1>
          <p className="text-[16px] text-text-muted max-w-sm">
            Se inkommande samtal, hantera bokningar, och låt AI:n svara när du
            inte hinner.
          </p>
        </div>

        <Button
          variant="navy"
          size="lg"
          onClick={() => signIn("google", { callbackUrl: "/inbox" })}
        >
          Logga in med Google
        </Button>

        <p className="text-xs text-text-faint max-w-xs">
          Genom att logga in godkänner du Switchboards användarvillkor och
          dataskyddspolicy.
        </p>
      </div>
    </div>
  );
}
