export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export async function fetchDashboard() {
  try {
    const res = await fetch(`${API_URL}/dashboard`, { next: { revalidate: 10 } });
    if (!res.ok) return { metrics: { source_count: 0, content_count: 0, discovery_count: 0, recommendation_count: 0, prediction_count: 0 }, profile_status: {} };
    return res.json();
  } catch (e) {
    return { metrics: { source_count: 0, content_count: 0, discovery_count: 0, recommendation_count: 0, prediction_count: 0 }, profile_status: {} };
  }
}

export async function fetchProfile() {
  const res = await fetch(`${API_URL}/profile`, { next: { revalidate: 60 } });
  if (!res.ok) {
    if (res.status === 404) return null;
    throw new Error("Failed to fetch profile");
  }
  return res.json();
}

export async function fetchPredictions(status?: string) {
  try {
    const url = new URL(`${API_URL}/predictions`);
    if (status) url.searchParams.append("status", status);

    const res = await fetch(url.toString(), { next: { revalidate: 10 } });
    if (!res.ok) return [];
    return res.json();
  } catch (e) {
    return [];
  }
}

export async function fetchDiscoveries() {
  try {
    const res = await fetch(`${API_URL}/discoveries?limit=30`, { next: { revalidate: 30 } });
    if (!res.ok) return [];
    return res.json();
  } catch (e) {
    return [];
  }
}

export async function fetchRecommendations() {
  try {
    const res = await fetch(`${API_URL}/recommendations?limit=10`, { next: { revalidate: 30 } });
    if (!res.ok) return [];
    return res.json();
  } catch (e) {
    return [];
  }
}
