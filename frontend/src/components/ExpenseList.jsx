// src/components/ExpenseList.jsx
import { format } from 'date-fns';
import { Trash2, Calendar, DollarSign, Tag } from 'lucide-react';
import { mcpAPI } from '../services/api';
import { useState } from 'react';

export default function ExpenseList({ expenses }) {
  const [deletingId, setDeletingId] = useState(null);

  const handleDelete = async (expenseId) => {
    if (!confirm('Delete this expense?')) return;
    
    setDeletingId(expenseId);
    try {
      await mcpAPI.execute('delete_expense', { expense_id: expenseId });
      window.location.reload(); // Simple refresh - you could use state management
    } catch (error) {
      alert('Failed to delete expense');
    } finally {
      setDeletingId(null);
    }
  };

  if (!expenses || expenses.length === 0) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">No expenses found</p>
        <p className="text-sm text-gray-400 mt-2">
          Try: "Show my expenses from last month"
        </p>
      </div>
    );
  }

  const totalAmount = expenses.reduce((sum, exp) => sum + exp.amount, 0);

  return (
    <div>
      {/* Summary Card */}
      <div className="bg-gradient-to-r from-indigo-50 to-purple-50 rounded-xl p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-600">Total Expenses</p>
            <p className="text-3xl font-bold text-indigo-600 mt-1">
              ${totalAmount.toFixed(2)}
            </p>
          </div>
          <div className="text-right">
            <p className="text-sm font-medium text-gray-600">Count</p>
            <p className="text-3xl font-bold text-purple-600 mt-1">
              {expenses.length}
            </p>
          </div>
        </div>
      </div>

      {/* Expense List */}
      <div className="space-y-3">
        {expenses.map((expense) => (
          <div
            key={expense.id}
            className="border border-gray-200 rounded-xl p-4 hover:border-indigo-300 hover:shadow-md transition-all"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-2">
                  <span className="px-3 py-1 bg-indigo-100 text-indigo-700 rounded-full text-sm font-medium">
                    {expense.category}
                  </span>
                  {expense.subcategory && (
                    <span className="px-2 py-1 bg-gray-100 text-gray-600 rounded-full text-xs">
                      {expense.subcategory}
                    </span>
                  )}
                </div>
                
                {expense.note && (
                  <p className="text-gray-700 mb-2">{expense.note}</p>
                )}
                
                <div className="flex items-center gap-4 text-sm text-gray-500">
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    {expense.date}
                  </div>
                  <div className="flex items-center gap-1">
                    <DollarSign className="w-4 h-4" />
                    {expense.amount.toFixed(2)}
                  </div>
                </div>
              </div>

              <button
                onClick={() => handleDelete(expense.id)}
                disabled={deletingId === expense.id}
                className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                title="Delete expense"
              >
                <Trash2 className="w-5 h-5" />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
