import type { NextAuthOptions } from "next-auth";
import GoogleProvider from "next-auth/providers/google";

const BACKEND_URL =
  process.env.SVARSA_BACKEND_INTERNAL_URL ?? "http://127.0.0.1:8000";
const BOOTSTRAP_TOKEN = process.env.SVARSA_BOOTSTRAP_INTERNAL_TOKEN ?? "";
const FALLBACK_FIRMA_ID =
  process.env.SVARSA_FALLBACK_FIRMA_ID ?? "01J0000FIRM0ANDERSSONSVVS00";

interface BootstrapResponse {
  user_id: string;
  firma_id: string;
  role: string;
  created_firma: boolean;
}

async function bootstrapWithBackend(params: {
  google_sub: string;
  email: string;
  name?: string | null;
}): Promise<BootstrapResponse | null> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (BOOTSTRAP_TOKEN) headers["X-Internal-Token"] = BOOTSTRAP_TOKEN;
  try {
    const r = await fetch(`${BACKEND_URL}/api/auth/bootstrap`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        google_sub: params.google_sub,
        email: params.email,
        name: params.name ?? null,
      }),
      cache: "no-store",
    });
    if (!r.ok) return null;
    return (await r.json()) as BootstrapResponse;
  } catch {
    return null;
  }
}

export const authOptions: NextAuthOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID ?? "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
    }),
  ],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, account, profile }) {
      if (account && profile && account.provider === "google") {
        const sub =
          (profile as { sub?: string }).sub ?? account.providerAccountId;
        const result = await bootstrapWithBackend({
          google_sub: sub,
          email: token.email as string,
          name: (token.name as string) ?? null,
        });
        if (result) {
          token.firma_id = result.firma_id;
          token.user_id = result.user_id;
          token.role = result.role;
        } else {
          token.firma_id = FALLBACK_FIRMA_ID;
          token.role = "owner";
        }
      }
      return token;
    },
    async session({ session, token }) {
      const s = session as typeof session & {
        firma_id?: string;
        role?: string;
        user_id?: string;
      };
      s.firma_id = token.firma_id as string | undefined;
      s.role = token.role as string | undefined;
      s.user_id = token.user_id as string | undefined;
      return s;
    },
  },
  pages: {
    signIn: "/login",
  },
};
