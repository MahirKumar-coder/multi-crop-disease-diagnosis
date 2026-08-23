import React from 'react';
import { jsPDF } from "jspdf";

const PdfExportModal = ({ data }) => {
  const downloadPdf = () => {
    try {
      const doc = new jsPDF();
      
      // Title
      doc.setFontSize(22);
      doc.setTextColor(22, 101, 52); // green-800
      doc.text("CropCare AI - Diagnosis Report", 20, 25);
      
      // Line separator
      doc.setDrawColor(22, 101, 52);
      doc.setLineWidth(0.5);
      doc.line(20, 30, 190, 30);

      // Metadata
      doc.setTextColor(0, 0, 0);
      doc.setFontSize(12);
      
      const diseaseName = data?.disease_name || "Disease data not received";
      const crop = data?.crop || "Unknown";
      const severity = data?.severity || "Unknown";
      const pathogenType = data?.pathogen_type || "Unknown";

      doc.setFont("helvetica", "bold");
      doc.text("Crop:", 20, 42);
      doc.setFont("helvetica", "normal");
      doc.text(crop, 60, 42);

      doc.setFont("helvetica", "bold");
      doc.text("Diagnosis:", 20, 50);
      doc.setFont("helvetica", "normal");
      doc.text(diseaseName, 60, 50);

      doc.setFont("helvetica", "bold");
      doc.text("Pathogen Type:", 20, 58);
      doc.setFont("helvetica", "normal");
      doc.text(pathogenType, 60, 58);

      doc.setFont("helvetica", "bold");
      doc.text("Severity:", 20, 66);
      doc.setFont("helvetica", "normal");
      doc.text(severity, 60, 66);

      // Description
      doc.setFont("helvetica", "bold");
      doc.text("Description:", 20, 76);
      doc.setFont("helvetica", "normal");
      const desc = data?.description || "No description available.";
      const splitDesc = doc.splitTextToSize(desc, 170);
      doc.text(splitDesc, 20, 82);

      // Section: Remediation Actions
      let yOffset = 82 + (splitDesc.length * 6) + 10;
      doc.setFont("helvetica", "bold");
      doc.setFontSize(14);
      doc.setTextColor(22, 101, 52);
      doc.text("Recommended Remediation Actions", 20, yOffset);
      doc.line(20, yOffset + 2, 190, yOffset + 2);
      yOffset += 10;

      doc.setFontSize(11);
      doc.setTextColor(0, 0, 0);

      // Organic
      doc.setFont("helvetica", "bold");
      doc.text("Organic Treatment:", 20, yOffset);
      doc.setFont("helvetica", "normal");
      const organicSteps = data?.remediation?.organic?.join("\n- ") || "No organic treatment data available";
      const splitOrganic = doc.splitTextToSize("- " + organicSteps, 160);
      doc.text(splitOrganic, 25, yOffset + 6);
      yOffset += 6 + (splitOrganic.length * 5) + 6;

      // Chemical
      doc.setFont("helvetica", "bold");
      doc.text("Chemical Treatment:", 20, yOffset);
      doc.setFont("helvetica", "normal");
      const chemicalSteps = data?.remediation?.chemical?.join("\n- ") || "No chemical treatment data available";
      const splitChemical = doc.splitTextToSize("- " + chemicalSteps, 160);
      doc.text(splitChemical, 25, yOffset + 6);
      yOffset += 6 + (splitChemical.length * 5) + 6;

      // Preventive
      doc.setFont("helvetica", "bold");
      doc.text("Preventive Actions:", 20, yOffset);
      doc.setFont("helvetica", "normal");
      const preventiveSteps = data?.remediation?.preventive?.join("\n- ") || "No preventive actions available";
      const splitPreventive = doc.splitTextToSize("- " + preventiveSteps, 160);
      doc.text(splitPreventive, 25, yOffset + 6);
      
      doc.save(`Diagnosis_Report_${crop}_${diseaseName.replace(/\s+/g, '_')}.pdf`);
      
    } catch (error) {
      console.error("PDF Error: ", error);
      alert("PDF download failed. Please check console.");
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