# 🎨 Frontend Development Plan - AdIntel Dashboard

**Complete UI/UX Implementation Checklist**

---

## 📋 Table of Contents

1. [Tech Stack](#tech-stack)
2. [Project Structure](#project-structure)
3. [Pages & Components](#pages--components)
4. [API Integration](#api-integration)
5. [State Management](#state-management)
6. [Design System](#design-system)
7. [Implementation Checklist](#implementation-checklist)
8. [Development Phases](#development-phases)

---

## 🛠️ Tech Stack

### Frontend Framework
- **Next.js 14** (App Router)
- **React 18**
- **TypeScript** (for type safety)

### Styling
- **Tailwind CSS** (utility-first)
- **shadcn/ui** (component library)

### Data Visualization
- **Recharts** (for charts)
- **Lucide React** (icons)

### State Management
- **React Context** (global state)
- **TanStack Query** (server state & caching)

### API Client
- **Axios** (HTTP requests)

### Deployment
- **Netlify** or **Railway** (no Vercel!)

---

## 📁 Project Structure

```
adIntel-frontend/
├── app/                          # Next.js app directory
│   ├── layout.tsx                # Root layout
│   ├── page.tsx                  # Dashboard (home)
│   ├── scrape/
│   │   └── page.tsx              # Scraper page
│   ├── competitors/
│   │   ├── page.tsx              # Competitors list
│   │   └── [id]/
│   │       └── page.tsx          # Competitor detail view
│   ├── analysis/
│   │   └── [jobId]/
│   │       └── page.tsx          # Analysis results
│   └── compare/
│       └── page.tsx              # Comparison view
├── components/
│   ├── ui/                       # shadcn/ui components
│   ├── dashboard/
│   │   ├── CompetitorCard.tsx
│   │   ├── OfferChart.tsx
│   │   ├── KeywordsList.tsx
│   │   └── TrendChart.tsx
│   ├── scraper/
│   │   ├── UrlInput.tsx
│   │   └── ScrapeProgress.tsx
│   ├── analysis/
│   │   ├── AdGallery.tsx
│   │   ├── AdDetailModal.tsx
│   │   └── InsightsPanel.tsx
│   └── layout/
│       ├── Header.tsx
│       ├── Sidebar.tsx
│       └── Footer.tsx
├── lib/
│   ├── api.ts                    # API client
│   ├── types.ts                  # TypeScript types
│   └── utils.ts                  # Utility functions
├── hooks/
│   ├── useJobStatus.ts           # Poll job status
│   ├── useCompetitors.ts         # Fetch competitors
│   └── useScrape.ts              # Scraping hook
├── context/
│   └── AppContext.tsx            # Global state
├── public/
│   └── images/                   # Static assets
└── styles/
    └── globals.css               # Global styles
```

---

## 📄 Pages & Components

### 1. Dashboard (Main Page) - `/`

**Purpose:** Overview of all competitors with key metrics

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  Header [Logo] [Dashboard] [Scrape] [Compare] [Profile]    │
├─────────────────────────────────────────────────────────────┤
│  🎯 Competitor Overview                    Last updated: 2h │
│  ┌──────────┬──────────┬──────────┬──────────┐             │
│  │ Talabat  │Deliveroo │  Keeta   │  Rafiq   │             │
│  │  🟢 847  │ 🟢 623   │ 🟢 412   │ 🟢 289   │  [+ Add]    │
│  │  ads     │  ads     │  ads     │  ads     │             │
│  │  Qatar   │  Qatar   │  Qatar   │  Qatar   │             │
│  │ [View]   │ [View]   │ [View]   │ [View]   │             │
│  └──────────┴──────────┴──────────┴──────────┘             │
│                                                               │
│  📊 Offer Strategy Comparison                                │
│  [Horizontal stacked bar chart showing offer distribution]  │
│                                                               │
│  ┌─────────────────────────┬─────────────────────────┐     │
│  │ 🏆 Top Keywords         │ 📈 Trend (30 days)      │     │
│  │ [List with frequency]   │ [Line chart]            │     │
│  └─────────────────────────┴─────────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
- ✅ `CompetitorCard` - Card showing competitor summary
- ✅ `OfferChart` - Stacked bar chart for offer comparison
- ✅ `KeywordsList` - Top keywords with frequency
- ✅ `TrendChart` - 30-day trend line chart

**API Calls:**
- `GET /api/competitors` - Load all competitors

**State:**
- `competitors: Competitor[]`
- `loading: boolean`
- `error: string | null`

---

### 2. Scraper Page - `/scrape`

**Purpose:** Scrape new competitor ads

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard                                         │
├─────────────────────────────────────────────────────────────┤
│  🚀 Scrape Competitor Ads                                    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Paste GATC URL:                                     │   │
│  │ [https://adstransparency.google.com/advertiser/...] │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                               │
│  Max ads to scrape: [400 ▾]                                 │
│                                                               │
│  [Scrape Ads]                                                │
│                                                               │
│  ─── OR ───                                                  │
│                                                               │
│  Quick scrape presets:                                       │
│  [Talabat] [Deliveroo] [Keeta] [Rafiq]                     │
└─────────────────────────────────────────────────────────────┘
```

**Progress View (After clicking Scrape):**
```
┌─────────────────────────────────────────────────────────────┐
│  🔄 Scraping in progress...                                  │
│                                                               │
│  Advertiser: Talabat (AR14306592000630063105)               │
│  Region: Qatar                                               │
│                                                               │
│  Progress: ████████████████░░░░░░░░ 70%                     │
│                                                               │
│  Status: Fetching ads...                                     │
│  Estimated time: 2-5 seconds                                 │
└─────────────────────────────────────────────────────────────┘
```

**Success View:**
```
┌─────────────────────────────────────────────────────────────┐
│  ✅ Scraping Complete!                                       │
│                                                               │
│  Successfully scraped 400 ads from Talabat                   │
│                                                               │
│  [View Ads] [Analyze Now] [Back to Dashboard]              │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
- ✅ `UrlInput` - URL input with validation
- ✅ `ScrapeProgress` - Progress indicator with status
- ✅ `PresetButtons` - Quick scrape for known competitors

**API Calls:**
- `POST /api/scrape` - Start scraping
- `GET /api/jobs/{jobId}` - Poll job status (every 2 seconds)

**State:**
- `url: string`
- `maxAds: number`
- `scraping: boolean`
- `jobId: string | null`
- `progress: number`
- `status: 'idle' | 'scraping' | 'success' | 'error'`

**Validation:**
- URL must match GATC pattern
- Max ads: 1-1000
- Show parsed advertiser ID/region before scraping

---

### 3. Competitor Detail View - `/competitors/[id]`

**Purpose:** Detailed view of single competitor's ads

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  ← Back to Dashboard              Talabat - Qatar            │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Campaign Overview                [Rescrape] [⋮]     │   │
│  │  847 ads active | Last updated: 2 hours ago          │   │
│  │  Date range: Jan 2025 - Oct 2025                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                               │
│  ┌────────────────┬────────────────┬────────────────┐       │
│  │ Offer Mix      │ Top Categories │ Top Keywords   │       │
│  │ [Pie Chart]    │ Groceries 45%  │ Free Delivery  │       │
│  │                │ Food 30%       │ Order Now      │       │
│  │                │ Electronics 15%│ Download App   │       │
│  └────────────────┴────────────────┴────────────────┘       │
│                                                               │
│  📸 Ad Gallery                              [Filter ▾]       │
│  ┌─────┬─────┬─────┬─────┬─────┬─────┐                     │
│  │ [Ad]│ [Ad]│ [Ad]│ [Ad]│ [Ad]│ [Ad]│  ← Click to see     │
│  │ img │ img │ img │ img │ img │ img │    AI analysis       │
│  └─────┴─────┴─────┴─────┴─────┴─────┘                     │
│  [Load More]                                                 │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
- ✅ `OfferPieChart` - Pie chart for offer distribution
- ✅ `CategoryBreakdown` - Top categories list
- ✅ `KeywordsCloud` - Keyword frequency display
- ✅ `AdGallery` - Grid of ad thumbnails (infinite scroll)
- ✅ `AdDetailModal` - Modal for ad detail view

**API Calls:**
- `GET /api/competitors` - Get competitor details
- `GET /api/insights/{csv_file}` - Get analysis results

**State:**
- `competitor: Competitor`
- `ads: Ad[]`
- `insights: Insights`
- `selectedAd: Ad | null`
- `filterBy: 'all' | 'free-delivery' | 'discount' | etc`

---

### 4. Ad Detail Modal (Overlay)

**Purpose:** Show full ad analysis when user clicks an ad

**Layout:**
```
┌─────────────────────────────────────────┐
│  Ad Analysis              [✕ Close]     │
├─────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────────┐ │
│  │             │  │ Extracted Text:  │ │
│  │   [Ad Img]  │  │ "Order now and   │ │
│  │             │  │  get FREE        │ │
│  │   (Large)   │  │  delivery!"      │ │
│  │             │  │                  │ │
│  └─────────────┘  │ Offer Type:      │ │
│                   │ Free Delivery ✅  │ │
│  Creative ID:     │                  │ │
│  CR13784...       │ Keywords:        │ │
│                   │ • Order Now      │ │
│  First shown:     │ • Free Delivery  │ │
│  Jan 15, 2025     │ • Download       │ │
│                   │                  │ │
│  Last shown:      │ Category:        │ │
│  Oct 16, 2025     │ Food Delivery    │ │
│                   │                  │ │
│                   │ Products:        │ │
│                   │ • Groceries      │ │
│                   └──────────────────┘ │
│  [← Previous] [Next →]                  │
└─────────────────────────────────────────┘
```

**Components:**
- ✅ `AdDetailModal` - Full modal component
- ✅ `AdImage` - Large image display
- ✅ `AnalysisPanel` - Extracted insights
- ✅ Navigation arrows (keyboard support)

**Features:**
- Click outside to close
- ESC key to close
- Arrow keys to navigate between ads
- Share ad link

---

### 5. Analysis Page - `/analysis/[jobId]`

**Purpose:** Show real-time analysis progress and results

**During Analysis:**
```
┌─────────────────────────────────────────────────────────────┐
│  🧠 Analyzing Ads...                                         │
│                                                               │
│  Analyzing ad 23/50                                          │
│  Progress: ██████████░░░░░░░░░░ 46%                         │
│                                                               │
│  Current ad:                                                 │
│  ┌──────────┐                                                │
│  │ [Ad img] │ Extracting text with llava...                 │
│  └──────────┘                                                │
│                                                               │
│  Estimated time remaining: 25 minutes                        │
│                                                               │
│  [Cancel Analysis]                                           │
└─────────────────────────────────────────────────────────────┘
```

**After Analysis:**
```
┌─────────────────────────────────────────────────────────────┐
│  ✅ Analysis Complete!                                       │
│                                                               │
│  Campaign Intelligence Report                                │
│  Talabat - 50 ads analyzed                                   │
│                                                               │
│  [View full insights below]                                  │
│                                                               │
│  📊 Offer Distribution                                       │
│  [Charts and data]                                           │
│                                                               │
│  [Export PDF] [Export CSV] [Share Report]                   │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
- ✅ `AnalysisProgress` - Real-time progress display
- ✅ `CurrentAdPreview` - Show current ad being analyzed
- ✅ `ResultsView` - Full insights display

**API Calls:**
- `POST /api/analyze` - Start analysis
- `GET /api/jobs/{jobId}` - Poll status (every 5 seconds)

**State:**
- `jobId: string`
- `status: JobStatus`
- `progress: number`
- `currentAd: number`
- `results: AnalysisResults | null`

---

### 6. Comparison View - `/compare`

**Purpose:** Side-by-side comparison of competitors

**Layout:**
```
┌─────────────────────────────────────────────────────────────┐
│  ⚖️ Compare Competitors                                      │
│                                                               │
│  Select competitors:                                         │
│  [✓ Talabat] [✓ Deliveroo] [✓ Keeta] [✓ Rafiq]            │
│                                                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Metric          Talabat  Deliveroo  Keeta   Rafiq   │  │
│  │  Total Ads         847       623      412     289    │  │
│  │  Free Delivery     40%       35%      25%     45%    │  │
│  │  Discounts         25%       35%      45%     20%    │  │
│  │  BOGO              15%       10%      12%     18%    │  │
│  └───────────────────────────────────────────────────────┘  │
│                                                               │
│  📊 Offer Distribution Comparison                            │
│  [Grouped bar chart]                                         │
│                                                               │
│  🔑 Unique Keywords                                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Talabat only: "Groceries", "Supermarket", "Express" │   │
│  │ Deliveroo only: "Premium", "Restaurants", "Plus"    │   │
│  │ Common: "Free", "Fast", "Order"                      │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Components:**
- ✅ `CompetitorSelector` - Multi-select for competitors
- ✅ `ComparisonTable` - Side-by-side metrics
- ✅ `GroupedBarChart` - Grouped comparison chart
- ✅ `UniqueKeywords` - Venn diagram or list

**API Calls:**
- `GET /api/competitors` - Get all competitors
- `GET /api/insights/{id}` - Get insights for each

**State:**
- `selectedCompetitors: string[]`
- `comparisonData: ComparisonData`

---

## 🔌 API Integration

### API Client Setup (`lib/api.ts`)

```typescript
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Types
export interface ScrapeRequest {
  url: string;
  max_ads: number;
  name?: string;
}

export interface ScrapeResponse {
  job_id: string;
  status: string;
  message: string;
  advertiser_id: string;
  region: string;
  estimated_time: string;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  result?: any;
  error?: string;
  created_at: string;
  completed_at?: string;
}

export interface Competitor {
  name: string;
  advertiser_id: string;
  region: string;
  total_ads: number;
  last_scraped: string;
  csv_file: string;
}

// API Functions
export const scrapeAds = (data: ScrapeRequest) =>
  api.post<ScrapeResponse>('/api/scrape', data);

export const getJobStatus = (jobId: string) =>
  api.get<JobStatus>(`/api/jobs/${jobId}`);

export const analyzeAds = (csvFile: string, analyzer = 'hybrid', sampleSize = 50) =>
  api.post('/api/analyze', { csv_file: csvFile, analyzer, sample_size: sampleSize });

export const getCompetitors = () =>
  api.get<Competitor[]>('/api/competitors');

export const getInsights = (csvFile: string) =>
  api.get(`/api/insights/${encodeURIComponent(csvFile)}`);
```

---

### Custom Hooks

#### `useJobStatus.ts` - Poll job status

```typescript
import { useQuery } from '@tanstack/react-query';
import { getJobStatus } from '@/lib/api';

export const useJobStatus = (jobId: string | null, enabled = true) => {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => getJobStatus(jobId!),
    enabled: enabled && !!jobId,
    refetchInterval: (data) => {
      // Stop polling if completed or failed
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false;
      }
      return 2000; // Poll every 2 seconds
    },
  });
};
```

#### `useScrape.ts` - Scraping hook

```typescript
import { useMutation } from '@tanstack/react-query';
import { scrapeAds, ScrapeRequest } from '@/lib/api';

export const useScrape = () => {
  return useMutation({
    mutationFn: (data: ScrapeRequest) => scrapeAds(data),
    onSuccess: (data) => {
      console.log('Scraping started:', data.job_id);
    },
    onError: (error) => {
      console.error('Scraping failed:', error);
    },
  });
};
```

#### `useCompetitors.ts` - Fetch competitors

```typescript
import { useQuery } from '@tanstack/react-query';
import { getCompetitors } from '@/lib/api';

export const useCompetitors = () => {
  return useQuery({
    queryKey: ['competitors'],
    queryFn: getCompetitors,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
};
```

---

## 🎨 Design System

### Colors

```css
/* Neutral palette */
--background: #FAFAFA;
--card: #FFFFFF;
--text-primary: #1A1A1A;
--text-secondary: #6B6B6B;
--border: #E5E5E5;

/* Accent */
--accent: #2563EB;
--accent-hover: #1D4ED8;

/* Status */
--success: #10B981;
--error: #EF4444;
--warning: #F59E0B;
--info: #3B82F6;

/* Competitor colors */
--talabat: #FF6B35;
--deliveroo: #00C2A8;
--keeta: #8B5CF6;
--rafiq: #F59E0B;
```

### Typography

```css
font-family: 'Inter', sans-serif;

/* Headings */
h1: 2.5rem (40px), font-weight: 700
h2: 2rem (32px), font-weight: 600
h3: 1.5rem (24px), font-weight: 600
h4: 1.25rem (20px), font-weight: 500

/* Body */
body: 1rem (16px), font-weight: 400
small: 0.875rem (14px)
```

### Spacing

```
xs: 4px
sm: 8px
md: 16px
lg: 24px
xl: 32px
2xl: 48px
```

### Components

**Button:**
- Primary: Blue background, white text
- Secondary: White background, blue border
- Ghost: Transparent background, blue text
- Sizes: sm (32px), md (40px), lg (48px)

**Card:**
- White background
- 1px light gray border
- 8px border radius
- 16px padding
- Subtle shadow on hover

**Input:**
- White background
- 1px border
- 8px border radius
- Focus: blue border

---

## ✅ Implementation Checklist

### Phase 1: Setup & Foundation (Week 1)

#### Project Setup
- [ ] Create Next.js project with TypeScript
- [ ] Install dependencies (Tailwind, shadcn/ui, Recharts, TanStack Query, Axios)
- [ ] Set up project structure (folders/files)
- [ ] Configure Tailwind with custom colors
- [ ] Set up API client with types
- [ ] Create environment variables (.env.local)

#### Layout Components
- [ ] Create `Header` component with navigation
- [ ] Create `Sidebar` component (optional for desktop)
- [ ] Create `Footer` component
- [ ] Create root layout with Header/Footer
- [ ] Add loading states component
- [ ] Add error boundary component

#### Design System
- [ ] Set up global CSS with design tokens
- [ ] Install and configure shadcn/ui components
- [ ] Create reusable UI components (Button, Card, Input, etc.)
- [ ] Set up color scheme
- [ ] Set up typography scale

---

### Phase 2: Dashboard & Scraper (Week 2)

#### Dashboard Page (`/`)
- [ ] Create dashboard layout
- [ ] Build `CompetitorCard` component
  - [ ] Show competitor name, region, ad count
  - [ ] Show last scraped time
  - [ ] Add "View" button
  - [ ] Add status indicator (🟢 active)
- [ ] Build `OfferChart` component (stacked bar)
  - [ ] Fetch competitor data
  - [ ] Calculate percentages
  - [ ] Render Recharts bar chart
- [ ] Build `KeywordsList` component
  - [ ] Show top 10 keywords with frequency
  - [ ] Add search/filter
- [ ] Build `TrendChart` component (line chart)
  - [ ] Show 30-day trend
  - [ ] Multiple lines for competitors
- [ ] Integrate API: `GET /api/competitors`
- [ ] Add loading skeleton states
- [ ] Add error handling with retry
- [ ] Add "Add Competitor" button → navigate to `/scrape`

#### Scraper Page (`/scrape`)
- [ ] Create scraper page layout
- [ ] Build `UrlInput` component
  - [ ] Input field with validation
  - [ ] Parse URL on blur
  - [ ] Show advertiser ID/region preview
  - [ ] Validate GATC URL format
- [ ] Build `MaxAdsSelector` component (dropdown: 50, 100, 200, 400)
- [ ] Build preset buttons (Talabat, Deliveroo, etc.)
  - [ ] Pre-fill URL on click
- [ ] Build `ScrapeProgress` component
  - [ ] Progress bar (0-100%)
  - [ ] Status text
  - [ ] Estimated time
  - [ ] Cancel button
- [ ] Integrate API:
  - [ ] `POST /api/scrape` on submit
  - [ ] Poll `GET /api/jobs/{jobId}` every 2 seconds
  - [ ] Stop polling when completed/failed
- [ ] Build success view
  - [ ] Show total ads scraped
  - [ ] "View Ads" button → competitor detail
  - [ ] "Analyze Now" button → analysis page
- [ ] Build error view with retry
- [ ] Add form validation
- [ ] Add keyboard shortcuts (Enter to submit)

---

### Phase 3: Competitor Detail & Ad Gallery (Week 3)

#### Competitor Detail Page (`/competitors/[id]`)
- [ ] Create competitor detail layout
- [ ] Build campaign overview section
  - [ ] Show total ads, date range
  - [ ] Add "Rescrape" button
  - [ ] Add menu (⋮) for options
- [ ] Build `OfferPieChart` component
  - [ ] Calculate offer distribution
  - [ ] Render pie chart with Recharts
  - [ ] Add legend
- [ ] Build `CategoryBreakdown` component
  - [ ] Show top 5 categories with percentages
  - [ ] Progress bars
- [ ] Build `TopKeywords` component
  - [ ] Show top 20 keywords
  - [ ] Frequency badges
  - [ ] Search/filter
- [ ] Build `AdGallery` component
  - [ ] Grid layout (responsive)
  - [ ] Lazy load images
  - [ ] Infinite scroll or pagination
  - [ ] Click to open modal
- [ ] Build filter dropdown
  - [ ] Filter by offer type
  - [ ] Filter by date range
  - [ ] Filter by category
- [ ] Integrate API:
  - [ ] `GET /api/competitors` (filter by ID)
  - [ ] `GET /api/insights/{csv_file}`
- [ ] Add loading states
- [ ] Add empty state (no ads)

#### Ad Detail Modal
- [ ] Build `AdDetailModal` component
  - [ ] Modal overlay (click outside to close)
  - [ ] Large image display
  - [ ] Analysis panel (extracted text, keywords, etc.)
  - [ ] Navigation arrows (previous/next)
  - [ ] Close button (X)
- [ ] Add keyboard navigation
  - [ ] ESC to close
  - [ ] Left/Right arrows to navigate
- [ ] Add share functionality (copy link)
- [ ] Add download image button
- [ ] Add responsive design (mobile-friendly)

---

### Phase 4: Analysis & Results (Week 4)

#### Analysis Page (`/analysis/[jobId]`)
- [ ] Create analysis page layout
- [ ] Build `AnalysisProgress` component
  - [ ] Show current ad number (23/50)
  - [ ] Progress bar with percentage
  - [ ] Estimated time remaining
  - [ ] Status text updates
- [ ] Build `CurrentAdPreview` component
  - [ ] Show current ad thumbnail
  - [ ] Show current stage (extracting text/analyzing)
- [ ] Build `ResultsView` component
  - [ ] Campaign intelligence report
  - [ ] Offer distribution charts
  - [ ] Top keywords list
  - [ ] Top products list
  - [ ] One-line summary
- [ ] Integrate API:
  - [ ] `POST /api/analyze` to start
  - [ ] Poll `GET /api/jobs/{jobId}` every 5 seconds
  - [ ] Load results when complete
- [ ] Build export buttons
  - [ ] Export to PDF
  - [ ] Export to CSV
  - [ ] Share report (generate link)
- [ ] Add cancel analysis button
- [ ] Add error handling
- [ ] Add "Analyze More" button (go back to scrape)

---

### Phase 5: Comparison View (Week 5)

#### Comparison Page (`/compare`)
- [ ] Create comparison page layout
- [ ] Build `CompetitorSelector` component
  - [ ] Checkboxes for each competitor
  - [ ] Select/deselect all
  - [ ] Minimum 2 competitors required
- [ ] Build `ComparisonTable` component
  - [ ] Side-by-side metrics table
  - [ ] Responsive (scroll on mobile)
  - [ ] Highlight winner (green)
- [ ] Build `GroupedBarChart` component
  - [ ] Offer distribution comparison
  - [ ] Grouped bars by competitor
  - [ ] Legend with competitor colors
- [ ] Build `UniqueKeywords` component
  - [ ] Show unique keywords per competitor
  - [ ] Show common keywords
  - [ ] Venn diagram (optional)
- [ ] Integrate API:
  - [ ] `GET /api/competitors` for all
  - [ ] `GET /api/insights/{id}` for each selected
- [ ] Add export comparison report
- [ ] Add save comparison (for later viewing)

---

### Phase 6: Polish & Features (Week 6)

#### UI/UX Improvements
- [ ] Add animations (fade in, slide, etc.)
- [ ] Add skeleton loading states everywhere
- [ ] Add empty states with helpful messages
- [ ] Add tooltips for unclear UI elements
- [ ] Add confirmation dialogs (delete, cancel, etc.)
- [ ] Improve mobile responsiveness
- [ ] Add dark mode toggle (optional)
- [ ] Add keyboard shortcuts guide (? key)

#### Performance
- [ ] Optimize images (Next.js Image component)
- [ ] Add caching with TanStack Query
- [ ] Lazy load components
- [ ] Code splitting for routes
- [ ] Optimize bundle size

#### Testing
- [ ] Test all API integrations
- [ ] Test error scenarios (network errors, API down, etc.)
- [ ] Test edge cases (0 ads, very large datasets, etc.)
- [ ] Cross-browser testing
- [ ] Mobile device testing

#### Documentation
- [ ] Add inline code comments
- [ ] Create component documentation
- [ ] Create user guide
- [ ] Add tooltips/help text in UI

---

## 🚀 Development Phases

### **Phase 1: MVP (Weeks 1-2)** ✅

**Goal:** Basic working dashboard with scraping

**Features:**
- Dashboard with competitor cards
- Scraper page with URL input
- Basic API integration
- Loading/error states

**Deliverable:** Can scrape ads and view competitors

---

### **Phase 2: Analysis (Weeks 3-4)** 📊

**Goal:** Full analysis pipeline with results

**Features:**
- Analysis progress tracking
- Results visualization
- Ad gallery with details
- Insights display

**Deliverable:** Can analyze ads and view insights

---

### **Phase 3: Advanced Features (Weeks 5-6)** 🎯

**Goal:** Comparison, exports, polish

**Features:**
- Competitor comparison
- Export functionality
- Responsive design
- Performance optimization

**Deliverable:** Production-ready dashboard

---

## 🔗 Backend Integration Points

### API Endpoints Used

| Endpoint | Method | Usage | Polling? |
|----------|--------|-------|----------|
| `/api/scrape` | POST | Start scraping | No |
| `/api/jobs/{id}` | GET | Check job status | Yes (2-5s) |
| `/api/analyze` | POST | Start analysis | No |
| `/api/competitors` | GET | List competitors | No |
| `/api/insights/{file}` | GET | Get insights | No |

### Data Flow

```
User Action → Frontend → API → Backend Tools → Results → Frontend → User
```

**Example: Scraping Flow**
1. User pastes URL in `/scrape`
2. Frontend validates URL
3. Frontend calls `POST /api/scrape`
4. Backend returns `job_id`
5. Frontend polls `GET /api/jobs/{job_id}` every 2s
6. Backend updates job status (pending → running → completed)
7. Frontend shows progress bar
8. When complete, frontend navigates to competitor detail

**Example: Analysis Flow**
1. User clicks "Analyze" on competitor
2. Frontend calls `POST /api/analyze` with CSV file
3. Backend returns `job_id`
4. Frontend polls `GET /api/jobs/{job_id}` every 5s
5. Backend updates progress (0-100%)
6. Frontend shows real-time progress
7. When complete, frontend displays insights

---

## 📦 Dependencies

```json
{
  "dependencies": {
    "next": "^14.0.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "@tanstack/react-query": "^5.0.0",
    "axios": "^1.6.0",
    "recharts": "^2.10.0",
    "lucide-react": "^0.300.0",
    "date-fns": "^3.0.0",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.0.0",
    "tailwind-merge": "^2.0.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/react": "^18.2.0",
    "eslint": "^8.0.0",
    "eslint-config-next": "^14.0.0"
  }
}
```

---

## 🎯 Key Implementation Notes

### Polling Strategy
- **Scraping:** Poll every 2 seconds (fast operation)
- **Analysis:** Poll every 5 seconds (slow operation)
- Stop polling when status is `completed` or `failed`
- Show estimated time based on backend response

### Error Handling
- Network errors → Show retry button
- API errors → Display error message from backend
- Validation errors → Inline form validation
- Timeout errors → Suggest refreshing

### State Management
- Use TanStack Query for server state (caching, refetching)
- Use React Context for global UI state (theme, user prefs)
- Use local component state for UI interactions

### Responsive Design
- Mobile-first approach
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)
- Stack cards vertically on mobile
- Horizontal scroll for tables on mobile

### Performance
- Lazy load images in ad gallery
- Infinite scroll or pagination (50 ads per page)
- Code split routes
- Optimize Recharts renders (memo)

---

## 📝 Environment Variables

```bash
# Frontend (.env.local)
NEXT_PUBLIC_API_URL=http://localhost:8001
NEXT_PUBLIC_APP_NAME=AdIntel
```

---

## 🚢 Deployment Checklist

### Pre-deployment
- [ ] Test all features end-to-end
- [ ] Fix all TypeScript errors
- [ ] Remove console.logs
- [ ] Add error tracking (Sentry optional)
- [ ] Test on production API URL
- [ ] Optimize images
- [ ] Check bundle size

### Deployment
- [ ] Build frontend: `npm run build`
- [ ] Test build locally: `npm start`
- [ ] Deploy to Netlify/Railway
- [ ] Set environment variables in deployment platform
- [ ] Configure custom domain (optional)
- [ ] Enable HTTPS

### Post-deployment
- [ ] Test production site
- [ ] Monitor errors
- [ ] Check performance (Lighthouse)
- [ ] Share with stakeholders

---

## 🎉 Success Criteria

A successful implementation will:

✅ Allow users to scrape competitor ads with one URL paste
✅ Show real-time scraping progress
✅ Display competitors in a beautiful dashboard
✅ Allow detailed competitor analysis
✅ Show AI-powered insights with charts
✅ Enable competitor comparison
✅ Work smoothly on desktop and mobile
✅ Have fast load times (<3s)
✅ Handle errors gracefully
✅ Be intuitive without documentation

---

**Ready to build?** Start with Phase 1 (Setup & Foundation)!

The backend is ready and waiting. Let's create something beautiful! 🎨
