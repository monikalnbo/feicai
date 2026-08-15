import { useState, useEffect, useCallback } from "react";
import {
  Activity,
  Monitor,
  Package,
  RefreshCw,
  AlertCircle,
  Globe,
  Cpu,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@nous-research/ui/ui/components/card";
import { Spinner } from "@nous-research/ui/ui/components/spinner";
import { Badge } from "@nous-research/ui/ui/components/badge";
import { Button } from "@nous-research/ui/ui/components/button";
/* ── Widget 类型 ── */
interface WidgetDef {
  name: string;
  label: string;
  description: string;
  icon: string;
  api_url: string;
  refresh_interval: number;
}

interface WidgetData {
  status: string;
  label: string;
  [key: string]: unknown;
}

const ICON_MAP: Record<string, React.ComponentType<{ className?: string }>> = {
  activity: Activity,
  monitor: Monitor,
  package: Package,
  cpu: Cpu,
  globe: Globe,
};

/* ── Widget 卡片组件 ── */
function WidgetCard({ widget: widget }: { widget: WidgetDef }) {
  const [data, setData] = useState<WidgetData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const resp = await fetch(`/api/feicai/widgets/${widget.name}/data`);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const json = await resp.json();
      setData(json);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [widget.name]);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, widget.refresh_interval * 1000);
    return () => clearInterval(interval);
  }, [fetchData, widget.refresh_interval]);

  const Icon = ICON_MAP[widget.icon] ?? Activity;

  const badgeTone =
    data?.status === "connected" || data?.status === "ok"
      ? "success"
      : data?.status === "disconnected" || data?.status === "error"
        ? "destructive"
        : "warning";

  return (
    <Card className="flex flex-col">
      <CardHeader className="flex flex-row items-center justify-between py-3 px-4">
        <div className="flex items-center gap-2">
          <Icon className="h-4 w-4 text-midground" />
          <CardTitle className="font-mondwest text-display text-xs tracking-[0.08em]">
            {widget.label}
          </CardTitle>
        </div>
        <div className="flex items-center gap-2">
          {loading ? (
            <Spinner className="h-3.5 w-3.5" />
          ) : (
            <Button ghost size="icon" onClick={fetchData} className="h-6 w-6" aria-label="Refresh">
              <RefreshCw className="h-3.5 w-3.5" />
            </Button>
          )}
        </div>
      </CardHeader>
      <CardContent className="px-4 pb-4 pt-0 flex-1">
        {error ? (
          <div className="flex items-center gap-2 text-xs text-destructive">
            <AlertCircle className="h-3.5 w-3.5" />
            <span>{error}</span>
          </div>
        ) : loading && !data ? (
          <div className="flex items-center justify-center py-6">
            <Spinner />
          </div>
        ) : data ? (
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <Badge
                tone={badgeTone}
                className="text-[0.65rem] px-1.5 py-0"
              >
                {data.status}
              </Badge>
              <span className="text-[0.65rem] text-text-tertiary">{widget.description}</span>
            </div>
            <WidgetDataDisplay data={data} />
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}

/* ── 数据展示（递归渲染） ── */
function WidgetDataDisplay({ data }: { data: Record<string, unknown> }) {
  const entries = Object.entries(data).filter(
    ([key]) => !["status", "label"].includes(key)
  );
  if (entries.length === 0) {
    return <p className="text-xs text-text-tertiary">No data</p>;
  }
  return (
    <div className="space-y-1">
      {entries.map(([key, value]) => (
        <div key={key} className="flex justify-between items-center text-xs">
          <span className="text-text-secondary capitalize">{key.replace(/_/g, " ")}</span>
          <span className="text-text-primary font-mono">
            {typeof value === "object" ? JSON.stringify(value).slice(0, 60) : String(value)}
          </span>
        </div>
      ))}
    </div>
  );
}

/* ── 仪表盘主页面 ── */
export default function WorkspacePage() {
  const [widgets, setWidgets] = useState<WidgetDef[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/feicai/widgets")
      .then((r) => r.json())
      .then((json) => setWidgets(json.widgets ?? []))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="flex flex-col gap-4 min-h-0 flex-1">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-midground" />
          <h1 className="font-mondwest text-display text-lg tracking-[0.08em]">工作台</h1>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Spinner />
        </div>
      ) : widgets.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-text-tertiary">
          <AlertCircle className="h-8 w-8 mb-2" />
          <p className="text-sm">暂无可用 Widget</p>
          <p className="text-xs">在 server.py 中注册 widget 即可显示</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {widgets.map((w) => (
            <WidgetCard key={w.name} widget={w} />
          ))}
        </div>
      )}

      {/* 拓展说明 */}
      <Card className="border-dashed border-border/40">
        <CardContent className="py-3 px-4">
          <p className="text-xs text-text-tertiary">
            💡 <strong>如何添加新 Widget？</strong>{" "}
            在 <code className="text-xs bg-background-base px-1 py-0.5 rounded">desktop/server.py</code> 中调用{" "}
            <code className="text-xs bg-background-base px-1 py-0.5 rounded">register_widget()</code> 即可。
            支持接入任意外部 API。
          </p>
        </CardContent>
      </Card>
    </div>
  );
}