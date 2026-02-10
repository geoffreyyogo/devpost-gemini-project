# Smart Shamba: Bridging the Digital Divide with AI & USSD

## Inspiration
The inspiration for **Smart Shamba** was born from a striking paradox in Kenya's agricultural landscape. Agriculture contributes 33% to our GDP and employs over 40% of the population, yet the smallholder farmers who form the backbone of this sector remain trapped in a cycle of poverty and vulnerability.

We realized that while high-fidelity agronomic data exists—satellites capture terabytes of imagery daily, and research institutions have advanced predictive models—this intelligence never reaches the rural farmer. They operate in an "**Information Desert**," relying on intuition in an era of erratic climate change.

We saw that most "AgTech" solutions fail because they are built for the wrong user: they require smartphones and high-speed internet, excluding the 53% of rural farmers who rely on basic feature phones. We wanted to build a bridge across this digital divide, decoupling high-tech intelligence from high-tech delivery.

## What it does
Smart Shamba is a **Satellite-to-Shamba** decision support system that democratizes access to precision agriculture. It synthesizes complex data from satellites, IoT sensors, and AI models into simple, actionable insights delivered via **USSD** (basic mobile menus) and **SMS**.

Key features include:
- **Precision Advisory**: Farmers receive hyper-local advice (e.g., "Yield Risk: High. Irrigate now.") based on real-time soil data and satellite imagery.
- **Flora AI Assistant**: A localized chatbot powered by **Gemini 3 Pro** that farmers can query via SMS in Swahili/English to diagnose pests or get agronomic advice.
- **Early Warning System**: Proactive SMS alerts for extreme weather or pest outbreaks predicted by our **PyTorch** models.
- **Digital Agrimart**: A USSD-based marketplace where farmers can buy certified inputs and sell produce directly to buyers, bypassing predatory brokers.

## How we built it
We architected a "Satellite-to-Shamba" pipeline that ingests massive datasets at the top and distills them into 160-character messages at the bottom.

1.  **The "Brain" (Hybrid AI Engine)**:
    -   **Predictive Analytics**: We used **PyTorch** to build LSTM models that analyze time-series data (rainfall, soil moisture, NDVI) to forecast yield and drought risk.
    -   **Generative AI**: We integrated **Google's Gemini 3 Pro** via **Google AI Studio** into a **RAG (Retrieval-Augmented Generation)** pipeline. This allows our "Flora AI" to answer farmer queries using verified agricultural manuals stored as vector embeddings in **pgvector**.
    -   **Computer Vision**: We deployed **EfficientNet** models (trained with **TorchVision**) to detect pests and diseases from uploaded images.

2.  **The "Factory" (Infrastructure)**:
    -   **Backend**: Built with **FastAPI** for high-performance async processing, deployed on **Render**.
    -   **Database**: We used **PostgreSQL** with **TimescaleDB** extensions for handling billions of IoT sensor readings and **pgvector** for semantic search.
    -   **Data Ingestion**: A robust pipeline using **MQTT** (EMQX broker) for IoT data and **Celery/RabbitMQ** for batch processing of **Google Earth Engine** satellite imagery.

3.  **The "Last Mile" (Connectivity)**:
    -   **Africa's Talking API**: Bridges our cloud backend to the GSM network, enabling USSD menus (*384*...) and SMS delivery to any mobile phone.

## Challenges we ran into
-   **The "Valet Key" Pattern**: Sending images from rural areas via limited bandwidth was a major bottleneck. We solved this by implementing a "Valet Key" pattern, where devices upload directly to **MinIO** object storage via pre-signed URLs, bypassing our application servers entirely.
-   **Hallucination in AI**: Early versions of our chatbot would invent agronomic advice. We fixed this by implementing a strict **RAG architecture**, grounding Gemini's responses in a curated knowledge base of KALRO datasheets and enforcing a "scientific constraints" system prompt.
-   **WSL2 Networking**: Developing a complex microservices architecture involving IoT simulators and localized databases on Windows/WSL2 presented significant networking challenges, which we overcame by containerizing our environment.

## Accomplishments that we're proud of
-   **True Accessibility**: Successfully executing a full AI pipeline that results in a simple SMS. Seeing a complex LSTM prediction turn into a text message on a "mulika mwizi" (dumbphone) was a magical moment.
-   **Polyglot Persistence**: effectively managing a database that handles relational transactions, time-series telemetry, and vector embeddings all within a single PostgreSQL instance.
-   **Frugal Innovation**: Building a system that brings the power of Google's Gemini Pro and Earth Engine to users who may not even have an internet connection.

