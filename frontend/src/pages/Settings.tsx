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
import {
  Settings2,
  User,
  Bell,
  Palette,
  Zap,
  CheckCircle2,
  Sparkles,
} from "lucide-react";
type Settings = {
  preferred_language?: string;
  theme?: "dark" | "light" | "system" | null;
  tts_speed?: number | null;
  audio_feedback_volume?: number | null;
  notifications_enabled?: boolean | null;
  email_notifications?: boolean | null;
  use_client_phoneme_extraction?: boolean | null;
  use_websocket?: boolean | null;
};

const initialSettings: Settings = {
  preferred_language: "english",
  theme: "light",
  tts_speed: 1.0,
  audio_feedback_volume: 0.5,
  notifications_enabled: true,
  email_notifications: true,
  use_client_phoneme_extraction: true,
  use_websocket: false,
};

const Settings = () => {
  const [savedStatus, setSavedStatus] = useState("");
  const { user } = useContext(AuthContext);
  const { settings, updateSettings } = useSettings();
  const [tempSettings, setTempSettings] = useState<Settings>(
    settings || initialSettings
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
    try {
      await updateSettings(tempSettings);
      setSavedStatus("Settings saved successfully!");
      setTimeout(() => setSavedStatus(""), 3000);
    } catch (error) {
      setSavedStatus("Failed to save settings.");
      console.error("Settings update error:", error);
    }
  };

  return (
    <div className="flex-1 overflow-auto bg-background">
      {/* Hero Header */}
      <div className="relative overflow-hidden bg-gradient-to-br from-primary/10 via-accent/5 to-primary/5 border-b border-border px-6 py-6">
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute -top-10 -right-10 w-40 h-40 bg-primary/10 rounded-full blur-3xl" />
          <div className="absolute -bottom-10 -left-10 w-32 h-32 bg-accent/10 rounded-full blur-3xl" />
          <Sparkles className="absolute top-4 right-16 w-6 h-6 text-primary/10 rotate-45" />
        </div>
        <div className="relative z-10 flex items-center gap-4 max-w-4xl mx-auto">
          <div className="hidden sm:flex shrink-0">
            <div className="relative w-14 h-14">
              <div className="absolute inset-0 bg-gradient-to-br from-primary/20 to-accent/20 rounded-2xl rotate-6" />
              <div className="absolute inset-0 bg-gradient-to-tl from-accent/20 to-primary/20 rounded-2xl -rotate-6" />
              <div className="absolute inset-0 flex items-center justify-center">
                <Settings2 className="w-7 h-7 text-primary" />
              </div>
            </div>
          </div>
          <div>
            <p className="text-xs text-muted-foreground font-medium uppercase tracking-wide mb-1">Configuration</p>
            <h1 className="text-2xl md:text-3xl font-bold bg-gradient-to-r from-primary via-primary/80 to-accent bg-clip-text text-transparent">
              Settings
            </h1>
            <p className="text-sm text-muted-foreground mt-0.5">Manage your account, preferences, and app behaviour</p>
          </div>
        </div>
      </div>

      <div className="container mx-auto py-6 px-4 max-w-4xl">
      <Tabs
        value={tab}
        onValueChange={(value) => {
          setTab(value);
          window.location.hash = value;
        }}
        className="w-full"
      >
        <TabsList className="flex flex-wrap h-auto gap-1 mb-6 bg-muted/60 p-1 rounded-xl">
          <TabsTrigger value="profile" className="flex items-center gap-1.5 rounded-lg flex-1 min-w-fit data-[state=active]:shadow-sm">
            <User className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Profile</span>
          </TabsTrigger>
          <TabsTrigger value="account" className="flex items-center gap-1.5 rounded-lg flex-1 min-w-fit data-[state=active]:shadow-sm">
            <Settings2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Account</span>
          </TabsTrigger>
          <TabsTrigger value="appearance" className="flex items-center gap-1.5 rounded-lg flex-1 min-w-fit data-[state=active]:shadow-sm">
            <Palette className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Appearance</span>
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-1.5 rounded-lg flex-1 min-w-fit data-[state=active]:shadow-sm">
            <Bell className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Notifications</span>
          </TabsTrigger>
          <TabsTrigger value="performance" className="flex items-center gap-1.5 rounded-lg flex-1 min-w-fit data-[state=active]:shadow-sm">
            <Zap className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Performance</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          <Card className="rounded-2xl border-2 border-border shadow-sm">
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
          <Card className="rounded-2xl border-2 border-border shadow-sm">
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
          <Card className="rounded-2xl border-2 border-border shadow-sm">
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
          <Card className="rounded-2xl border-2 border-border shadow-sm">
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

        <TabsContent value="performance">
          <Card className="rounded-2xl border-2 border-border shadow-sm">
            <CardHeader>
              <CardTitle>Performance Settings</CardTitle>
              <CardDescription>
                Optimize how the application processes audio and AI features.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex-1 pr-4">
                  <Label htmlFor="clientProcessing">
                    Client-Side Phoneme Processing
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    Process phonemes in your browser for 50-70% faster results.
                    Requires ~100MB model download on first use. Disable on
                    slower devices or poor connections.
                  </p>
                </div>
                <Switch
                  id="clientProcessing"
                  checked={!!tempSettings.use_client_phoneme_extraction}
                  onCheckedChange={(checked) =>
                    handleChange("use_client_phoneme_extraction", checked)
                  }
                />
              </div>

              <Separator />

              <div className="flex items-center justify-between">
                <div className="flex-1 pr-4">
                  <Label htmlFor="websocketConnection">
                    WebSocket Connection (Experimental)
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    Use persistent WebSocket connection instead of creating new
                    connections for each request. Eliminates 5-second connection
                    overhead on subsequent recordings. Recommended for faster
                    experience.
                  </p>
                </div>
                <Switch
                  id="websocketConnection"
                  checked={!!tempSettings.use_websocket}
                  onCheckedChange={(checked) =>
                    handleChange("use_websocket", checked)
                  }
                />
              </div>

              <Separator />

              <div className="rounded-xl bg-muted/60 border border-border p-4">
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="w-4 h-4 text-primary" />
                  <h4 className="text-sm font-semibold text-foreground">Performance Tips</h4>
                </div>
                <ul className="text-sm text-muted-foreground space-y-1.5 list-disc list-inside">
                  <li>Model downloads once and caches for future sessions</li>
                  <li>Automatically disabled on low-memory devices</li>
                  <li>Falls back to server processing if any issues occur</li>
                  <li>Best results on desktop with good internet connection</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      <div className="mt-6 flex justify-between items-center gap-4 pt-4 border-t border-border">
        <div className="flex items-center gap-2 min-h-[20px]">
          {savedStatus && (
            <div className={`flex items-center gap-1.5 text-sm font-medium ${
              savedStatus.includes("Failed")
                ? "text-destructive"
                : "text-emerald-600 dark:text-emerald-400"
            }`}>
              {!savedStatus.includes("Failed") && <CheckCircle2 className="w-4 h-4" />}
              {savedStatus}
            </div>
          )}
        </div>
        <Button onClick={handleSave} className="rounded-xl px-6 font-semibold">
          Save changes
        </Button>
      </div>
      </div>
    </div>
  );
};

export default Settings;
