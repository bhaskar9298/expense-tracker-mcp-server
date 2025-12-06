// src/components/Dashboard.jsx
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authAPI, mcpAPI } from '../services/api';
import { parseNaturalLanguage } from '../services/gemini';
import ExpenseList from './ExpenseList';
import Summary from './Summary';
import { Sparkles, LogOut, Loader2 } from 'lucide-react';

export default function Dashboard({ user, setUser }) {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [expenses, setExpenses] = useState([]);
  const [summary, setSummary] = useState([]);
  const [activeTab, setActiveTab] = useState('add');
  const navigate = useNavigate();

  useEffect(() => {
    if (!user) {
      checkAuth();
    }
  }, [user]);

  const checkAuth = async () => {
    try {
      const response = await authAPI.getMe();
      setUser(response.data);
    } catch (error) {
      navigate('/login');
    }
  };

  const handleLogout = async () => {
    try {
      await authAPI.logout();
      setUser(null);
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    setLoading(true);
    setMessage('');

    try {
      // Step 1: Parse natural language with Gemini
      const { tool, args } = await parseNaturalLanguage(input);
      
      // Step 2: Execute MCP tool via FastAPI gateway
      const response = await mcpAPI.execute(tool, args);
      
      // Handle response based on tool
      if (tool === 'add_expense' && response.data.status === 'success') {
        setMessage('✅ Expense added successfully!');
        setInput('');
      } else if (tool === 'list_expenses' && Array.isArray(response.data)) {
        setExpenses(response.data);
        setActiveTab('list');
        setMessage(`✅ Found ${response.data.length} expenses`);
      } else if (tool === 'summarize' && Array.isArray(response.data)) {
        setSummary(response.data);
        setActiveTab('summary');
        setMessage('✅ Summary generated');
      } else if (response.data.status === 'error') {
        setMessage(`❌ Error: ${response.data.message}`);
      }
      
    } catch (error) {
      console.error('Error:', error);
      setMessage('❌ Failed to process request: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Expense Tracker</h1>
              <p className="text-sm text-gray-600">
                Welcome, {user?.full_name || user?.email}
              </p>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Natural Language Input */}
        <div className="bg-white rounded-2xl shadow-lg p-6 mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-indigo-600" />
            <h2 className="text-xl font-semibold text-gray-900">AI Assistant</h2>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                disabled={loading}
                placeholder="Try: 'Add coffee expense of $5 today' or 'Show my expenses this month'"
                className="w-full px-4 py-4 pr-12 border-2 border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-transparent disabled:bg-gray-50 disabled:cursor-not-allowed"
              />
              {loading && (
                <Loader2 className="absolute right-4 top-4 w-6 h-6 text-indigo-600 animate-spin" />
              )}
            </div>

            <button
              type="submit"
              disabled={loading || !input.trim()}
              className="w-full bg-indigo-600 text-white py-3 rounded-xl font-medium hover:bg-indigo-700 transition-colors disabled:bg-indigo-400 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Processing...
                </>
              ) : (
                'Process with AI'
              )}
            </button>
          </form>

          {message && (
            <div className={`mt-4 p-3 rounded-lg ${
              message.startsWith('✅') 
                ? 'bg-green-50 text-green-800 border border-green-200' 
                : 'bg-red-50 text-red-800 border border-red-200'
            }`}>
              {message}
            </div>
          )}

          {/* Examples */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <p className="text-sm font-medium text-gray-700 mb-2">Try these examples:</p>
            <div className="flex flex-wrap gap-2">
              {[
                'Add lunch expense of $15 today',
                'Show expenses from last week',
                'Summarize my spending this month'
              ].map((example) => (
                <button
                  key={example}
                  onClick={() => setInput(example)}
                  className="px-3 py-1 text-sm bg-indigo-50 text-indigo-700 rounded-full hover:bg-indigo-100 transition-colors"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <div className="border-b border-gray-200">
            <nav className="flex">
              {['add', 'list', 'summary'].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`px-6 py-4 text-sm font-medium transition-colors ${
                    activeTab === tab
                      ? 'border-b-2 border-indigo-600 text-indigo-600'
                      : 'text-gray-500 hover:text-gray-700'
                  }`}
                >
                  {tab.charAt(0).toUpperCase() + tab.slice(1)}
                </button>
              ))}
            </nav>
          </div>

          <div className="p-6">
            {activeTab === 'add' && (
              <div className="text-center py-12 text-gray-500">
                <p>Use the AI assistant above to add expenses</p>
              </div>
            )}
            {activeTab === 'list' && <ExpenseList expenses={expenses} />}
            {activeTab === 'summary' && <Summary summary={summary} />}
          </div>
        </div>
      </main>
    </div>
  );
}
