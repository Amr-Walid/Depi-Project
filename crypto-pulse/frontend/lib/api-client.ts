/**
 * CryptoPulse API Client
 * Centralized fetch wrapper for communicating with the FastAPI backend.
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type RequestOptions = RequestInit & {
  params?: Record<string, string>;
};

export async function apiClient<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const { params, headers, ...rest } = options;

  // 1. Construct URL with query parameters
  const url = new URL(`${API_BASE_URL}${endpoint.startsWith("/") ? endpoint : `/${endpoint}`}`);
  if (params) {
    Object.keys(params).forEach((key) => url.searchParams.append(key, params[key]));
  }

  // 2. Get JWT token from localStorage
  const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

  // 3. Prepare headers
  const defaultHeaders: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    defaultHeaders["Authorization"] = `Bearer ${token}`;
  }

  // 4. Make the request
  const response = await fetch(url.toString(), {
    ...rest,
    cache: "no-store",
    headers: {
      ...defaultHeaders,
      ...headers,
    },
  });

  // 5. Handle unauthorized (token expired)
  if (response.status === 401) {
    // In a real app, we would handle token refresh here.
    // For now, we'll just clear the token.
    if (typeof window !== "undefined") {
      localStorage.removeItem("access_token");
    }
  }

  // 6. Parse and handle errors
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || "An error occurred while fetching data");
  }

  // Handle 204 No Content or empty responses safely
  if (response.status === 204) {
    return null as any;
  }

  const text = await response.text();
  return text ? JSON.parse(text) : (null as any);
}
