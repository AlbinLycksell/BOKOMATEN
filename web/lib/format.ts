const SE_DATE = new Intl.DateTimeFormat("sv-SE", {
  year: "numeric",
  month: "short",
  day: "2-digit",
});

const SE_TIME = new Intl.DateTimeFormat("sv-SE", {
  hour: "2-digit",
  minute: "2-digit",
});

const SE_RELATIVE = new Intl.RelativeTimeFormat("sv-SE", { numeric: "auto" });

export function formatDateSv(d: Date | string): string {
  const date = typeof d === "string" ? new Date(d) : d;
  return SE_DATE.format(date);
}

export function formatTimeSv(d: Date | string): string {
  const date = typeof d === "string" ? new Date(d) : d;
  return SE_TIME.format(date);
}

export function formatTimeAgoSv(d: Date | string): string {
  const date = typeof d === "string" ? new Date(d) : d;
  const seconds = (date.getTime() - Date.now()) / 1000;
  const ranges: [number, Intl.RelativeTimeFormatUnit][] = [
    [60, "second"],
    [3600, "minute"],
    [86400, "hour"],
    [604800, "day"],
    [2592000, "week"],
    [31536000, "month"],
    [Infinity, "year"],
  ];
  for (const [limit, unit] of ranges) {
    if (Math.abs(seconds) < limit) {
      const divisor =
        unit === "second"
          ? 1
          : unit === "minute"
            ? 60
            : unit === "hour"
              ? 3600
              : unit === "day"
                ? 86400
                : unit === "week"
                  ? 604800
                  : unit === "month"
                    ? 2592000
                    : 31536000;
      return SE_RELATIVE.format(Math.round(seconds / divisor), unit);
    }
  }
  return formatDateSv(date);
}

export function formatPhoneSv(e164: string): string {
  if (!e164.startsWith("+46")) return e164;
  const digits = e164.slice(3);
  if (digits.length === 9) {
    return `0${digits.slice(0, 2)}-${digits.slice(2, 5)} ${digits.slice(5, 7)} ${digits.slice(7)}`;
  }
  return `0${digits}`;
}

export function formatSEK(value: number): string {
  return new Intl.NumberFormat("sv-SE", {
    style: "currency",
    currency: "SEK",
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatDurationSv(seconds: number): string {
  if (seconds < 60) return `${seconds} s`;
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  if (m < 60) return s ? `${m} min ${s}s` : `${m} min`;
  const h = Math.floor(m / 60);
  return `${h}h ${m % 60}m`;
}
