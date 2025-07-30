import { useContext, useEffect, useState } from "react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { AuthContext } from "@/contexts/AuthContext";
import { useSettings } from "@/contexts/SettingsContext";
import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
type Settings = {
  preferred_language?: string;
  theme?: "dark" | "light" | "system" | null;
  tts_speed?: number | null;
  audio_feedback_volume?: number | null;
  notifications_enabled?: boolean | null;
  email_notifications?: boolean | null;
};

const initialSettings: Settings = {
  preferred_language: "english",
  theme: "light",
  tts_speed: 1.0,
  audio_feedback_volume: 0.5,
  notifications_enabled: true,
  email_notifications: true,
};

const Settings = () => {
  const [savedStatus, setSavedStatus] = useState("");
  const { user } = useContext(AuthContext);
  const { settings, updateSettings } = useSettings();
  const [tempSettings, setTempSettings] = useState<Settings>(
    settings || initialSettings,
  );
  const [tab, setTab] = useState(() => {
    const hash =
      typeof window !== "undefined"
        ? window.location.hash.replace("#", "")
        : "";
    return hash || "profile";
  });

  useEffect(() => {
    if (settings) {
      setTempSettings(settings);
    }
  }, [settings]);

  const handleChange = (field: keyof Settings, value: any) => {
    setTempSettings((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    const response = await updateSettings(tempSettings);
    if (response) {
      setSavedStatus("Settings saved successfully!");
      setTimeout(() => setSavedStatus(""), 3000);
    } else {
      setSavedStatus("Failed to save settings.");
    }
    console.log("Settings updated:", response);
  };

  return (
    <div className="container mx-auto py-8 px-4 max-w-4xl">
      <h1 className="text-3xl font-bold mb-6">Settings</h1>

      <Tabs
        value={tab}
        onValueChange={(value) => {
          setTab(value);
          window.location.hash = value;
        }}
        className="w-full"
      >
        <TabsList className="grid grid-cols-4 mb-8">
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="account">Account</TabsTrigger>
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          <Card>
            <CardHeader>
              <CardTitle>Profile Settings</CardTitle>
              <CardDescription>
                Manage your personal profile information.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="fullName">Full Name</Label>
                  <Input
                    id="fullName"
                    placeholder="Enter your full name"
                    value={user?.full_name || ""}
                    disabled
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="your@email.com"
                    disabled
                    value={user?.email || ""}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="account">
          <Card>
            <CardHeader>
              <CardTitle>Account Settings</CardTitle>
              <CardDescription>
                Manage your account preferences.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="space-y-4">
                <Label htmlFor="language">Language</Label>
                <Select
                  defaultValue="english"
                  onValueChange={(value) =>
                    handleChange("preferred_language", value)
                  }
                >
                  <SelectTrigger id="language">
                    <SelectValue placeholder="Select language" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="english">English</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div>
                  <h4 className="font-medium">Delete Account</h4>
                  <p className="text-sm text-muted-foreground">
                    Permanently delete your account and all associated data.
                  </p>
                </div>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button variant="destructive">Delete Account</Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>
                        Feature not implemented
                      </AlertDialogTitle>
                      <AlertDialogDescription>
                        Deleting your account is not implemented yet.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Close</AlertDialogCancel>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="appearance">
          <Card>
            <CardHeader>
              <CardTitle>Appearance Settings</CardTitle>
              <CardDescription>
                Customize how the application looks.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="darkMode">Dark Mode</Label>
                  <p className="text-sm text-muted-foreground">
                    Toggle between light and dark mode.
                  </p>
                </div>
                <Select
                  value={tempSettings.theme ?? "light"}
                  onValueChange={(value) =>
                    handleChange("theme", value as "dark" | "light" | "system")
                  }
                >
                  <SelectTrigger id="theme" className="w-32">
                    <SelectValue placeholder="Select theme" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Light</SelectItem>
                    <SelectItem value="dark">Dark</SelectItem>
                    <SelectItem value="system">System</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="notifications">
          <Card>
            <CardHeader>
              <CardTitle>Notification Settings</CardTitle>
              <CardDescription>
                Manage when and how you receive notifications.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="emailNotifs">Email Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive updates and information via email.
                  </p>
                </div>
                <Switch
                  id="emailNotifs"
                  checked={!!tempSettings.email_notifications}
                  onCheckedChange={(checked) =>
                    handleChange("email_notifications", checked)
                  }
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="pushNotifs">Push Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive notifications on your device.
                  </p>
                </div>
                <Switch
                  id="pushNotifs"
                  checked={!!tempSettings.notifications_enabled}
                  onCheckedChange={(checked) =>
                    handleChange("notifications_enabled", checked)
                  }
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="mt-6 flex justify-between items-center">
        <p className="text-green-600">{savedStatus}</p>
        <Button onClick={handleSave}>Save Changes</Button>
      </div>
    </div>
  );
};

export default Settings;
