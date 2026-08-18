export interface League {
  idLeague: string;
  strLeague: string;
  strSport: string;
  strLeagueAlternate?: string | null;
}

export interface LeaguesResponse {
  leagues: League[] | null;
}

export interface SeasonBadge {
  idLeague: string;
  strSeason: string;
  strBadge: string | null;
}

export interface SeasonBadgesResponse {
  seasons: SeasonBadge[] | null;
}

export interface Sport {
  idSport: string;
  strSport: string;
}

export interface SportsResponse {
  sports: Sport[] | null;
}
