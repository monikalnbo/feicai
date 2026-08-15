import { useState, useEffect, useCallback } from "react";
import { Save, RefreshCw, BookHeart } from "lucide-react";
import { Button } from "@nous-research/ui/ui/components/button";
import { Spinner } from "@nous-research/ui/ui/components/spinner";
import { Card, CardContent, CardHeader, CardTitle } from "@nous-research/ui/ui/components/card";
import { useToast } from "@nous-research/ui/hooks/use-toast";
import { Toast } from "@nous-research/ui/ui/components/toast";
import { cn } from "@/lib/utils";

export default function SoulEditorPage() {
  const [content, setContent] = useState("");
  const [original, setOriginal] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { toast, showToast } = useToast();

  const fetchSoul = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await fetch("/api/soul");
      const data = await resp.json();
      const text = data.content || "";
      setContent(text);
      setOriginal(text);
    } catch (err) {
      showToast({ title: "Error", description: "Failed to load SOUL.md", variant: "error" });
    } finally {
      setLoading(false);
    }
  }, [showToast]);

  useEffect(() => {
    fetchSoul();
  }, [fetchSoul]);

  const hasChanges = content !== original;

  const handleSave = async () => {
    setSaving(true);
    try {
      const resp = await fetch("/api/soul", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      if (resp.ok) {
        setOriginal(content);
        showToast({ title: "Saved", description: "SOUL.md updated successfully", variant: "success" });
      } else {
        throw new Error("Save failed");
      }
    } catch (err) {
      showToast({ title: "Error", description: "Failed to save SOUL.md", variant: "error" });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex flex-col gap-4 min-h-0 flex-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <BookHeart className="h-5 w-5 text-midground" />
          <h1 className="font-mondwest text-display text-lg tracking-[0.08em]">SOUL.md</h1>
        </div>
        <div className="flex items-center gap-2">
          <span className={cn(
            "text-xs font-sans transition-colors",
            hasChanges ? "text-warning" : "text-text-tertiary"
          )}>
            {hasChanges ? "● Unsaved changes" : "Saved"}
          </span>
          <Button
            ghost
            size="icon"
            onClick={fetchSoul}
            disabled={loading}
            aria-label="Reload"
          >
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          </Button>
          <Button
            onClick={handleSave}
            disabled={!hasChanges || saving}
            className="gap-1.5"
          >
            {saving ? (
              <Spinner className="h-4 w-4" />
            ) : (
              <Save className="h-4 w-4" />
            )}
            Save
          </Button>
        </div>
      </div>

      <Card className="flex-1 min-h-0 flex flex-col">
        <CardContent className="flex-1 min-h-0 p-0">
          {loading ? (
            <div className="flex items-center justify-center h-full min-h-[200px]">
              <Spinner />
            </div>
          ) : (
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className={cn(
                "w-full h-full min-h-[300px] resize-none",
                "bg-transparent text-text-primary font-mono text-sm",
                "p-4 outline-none border-none",
                "focus:ring-0 focus:outline-none",
                "placeholder:text-text-tertiary"
              )}
              placeholder="Edit your Hermes SOUL.md here..."
              spellCheck={false}
            />
          )}
        </CardContent>
      </Card>

      <Toast toast={toast} />
    </div>
  );
}