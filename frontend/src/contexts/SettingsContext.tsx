import React, { createContext, useContext, useState, useEffect } from "react";
import type { ReactNode } from "react";
import {
  updateSettings as apiUpdateSettings,
  fetchSettings as apiFetchSettings,
} from "../api";
import { AuthContext } from "./AuthContext";

type Settings = {
  preferred_language?: string;
  theme?: "dark" | "light" | "system" | null;
  tts_speed?: number | null;
  audio_feedback_volume?: number | null;
  notifications_enabled?: boolean | null;
  email_notifications?: boolean | null;
};

type SettingsContextType = {
  settings: Settings | null;
  loading: boolean;
  error: string | null;
  fetchSettings: () => Promise<void>;
  updateSettings: (newSettings: Partial<Settings>) => Promise<void>;
};

const SettingsContext = createContext<SettingsContextType | undefined>(
  undefined,
);

export const useSettings = () => {
  const ctx = useContext(SettingsContext);
  if (!ctx) throw new Error("useSettings must be used within SettingsProvider");
  return ctx;
};

export const SettingsProvider = ({ children }: { children: ReactNode }) => {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { token } = useContext(AuthContext);

  const fetchSettings = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiFetchSettings(token || "");
      setSettings(data);
      console.log("Fetched settings:", data);
    } catch (e: any) {
      setError(e.message || "Failed to fetch settings");
    } finally {
      setLoading(false);
    }
  };

  const updateSettings = async (newSettings: Partial<Settings>) => {
    setLoading(true);
    setError(null);
    try {
      const updated = await apiUpdateSettings(token || "", newSettings);
      setSettings(updated);
      setLoading(false);
      return updated;
    } catch (e: any) {
      setError(e.message || "Failed to update settings");
      setLoading(false);
      return null;
    }
  };

  useEffect(() => {
    if (token !== null) {
      fetchSettings();
    }
  }, [token]);

  return (
    <SettingsContext.Provider
      value={{ settings, loading, error, fetchSettings, updateSettings }}
    >
      {children}
    </SettingsContext.Provider>
  );
};
