import React from 'react';
import { CloudRain, Sun, Wind, Thermometer } from 'lucide-react';
import { WeatherData } from '../types';

interface WeatherWidgetProps {
  weather: WeatherData;
}

export const WeatherWidget: React.FC<WeatherWidgetProps> = ({ weather }) => {
  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-sm font-bold text-gray-200 uppercase tracking-wide flex items-center space-x-2">
          <span>Weather Conditions</span>
          {weather.is_wet && (
            <span className="bg-blue-600 text-white text-[10px] px-2 py-0.5 rounded font-bold">
              WET SESSION
            </span>
          )}
        </h3>
        <span className="text-[10px] text-gray-400">Source: Open-Meteo</span>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
        <div className="bg-gray-900/60 p-2.5 rounded border border-gray-700/50 flex items-center space-x-2.5">
          <Thermometer className="w-5 h-5 text-red-400" />
          <div>
            <span className="text-gray-400 text-[10px] block">AIR TEMP</span>
            <span className="font-bold text-white text-sm">{weather.temperature_c ?? 22}°C</span>
          </div>
        </div>

        <div className="bg-gray-900/60 p-2.5 rounded border border-gray-700/50 flex items-center space-x-2.5">
          <CloudRain className="w-5 h-5 text-blue-400" />
          <div>
            <span className="text-gray-400 text-[10px] block">RAIN PROB</span>
            <span className="font-bold text-white text-sm">{weather.precipitation_probability ?? 10}%</span>
          </div>
        </div>

        <div className="bg-gray-900/60 p-2.5 rounded border border-gray-700/50 flex items-center space-x-2.5">
          <Wind className="w-5 h-5 text-teal-400" />
          <div>
            <span className="text-gray-400 text-[10px] block">WIND SPEED</span>
            <span className="font-bold text-white text-sm">{weather.wind_speed_ms ?? 4} m/s</span>
          </div>
        </div>

        <div className="bg-gray-900/60 p-2.5 rounded border border-gray-700/50 flex items-center space-x-2.5">
          <Sun className="w-5 h-5 text-yellow-400" />
          <div>
            <span className="text-gray-400 text-[10px] block">CLOUD COVER</span>
            <span className="font-bold text-white text-sm">{weather.cloud_cover_pct ?? 20}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};
