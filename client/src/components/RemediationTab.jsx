import React, { useState } from 'react';

const RemediationTab = ({ remediationData }) => {
  const [tab, setTab] = useState('organic');
  if (!remediationData) return null;

  return (
    <div className="bg-white p-6 rounded-lg shadow-md mt-6">
      <div className="flex border-b mb-4">
        {/* Dual-tab configuration[cite: 2] */}
        <button className={`px-4 py-2 ${tab === 'organic' ? 'border-b-2 border-green-600 text-green-600' : 'text-gray-500'}`} onClick={() => setTab('organic')}>Organic Treatment</button>
        <button className={`px-4 py-2 ${tab === 'chemical' ? 'border-b-2 border-blue-600 text-blue-600' : 'text-gray-500'}`} onClick={() => setTab('chemical')}>Chemical Treatment</button>
      </div>
      <ul className="list-disc pl-5 text-gray-700">
        {remediationData[tab]?.map((step, i) => <li key={i} className="mb-2">{step}</li>)}
      </ul>
    </div>
  );
};

export default RemediationTab;