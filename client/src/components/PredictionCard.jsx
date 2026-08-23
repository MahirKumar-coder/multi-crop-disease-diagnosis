import React from 'react';

const PredictionCard = ({ result }) => {
  // Backend ab 'top_3_predictions' bhej raha hai
  if (!result || !result.top_3_predictions) return null;

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mt-6 border-t-4 border-green-500">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-bold text-gray-800">Diagnosis Results</h2>
        <span className={`px-3 py-1 font-semibold rounded-full text-sm ${result.severity === 'High' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
          Severity: {result.severity || 'Unknown'}
        </span>
      </div>

      <div className="mb-6">
        <h3 className="text-lg font-medium text-gray-700">Primary Detection:</h3>
        <p className="text-xl font-bold text-green-700">{result.disease_name}</p>
      </div>

      <div className="space-y-4">
        <h4 className="text-md font-semibold text-gray-600 mb-2">Confidence Scores</h4>
        {result.top_3_predictions.map((pred, i) => (
          <div key={i} className="w-full">
            <div className="flex justify-between text-sm mb-1 text-gray-700">
              {/* Backend ne class ka naam 'disease_name' rakha hai */}
              <span>{pred.disease_name}</span>
              <span className="font-bold">{pred.confidence}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className={`h-2.5 rounded-full ${i === 0 ? 'bg-green-600' : 'bg-blue-400'}`} 
                style={{ width: `${Math.max(0, Math.min(100, pred.confidence))}%` }}
              ></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PredictionCard;