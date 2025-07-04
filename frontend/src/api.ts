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

const sendAudioRecording = async (
  audioFile: File,
  sentence: string,
  token: string | null,
) => {
  try {
    const formData = new FormData();
    console.log(audioFile);
    formData.append("audio_file", audioFile, audioFile.name || "recording.wav");
    formData.append("attempted_sentence", sentence);

    const headers: Record<string, string> = {
      Accept: "application/json",
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await axios.post(`${API_URL}/ai/analyze-audio`, formData, {
      headers,
    });
    return response.data;
  } catch (error) {
    console.error("Send audio recording error:", error);
    throw error;
  }
};

export {
  loginUser,
  registerUser,
  fetchUserProfile,
  googleLogin,
  sendAudioRecording,
};
