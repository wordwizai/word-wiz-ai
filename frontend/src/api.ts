import axios from "axios";

const API_URL = "http://localhost:8000";

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
  },
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

export {
  loginUser,
  registerUser,
  fetchUserProfile,
  googleLogin,
  API_URL,
  updateSettings,
  fetchSettings,
};
