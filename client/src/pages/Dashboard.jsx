import React, { useState } from 'react';
import LeafUploader from '../components/LeafUploader';
import PredictionCard from '../components/PredictionCard';
import RemediationTab from '../components/RemediationTab';
import PdfExportModal from '../components/PdfExportModal';
import HeatmapSlider from '../components/HeatmapSlider';

const Dashboard = () => {
  const [data, setData] = useState(null);

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="text-center mb-8">
        <h1 className="text-3xl font-extrabold text-green-700">Real-time Leaf Diagnosis</h1>
      </div>
      
      <LeafUploader onUploadSuccess={setData} />
      
      {data && (
        <div className="mt-8">
          
          {/* Dashboard Components */}
          <PredictionCard result={data} />
          
          {/* Heatmap tabhi dikhega jab backend se image aayegi */}
          {data.gradcam_heatmap_base64 && (
             <HeatmapSlider 
                originalImg={data.original_url || "images.jpg"} 
                heatmapImg={data.gradcam_heatmap_base64} 
             />
          )}
          
          <RemediationTab remediationData={data.remediation} />
          <PdfExportModal data={data} />
          
        </div>
      )}
    </div>
  );
};

export default Dashboard;