export const API_URL = "http://localhost:8000/api";

export async function fetchDashboard() {
  const res = await fetch(`${API_URL}/dashboard`, { next: { revalidate: 10 } });
  if (!res.ok) throw new Error("Failed to fetch dashboard");
  return res.json();
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
  const url = new URL(`${API_URL}/predictions`);
  if (status) url.searchParams.append("status", status);
  
  const res = await fetch(url.toString(), { next: { revalidate: 10 } });
  if (!res.ok) throw new Error("Failed to fetch predictions");
  return res.json();
}

export async function fetchDiscoveries() {
  const res = await fetch(`${API_URL}/discoveries?limit=30`, { next: { revalidate: 30 } });
  if (!res.ok) throw new Error("Failed to fetch discoveries");
  return res.json();
}

export async function fetchRecommendations() {
  const res = await fetch(`${API_URL}/recommendations?limit=10`, { next: { revalidate: 30 } });
  if (!res.ok) throw new Error("Failed to fetch recommendations");
  return res.json();
}
