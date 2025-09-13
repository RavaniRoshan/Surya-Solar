# ZERO-COMP Frontend

Next.js dashboard for the ZERO-COMP solar weather prediction platform.

## Features

- **Authentication**: Supabase-powered user authentication with JWT tokens
- **Protected Routes**: Middleware-based route protection
- **Responsive Design**: Mobile-first design with Tailwind CSS
- **Real-time Updates**: WebSocket integration for live solar weather data
- **API Integration**: Axios-based API client with automatic token management

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Supabase project with authentication enabled

### Installation

1. Install dependencies:
```bash
npm install
```

2. Set up environment variables:
```bash
cp .env.local.example .env.local
```

Edit `.env.local` with your Supabase credentials:
```
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url_here
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key_here
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

3. Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the application.

## Project Structure

```
src/
├── app/                    # Next.js App Router pages
│   ├── auth/              # Authentication pages
│   │   ├── login/         # Login page
│   │   └── signup/        # Signup page
│   ├── dashboard/         # Protected dashboard pages
│   └── layout.tsx         # Root layout with AuthProvider
├── contexts/              # React contexts
│   └── AuthContext.tsx    # Authentication context
├── lib/                   # Utility libraries
│   ├── supabase.ts        # Supabase client (browser)
│   ├── supabase-server.ts # Supabase client (server)
│   └── api-client.ts      # API client with auth
└── __tests__/             # Test files
    └── auth/              # Authentication tests
```

## Authentication Flow

1. **Signup**: Users create accounts via Supabase Auth
2. **Email Confirmation**: Users confirm email addresses
3. **Login**: JWT tokens stored in HTTP-only cookies
4. **Protected Routes**: Middleware validates tokens
5. **API Calls**: Automatic token injection via interceptors

## Testing

Run the test suite:
```bash
npm test
```

Run tests in watch mode:
```bash
npm run test:watch
```

Generate coverage report:
```bash
npm run test:coverage
```

## API Integration

The frontend communicates with the FastAPI backend through:

- **REST Endpoints**: Current alerts, historical data, user management
- **WebSocket**: Real-time alert streaming
- **Authentication**: JWT token-based API access

## Deployment

### Vercel (Recommended)

1. Connect your GitHub repository to Vercel
2. Set environment variables in Vercel dashboard
3. Deploy automatically on push to main branch

### Manual Deployment

1. Build the application:
```bash
npm run build
```

2. Start the production server:
```bash
npm start
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project URL | Yes |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anonymous key | Yes |
| `NEXT_PUBLIC_API_BASE_URL` | Backend API base URL | Yes |

## Contributing

1. Follow the existing code style and patterns
2. Write tests for new components and features
3. Ensure all tests pass before submitting PRs
4. Update documentation for new features