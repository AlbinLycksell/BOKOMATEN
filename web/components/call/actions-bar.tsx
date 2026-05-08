"use client";

import { Button } from "@/components/ui/button";
import { HandledIcon, MessageIcon, PhoneCallIcon } from "@/components/icons";

export function ActionsBar() {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button>
        <PhoneCallIcon className="h-4 w-4" />
        Ring tillbaka
      </Button>
      <Button variant="outline">
        <MessageIcon className="h-4 w-4" />
        Skicka SMS
      </Button>
      <Button variant="ghost">
        <HandledIcon className="h-4 w-4" />
        Markera hanterad
      </Button>
    </div>
  );
}
