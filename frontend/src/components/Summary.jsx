// src/components/Summary.jsx
import { PieChart, TrendingUp, DollarSign } from 'lucide-react';

export default function Summary({ summary }) {
  if (!summary || summary.length === 0) {
    return (
      <div className="text-center py-12">
        <PieChart className="w-16 h-16 text-gray-300 mx-auto mb-4" />
        <p className="text-gray-500">No summary data available</p>
        <p className="text-sm text-gray-400 mt-2">
          Try: "Summarize my expenses this month"
        </p>
      </div>
    );
  }

  const totalAmount = summary.reduce((sum, item) => sum + item.total_amount, 0);
  const maxAmount = Math.max(...summary.map(item => item.total_amount));

  const getCategoryColor = (index) => {
    const colors = [
      'from-blue-500 to-blue-600',
      'from-purple-500 to-purple-600',
      'from-pink-500 to-pink-600',
      'from-green-500 to-green-600',
      'from-yellow-500 to-yellow-600',
      'from-red-500 to-red-600',
      'from-indigo-500 to-indigo-600',
      'from-teal-500 to-teal-600',
    ];
    return colors[index % colors.length];
  };

  const getCategoryBg = (index) => {
    const colors = [
      'bg-blue-50 border-blue-200',
      'bg-purple-50 border-purple-200',
      'bg-pink-50 border-pink-200',
      'bg-green-50 border-green-200',
      'bg-yellow-50 border-yellow-200',
      'bg-red-50 border-red-200',
      'bg-indigo-50 border-indigo-200',
      'bg-teal-50 border-teal-200',
    ];
    return colors[index % colors.length];
  };

  return (
    <div>
      {/* Total Summary Card */}
      <div className="bg-gradient-to-r from-indigo-500 to-purple-600 rounded-xl p-6 text-white mb-6">
        <div className="flex items-center gap-2 mb-2">
          <TrendingUp className="w-6 h-6" />
          <h3 className="text-lg font-semibold">Total Spending</h3>
        </div>
        <p className="text-4xl font-bold mb-2">${totalAmount.toFixed(2)}</p>
        <p className="text-indigo-100">Across {summary.length} categories</p>
      </div>

      {/* Category Breakdown */}
      <div className="space-y-4">
        {summary.map((item, index) => {
          const percentage = ((item.total_amount / totalAmount) * 100).toFixed(1);
          const barWidth = (item.total_amount / maxAmount) * 100;

          return (
            <div
              key={item.category}
              className={`border rounded-xl p-5 ${getCategoryBg(index)}`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-3 h-3 rounded-full bg-gradient-to-r ${getCategoryColor(index)}`} />
                  <h4 className="font-semibold text-gray-900">{item.category}</h4>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-900">
                    ${item.total_amount.toFixed(2)}
                  </p>
                  <p className="text-sm text-gray-600">{percentage}% of total</p>
                </div>
              </div>

              {/* Progress Bar */}
              <div className="relative h-3 bg-white bg-opacity-50 rounded-full overflow-hidden mb-2">
                <div
                  className={`absolute top-0 left-0 h-full bg-gradient-to-r ${getCategoryColor(index)} transition-all duration-500`}
                  style={{ width: `${barWidth}%` }}
                />
              </div>

              <p className="text-sm text-gray-700">
                {item.count} {item.count === 1 ? 'expense' : 'expenses'}
              </p>
            </div>
          );
        })}
      </div>

      {/* Insights */}
      <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-xl">
        <div className="flex items-start gap-2">
          <DollarSign className="w-5 h-5 text-amber-600 mt-0.5" />
          <div>
            <p className="font-medium text-amber-900">Top Category</p>
            <p className="text-sm text-amber-700 mt-1">
              You spent the most on <span className="font-semibold">{summary[0].category}</span> 
              {' '}(${summary[0].total_amount.toFixed(2)})
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
