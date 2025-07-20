// TradingView Charting Library TypeScript definitions

declare global {
  interface Window {
    TradingView: {
      widget: new (options: TradingViewWidgetOptions) => TradingViewWidget;
      version: () => string;
    };
  }
}

export interface TradingViewWidgetOptions {
  symbol: string;
  datafeed: DatafeedConfiguration;
  interval: string;
  container: string | HTMLElement;
  library_path: string;
  locale?: string;
  disabled_features?: string[];
  enabled_features?: string[];
  charts_storage_url?: string;
  charts_storage_api_version?: string;
  client_id?: string;
  user_id?: string;
  fullscreen?: boolean;
  autosize?: boolean;
  studies_overrides?: Record<string, any>;
  theme?: 'light' | 'dark';
  custom_css_url?: string;
  overrides?: Record<string, any>;
}

export interface TradingViewWidget {
  chart(): ChartApi;
  onChartReady(callback: () => void): void;
  remove(): void;
  save(callback: (state: any) => void): void;
  load(state: any): void;
  setSymbol(symbol: string, interval?: string, callback?: () => void): void;
  getSavedCharts(callback: (charts: any[]) => void): void;
}

export interface ChartApi {
  setSymbol(symbol: string, callback?: () => void): void;
  setResolution(resolution: string, callback?: () => void): void;
  createStudy(name: string, forceOverlay?: boolean, lock?: boolean, inputs?: any[], callback?: (studyId: string) => void, overrides?: Record<string, any>): string;
  removeEntity(entityId: string): void;
  createShape(point: any, options: any): string;
  removeEntity(entityId: string): void;
  onDataLoaded(): Subscription;
  exportData(options: any, callback: (data: any) => void): void;
}

export interface Subscription {
  subscribe(guid: string | null, callback: () => void): void;
  unsubscribe(guid: string | null, callback: () => void): void;
}

export interface DatafeedConfiguration {
  onReady(callback: (configuration: DatafeedConfigurationData) => void): void;
  searchSymbols(userInput: string, exchange: string, symbolType: string, onResult: (symbols: SearchSymbolResultItem[]) => void): void;
  resolveSymbol(symbolName: string, onResolve: (symbolInfo: LibrarySymbolInfo) => void, onError: (error: string) => void): void;
  getBars(symbolInfo: LibrarySymbolInfo, resolution: ResolutionString, periodParams: PeriodParams, onResult: (bars: Bar[], meta: HistoryMetadata) => void, onError: (error: string) => void): void;
  subscribeBars(symbolInfo: LibrarySymbolInfo, resolution: ResolutionString, onTick: (bar: Bar) => void, subscriberUID: string, onResetCacheNeededCallback: () => void): void;
  unsubscribeBars(subscriberUID: string): void;
}

export interface DatafeedConfigurationData {
  supported_resolutions: ResolutionString[];
  supports_group_request?: boolean;
  supports_marks?: boolean;
  supports_search?: boolean;
  supports_timescale_marks?: boolean;
  exchanges?: ExchangeDescriptor[];
}

export interface ExchangeDescriptor {
  value: string;
  name: string;
  desc: string;
}

export interface SearchSymbolResultItem {
  symbol: string;
  full_name: string;
  description: string;
  exchange: string;
  ticker: string;
  type: string;
}

export interface LibrarySymbolInfo {
  name: string;
  full_name: string;
  description: string;
  type: string;
  session: string;
  timezone: string;
  ticker: string;
  exchange: string;
  minmov: number;
  pricescale: number;
  has_intraday: boolean;
  has_no_volume: boolean;
  has_weekly_and_monthly: boolean;
  supported_resolutions: ResolutionString[];
  volume_precision: number;
  data_status: 'streaming' | 'endofday' | 'pulsed' | 'delayed_streaming';
}

export interface PeriodParams {
  from: number;
  to: number;
  firstDataRequest: boolean;
}

export interface Bar {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume?: number;
}

export interface HistoryMetadata {
  noData: boolean;
  nextTime?: number;
}

export type ResolutionString = '1' | '3' | '5' | '15' | '30' | '45' | '60' | '120' | '180' | '240' | '1D' | '1W' | '1M';

export {};