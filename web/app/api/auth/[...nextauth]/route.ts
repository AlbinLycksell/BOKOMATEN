import NextAuth from "next-auth";
import GoogleProvider from "next-auth/providers/google";

const DEMO_FIRMA_ID = "01J0000FIRM0ANDERSSONSVVS00";

const handler = NextAuth({
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID ?? "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET ?? "",
    }),
  ],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        // First sign-in: stamp the firma_id and role.
        // Production replaces this with a backend lookup of the user's firma.
        token.firma_id = DEMO_FIRMA_ID;
        token.role = "owner";
      }
      return token;
    },
    async session({ session, token }) {
      (session as { firma_id?: string }).firma_id = token.firma_id as string | undefined;
      (session as { role?: string }).role = token.role as string | undefined;
      return session;
    },
  },
});

export { handler as GET, handler as POST };
