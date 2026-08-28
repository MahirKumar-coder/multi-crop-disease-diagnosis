import React, { useState } from 'react';
import { Camera as CameraIcon, Info, Loader2 } from 'lucide-react';
import LeafUploader from '../components/LeafUploader';
import CameraModal from '../components/CameraModal';
import HeatmapSlider from '../components/HeatmapSlider';
import PredictionCard from '../components/PredictionCard';
import RemediationTab from '../components/RemediationTab';
import PdfReportGenerator from '../components/PdfReportGenerator';
// FIX: Backend API import karni zaroori hai camera image bhejne ke liye
import { predictDisease } from '../services/api'; 

const Dashboard = () => {
    const [showCamera, setShowCamera] = useState(false);
    const [data, setData] = useState(null);
    // FIX: Naya loading state add kiya hai
    const [isProcessing, setIsProcessing] = useState(false);

    // FIX: Ab ye function photo ko seedha Mahir ke AI backend par bhejega
    const handleCameraCapture = async (file, imageUrl) => {
        setShowCamera(false);
        setIsProcessing(true); // Loading screen chalu

        try {
            const response = await predictDisease(file);
            setData(response.data); // Result aate hi screen par dikhega
        } catch (error) {
            console.error("Camera prediction error:", error);
            alert("Failed to analyze image. Please try again or check your internet connection.");
        } finally {
            setIsProcessing(false); // Loading screen band
        }
    };

    return (
        <div 
            className="min-h-screen py-10 px-4 md:px-8 font-sans bg-cover bg-center bg-fixed relative"
            style={{ 
                backgroundImage: `linear-gradient(rgba(255, 255, 255, 0.85), rgba(255, 255, 255, 0.85)), url('https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8?q=80&w=1920&auto=format&fit=crop')` 
            }}
        >
            {/* 🚀 NAYA LOADING OVERLAY 🚀 */}
            {isProcessing && (
                <div className="fixed inset-0 z-[60] flex flex-col items-center justify-center bg-white/80 backdrop-blur-sm">
                    <div className="bg-white p-8 rounded-2xl shadow-2xl flex flex-col items-center border border-emerald-100 animate-in zoom-in-95 duration-300">
                        <Loader2 className="w-12 h-12 text-emerald-600 animate-spin mb-4" />
                        <h3 className="text-xl font-bold text-slate-800">Analyzing Image...</h3>
                        <p className="text-slate-500 mt-2 text-sm text-center max-w-[250px]">
                            Please wait while our AI detects diseases and generates a prescription.
                        </p>
                    </div>
                </div>
            )}

            <div className="max-w-5xl mx-auto space-y-8 relative z-10">
                
                {/* Header & Scanner Launch */}
                <div className="flex flex-col md:flex-row justify-between items-center bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow-sm border border-gray-200 gap-4">
                    <div>
                        <h1 className="text-3xl font-extrabold text-green-700 tracking-tight">Real-time Leaf Diagnosis</h1>
                        <p className="text-slate-500 mt-1">Upload a leaf image or use the camera to detect diseases instantly.</p>
                    </div>
                    <button 
                        onClick={() => setShowCamera(true)}
                        className="px-6 py-3 bg-emerald-100 text-emerald-700 rounded-xl font-bold hover:bg-emerald-200 transition flex items-center gap-2 w-full md:w-auto justify-center"
                    >
                        <CameraIcon className="w-5 h-5"/> Launch Scanner
                    </button>
                </div>

                {/* Camera Modal */}
                {showCamera && (
                    <CameraModal 
                        onClose={() => setShowCamera(false)} 
                        onCapture={handleCameraCapture} 
                    />
                )}
                
                {/* Uploader Component */}
                <div className="bg-white/90 backdrop-blur-md p-6 rounded-2xl shadow-sm border border-gray-200">
                    <LeafUploader onUploadSuccess={setData} />
                </div>
                
                {data && (
                    <div className="space-y-6 animate-in fade-in duration-500 mt-8">
                        
                        {/* Printable/Report Container */}
                        <div id="diagnostic-report" className="bg-white p-6 sm:p-8 rounded-3xl shadow-sm border border-gray-200 space-y-6">
                            
                            <div className="flex items-center gap-2 border-b pb-4">
                                <Info className="w-6 h-6 text-emerald-600" />
                                <h2 className="text-2xl font-bold text-slate-800">Diagnostic Report</h2>
                            </div>

                            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
                                {/* Left Side: Prediction & Heatmap */}
                                <div className="lg:col-span-5 space-y-6">
                                    <PredictionCard result={data} />
                                    
                                    {data.gradcam_heatmap_base64 && (
                                        <HeatmapSlider 
                                            originalImage={data.original_url || "https://images.unsplash.com/photo-1599598425947-330026e64119?w=500"} 
                                            heatmapBase64={data.gradcam_heatmap_base64} 
                                        />
                                    )}
                                </div>

                                {/* Right Side: Remediation Tabs */}
                                <div className="lg:col-span-7">
                                    <h3 className="font-bold text-lg text-slate-800 mb-4">Recommended Action Plan</h3>
                                    <RemediationTab treatmentData={data.remediation} />
                                </div>
                            </div>
                        </div>
                        
                        {/* PDF Download Button */}
                        <div className="flex justify-end pt-4">
                            <PdfReportGenerator targetElementId="diagnostic-report" fileName="CropCare_Advisory_Report.pdf" />
                        </div>
                        
                    </div>
                )}
            </div>
        </div>
    );
};

export default Dashboard;