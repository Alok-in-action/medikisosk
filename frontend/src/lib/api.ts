export class ApiError extends Error {
  constructor(
    message: string,
    public status?: number,
    public code?: "NETWORK" | "TIMEOUT" | "SERVER" | "INVALID_RESPONSE"
  ) {
    super(message);
    this.name = "ApiError";
  }
}

const configuredUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");

if (!configuredUrl && process.env.NODE_ENV === "production") {
  throw new Error("NEXT_PUBLIC_API_BASE_URL is not configured.");
}

export const API_BASE_URL = configuredUrl || "http://localhost:8000";

export async function apiFetch<T = any>(
  path: string,
  options: RequestInit = {},
  timeoutMs = 30000,
  responseType: "json" | "blob" = "json"
): Promise<T> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
  
  const config = {
    ...options,
    signal: controller.signal,
    headers: {
      ...options.headers,
    }
  };

  try {
    const url = `${API_BASE_URL}${path.startsWith('/') ? path : `/${path}`}`;
    const response = await fetch(url, config);

    if (!response.ok) {
      let errorMessage = "Unknown API Error";
      let errorCode = "SERVER";
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail?.message || errorData.detail || errorData.message || JSON.stringify(errorData);
        if (errorData.detail?.code) {
          errorCode = errorData.detail.code;
        }
      } catch (e) {
        errorMessage = await response.text() || response.statusText;
      }
      throw new ApiError(errorMessage, response.status, errorCode as any);
    }

    if (responseType === "blob") {
      const data = await response.blob();
      return data as any;
    }

    try {
      const data = await response.json();
      return data;
    } catch (e) {
      throw new ApiError("Failed to parse JSON response", response.status, "INVALID_RESPONSE");
    }
  } catch (error: any) {
    if (error.name === "AbortError") {
      throw new ApiError("Request timeout", undefined, "TIMEOUT");
    }
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(error.message || "Network Error", undefined, "NETWORK");
  } finally {
    clearTimeout(timeoutId);
  }
}
