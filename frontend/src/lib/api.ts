const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

export interface ModerationResult {
  safe: boolean;
  confidence: number;
  action: string;
  scores: Record<string, any>;
  explanation: string;
  flagged_categories: string[];
}

export interface VideoModerationResponse {
  job_id: string;
  status: string;
}

export interface JobStatusResponse {
  job_id: string;
  status: string;
  error?: string;
  result?: any;
}

export const moderateImage = async (file: File, caption?: string): Promise<ModerationResult> => {
  const formData = new FormData();
  formData.append("file", file);
  if (caption) formData.append("caption", caption);

  const response = await fetch(`${API_BASE}/moderate/image`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Image moderation failed");
  }
  return response.json();
};

export const moderateText = async (text: string): Promise<ModerationResult> => {
  const response = await fetch(`${API_BASE}/moderate/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Text moderation failed");
  }
  const result = await response.json();
  const flagged_categories = [
    ["toxic", "toxicity"], ["threat", "threats"], ["harassment", "harassment"],
    ["profanity", "profanity"], ["adult_promo", "adult promotion"],
  ].filter(([key]) => result[key] >= 0.4).map(([, label]) => label);
  return {
    ...result,
    action: result.safe ? "approve" : "review",
    flagged_categories,
    scores: Object.fromEntries([
      "toxic", "threat", "harassment", "profanity", "adult_promo",
    ].map((key) => [key, result[key]])),
  };
};

export const moderateVideo = async (
  file: File,
  caption?: string,
  sampleInterval: number = 2.0
): Promise<ModerationResult> => {
  const formData = new FormData();
  formData.append("file", file);
  if (caption) formData.append("caption", caption);
  formData.append("sample_interval", sampleInterval.toString());

  const response = await fetch(`${API_BASE}/moderate/video`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Video moderation submission failed");
  }
  const { job_id } = await response.json() as VideoModerationResponse;
  for (let attempt = 0; attempt < 600; attempt += 1) {
    await new Promise((resolve) => window.setTimeout(resolve, 1000));
    const status = await getJobStatus(job_id);
    if (status.status === "completed" && status.result) return status.result as ModerationResult;
    if (status.status === "failed") throw new Error(status.error || "Video moderation failed");
  }
  throw new Error("Video moderation timed out. Check the API job status and try again.");
};

export const getJobStatus = async (jobId: string): Promise<JobStatusResponse> => {
  const response = await fetch(`${API_BASE}/moderate/status/${jobId}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "Failed to fetch job status");
  }
  return response.json();
};

export const getHealthStatus = async (): Promise<{ status: string }> => {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) throw new Error("Health check failed");
  return response.json();
};
