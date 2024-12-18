// main.tsx
import React from 'react'
import { createRoot } from 'react-dom/client'
import App from './App'

// Debug logs
console.log('🚀 main.tsx is executing');
console.log('📝 Looking for root element...');

const rootElement = document.getElementById('react-root');
if (!rootElement) {
  console.error('❌ Failed to find the react-root element');
  throw new Error('Failed to find the react-root element');
}

console.log('✅ Root element found:', rootElement);

try {
  const root = createRoot(rootElement);
  console.log('🌳 Created React root');
  
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
  console.log('🎉 React app rendered successfully');
} catch (error) {
  console.error('💥 Error rendering React app:', error);
}