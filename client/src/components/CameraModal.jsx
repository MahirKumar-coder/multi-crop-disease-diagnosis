import React, { useRef, useState, useCallback, useEffect } from 'react';
import { X, Camera as CameraIcon } from 'lucide-react';

const CameraModal = ({ onClose, onCapture }) => {
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const [stream, setStream] = useState(null);

    useEffect(() => {
        const startCamera = async () => {
            try {
                const mediaStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
                setStream(mediaStream);
                if (videoRef.current) {
                    videoRef.current.srcObject = mediaStream;
                }
            } catch (error) {
                console.error("Error accessing camera:", error);
                alert("Camera access denied or not available.");
            }
        };
        startCamera();

        return () => {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
            }
        };
    }, []);

    const handleCapture = useCallback(() => {
        if (videoRef.current && canvasRef.current) {
            const video = videoRef.current;
            const canvas = canvasRef.current;
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            
            const ctx = canvas.getContext('2d');
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            
            canvas.toBlob((blob) => {
                const file = new File([blob], "camera_capture.jpg", { type: "image/jpeg" });
                const imageUrl = URL.createObjectURL(blob);
                
                if (stream) {
                    stream.getTracks().forEach(track => track.stop());
                }
                
                onCapture(file, imageUrl);
            }, 'image/jpeg');
        }
    }, [onCapture, stream]);

    const handleClose = () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
        }
        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden animate-in zoom-in-95 duration-200">
                
                {/* Header */}
                <div className="flex justify-between items-center p-4 border-b">
                    <h3 className="font-bold text-lg text-slate-800 flex items-center gap-2">
                        <CameraIcon className="w-5 h-5 text-emerald-600" />
                        Live Scanner
                    </h3>
                    <button onClick={handleClose} className="text-slate-400 hover:text-slate-700 transition">
                        <X className="w-6 h-6" />
                    </button>
                </div>

                {/* Camera View */}
                <div className="relative bg-black aspect-video flex items-center justify-center overflow-hidden">
                    <video 
                        ref={videoRef} 
                        autoPlay 
                        playsInline 
                        muted 
                        className="w-full h-full object-cover -scale-x-100" 
                    />
                    <canvas ref={canvasRef} className="hidden" />
                </div>

                {/* Controls */}
                <div className="p-6 flex justify-center bg-slate-50">
                    <button 
                        onClick={handleCapture}
                        className="w-16 h-16 rounded-full bg-emerald-500 border-4 border-emerald-200 shadow-md hover:scale-105 hover:bg-emerald-600 transition-all flex items-center justify-center"
                    >
                        <div className="w-6 h-6 bg-white rounded-full"></div>
                    </button>
                </div>
                
            </div>
        </div>
    );
};

export default CameraModal;