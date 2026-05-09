"use client";

import { signIn } from "next-auth/react";

import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";

export default function LoginPage() {
  return (
    <div className="min-h-screen grid place-items-center bg-bg px-4">
      <Card className="w-full max-w-sm">
        <CardContent className="flex flex-col gap-6 py-10 px-8 items-center text-center">
          <div className="flex items-center gap-2">
            <div className="h-10 w-10 rounded-md bg-accent text-on-accent grid place-items-center font-semibold">
              S
            </div>
            <span className="text-base font-semibold text-text-strong">Switchboard</span>
          </div>
          <p className="text-sm text-text-muted">
            Logga in för att se inkommande samtal och hantera bokningar.
          </p>
          <Button onClick={() => signIn("google", { callbackUrl: "/inbox" })} size="lg">
            Logga in med Google
          </Button>
          <p className="text-[11px] text-text-faint">
            Genom att logga in godkänner du Switchboards användarvillkor och dataskyddspolicy.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}
