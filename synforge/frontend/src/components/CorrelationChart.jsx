import { Scatter } from 'react-chartjs-2';
import { Chart as ChartJS, LinearScale, PointElement, LineElement, Tooltip, Legend } from 'chart.js';

ChartJS.register(LinearScale, PointElement, LineElement, Tooltip, Legend);

const CorrelationChart = ({ realData, syntheticData, xField, yField }) => {
  const data = {
    datasets: [
      {
        label: 'Real Data',
        data: realData.map(d => ({ x: d[xField], y: d[yField] })),
        backgroundColor: 'rgba(59, 130, 246, 0.5)', // Blue
      },
      {
        label: 'Synthetic Data',
        data: synthetic_data.map(d => ({ x: d[xField], y: d[yField] })),
        backgroundColor: 'rgba(34, 197, 94, 0.5)', // Green
      },
    ],
  };

  return (
    <div className="bg-slate-900 p-6 rounded-lg border border-slate-800 mt-6">
      <h3 className="text-slate-400 text-sm mb-4">Distribution Parity: {xField} vs {yField}</h3>
      <div className="h-64">
        <Scatter data={data} options={{ maintainAspectRatio: false, scales: { x: { grid: { color: '#1e293b' } }, y: { grid: { color: '#1e293b' } } } }} />
      </div>
    </div>
  );
};