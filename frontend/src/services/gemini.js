// src/services/gemini.js - Gemini Flash tool-call generation
import { GoogleGenerativeAI } from '@google/generative-ai';

const genAI = new GoogleGenerativeAI(import.meta.env.VITE_GEMINI_API_KEY);

// Tool definitions matching MCP server
const tools = [
  {
    name: 'add_expense',
    description: 'Add a new expense. Extract date, amount, category, subcategory, and note from user input.',
    parameters: {
      type: 'object',
      properties: {
        date: { type: 'string', description: 'ISO date format YYYY-MM-DD' },
        amount: { type: 'number', description: 'Expense amount' },
        category: { type: 'string', description: 'Expense category (Food, Transport, etc.)' },
        subcategory: { type: 'string', description: 'Optional subcategory' },
        note: { type: 'string', description: 'Optional note' },
      },
      required: ['date', 'amount', 'category'],
    },
  },
  {
    name: 'list_expenses',
    description: 'List all expenses in a date range',
    parameters: {
      type: 'object',
      properties: {
        start_date: { type: 'string', description: 'Start date YYYY-MM-DD' },
        end_date: { type: 'string', description: 'End date YYYY-MM-DD' },
      },
      required: ['start_date', 'end_date'],
    },
  },
  {
    name: 'summarize',
    description: 'Summarize spending by category',
    parameters: {
      type: 'object',
      properties: {
        start_date: { type: 'string' },
        end_date: { type: 'string' },
        category: { type: 'string', description: 'Optional: filter by specific category' },
      },
      required: ['start_date', 'end_date'],
    },
  },
];

export async function parseNaturalLanguage(userInput) {
  const model = genAI.getGenerativeModel({ 
    model: 'gemini-2.5-flash',
    generationConfig: { 
      temperature: 0.1,
      responseMimeType: 'application/json'
    }
  });

  const prompt = `You are an expense tracker assistant. Parse the user's natural language input and output ONLY valid JSON in this format:
{
  "tool": "tool_name",
  "args": { ... }
}

Available tools: add_expense, list_expenses, summarize

Rules:
- Extract dates intelligently ("today" = ${new Date().toISOString().split('T')[0]})
- Extract amounts (handle "8 rupees", "$10", "5 dollars")
- Map to appropriate categories (Food, Transport, Shopping, Entertainment, Bills, Other)
- NO additional text, NO explanation, ONLY JSON

User input: "${userInput}"`;

  const result = await model.generateContent(prompt);
  const text = result.response.text();
  
  try {
    return JSON.parse(text);
  } catch (error) {
    throw new Error('Failed to parse Gemini response as JSON');
  }
}
