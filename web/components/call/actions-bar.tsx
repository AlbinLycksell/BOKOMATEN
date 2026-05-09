"use client";

import { Button } from "@/components/ui/button";
import { HandledIcon, MessageIcon, PhoneCallIcon } from "@/components/icons";

export function ActionsBar() {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button variant="navy" size="sm">
        <PhoneCallIcon className="h-4 w-4" strokeWidth={1.75} />
        Ring tillbaka
      </Button>
      <Button variant="secondary" size="sm">
        <MessageIcon className="h-4 w-4" strokeWidth={1.75} />
        Skicka SMS
      </Button>
      <Button variant="ghost" size="sm">
        <HandledIcon className="h-4 w-4" strokeWidth={1.75} />
        Markera hanterad
      </Button>
    </div>
  );
}