## What's next for Smart Shamba
-   **Voice Integration**: Integrating voice-to-text models to allow illiterate farmers to interact with Flora AI via voice notes.
-   **Hyper-local Weather**: Deploying more low-cost ESP32 weather stations to refine our micro-climate models.
-   **Financial Inclusion**: Using our yield prediction models to generate "credit scores" for farmers, unlocking access to micro-loans and crop insurance.

---

# Smart Shamba - Frontend (Next.js)

## Overview

This is the complete Next.js + TypeScript + Tailwind CSS for Smart ShambaBuilt with modern React best practices and a security-first approach.

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

### Farmer Dashboard
- Real-time crop health monitoring
- Bloom event detection and alerts
- Interactive NDVI/NDWI visualizations
- Regional data exploration
- SMS/Email alert preferences
- Profile management

### Admin Dashboard
- Farmer management (CRUD operations)
- Statistics and analytics
- Alert broadcasting system
- Recent registrations tracking
- Message queue monitoring

### Flora AI Chatbot
- Intelligent farming advice
- Bilingual support (English/Kiswahili)
- Context-aware recommendations
- Integration with bloom data

### Security Features
- JWT-based authentication
- CSRF protection
- Rate limiting on API routes
- Input validation with Zod
- XSS protection
- Secure password hashing (backend)
- HTTP-only cookies for sessions

### UI/UX Features
- Responsive design (mobile-first)
- Dark/Light theme toggle
- Smooth animations
- Loading states
- Error handling with toast notifications
- Accessible components (ARIA)

---

# Smart Shamba - Backend (FastAPI)

The backend is a robust FastAPI application that powers all Smart Shamba services, providing RESTful APIs for the Next.js frontend, USSD/SMS, and integrations with AI, IoT, and satellite data. It is highly modular, with each service encapsulated in its own Python module.

## Key Components
- **API Server:** FastAPI app with CORS, security, and rate limiting middleware.
- **Authentication:** JWT-based, with endpoints for login, registration, session verification, and password management.
- **Database:** PostgreSQL (with TimescaleDB for time-series and pgvector for AI search).
- **IoT & Data Ingestion:** Handles sensor data via MQTT, batch satellite data via scheduled jobs, and supports continuous aggregates.
- **AI & ML:** 
  - LSTM and EfficientNet models (safetensors) for prediction and vision.
  - Gemini Pro-powered RAG chatbot (Flora AI).
  - ML retraining and inference endpoints.
- **Alerting:** Smart alert system for SMS/email/USSD, with risk classification and RAG-based advice.
- **USSD & SMS:** Africa's Talking integration for feature phone access, including a USSD-based marketplace and advisory.
- **Scheduler:** Automated weekly and daily jobs for data fetching, cleanup, and retraining.
- **Admin & Farmer APIs:** Endpoints for dashboards, farm management, admin analytics, and more.
- **Climate & Map Data:** Real-time and historical data for all Kenyan counties, with NDVI/NDWI and weather stats.
- **Extensibility:** Modular services for agrovets, buyers, disease detection, and more.

## How it Works
- All services are initialized at startup and injected where needed.
- Background tasks fetch and process satellite data.
- The scheduler automates data refresh and ML retraining.
- IoT ingestion supports real-time farm telemetry.
- REST endpoints are grouped by function (auth, dashboard, admin, AI, etc.).
- Security is enforced via JWT, CSRF, and rate limiting.

## Getting Started
- Install dependencies from requirements-fastapi.txt.
- Configure environment variables for DB, APIs, and secrets.
- Start the server with start_server.sh or python main.py.
- Access API docs at /api/docs.

## Directory Structure
- `main.py`: FastAPI app and all API routes.
- `auth_service_pg.py`: Auth logic.
- `bloom_processor.py`: Satellite/AI data processing.
- `disease_detection_service.py`: Vision/ML for disease.
- `flora_ai_gemini.py`: Gemini-powered chatbot.
- `smart_alert_service.py`: Alerting and advice.
- `ussd_pg_service.py`: USSD/SMS logic.
- `scheduler_service.py`: Background jobs.
- `streamlit_data_loader.py`: Data for dashboards/maps.
- `kenya_data_fetcher.py`: County/region data.
- `agrovet_service.py`: Agrovet marketplace logic.
- `email_service.py`: Email notifications.
- `iot_ingestion_service.py`: Sensor data pipeline.
- `database/`: DB models and connection logic.

---
