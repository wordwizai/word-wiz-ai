import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

interface Session {
  id: number;
  activity_id: number;
  is_completed: boolean;
  created_at: string;
  activity: {
    activity_type: string;
    title: string;
    target_phoneme: string | null;
    activity_settings: {
      first_sentence?: string;
      sentence_options?: {
        option_1: string;
        option_2: string;
      };
      [key: string]: any; // Allow other settings
    };
    id: number;
  };
}

const loginUser = async (credentials) => {
  try {
    const params = new URLSearchParams();
    for (const key in credentials) {
      params.append(key, credentials[key]);
    }

    const response = await axios.post(`${API_URL}/auth/token`, params, {
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    });
    return response.data;
  } catch (error) {
    console.error("Login error:", error);
    throw error;
  }
};

const registerUser = async (userData) => {
  try {
    await axios.post(`${API_URL}/auth/register`, userData);
  } catch (error) {
    console.error("Registration error:", error);
    throw error;
  }
};

const fetchUserProfile = async (token) => {
  try {
    const response = await axios.get(`${API_URL}/users/me/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Fetch user profile error:", error);
    throw error;
  }
};

const googleLogin = async () => {
  try {
    // Redirect to your backend's Google login route
    window.location.href = `${API_URL}/auth/google/login`;
  } catch (error) {
    console.error("Google login error:", error);
    throw error;
  }
};

const updateSettings = async (
  token: string,
  settings: {
    preferred_language?: string;
    theme?: string | null;
    tts_speed?: number | null;
    audio_feedback_volume?: number | null;
    notifications_enabled?: boolean | null;
    email_notifications?: boolean | null;
  }
) => {
  try {
    const response = await axios.put(`${API_URL}/users/me/settings`, settings, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Update settings error:", error);
    throw error;
  }
};

const fetchSettings = async (token: string) => {
  try {
    const response = await axios.get(`${API_URL}/users/me/settings`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Fetch settings error:", error);
    throw error;
  }
};

const getSession = async (
  token: string,
  sessionId: number
): Promise<Session> => {
  try {
    const response = await axios.get(`${API_URL}/session/${sessionId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Fetch session error:", error);
    throw error;
  }
};

const getCurrentSessionState = async (
  token: string,
  sessionId: number
): Promise<any> => {
  try {
    const response = await axios.get(
      `${API_URL}/session/${sessionId}/current-data`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error("Fetch latest session feedback error:", error);
    throw error;
  }
};

const getSessions = async (token: string) => {
  try {
    const response = await axios.get(`${API_URL}/session/all`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Fetch sessions error:", error);
    throw error;
  }
};

const createSession = async (token: string, activityId: number) => {
  try {
    console.log("Token:", token);
    console.log("Headers:", {
      Authorization: `Bearer ${token}`,
    });
    const response = await axios.post(
      `${API_URL}/session/`,
      { activity_id: activityId },
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error("Create session error:", error);
    throw error;
  }
};

const getActivities = async (token: string) => {
  try {
    const response = await axios.get(`${API_URL}/activities/`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Fetch activities error:", error);
    throw error;
  }
};

const getActivity = async (token: string, activityId: number) => {
  try {
    const response = await axios.get(`${API_URL}/activities/${activityId}`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Fetch activity error:", error);
    throw error;
  }
};

const getSentencePers = async (token: string) => {
  try {
    const response = await axios.get(`${API_URL}/feedback/user/sentence-pers`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Fetch sentence pers error:", error);
    throw error;
  }
};

const getPhonemesPerMistakeType = async (
  token: string,
  errorType: "insertion" | "deletion" | "substitution"
) => {
  try {
    const response = await axios.get(
      `${API_URL}/feedback/user/mistake-type-phonemes?mistake_type=${errorType}&limit=10`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      }
    );
    return response.data;
  } catch (error) {
    console.error("Fetch phonemes per mistake type error:", error);
    throw error;
  }
};

interface UserStatistics {
  total_sessions: number;
  current_streak: number;
  longest_streak: number;
  words_read: number;
}

const getUserStatistics = async (token: string): Promise<UserStatistics> => {
  try {
    const response = await axios.get(`${API_URL}/feedback/statistics`, {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    });
    return response.data;
  } catch (error) {
    console.error("Fetch user statistics error:", error);
    throw error;
  }
};

export {
  loginUser,
  registerUser,
  fetchUserProfile,
  googleLogin,
  API_URL,
  updateSettings,
  fetchSettings,
  getSession,
  getCurrentSessionState,
  getSessions,
  createSession,
  getActivities,
  getActivity,
  getSentencePers,
  getPhonemesPerMistakeType,
  getUserStatistics,
};
export type { Session, UserStatistics };
