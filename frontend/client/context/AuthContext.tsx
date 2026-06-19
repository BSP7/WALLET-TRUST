import React, { createContext, useContext, useState, useCallback, useEffect } from "react";

export interface User {
  email: string;
  fullName: string;
  userId?: string;
  phone?: string | null;
  dob?: string | null;
  createdAt?: number;
}

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  setUser: (user: User | null) => void;
  login: (email: string, password: string) => Promise<any>;
  register: (userData: any) => Promise<any>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<boolean>;
  getAccessToken: () => string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = "access_token";
const REFRESH_TOKEN_KEY = "refresh_token";
const USER_KEY = "currentUser";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUserState] = useState<User | null>(() => {
    if (typeof window === "undefined") return null;
    const storedUser = localStorage.getItem(USER_KEY);
    return storedUser ? JSON.parse(storedUser) : null;
  });

  const [isAuthenticated, setIsAuthenticated] = useState(
    () => typeof window !== "undefined" && !!localStorage.getItem(TOKEN_KEY)
  );

  // Set user and persist to localStorage
  const setUser = useCallback((newUser: User | null) => {
    setUserState(newUser);
    if (newUser) {
      localStorage.setItem(USER_KEY, JSON.stringify(newUser));
      setIsAuthenticated(true);
    } else {
      localStorage.removeItem(USER_KEY);
      setIsAuthenticated(false);
    }
  }, []);

  // Get access token from storage
  const getAccessToken = useCallback(() => {
    return localStorage.getItem(TOKEN_KEY);
  }, []);

  // Store tokens
  const storeTokens = useCallback((accessToken: string, refreshToken: string) => {
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
    setIsAuthenticated(true);
  }, []);

  // Refresh access token using refresh token
  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      const refreshTokenValue = localStorage.getItem(REFRESH_TOKEN_KEY);
      if (!refreshTokenValue) {
        return false;
      }

      const response = await fetch("/api/auth/refresh", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      });

      if (!response.ok) {
        logout();
        return false;
      }

      const data = await response.json();
      localStorage.setItem(TOKEN_KEY, data.access_token);
      return true;
    } catch (error) {
      console.error("Token refresh failed:", error);
      logout();
      return false;
    }
  }, []);

  // Logout function
  const logout = useCallback(async () => {
    try {
      const token = getAccessToken();
      if (token) {
        await fetch("/api/auth/logout", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        });
      }
    } catch (error) {
      console.error("Logout error:", error);
    } finally {
      // Clear all auth data
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(REFRESH_TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      setUserState(null);
      setIsAuthenticated(false);
    }
  }, [getAccessToken]);

  const fetchAndStoreProfile = useCallback(
    async (accessToken: string) => {
      const profileResponse = await fetch("/api/users/profile", {
        method: "GET",
        headers: {
          Authorization: `Bearer ${accessToken}`,
        },
      });

      if (!profileResponse.ok) {
        return null;
      }

      const profile = await profileResponse.json();
      const userData: User = {
        email: profile.email,
        fullName: profile.name,
        userId: profile.id,
        phone: profile.phone ?? null,
        dob: profile.dob ?? null,
        createdAt: profile.created_at,
      };
      setUser(userData);
      return userData;
    },
    [setUser]
  );

  // Login function
  const login = useCallback(
    async (email: string, password: string) => {
      try {
        const response = await fetch("/api/auth/login", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || "Login failed");
        }

        const data = await response.json();

        // Store tokens
        storeTokens(data.access_token, data.refresh_token);

        // Load real user profile (includes name)
        await fetchAndStoreProfile(data.access_token);

        return data;
      } catch (error) {
        console.error("Login error:", error);
        throw error;
      }
    },
    [storeTokens, fetchAndStoreProfile]
  );

  // Register function
  const register = useCallback(
    async (userData: any) => {
      try {
        const response = await fetch("/api/auth/register", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            name: userData.fullName,
            email: userData.email,
            password: userData.password,
            dob: userData.dateOfBirth,
          }),
        });

        if (!response.ok) {
          const error = await response.json();
          throw new Error(error.error || "Registration failed");
        }

        const data = await response.json();

        // Store tokens
        storeTokens(data.access_token, data.refresh_token);

        // Store user info (backend returns name/email in data.user)
        if (data?.user?.user_id) {
          const newUser: User = {
            email: data.user.email,
            fullName: data.user.name,
            userId: data.user.user_id,
          };
          setUser(newUser);
        } else {
          await fetchAndStoreProfile(data.access_token);
        }

        return data;
      } catch (error) {
        console.error("Registration error:", error);
        throw error;
      }
    },
    [storeTokens, setUser, fetchAndStoreProfile]
  );

  // Hydrate profile if a token exists (e.g., refresh after page reload)
  useEffect(() => {
    const token = localStorage.getItem(TOKEN_KEY);
    if (!token) {
      return;
    }

    // If we already have a user, don't spam the API.
    if (user?.email && user?.fullName) {
      return;
    }

    fetchAndStoreProfile(token).catch(() => {
      // If profile fetch fails, leave state as-is.
    });
  }, [fetchAndStoreProfile, user]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        setUser,
        login,
        register,
        logout,
        refreshToken,
        getAccessToken,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
