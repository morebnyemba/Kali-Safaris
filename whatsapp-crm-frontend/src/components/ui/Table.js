import React from 'react';

export function Table({ columns, data }) {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col) => (
              <th key={col.key} className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                {col.title}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.length === 0 && (
            <tr>
              <td colSpan={columns.length} className="px-4 py-4 text-center text-gray-400">No data</td>
            </tr>
          )}
          {data.map((row, i) => (
            <tr key={i}>
              {columns.map((col) => (
                <td key={col.key} className="px-4 py-2 whitespace-nowrap text-sm text-gray-700">
                  {row[col.key] ?? ''}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
