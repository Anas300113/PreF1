export interface Circuit {
  id: string;
  name: string;
  country?: string;
  locality?: string;
  latitude?: number;
  longitude?: number;
  circuit_type?: string;
  overtaking_difficulty?: number;
  tyre_degradation_index?: number;
  safety_car_rate?: number;
}

export interface Race {
  id: string;
  season_year: number;
  round_number: number;
  name: string;
  race_date?: string;
  circuit?: Circuit;
  is_sprint_weekend: boolean;
  status: string;
}

export interface DriverPrediction {
  driver_id: string;
  code: string;
  full_name: string;
  team: string;
  team_color: string;
  win_probability: number;
  podium_probability: number;
  top5_probability: number;
  top10_probability: number;
  points_probability: number;
  dnf_probability: number;
  expected_position: number;
  median_position: number;
  p10_position: number;
  p25_position: number;
  p75_position: number;
  p90_position: number;
  expected_points: number;
  position_distribution: Record<string, number>;
}

export interface WeatherData {
  source: string;
  retrieved_at: string;
  temperature_c?: number;
  precipitation_probability?: number;
  precipitation_mm?: number;
  wind_speed_ms?: number;
  cloud_cover_pct?: number;
  humidity_pct?: number;
  is_wet: boolean;
  weather_code?: number;
}

export interface DriverExplanation {
  positive_factors: string[];
  negative_factors: string[];
  shap_values: Record<string, number>;
}

export interface PredictionResponse {
  race: Race;
  model: {
    version: string;
    training_cutoff: string;
    simulation_count: number;
    simulation_seed: number;
    feature_version: string;
    created_at: string;
  };
  drivers: DriverPrediction[];
  qualifying_prediction: Array<{ driver_id: string; code: string; expected_position: number }>;
  weather: WeatherData;
  explanations: Record<string, DriverExplanation>;
  disclaimer: string;
  data_status?: 'ok' | 'unavailable';
  scenarios?: Record<string, string>;
}

export interface BaselineSummary {
  winner_accuracy: number;
  podium_accuracy: number;
  top5_accuracy: number;
  mae_position: number;
  rmse_position: number;
  kendall_tau: number;
  n_races: number;
}

export interface BaselineComparison {
  winner_accuracy_delta: number;
  podium_accuracy_delta: number;
  mae_delta: number;
  beats_on_winner: boolean;
  beats_on_mae: boolean;
}

export interface ChampionshipDriverStanding {
  driver_id: string;
  code: string;
  team_id: string;
  championship_win_probability: number;
  expected_championship_points: number;
  expected_championship_position: number;
  position_distribution: Record<string, number>;
}

export interface ChampionshipConstructorStanding {
  team_id: string;
  championship_win_probability: number;
  expected_championship_points: number;
}

export interface ChampionshipResponse {
  season: number;
  races_remaining: number;
  n_simulations: number;
  driver_standings: ChampionshipDriverStanding[];
  constructor_standings: ChampionshipConstructorStanding[];
  convergence_report: {
    n_simulations: number;
    n_races: number;
    n_drivers: number;
  };
}

export interface BacktestResult {
  season: number;
  n_races: number;
  model_version: string;
  training_cutoff: string;
  n_simulations: number;
  simulation_seed: number;
  winner_accuracy: number;
  podium_accuracy: number;
  top5_accuracy: number;
  mean_abs_position_error: number;
  rmse_position_error: number;
  brier_score_win: number;
  log_loss_win: number;
  kendall_tau: number;
  expected_points_error: number;
  baselines: Record<string, BaselineSummary>;
  comparison: Record<string, BaselineComparison>;
}
