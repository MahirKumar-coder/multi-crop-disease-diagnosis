import React, { useState } from 'react';
import { Download, Loader2 } from 'lucide-react';
import jsPDF from 'jspdf';
// FIX: Import ka naya tarika Vite ke liye
import autoTable from 'jspdf-autotable'; 
import html2canvas from 'html2canvas';

const PdfReportGenerator = ({ targetElementId, fileName, data }) => {
    const [isGenerating, setIsGenerating] = useState(false);

    const generatePdf = async () => {
        setIsGenerating(true);
        try {
            const element = document.getElementById(targetElementId);
            const canvas = await html2canvas(element, { scale: 2, useCORS: true });
            const imgData = canvas.toDataURL('image/png');

            const pdf = new jsPDF('p', 'mm', 'a4');
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = (canvas.height * pdfWidth) / canvas.width;

            // Page 1: UI Visuals
            pdf.setFontSize(20);
            pdf.setTextColor(4, 120, 87);
            pdf.text("CropCare AI - Agronomy Advisory Report", 14, 15);
            pdf.addImage(imgData, 'PNG', 0, 25, pdfWidth, pdfHeight);

            // Page 2: Dosage Tables
            if (data && data.remediation) {
                pdf.addPage();
                pdf.setFontSize(16);
                pdf.setTextColor(30, 41, 59);
                pdf.text("Detailed Treatment Prescriptions", 14, 20);

                if (data.remediation.chemical && data.remediation.chemical.length > 0) {
                    const chemicalData = data.remediation.chemical.map(item => [
                        item.name || item.action,
                        item.dosage || 'N/A',
                        item.frequency || 'N/A'
                    ]);

                    // FIX: Direct autoTable function call instead of pdf.autoTable()
                    autoTable(pdf, {
                        startY: 30,
                        head: [['Chemical / Product', 'Dosage', 'Frequency']],
                        body: chemicalData,
                        theme: 'grid',
                        headStyles: { fillColor: [217, 119, 6] }
                    });
                }

                if (data.remediation.organic && data.remediation.organic.length > 0) {
                    const organicData = data.remediation.organic.map(item => [
                        item.name || item.action,
                        item.method || item.frequency || 'N/A'
                    ]);

                    // FIX: Direct autoTable function call
                    autoTable(pdf, {
                        startY: pdf.lastAutoTable ? pdf.lastAutoTable.finalY + 15 : 30,
                        head: [['Organic Solution', 'Application Method']],
                        body: organicData,
                        theme: 'grid',
                        headStyles: { fillColor: [5, 150, 105] }
                    });
                }
            }

            pdf.save(fileName);
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to generate PDF. Please try again.');
        } finally {
            setIsGenerating(false);
        }
    };

    return (
        <button onClick={generatePdf} disabled={isGenerating} className="flex items-center gap-2 px-6 py-3 bg-slate-900 text-white rounded-xl font-bold hover:bg-slate-800 transition disabled:opacity-70">
            {isGenerating ? <Loader2 className="w-5 h-5 animate-spin" /> : <Download className="w-5 h-5" />}
            <span>{isGenerating ? 'Generating Report...' : 'Download Full Report (PDF)'}</span>
        </button>
    );
};

export default PdfReportGenerator;