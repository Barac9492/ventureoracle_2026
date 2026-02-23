export const dynamic = 'force-dynamic';
import { fetchDiscoveries, fetchRecommendations } from '@/lib/api';

export default async function Discoveries() {
    const [discoveries, recommendations] = await Promise.all([
        fetchDiscoveries(),
        fetchRecommendations()
    ]);

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <header>
                <h1 className="text-4xl font-extrabold tracking-tight mb-2">Discoveries</h1>
                <p className="text-gray-400">Trending content and AI topic recommendations.</p>
            </header>

            <div className="grid lg:grid-cols-2 gap-8">
                <section>
                    <h2 className="text-2xl font-bold mb-6 text-gradient">Topic Recommendations</h2>
                    <div className="space-y-4">
                        {recommendations.map((r: any) => (
                            <div key={r.id} className="glass-card flex flex-col">
                                <div className="flex justify-between items-center mb-2">
                                    <h3 className="text-lg font-semibold text-white">{r.title}</h3>
                                    <span className="text-green-400 font-mono text-sm px-2 py-1 bg-green-500/10 rounded-md">
                                        {(r.relevance * 100).toFixed(0)}% Match
                                    </span>
                                </div>
                                <p className="text-gray-400 text-sm leading-relaxed">{r.rationale}</p>
                            </div>
                        ))}
                    </div>
                </section>

                <section>
                    <h2 className="text-2xl font-bold mb-6 text-gradient">Recent Signals</h2>
                    <div className="space-y-4">
                        {discoveries.map((d: any) => (
                            <a key={d.id} href={d.url} target="_blank" rel="noopener noreferrer" className="block glass-card hover:bg-surface-800/80 transition-colors">
                                <h3 className="text-md font-medium text-blue-400 mb-2 leading-snug">{d.title}</h3>
                                <p className="text-gray-400 text-sm line-clamp-2 mb-3">{d.summary}</p>
                                <div className="flex items-center text-xs text-gray-500">
                                    <span className="uppercase tracking-wider">{d.platform}</span>
                                    <span className="mx-2">•</span>
                                    <span>{new Date(d.discovered_at).toLocaleDateString()}</span>
                                </div>
                            </a>
                        ))}
                    </div>
                </section>
            </div>
        </div>
    );
}
