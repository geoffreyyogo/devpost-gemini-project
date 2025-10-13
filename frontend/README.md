# BloomWatch Kenya - Frontend (Next.js)

## Overview

This is the complete Next.js + TypeScript + Tailwind CSS conversion of the BloomWatch Kenya Streamlit application. Built with modern React best practices and a security-first approach.

## Tech Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **UI Components**: shadcn/ui (Radix UI primitives)
- **State Management**: Zustand
- **Forms**: React Hook Form + Zod validation
- **Data Tables**: TanStack Table
- **Charts**: Recharts
- **Maps**: React Leaflet
- **API Client**: Axios
- **Authentication**: Custom JWT implementation
- **Theme**: next-themes (Dark/Light mode)

## Project Structure

```
frontend/
├── src/
│   ├── app/                      # Next.js App Router
│   │   ├── (auth)/              # Authentication routes
│   │   │   ├── login/           # Login page
│   │   │   └── register/        # Registration page
│   │   ├── dashboard/           # Farmer dashboard
│   │   ├── admin/               # Admin dashboard
│   │   ├── profile/             # User profile
│   │   ├── api/                 # API routes (Next.js API)
│   │   ├── layout.tsx           # Root layout
│   │   ├── page.tsx             # Home/Landing page
│   │   └── globals.css          # Global styles
│   ├── components/              # React components
│   │   ├── ui/                  # shadcn/ui components
│   │   ├── dashboard/           # Dashboard-specific components
│   │   ├── admin/               # Admin-specific components
│   │   ├── charts/              # Chart components
│   │   └── maps/                # Map components
│   ├── lib/                     # Utilities
│   │   ├── api.ts               # API client
│   │   └── utils.ts             # Helper functions
│   ├── store/                   # Zustand stores
│   │   ├── authStore.ts         # Authentication state
│   │   ├── dashboardStore.ts    # Dashboard state
│   │   └── adminStore.ts        # Admin state
│   ├── types/                   # TypeScript types
│   │   └── index.ts             # All type definitions
│   └── hooks/                   # Custom React hooks
├── public/                      # Static assets
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── next.config.mjs
└── .env.local                   # Environment variables
```

## Features

### 🌾 Farmer Dashboard
- Real-time crop health monitoring
- Bloom event detection and alerts
- Interactive NDVI/NDWI visualizations
- Regional data exploration
- SMS/Email alert preferences
- Profile management

### 🔧 Admin Dashboard
- Farmer management (CRUD operations)
- Statistics and analytics
- Alert broadcasting system
- Recent registrations tracking
- Message queue monitoring

### 🤖 Flora AI Chatbot
- Intelligent farming advice
- Bilingual support (English/Kiswahili)
- Context-aware recommendations
- Integration with bloom data

### 🔐 Security Features
- JWT-based authentication
- CSRF protection
- Rate limiting on API routes
- Input validation with Zod
- XSS protection
- Secure password hashing (backend)
- HTTP-only cookies for sessions

### 🎨 UI/UX Features
- Responsive design (mobile-first)
- Dark/Light theme toggle
- Smooth animations
- Loading states
- Error handling with toast notifications
- Accessible components (ARIA)

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- MongoDB instance (backend)
- Backend API running

### Installation

1. **Navigate to frontend directory:**
   ```bash
   cd bloom-detector/frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create environment file:**
   ```bash
   cp .env.local.example .env.local
   ```

4. **Configure environment variables:**
   Edit `.env.local` with your actual values:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:5000
   MONGODB_URI=mongodb://localhost:27017/bloomwatch_kenya
   NEXTAUTH_SECRET=your-secret-key
   ```

5. **Run development server:**
   ```bash
   npm run dev
   ```

6. **Open browser:**
   Navigate to `http://localhost:3000`

### Building for Production

```bash
npm run build
npm run start
```

## API Integration

The frontend communicates with the backend via the API client (`src/lib/api.ts`).

### Backend Endpoints Required

- `POST /api/auth/login` - User login
- `POST /api/auth/register` - User registration
- `POST /api/auth/logout` - User logout
- `GET /api/auth/verify` - Session verification
- `GET /api/dashboard` - Dashboard data
- `GET /api/bloom/events` - Bloom events
- `GET /api/alerts` - User alerts
- `PUT /api/farmers/profile` - Update profile
- `POST /api/chat` - Flora AI chatbot

### Admin Endpoints

