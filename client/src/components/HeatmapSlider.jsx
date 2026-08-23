import React, { useState } from 'react';

const HeatmapSlider = ({ originalImg, heatmapImg }) => {
  const [sliderPos, setSliderPos] = useState(50);

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mt-6">
      <h3 className="text-xl font-bold text-gray-800 mb-4">Grad-CAM Heatmap Analysis</h3>
      <div className="relative w-full aspect-video overflow-hidden rounded bg-gray-200">
        <img src={originalImg} alt="Original" className="absolute w-full h-full object-cover" />
        <img 
          src={heatmapImg} 
          alt="Heatmap" 
          className="absolute w-full h-full object-cover" 
          style={{ clipPath: `polygon(0 0, ${sliderPos}% 0, ${sliderPos}% 100%, 0 100%)` }}
        />
        <input 
          type="range" min="0" max="100" value={sliderPos} 
          onChange={(e) => setSliderPos(e.target.value)}
          className="absolute inset-0 w-full h-full opacity-0 cursor-ew-resize z-10"
        />
        <div className="absolute top-0 bottom-0 w-1 bg-white" style={{ left: `${sliderPos}%` }}></div>
      </div>
    </div>
  );
};

export default HeatmapSlider;