import React, { useState } from 'react';
import { Leaf, FlaskConical, ShieldCheck } from 'lucide-react';
import TreatmentSteps from './TreatmentSteps';

const RemediationTab = ({ treatmentData }) => {
    const [activeTab, setActiveTab] = useState('organic');
    
    if (!treatmentData) return null;

    const tabs = [
        { id: 'organic', label: 'Organic', icon: Leaf, color: 'text-emerald-600', bg: 'bg-emerald-50' },
        { id: 'chemical', label: 'Chemical', icon: FlaskConical, color: 'text-amber-600', bg: 'bg-amber-50' },
        { id: 'prevention', label: 'Prevention', icon: ShieldCheck, color: 'text-blue-600', bg: 'bg-blue-50' },
    ];

    // FIX: Yahan 'preventive' word add kiya gaya hai (Backend se yahi naam aa raha hai)
    const getStepsData = () => {
        if (activeTab === 'prevention') {
            return treatmentData.preventive || treatmentData.prevention || treatmentData.preventive_measures;
        }
        return treatmentData[activeTab];
    };

    return (
        <div className="w-full bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="flex border-b border-gray-100">
                {tabs.map((tab) => {
                    const Icon = tab.icon;
                    const isActive = activeTab === tab.id;
                    return (
                        <button
                            key={tab.id}
                            className={`flex-1 py-4 flex flex-col items-center gap-1 text-sm font-semibold transition-all
                            ${isActive ? `border-b-2 border-slate-800 text-slate-800 ${tab.bg}` : 'text-slate-400 hover:bg-gray-50'}`}
                            onClick={() => setActiveTab(tab.id)}
                        >
                            <Icon className={`w-5 h-5 ${isActive ? tab.color : ''}`} />
                            <span>{tab.label}</span>
                        </button>
                    );
                })}
            </div>
            <div className="p-6 min-h-[200px] bg-slate-50/50">
                {/* Updated function calling */}
                <TreatmentSteps steps={getStepsData()} />
            </div>
        </div>
    );
};

export default RemediationTab;