- `GET /api/admin/farmers` - Get all farmers
- `GET /api/admin/statistics` - Get statistics
- `POST /api/admin/alerts/send` - Send alerts
- `DELETE /api/admin/farmers/:id` - Delete farmer

## State Management

The application uses Zustand for state management with three main stores:

### Auth Store (`authStore.ts`)
- User authentication state
- Login/logout actions
- Session management
- Profile updates

### Dashboard Store (`dashboardStore.ts`)
- Dashboard data
- Bloom events
- Alerts
- Data fetching and caching

### Admin Store (`adminStore.ts`)
- Farmers list
- Statistics
- Admin actions (delete, send alerts)

## Component Library

### shadcn/ui Components
- Button
- Card
- Input
- Label
- Select
- Tabs
- Toast
- Dialog
- Dropdown Menu
- Avatar

### Custom Components
- BloomMap (Leaflet integration)
- NDVIChart (Recharts)
- HealthScoreCard
- AlertsTable (TanStack Table)
- FarmersList
- ChatInterface (Flora AI)

## Styling

### Tailwind CSS Configuration
- Custom color palette (green theme for BloomWatch)
- Dark mode support
- Custom animations
- Responsive breakpoints

### CSS Variables
Theme colors are defined using CSS variables for easy customization:
```css
--primary: hsl(142 76% 36%);  /* Green */
--background: hsl(0 0% 100%);  /* White */
--foreground: hsl(0 0% 3.9%);  /* Dark */
```

## Form Handling

Forms use React Hook Form with Zod validation:

```typescript
const schema = z.object({
  phone: z.string().regex(/^\+254\d{9}$/),
  password: z.string().min(6),
})

const form = useForm<FormData>({
  resolver: zodResolver(schema),
})
```

## Data Visualization

### Charts (Recharts)
- Line charts for NDVI trends
- Bar charts for regional statistics
- Area charts for bloom patterns
- Pie charts for crop distribution

### Maps (React Leaflet)
- Interactive Kenya map
- Bloom hotspots markers
- Region overlays
- Farmer locations

## Deployment

### Vercel (Recommended)
```bash
vercel deploy
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
CMD ["npm", "start"]
```

### Environment Variables for Production
Ensure all required environment variables are set in your deployment platform.

## Testing

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Build test
npm run build
```

## Performance Optimization

- Server-side rendering (SSR) for initial page load
- Static generation for public pages
- Image optimization with Next.js Image
- Code splitting with dynamic imports
- API response caching
- Debounced search inputs
- Lazy loading for heavy components

## Accessibility

- Semantic HTML
- ARIA labels on all interactive elements
- Keyboard navigation support
- Screen reader friendly
- Focus management
- Color contrast compliance (WCAG AA)

## Browser Support

- Chrome (last 2 versions)
- Firefox (last 2 versions)
- Safari (last 2 versions)
- Edge (last 2 versions)

## Contributing

1. Follow the existing code style
2. Use TypeScript strictly
3. Write semantic commit messages
4. Test thoroughly before submitting
5. Update documentation as needed

## Migration from Streamlit

### Key Differences

| Feature | Streamlit | Next.js |
|---------|-----------|---------|
| State Management | `st.session_state` | Zustand stores |
| Forms | `st.form()` | React Hook Form |
| Components | Streamlit widgets | React components |
| Routing | Multi-page app | Next.js App Router |
| Styling | Custom CSS injection | Tailwind CSS |
| Data Fetching | Direct Python calls | API routes |

### Advantages of Next.js Version

1. **Better Performance**: SSR, code splitting, optimized assets
2. **SEO Friendly**: Server-side rendering for better indexing
3. **Mobile Responsive**: Better mobile experience
4. **Offline Support**: Service worker capabilities
5. **Scalability**: Better suited for production use
6. **Developer Experience**: Hot reload, TypeScript, modern tooling

## Troubleshooting

### Common Issues

**Build Errors:**
- Clear `.next` folder: `rm -rf .next`
- Reinstall dependencies: `rm -rf node_modules && npm install`

**API Connection:**
- Check backend is running on correct port
- Verify `NEXT_PUBLIC_API_URL` in `.env.local`
- Check CORS settings on backend

**Styling Issues:**
- Run `npm run build` to check for CSS conflicts
- Clear browser cache
- Check Tailwind configuration

## Support

For issues or questions:
- GitHub Issues: [Create an issue]
- Email: support@bloomwatch.co.ke
- Documentation: [Wiki]

## License

Copyright © 2025 BloomWatch Kenya. All rights reserved.

---

Built with ❤️ for Kenyan farmers 🌾

