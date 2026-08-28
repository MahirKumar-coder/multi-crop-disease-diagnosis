import React, { useState } from 'react';

const HeatmapSlider = ({ originalImage, heatmapBase64 }) => {
    const [sliderValue, setSliderValue] = useState(50);
    const heatmapSrc = heatmapBase64?.startsWith('data:image') ? heatmapBase64 : `data:image/jpeg;base64,${heatmapBase64}`;

    return (
        <div className="bg-white p-5 rounded-2xl shadow-sm border border-gray-100 space-y-4">
            <h3 className="font-bold text-slate-800 text-lg">AI Lesion Localization</h3>
            <div className="relative w-full h-64 sm:h-80 overflow-hidden rounded-xl shadow-inner bg-gray-100 group">
                <img src={originalImage} alt="Original" className="absolute inset-0 w-full h-full object-cover" />
                <img 
                    src={heatmapSrc} 
                    alt="Grad-CAM" 
                    className="absolute inset-0 w-full h-full object-cover"
                    style={{ clipPath: `inset(0 ${100 - sliderValue}% 0 0)` }}
                />
                <input
                    type="range" min="0" max="100" value={sliderValue}
                    onChange={(e) => setSliderValue(e.target.value)}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-10"
                />
                <div 
                    className="absolute top-0 bottom-0 w-1 bg-white shadow-[0_0_10px_rgba(0,0,0,0.5)] z-0 transition-transform"
                    style={{ left: `${sliderValue}%`, transform: 'translateX(-50%)' }}
                >
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-lg border border-gray-200">
                        <span className="text-slate-400 text-xs font-bold tracking-tighter">&lt;&gt;</span>
                    </div>
                </div>
            </div>
            <p className="text-xs text-center text-slate-500 font-medium uppercase tracking-wider">Slide to compare Raw Image vs Grad-CAM</p>
        </div>
    );
};

export default HeatmapSlider;