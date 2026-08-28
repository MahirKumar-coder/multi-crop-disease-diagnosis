import React from 'react';
import { Activity } from 'lucide-react';

const PredictionCard = ({ predictions }) => {
    if (!predictions || predictions.length === 0) return null;

    return (
        <div className="p-5 bg-white rounded-2xl shadow-sm border border-gray-100 space-y-5">
            <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2 border-b pb-3">
                <Activity className="w-5 h-5 text-emerald-500"/> Confidence Breakdown
            </h3>
            <div className="space-y-4">
                {predictions.slice(0, 3).map((pred, index) => (
                    <div key={index} className="space-y-1.5">
                        <div className="flex justify-between text-sm">
                            <span className="font-semibold text-slate-700">{pred.className.replace(/_/g, ' ')}</span>
                            <span className={`font-bold ${index === 0 ? 'text-emerald-600' : 'text-slate-500'}`}>
                                {(pred.probability * 100).toFixed(1)}%
                            </span>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                            <div 
                                className={`h-full rounded-full transition-all duration-1000 ${index === 0 ? 'bg-emerald-500' : 'bg-slate-400'}`}
                                style={{ width: `${pred.probability * 100}%` }}
                            ></div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default PredictionCard;