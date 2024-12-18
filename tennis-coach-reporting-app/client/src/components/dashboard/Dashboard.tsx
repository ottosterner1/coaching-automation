// components/dashboard/Dashboard.tsx
const Dashboard = () => {
  console.log('📊 Dashboard component rendering');
  
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 bg-white shadow-lg rounded-lg mt-8">
      <h1 className="text-3xl font-bold text-gray-900 py-6">Hello World</h1>
      <p className="text-gray-600 pb-6">Your dashboard content will go here</p>
    </div>
  );
};

export default Dashboard;