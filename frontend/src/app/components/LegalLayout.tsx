import React from 'react';

export default function LegalLayout({ children, title, lastUpdated }: { children: React.ReactNode, title: string, lastUpdated: string }) {
  return (
    <div className="min-h-screen bg-white py-16 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <header className="mb-12 border-b border-gray-200 pb-8">
          <h1 className="text-4xl font-extrabold text-gray-900 sm:text-5xl">
            {title}
          </h1>
          <p className="mt-4 text-sm text-gray-500">
            Last updated: {lastUpdated}
          </p>
        </header>
        {/* We use prose class from @tailwindcss/typography if available, 
            otherwise standard spacing classes */}
        <div className="prose prose-blue max-w-none text-gray-700 leading-relaxed">
          {children}
        </div>
      </div>
    </div>
  );
}