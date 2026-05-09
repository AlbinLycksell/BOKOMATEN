"use client";

import { useQuery } from "@tanstack/react-query";

import { getCall, listCalls, listCustomers, getFirma } from "./api";
import type { Intent } from "./api-models";
import { QueryKey } from "./constants/query-keys";

export function useCallsQuery(filters?: { intent?: Intent; status?: string; source?: string }) {
  return useQuery({
    queryKey: QueryKey.calls(
      filters?.intent ?? null,
      filters?.status ?? null,
      filters?.source ?? null,
    ),
    queryFn: () => listCalls(filters),
  });
}

export function useCallQuery(id: string) {
  return useQuery({
    queryKey: QueryKey.call(id),
    queryFn: () => getCall(id),
    enabled: !!id,
  });
}

export function useCustomersQuery(q?: string) {
  return useQuery({
    queryKey: QueryKey.customers(q ?? null),
    queryFn: () => listCustomers(q),
  });
}

export function useFirmaQuery() {
  return useQuery({
    queryKey: QueryKey.firma(),
    queryFn: () => getFirma(),
  });
}
