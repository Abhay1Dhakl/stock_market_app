export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api";

type RequestOptions = {
  token?: string | null;
  method?: "GET" | "POST" | "PATCH";
  body?: unknown;
};

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers: {
      "Content-Type": "application/json",
      ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
    },
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await safeReadError(response);
    throw new Error(detail || `Request failed with status ${response.status}`);
  }

  return (await response.json()) as T;
}

async function safeReadError(response: Response): Promise<string | null> {
  try {
    const payload = (await response.json()) as {
      detail?:
        | string
        | Array<{ loc?: Array<string | number>; msg?: string; type?: string }>
        | Record<string, unknown>;
    };

    if (typeof payload.detail === "string") {
      return payload.detail;
    }

    if (Array.isArray(payload.detail)) {
      return payload.detail
        .map((item) => {
          const field = item.loc?.slice(1).join(".") ?? "request";
          return item.msg ? `${field}: ${item.msg}` : null;
        })
        .filter((value): value is string => Boolean(value))
        .join("; ");
    }

    if (payload.detail && typeof payload.detail === "object") {
      return JSON.stringify(payload.detail);
    }

    return null;
  } catch {
    return null;
  }
}
