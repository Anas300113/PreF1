import React from 'react';
import { CloudRain, Sun, Wind, Thermometer } from 'lucide-react';
import { WeatherData } from '../types';

interface WeatherWidgetProps {
  weather: WeatherData;
}

export const WeatherWidget: React.FC<WeatherWidgetProps> = ({ weather }) => {
  return (
    <div className="panel p-4">
      <div className="flex justify-between items-center mb-3">
        <h3 className="eyebrow !text-[#9BA1AA]">Track weather</h3>
        {weather.is_wet ? <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#38BDF8]/15 text-[#38BDF8] border border-[#38BDF8]/25">WET</span> : <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-[#20C997]/10 text-[#20C997] border border-[#20C997]/25">DRY</span>}
      </div>

      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-black/30 p-2.5 rounded-lg border border-white/[0.05] flex items-center gap-2.5">
          <Thermometer className="w-5 h-5 text-[#E10600]" />
          <div>
            <span className="text-[#636973] text-[10px] font-bold block tracking-wide">AIR TEMP</span>
            <span className="font-mono font-bold text-white text-[15px]">{weather.temperature_c ?? 22}°C</span>
          </div>
        </div>

        <div className="bg-black/30 p-2.5 rounded-lg border border-white/[0.05] flex items-center gap-2.5">
          <CloudRain className="w-5 h-5 text-[#38BDF8]" />
          <div>
            <span className="text-[#636973] text-[10px] font-bold block tracking-wide">RAIN</span>
            <span className="font-mono font-bold text-white text-[15px]">{weather.precipitation_probability ?? 10}%</span>
          </div>
        </div>

        <div className="bg-black/30 p-2.5 rounded-lg border border-white/[0.05] flex items-center gap-2.5">
          <Wind className="w-5 h-5 text-[#9BA1AA]" />
          <div>
            <span className="text-[#636973] text-[10px] font-bold block tracking-wide">WIND</span>
            <span className="font-mono font-bold text-white text-[15px]">{weather.wind_speed_ms ?? 4} m/s</span>
          </div>
        </div>

        <div className="bg-black/30 p-2.5 rounded-lg border border-white/[0.05] flex items-center gap-2.5">
          <Sun className="w-5 h-5 text-[#F5B942]" />
          <div>
            <span className="text-[#636973] text-[10px] font-bold block tracking-wide">CLOUD</span>
            <span className="font-mono font-bold text-white text-[15px]">{weather.cloud_cover_pct ?? 20}%</span>
          </div>
        </div>
      </div>
    </div>
  );
};
