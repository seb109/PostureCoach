"use client";

import { useEffect, useRef, useState } from "react";
import { Play, Square, Video } from "lucide-react";
import { useRouter } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { postureApi, sessionApi } from "@/services/api";
import type { FrameAnalysis, Session } from "@/types/api";
import { useRequireAuth } from "@/hooks/use-require-auth";

export function Monitor() {
  const ready = useRequireAuth();
  const router = useRouter();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [reading, setReading] = useState<FrameAnalysis | null>(null);
  const [running, setRunning] = useState(false);

  async function start() {
    const started = await sessionApi.start();
    const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 960, height: 540 }, audio: false });
    if (videoRef.current) videoRef.current.srcObject = stream;
    setSession(started);
    setRunning(true);
  }

  async function stop() {
    setRunning(false);
    videoRef.current?.srcObject && (videoRef.current.srcObject as MediaStream).getTracks().forEach((track) => track.stop());
    if (session) {
      const stopped = await sessionApi.stop(session.id);
      if (stopped.report_id) router.push(`/reports/${stopped.report_id}`);
    }
  }

  useEffect(() => {
    if (!running || !session) return;
    const id = window.setInterval(async () => {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      if (!video || !canvas || video.readyState < 2) return;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext("2d")?.drawImage(video, 0, 0);
      const image = canvas.toDataURL("image/jpeg", 0.75);
      const result = await postureApi.analyze(image).catch(() => null);
      if (!result) return;
      setReading(result);
      if (result.ratio !== null && result.status) {
        const score = Math.max(0, Math.min(100, result.ratio));
        await sessionApi.metric({ session_id: session.id, score, classification: result.status, ratio: result.ratio, distance: result.distance, angle: result.angle, alert: result.is_flashing ? "Posture alert" : null }).catch(() => undefined);
      }
    }, 1200);
    return () => window.clearInterval(id);
  }, [running, session]);

  if (!ready) return null;

  return (
    <AppShell>
      <div className="mb-5 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Live monitoring</h1>
          <p className="text-sm text-slate-600">{session ? `Session ${session.id}` : "Ready to start"}</p>
        </div>
        <div className="flex gap-2">
          <Button onClick={start} disabled={running}><Play className="h-4 w-4" /> Start</Button>
          <Button onClick={stop} disabled={!running} className="bg-red-600"><Square className="h-4 w-4" /> Stop</Button>
        </div>
      </div>
      <div className="grid gap-4 lg:grid-cols-[1fr_320px]">
        <div className="overflow-hidden rounded-lg border border-border bg-slate-950">
          <video ref={videoRef} autoPlay playsInline muted className="aspect-video w-full object-cover" />
          {!running && <div className="flex h-28 items-center justify-center gap-2 text-white"><Video className="h-5 w-5" /> Camera idle</div>}
          <canvas ref={canvasRef} className="hidden" />
        </div>
        <div className="space-y-4">
          <Card><p className="text-sm text-slate-500">Score</p><p className="mt-2 text-4xl font-bold">{reading?.ratio ?? "--"}</p></Card>
          <Card><p className="text-sm text-slate-500">Classification</p><p className="mt-2 text-xl font-bold">{reading?.status ?? "Waiting"}</p></Card>
          <Card>
            <p className="text-sm text-slate-500">Metrics</p>
            <div className="mt-3 space-y-2 text-sm">
              <p>Distance: {reading?.distance ?? "--"}</p>
              <p>Angle: {reading?.angle ?? "--"}</p>
              <p>Pose visible: {reading?.pose_visible ? "Yes" : "No"}</p>
              <p>Alert: {reading?.is_flashing ? "Active" : "Clear"}</p>
            </div>
          </Card>
        </div>
      </div>
    </AppShell>
  );
}
