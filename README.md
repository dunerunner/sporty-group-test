# Sporty Group Test Task

Single-page Angular application for browsing sports leagues from TheSportsDB API. Users can search leagues by name, filter by sport type, and see available season badges in the league list.

## Technologies

- Angular 22 with standalone components
- Angular Material 22 for UI components
- Angular CDK as a Material dependency
- TypeScript 6
- RxJS 7 for HTTP streams and response caching
- SCSS for global and component styles
- Vitest through the Angular CLI unit-test builder

## API

The app uses the free TheSportsDB endpoints:

- All leagues: `https://www.thesportsdb.com/api/v1/json/3/all_leagues.php`
- All sports: `https://www.thesportsdb.com/api/v1/json/3/all_sports.php`
- Season badge lookup: `https://www.thesportsdb.com/api/v1/json/3/search_all_seasons.php?badge=1&id=<id>`

League and sport responses are cached with `shareReplay(1)` to avoid repeated list requests. Badge responses are cached per league id after the first row-level lookup.

## Development

Angular 22 requires Node `^22.22.3`, `^24.15.0`, or `^26.0.0`. If your system Node is older on the same major line, upgrade Node before running Angular CLI commands.

Install dependencies:

```bash
npm install
```

Run the development server:

```bash
npm start
```

Build the project:

```bash
npm run build
```

Run unit tests:

```bash
npm test
```

See [NOTES.md](./NOTES.md) for concise AI-tool and design-decision notes.
