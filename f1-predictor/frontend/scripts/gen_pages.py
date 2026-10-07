import os, json

BASE = os.path.dirname(os.path.abspath(__file__))
FRONTEND = os.path.join(BASE, '..')

def write_file(rel_path, content):
    full = os.path.join(FRONTEND, rel_path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, 'w') as f:
        f.write(content)
    print(f"{rel_path}: {len(content)} chars")

# 1. hooks/useRace.ts
write_file('src/hooks/useRace.ts', """import { useState, useEffect } from 'react';
import { Race } from '../types';
import { fetchNextRace } from '../api/client';

export const useNextRace = () => {
  const [race, setRace] = useState<Race | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchNextRace()
      .then(setRace)
      .catch(setError)
      .finally(() => setLoading(false));
  }, []);

  return { race, loading, error };
};
""")

print("Phase 1 complete")

# 2. pages/Weather.tsx
weather = """import React from 'react';
import { Cloud, Thermometer, Wind, Droplets, Eye, Sun } from 'lucide-react';
import { WeatherData } from '../types';
import { useNextRace } from '../hooks/useRace';
import { CircuitSVG } from '../components/CircuitSVG';

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
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-12 h-12 border-4 border-f1-red border-t-transparent rounded-full animate-spin mx-auto" />
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in pb-20 lg:pb-0">
      <div className="flex items-center space-x-3">
        <Cloud className="w-6 h-6 text-f1-red" />
        <h1 className="text-2xl font-black text-white tracking-tight font-display">WEATHER ANALYSIS</h1>
      </div>

      {race && (
        <div className="glass-panel p-5 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-white">{race.name}</h2>
            <p className="text-sm text-secondary">{race.circuit?.name}</p>
          </div>
          <div className="w-48 h-24">
            <CircuitSVG circuitId={race.circuit?.id} className="w-full h-full" />
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="glass-panel p-5 flex items-center space-x-4">
          <Thermometer className="w-8 h-8 text-f1-red" />
          <div>
            <span className="text-xs text-secondary uppercase">Track Temp</span>
            <div className="text-2xl font-display font-black text-white tabular-nums">{weather.temperature_c}°C</div>
          </div>
        </div>
        <div className="glass-panel p-5 flex items-center space-x-4">
          <Sun className="w-8 h-8 text-yellow-400" />
          <div>
            <span className="text-xs text-secondary uppercase">Rain Probability</span>
            <div className="text-2xl font-display font-black text-white tabular-nums">{weather.precipitation_probability}%</div>
          </div>
        </div>
        <div className="glass-panel p-5 flex items-center space-x-4">
          <Wind className="w-8 h-8 text-accent-secondary" />
          <div>
            <span className="text-xs text-secondary uppercase">Wind Speed</span>
                        <div className="text-2xl font-display font-black text-white tabular-nums">{(weather.wind_speed_ms! * 3.6).toFixed(0)} km/h</div>
          </div>
        </div>
        <div className="glass-panel p-5 flex items-center space-x-4">
          <Droplets className="w-8 h-8 text-blue-400" />
          <div>
            <span className="text-xs text-secondary uppercase">Humidity</span>
            <div className="text-2xl font-display font-black text-white tabular-nums">{weather.humidity_pct}%</div>
          </div>
        </div>
      </div>

      <div className="glass-panel p-6">
        <h2 className="text-lg font-bold text-white mb-4">Race Timeline Weather</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div className="flex justify-between py-2 border-b border-border">
            <span className="text-secondary">Cloud Cover</span>
            <span className="text-white font-mono">{weather.cloud_cover_pct}%</span>
          </div>
          <div className="flex justify-between py-2 border-b border-border">
            <span className="text-secondary">Precipitation</span>
            <span className="text-white font-mono">{weather.precipitation_mm} mm</span>
          </div>
          <div className="flex justify-between py-2 border-b border-border">
            <span className="text-secondary">Weather Code</span>
            <span className="text-white font-mono">{weather.weather_code}</span>
          </div>
        </div>
      </div>

      <div className="glass-panel p-6">
        <h2 className="text-lg font-bold text-white mb-4">Weather Impact on Strategy</h2>
        <div className="space-y-3 text-sm">
          <div className="flex items-start space-x-3">
            <Eye className="w-4 h-4 text-secondary mt-0.5" />
            <div>
              <span className="font-bold text-white">Dry Track:</span>
              <span className="text-secondary"> 1-stop medium-hard optimal. Low degradation.</span>
            </div>
          </div>
          <div className="flex items-start space-x-3">
            <Cloud className="w-4 h-4 text-secondary mt-0.5" />
            <div>
              <span className="font-bold text-white">Wet:</span>
              <span className="text-secondary"> Intermediates preferred. Overtaking increases.</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
"""
write_file('src/pages/Weather.tsx', weather)
print("Phase 2 complete")

