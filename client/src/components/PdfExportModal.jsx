import React from 'react';
import { jsPDF } from "jspdf";

const PdfExportModal = ({ data }) => {
  const downloadPdf = () => {
    try {
      const doc = new jsPDF();
      
      // Title
      doc.setFontSize(20);
      doc.text("CropCare AI - Diagnosis Report", 20, 20);
      
      // Disease Name
      doc.setFontSize(14);
      const diseaseName = data?.disease_name || "Disease data not received";
      doc.text(`Disease Detected: ${diseaseName}`, 20, 40);
      
      // Severity & Crop Type
      doc.text(`Crop: ${data?.crop || "Unknown"}`, 20, 50);
      doc.text(`Severity: ${data?.severity || "Unknown"}`, 20, 60);
      
      // Organic Treatment
      doc.text("Organic Treatment:", 20, 80);
      doc.setFontSize(12);
      const organicSteps = data?.remediation?.organic?.join(", ") || "No treatment data available";
      doc.text(organicSteps, 20, 90, { maxWidth: 170 });
      
      doc.save("Diagnosis_Prescription.pdf");
      
    } catch (error) {
      console.error("PDF Error: ", error);
      alert("PDF download fail ho gaya. Console check karein.");
    }
  };

  return (
    <div className="text-center mt-6">
      <button 
        onClick={downloadPdf} 
        className="bg-red-600 text-white px-6 py-2 rounded font-medium shadow hover:bg-red-700 transition"
      >
        Download PDF Prescription
      </button>
    </div>
  );
};

export default PdfExportModal;