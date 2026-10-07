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
  Settings2,
  User,
  Palette,
  Zap,
  CheckCircle2,
} from "lucide-react";
import { AppPage, PageHeader } from "@/components/AppPage";
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

const TABS = ["profile", "account", "appearance", "performance"];

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
    // Old links can still point at tabs that are gone (#notifications).
    return TABS.includes(hash) ? hash : "profile";
  });

  useEffect(() => {
    if (settings) {
      setTempSettings(settings);
    }
  }, [settings]);

  const handleChange = (field: keyof Settings, value: Settings[keyof Settings]) => {
    setTempSettings((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    // updateSettings reports failure by resolving to null rather than
    // throwing, so this used to say "saved" even when nothing was saved.
    const saved = await updateSettings(tempSettings);
    if (saved) {
      setSavedStatus("Settings saved successfully!");
      setTimeout(() => setSavedStatus(""), 3000);
    } else {
      setSavedStatus("Failed to save settings. Please try again.");
    }
  };

  return (
    <AppPage width="narrow" title="Settings">
      <PageHeader
        title="Settings"
        description="Your account, how the app looks, and how it processes audio."
      />

      <div>
      <Tabs
        value={tab}
        onValueChange={(value) => {
          setTab(value);
          window.location.hash = value;
        }}
        className="w-full"
      >
        <TabsList className="grid w-full grid-cols-2 lg:flex lg:w-fit h-auto gap-1 mb-6 bg-muted/60 p-1 rounded-xl">
          <TabsTrigger value="profile" className="flex items-center gap-1.5 rounded-lg flex-1 min-w-fit data-[state=active]:shadow-sm">
            <User className="w-3.5 h-3.5" />
            <span>Profile</span>
          </TabsTrigger>
          <TabsTrigger value="account" className="flex items-center gap-1.5 rounded-lg flex-1 min-w-fit data-[state=active]:shadow-sm">
            <Settings2 className="w-3.5 h-3.5" />
            <span>Account</span>
          </TabsTrigger>
          <TabsTrigger value="appearance" className="flex items-center gap-1.5 rounded-lg flex-1 min-w-fit data-[state=active]:shadow-sm">
            <Palette className="w-3.5 h-3.5" />
            <span>Appearance</span>
          </TabsTrigger>
          <TabsTrigger value="performance" className="flex items-center gap-1.5 rounded-lg flex-1 min-w-fit data-[state=active]:shadow-sm">
            <Zap className="w-3.5 h-3.5" />
            <span>Performance</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile">
          <Card className="rounded-2xl shadow-xs">
            <CardHeader>
              <CardTitle>Profile Settings</CardTitle>
              <CardDescription>
                The name and email on your account.
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
          <Card className="rounded-2xl shadow-xs">
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

              <div className="flex items-center justify-between gap-4">
                <div>
                  <h4 className="font-medium">Delete account</h4>
                  <p className="text-sm text-muted-foreground">
                    Email contactwordwizai@gmail.com from this address and we'll
                    permanently delete your account and its reading data.
                  </p>
                </div>
                <Button variant="outline" asChild>
                  <a href="mailto:contactwordwizai@gmail.com?subject=Delete%20my%20account">
                    Email us
                  </a>
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="appearance">
          <Card className="rounded-2xl shadow-xs">
            <CardHeader>
              <CardTitle>Appearance Settings</CardTitle>
              <CardDescription>
                Customize how the application looks.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label htmlFor="theme">Theme</Label>
                  <p className="text-sm text-muted-foreground">
                    Light, dark, or match your device.
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


        <TabsContent value="performance">
          <Card className="rounded-2xl shadow-xs">
            <CardHeader>
              <CardTitle>Performance Settings</CardTitle>
              <CardDescription>
                Choose how your child's reading gets checked.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex-1 pr-4">
                  <Label htmlFor="clientProcessing">
                    Check sounds on this device
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    Works out the sounds in this browser instead of waiting
                    on our server, which is usually 50 to 70% faster. The
                    first time, it downloads about 100 MB. Turn it off on
                    older devices or slow internet.
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
                    Stay connected between recordings (experimental)
                  </Label>
                  <p className="text-sm text-muted-foreground mt-1">
                    Keeps one connection to our server open instead of
                    starting a new one for every sentence, so feedback after
                    the first recording can come back up to 5 seconds sooner.
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
                  <li>The download happens once and is saved for next time</li>
                  <li>Turns itself off on devices without enough memory</li>
                  <li>If anything goes wrong, our server checks the reading instead</li>
                  <li>Works best on a computer with a good internet connection</li>
                </ul>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Profile is read-only, so a save button there did nothing. */}
      {tab !== "profile" && (
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
      )}
      </div>
    </AppPage>
  );
};

export default Settings;
