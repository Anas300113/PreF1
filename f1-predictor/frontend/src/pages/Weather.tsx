import React from 'react';
import { Cloud, Thermometer, Wind, Droplets } from 'lucide-react';
import { WeatherData } from '../types';
import { useNextRace } from '../hooks/useRace';
import { LoadingState } from '../components/ui';

const mockWeather: WeatherData = {
  source: 'Open-Meteo / Archive',
  retrieved_at: new Date().toISOString(),
  temperature_c: 28.9,
  precipitation_probability: 0,
  precipitation_mm: 0,
  wind_speed_ms: 3.6,
  cloud_cover_pct: 10,
  humidity_pct: 45,
  is_wet: false,
  weather_code: 0,
};

export const Weather: React.FC = () => {
  const { race, loading } = useNextRace();
  const weather = mockWeather;

  if (loading) {
    return <LoadingState label="Loading track weather..." />;
  }

  return (
    <div className="space-y-5 animate-fade-in">
      <div className="flex items-center gap-3">
        <span className="w-9 h-9 rounded-[10px] bg-[#15191F] border border-[rgba(255,255,255,0.08)] flex items-center justify-center text-[#E10600]"><Cloud className="w-[18px] h-[18px]" /></span>
        <div>
          <div className="eyebrow">{race ? `${race.name} · ${race.circuit?.name || ''}` : 'Weather'}</div>
          <h1 className="font-display font-bold text-white text-[24px] tracking-tight leading-none">Track weather</h1>
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
        <div className="panel p-4">
          <div className="flex items-center gap-2"><Thermometer className="w-4 h-4 text-[#E10600]" /><span className="text-[10px] font-bold text-[#636973] tracking-wide">AIR TEMP</span></div>
          <div className="font-display font-bold text-white text-[28px] tnum mt-1">{weather.temperature_c}°</div>
        </div>
        <div className="panel p-4">
          <div className="flex items-center gap-2"><Cloud className="w-4 h-4 text-[#38BDF8]" /><span className="text-[10px] font-bold text-[#636973] tracking-wide">RAIN RISK</span></div>
          <div className="font-display font-bold text-white text-[28px] tnum mt-1">{weather.precipitation_probability}%</div>
        </div>
        <div className="panel p-4">
          <div className="flex items-center gap-2"><Wind className="w-4 h-4 text-[#9BA1AA]" /><span className="text-[10px] font-bold text-[#636973] tracking-wide">WIND</span></div>
          <div className="font-display font-bold text-white text-[28px] tnum mt-1">{(weather.wind_speed_ms! * 3.6).toFixed(0)}<span className="text-[14px] text-[#636973]"> kph</span></div>
        </div>
        <div className="panel p-4">
          <div className="flex items-center gap-2"><Droplets className="w-4 h-4 text-[#20C997]" /><span className="text-[10px] font-bold text-[#636973] tracking-wide">HUMIDITY</span></div>
          <div className="font-display font-bold text-white text-[28px] tnum mt-1">{weather.humidity_pct}%</div>
        </div>
      </div>

      <div className="panel p-5">
        <h2 className="eyebrow !text-[#9BA1AA] mb-4">Session detail</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-y-3 gap-x-6 text-[13px]">
          <div className="flex justify-between py-2 border-b border-white/[0.05]"><span className="text-[#636973]">Cloud</span><span className="text-white font-mono">{weather.cloud_cover_pct}%</span></div>
          <div className="flex justify-between py-2 border-b border-white/[0.05]"><span className="text-[#636973]">Precip</span><span className="text-white font-mono">{weather.precipitation_mm} mm</span></div>
          <div className="flex justify-between py-2 border-b border-white/[0.05]"><span className="text-[#636973]">Condition</span><span className="text-white font-mono">{weather.is_wet ? 'WET' : 'DRY'}</span></div>
        </div>
      </div>

      <div className="panel p-5">
        <h2 className="eyebrow !text-[#9BA1AA] mb-3">Strategy read</h2>
        <p className="text-[13px] text-[#9BA1AA] leading-relaxed">{weather.is_wet ? 'Wet running favours intermediates, longer braking zones, and higher safety-car exposure. Expect strategy variance.' : 'Dry and stable. Medium to Hard one-stop is the baseline. Low degradation risk unless track temp spikes.'}</p>
      </div>
    </div>
  );
};
