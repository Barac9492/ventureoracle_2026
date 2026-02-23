export const dynamic = 'force-dynamic';
import { fetchDashboard } from '@/lib/api';

export default async function Dashboard() {
  const data = await fetchDashboard();
  const { metrics, profile_status } = data;

  const statCards = [
    { label: 'Content Sources', value: metrics.source_count },
    { label: 'Ingested Pieces', value: metrics.content_count },
    { label: 'Discovered', value: metrics.discovery_count },
    { label: 'Recommendations', value: metrics.recommendation_count },
    { label: 'Predictions', value: metrics.prediction_count },
  ];

  return (
    <div className="space-y-8 animate-in fade-in duration-500">
      <header>
        <h1 className="text-4xl font-extrabold tracking-tight mb-2">Dashboard</h1>
        <p className="text-gray-400">Overview of your VentureOracle engine.</p>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
        {statCards.map((stat) => (
          <div key={stat.label} className="glass-card">
            <h3 className="text-sm font-medium text-gray-400 mb-1">{stat.label}</h3>
            <p className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-gray-400">
              {stat.value}
            </p>
          </div>
        ))}
      </div>

      <section className="glass-card mt-8">
        <h2 className="text-xl font-semibold mb-4 text-white">Profile Status</h2>
        {profile_status.version ? (
          <div className="space-y-2 text-gray-300">
            <p>
              <span className="text-gray-500 w-32 inline-block">Version:</span>
              <span className="font-mono text-primary-400">v{profile_status.version}</span>
            </p>
            <p>
              <span className="text-gray-500 w-32 inline-block">Samples:</span>
              <span className="font-mono text-white">{profile_status.sample_count} analyzed</span>
            </p>
            <p>
              <span className="text-gray-500 w-32 inline-block">Last Built:</span>
              <span className="font-mono text-white">{new Date(profile_status.built_at).toLocaleString()}</span>
            </p>
          </div>
        ) : (
          <div className="text-yellow-500/80 bg-yellow-500/10 p-4 rounded-xl border border-yellow-500/20">
            No profile generated yet. Ingest content and run analysis in the CLI.
          </div>
        )}
      </section>
    </div>
  );
}
