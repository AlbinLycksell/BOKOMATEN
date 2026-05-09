"use client";

import { useQuery } from "@tanstack/react-query";

import { getCall, listCalls, listCustomers, getFirma } from "./api";
import type { Intent } from "./api-models";

export function useCallsQuery(filters?: { intent?: Intent; status?: string }) {
  return useQuery({
    queryKey: ["calls", filters?.intent ?? null, filters?.status ?? null],
    queryFn: () => listCalls(filters),
  });
}

export function useCallQuery(id: string) {
  return useQuery({
    queryKey: ["call", id],
    queryFn: () => getCall(id),
    enabled: !!id,
  });
}

export function useCustomersQuery(q?: string) {
  return useQuery({
    queryKey: ["customers", q ?? null],
    queryFn: () => listCustomers(q),
  });
}

export function useFirmaQuery() {
  return useQuery({
    queryKey: ["firma"],
    queryFn: () => getFirma(),
  });
}
