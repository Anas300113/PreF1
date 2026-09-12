import axios from 'axios';
import { Race, PredictionResponse, BacktestResult } from '../types';

const api = axios.create({
  baseURL: '/api',
});

export const fetchNextRace = async (): Promise<Race> => {
  const res = await api.get<Race>('/races/next');
  return res.data;
};

export const fetchRaces = async (season?: number): Promise<Race[]> => {
  const res = await api.get<Race[]>('/races', { params: { season } });
  return res.data;
};

export const fetchRace = async (raceId: string): Promise<Race> => {
  const res = await api.get<Race>(`/races/${raceId}`);
  return res.data;
};

export const fetchPrediction = async (raceId: string, simCount: number = 10000): Promise<PredictionResponse> => {
  const res = await api.get<PredictionResponse>(`/races/${raceId}/prediction`, { params: { sim_count: simCount } });
  return res.data;
};

export interface ScenarioParams {
  simulation_count?: number;
  seed?: number;
  weather_override?: string;
  safety_car_override?: string;
  tyre_deg_override?: string;
}

export const runScenarioSimulation = async (
  raceId: string,
  params: ScenarioParams
): Promise<PredictionResponse> => {
  const res = await api.post<PredictionResponse>(`/races/${raceId}/simulate`, {
    simulation_count: params.simulation_count ?? 10000,
    seed: params.seed ?? 42,
    weather_override: params.weather_override,
    safety_car_override: params.safety_car_override,
    tyre_deg_override: params.tyre_deg_override,
  });
  return res.data;
};

export const fetchBacktests = async (): Promise<BacktestResult[]> => {
  const res = await api.get<BacktestResult[]>('/backtests');
  return res.data;
};

export const fetchModelsInfo = async (): Promise<any> => {
  const res = await api.get('/models');
  return res.data;
};
