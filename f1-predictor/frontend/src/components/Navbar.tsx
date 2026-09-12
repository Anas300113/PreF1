import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, Flag, BarChart3, Cpu, Trophy } from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <nav className="bg-gray-800 border-b border-gray-700 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <Link to="/" className="flex items-center space-x-2">
              <span className="bg-f1-red text-white font-extrabold px-2.5 py-1 rounded text-xl tracking-wider">
                PreF1
              </span>
              <span className="text-gray-300 font-semibold hidden sm:inline text-sm tracking-wide">
                RACE SIMULATOR
              </span>
            </Link>
          </div>

          <div className="flex space-x-4">
            <Link
              to="/"
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/') ? 'bg-f1-red text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              <Flag className="w-4 h-4" />
              <span>Next Race</span>
            </Link>

            <Link
              to="/championship"
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/championship') ? 'bg-f1-red text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              <Trophy className="w-4 h-4" />
              <span>Championship</span>
            </Link>

            <Link
              to="/backtesting"
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/backtesting') ? 'bg-f1-red text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span>Backtesting</span>
            </Link>

            <Link
              to="/models"
              className={`flex items-center space-x-1.5 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                isActive('/models') ? 'bg-f1-red text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'
              }`}
            >
              <Cpu className="w-4 h-4" />
              <span>Models</span>
            </Link>
          </div>
        </div>
      </div>
    </nav>
  );
};
