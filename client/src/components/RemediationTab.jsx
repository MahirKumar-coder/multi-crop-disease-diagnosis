import React, { useState } from 'react';

const RemediationTab = ({ remediationData }) => {
  const [tab, setTab] = useState('organic');
  if (!remediationData) return null;

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mt-6">
      <div className="flex border-b mb-4 gap-2 overflow-x-auto">
        <button 
          className={`px-4 py-2 font-medium transition-all ${tab === 'organic' ? 'border-b-2 border-green-600 text-green-600' : 'text-gray-500 hover:text-green-500'}`} 
          onClick={() => setTab('organic')}
        >
          Organic Treatment
        </button>
        <button 
          className={`px-4 py-2 font-medium transition-all ${tab === 'chemical' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500 hover:text-blue-500'}`} 
          onClick={() => setTab('chemical')}
        >
          Chemical Treatment
        </button>
        <button 
          className={`px-4 py-2 font-medium transition-all ${tab === 'preventive' ? 'border-b-2 border-orange-600 text-orange-600' : 'text-gray-500 hover:text-orange-500'}`} 
          onClick={() => setTab('preventive')}
        >
          Preventive Actions
        </button>
      </div>
      <ul className="list-disc pl-5 text-gray-700">
        {remediationData[tab]?.map((step, i) => <li key={i} className="mb-2">{step}</li>)}
        {(!remediationData[tab] || remediationData[tab].length === 0) && (
          <li className="list-none text-gray-400">No suggestions available for this section.</li>
        )}
      </ul>
    </div>
  );
};

export default RemediationTab;