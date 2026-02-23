export const dynamic = 'force-dynamic';
import { fetchPredictions } from '@/lib/api';

export default async function Predictions() {
    const predictions = await fetchPredictions();

    return (
        <div className="space-y-8 animate-in fade-in duration-500">
            <header>
                <h1 className="text-4xl font-extrabold tracking-tight mb-2">Predictions</h1>
                <p className="text-gray-400">Your AI-generated forecasts based on domain expertise.</p>
            </header>

            <div className="space-y-4">
                {predictions.map((p: any) => (
                    <div key={p.id} className="glass-card flex flex-col gap-4">
                        <div className="flex justify-between items-start">
                            <span className="text-xs uppercase tracking-widest text-primary-500 font-bold bg-primary-500/10 px-3 py-1 rounded-full">
                                {p.domain}
                            </span>
                            <span className={`text-xs uppercase tracking-widest px-3 py-1 rounded-full font-bold
                ${p.status === 'active' ? 'text-yellow-400 bg-yellow-400/10' :
                                    p.status === 'correct' ? 'text-green-400 bg-green-400/10' :
                                        p.status === 'incorrect' ? 'text-red-400 bg-red-400/10' : 'text-gray-400 bg-gray-400/10'}`}>
                                {p.status}
                            </span>
                        </div>
                        <h2 className="text-xl font-medium text-white">{p.claim}</h2>

                        <div className="grid grid-cols-2 gap-4 text-sm bg-surface-800/50 p-4 rounded-xl">
                            <div>
                                <span className="text-gray-500 block mb-1">Timeframe</span>
                                <span className="text-gray-300">{p.timeframe}</span>
                            </div>
                            <div>
                                <span className="text-gray-500 block mb-1">Confidence</span>
                                <strong className={p.confidence > 0.7 ? 'text-green-400' : 'text-yellow-400'}>
                                    {(p.confidence * 100).toFixed(0)}%
                                </strong>
                            </div>
                        </div>

                        <div className="text-sm mt-2">
                            <h4 className="text-gray-400 font-medium mb-1">Reasoning</h4>
                            <p className="text-gray-300 leading-relaxed">{p.reasoning}</p>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
