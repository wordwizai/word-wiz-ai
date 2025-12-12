import { Toaster as Sonner } from "sonner";

export function Toaster() {
  return (
    <Sonner
      position="top-center"
      toastOptions={{
        duration: 5000,
        classNames: {
          toast: "bg-card text-card-foreground border-border",
          title: "text-foreground font-semibold",
          description: "text-muted-foreground",
          error: "bg-destructive text-destructive-foreground border-destructive",
          success: "bg-green-600 text-white border-green-600",
          info: "bg-blue-600 text-white border-blue-600",
        },
      }}
    />
  );
}
