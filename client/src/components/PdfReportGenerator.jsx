import React, { useState } from 'react';
import { jsPDF } from 'jspdf';
import html2canvas from 'html2canvas';
import { Download, Loader2 } from 'lucide-react';

// FIX: targetId ko targetElementId kar diya gaya hai
const PdfReportGenerator = ({ targetElementId, fileName = "CropCare_Prescription.pdf" }) => {
    const [loading, setLoading] = useState(false);

    const generatePdf = async () => {
        setLoading(true);
        // FIX: Yahan bhi targetElementId use kiya hai
        const element = document.getElementById(targetElementId); 
        
        if (!element) {
            console.error("Error: PDF report div not found!");
            alert("Error: Please wait for the report to fully load before downloading.");
            setLoading(false);
            return;
        }

        try {
            const canvas = await html2canvas(element, { scale: 2, useCORS: true, logging: false });
            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF('p', 'mm', 'a4');
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
            
            pdf.addImage(imgData, 'PNG', 0, 10, pdfWidth, pdfHeight);
            pdf.save(fileName);
        } catch (error) {
            console.error("PDF Generation Failed:", error);
        } finally {
            setLoading(false);
        }
    };

    return (
        <button 
            onClick={generatePdf}
            disabled={loading}
            className="w-full sm:w-auto px-8 py-3.5 bg-slate-900 text-white rounded-xl font-semibold shadow-lg hover:bg-slate-800 hover:shadow-xl hover:-translate-y-0.5 transition-all flex items-center justify-center gap-2"
        >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" />}
            {loading ? 'Generating Report...' : 'Download Full Report (PDF)'}
        </button>
    );
};

export default PdfReportGenerator;