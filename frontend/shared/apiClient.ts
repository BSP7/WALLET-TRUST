// frontend/shared/apiClient.ts
/**
 * API Client for authenticated requests
 * Automatically includes JWT token in headers
 */

const TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";

export interface FetchOptions extends RequestInit {
  skipAuth?: boolean;
}

/**
 * Fetch wrapper with automatic JWT token handling
 */
export async function apiCall(
  url: string,
  options: FetchOptions = {}
): Promise<Response> {
  const { skipAuth = false, ...fetchOptions } = options;

  // Prepare headers
  const headers = new Headers(fetchOptions.headers || {});

  // Add content-type if not present
  if (!headers.has("Content-Type") && fetchOptions.body) {
    headers.set("Content-Type", "application/json");
  }

  // Add authorization token if available and not skipped
  if (!skipAuth) {
    const token = localStorage.getItem(TOKEN_KEY);
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  // Make the request
  let response = await fetch(url, {
    ...fetchOptions,
    headers,
  });

  // If we get 401, try to refresh token
  if (response.status === 401 && !skipAuth) {
    const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY);
    if (refreshToken) {
      try {
        // Try to refresh the token
        const refreshResponse = await fetch("/api/auth/refresh", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ refresh_token: refreshToken }),
        });

        if (refreshResponse.ok) {
          const data = await refreshResponse.json();
          localStorage.setItem(TOKEN_KEY, data.access_token);

          // Retry the original request with new token
          headers.set("Authorization", `Bearer ${data.access_token}`);
          response = await fetch(url, {
            ...fetchOptions,
            headers,
          });
        } else {
          // Refresh failed, clear tokens and redirect to login
          localStorage.removeItem(TOKEN_KEY);
          localStorage.removeItem(REFRESH_TOKEN_KEY);
          window.location.href = "/login";
        }
      } catch (error) {
        console.error("Token refresh failed:", error);
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_TOKEN_KEY);
        window.location.href = "/login";
      }
    }
  }

  return response;
}

/**
 * Helper for GET requests
 */
export async function apiGet(url: string, options: FetchOptions = {}) {
  return apiCall(url, {
    method: "GET",
    ...options,
  });
}

/**
 * Helper for POST requests
 */
export async function apiPost(
  url: string,
  data?: any,
  options: FetchOptions = {}
) {
  return apiCall(url, {
    method: "POST",
    body: data ? JSON.stringify(data) : undefined,
    ...options,
  });
}

/**
 * Helper for PUT requests
 */
export async function apiPut(
  url: string,
  data?: any,
  options: FetchOptions = {}
) {
  return apiCall(url, {
    method: "PUT",
    body: data ? JSON.stringify(data) : undefined,
    ...options,
  });
}

/**
 * Helper for DELETE requests
 */
export async function apiDelete(url: string, options: FetchOptions = {}) {
  return apiCall(url, {
    method: "DELETE",
    ...options,
  });
}
