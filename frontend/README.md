# News Tunneler Frontend

Real-time news scoring dashboard built with SolidJS, Vite, and Tailwind CSS.

## Features

- **Real-time Alerts**: WebSocket connection for live article updates
- **Advanced Filtering**: Search, score threshold, ticker filtering
- **Source Management**: Add, enable/disable RSS/Atom/NewsAPI feeds
- **Scoring Weights**: Adjust catalyst, novelty, credibility, sentiment, and liquidity weights
- **Dark Mode**: Toggle between light and dark themes
- **Responsive Design**: Mobile-friendly interface

## Tech Stack

- **SolidJS**: Reactive UI framework
- **Vite**: Fast build tool
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Zustand**: State management
- **Axios**: HTTP client
- **date-fns**: Date formatting

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

The app will be available at `http://localhost:5173`

### Build

```bash
npm run build
```

### Environment Variables

Create a `.env.local` file:

```env
VITE_API_BASE=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws/alerts
```

## Project Structure

```
src/
├── components/          # Reusable UI components
│   ├── Navigation.tsx
│   ├── Kpis.tsx
│   ├── AlertRow.tsx
│   ├── AlertTable.tsx
│   ├── SourceForm.tsx
│   └── WeightSliders.tsx
├── pages/              # Page components
│   ├── Dashboard.tsx
│   ├── Alerts.tsx
│   ├── Sources.tsx
│   └── Settings.tsx
├── lib/                # Utilities and services
│   ├── api.ts         # API client
│   ├── ws.ts          # WebSocket client
│   └── store.ts       # Zustand store
├── App.tsx            # Root component
├── main.tsx           # Entry point
└── app.css            # Global styles
```

## Pages

### Dashboard
- KPI cards (24h alerts, average score, top tickers)
- Live alerts table
- Real-time updates via WebSocket

### Alerts
- Advanced filtering (search, score, ticker)
- Paginated article table
- Score-based color coding

### Sources
- Add new RSS/Atom/NewsAPI feeds
- Enable/disable sources
- Delete sources
- View last fetch time

### Settings
- Adjust scoring weights (0-5 scale)
- Set minimum alert threshold
- Configure polling interval
- View scoring formula

## API Integration

The frontend communicates with the backend via:

- **REST API**: `/api/articles`, `/api/sources`, `/api/settings`
- **WebSocket**: `/ws/alerts` for real-time alerts

## State Management

Uses Zustand for global state:

- Articles list
- Live alerts
- Settings
- Filters
- Dark mode toggle
- WebSocket connection status

## Styling

Tailwind CSS with custom components:

- `.btn`, `.btn-primary`, `.btn-secondary`, `.btn-danger`
- `.card`
- `.input`
- `.label`

Dark mode support via `dark:` prefix.

## Development Tips

- Use `createSignal` for component state
- Use `createEffect` for side effects
- Use `createMemo` for computed values
- Use `For` for list rendering
- Use `Show` for conditional rendering

## Building for Production

```bash
npm run build
```

Output is in the `dist/` directory.

## Docker

Build and run with Docker:

```bash
docker build -t news-tunneler-frontend .
docker run -p 5173:5173 news-tunneler-frontend
```

## License

MIT

