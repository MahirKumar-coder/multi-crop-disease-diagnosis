import React from 'react';
import { CheckCircle2 } from 'lucide-react';

const TreatmentSteps = ({ steps }) => {
    if (!steps || steps.length === 0) {
        return <p className="text-slate-500 italic p-4 text-center">No specific steps available.</p>;
    }

    return (
        <ul className="space-y-3">
            {steps.map((step, index) => (
                <li key={index} className="flex items-start bg-white p-4 rounded-xl border border-gray-100 shadow-sm transition hover:shadow-md">
                    <CheckCircle2 className="w-5 h-5 text-emerald-500 mr-3 flex-shrink-0 mt-0.5" />
                    
                    {/* Yahan humne check laga diya ki text hai ya object */}
                    {typeof step === 'object' && step !== null ? (
                        <div className="text-slate-700 leading-relaxed text-sm flex flex-col">
                            {/* Dawai ka naam bold me */}
                            <span className="font-bold text-slate-800 text-base">{step.name || "Treatment Step"}</span>
                            
                            {/* Baki details chote text me */}
                            <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500 mt-1">
                                {step.dosage && <span><b className="text-slate-600">Dosage:</b> {step.dosage}</span>}
                                {step.frequency && <span><b className="text-slate-600">Freq:</b> {step.frequency}</span>}
                                {step.stage && <span><b className="text-slate-600">Stage:</b> {step.stage}</span>}
                            </div>
                        </div>
                    ) : (
                        /* Agar purana normal text aaya toh aise dikhega */
                        <span className="text-slate-700 leading-relaxed text-sm">{step}</span>
                    )}
                </li>
            ))}
        </ul>
    );
};

export default TreatmentSteps;