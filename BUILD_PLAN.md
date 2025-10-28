# 🏗️ Practical Build Plan - Start to Finish

**Goal:** Build a simple, clean, working dashboard in the right order

---

## 🎯 Core Principle: Build Vertically, Not Horizontally

**❌ Wrong Approach:**
- Build all layouts first
- Then add all components
- Then connect API
- Then fix bugs

**✅ Right Approach:**
- Build ONE complete feature end-to-end
- Make it work perfectly
- Move to next feature
- Reuse what you built

---

## 🚀 Starting Point: Where We Begin

### **Step 0: Project Setup (1 hour)**

```bash
# Create Next.js project
npx create-next-app@latest adIntel-frontend --typescript --tailwind --app

cd adIntel-frontend

# Install dependencies
npm install @tanstack/react-query axios recharts lucide-react
npm install date-fns clsx tailwind-merge

# Install shadcn/ui CLI
npx shadcn-ui@latest init

# Install specific shadcn components we'll need
npx shadcn-ui@latest add button card input badge progress
```

**Project structure:**
```
adIntel-frontend/
├── app/
│   ├── layout.tsx          # Root layout
│   ├── page.tsx            # Dashboard
│   └── globals.css         # Global styles
├── components/
│   └── ui/                 # shadcn components
├── lib/
│   ├── api.ts              # API client
│   ├── types.ts            # TypeScript types
│   └── utils.ts            # Utilities
└── public/
```

**Set up API client first:**

```typescript
// lib/api.ts
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001';

export const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// Start with just these 2 endpoints
export const getCompetitors = () => api.get('/api/competitors');
export const scrapeAds = (url: string, maxAds: number) =>
  api.post('/api/scrape', { url, max_ads: maxAds });
```

**Set up types:**

```typescript
// lib/types.ts
export interface Competitor {
  name: string;
  advertiser_id: string;
  region: string;
  total_ads: number;
  last_scraped: string;
  csv_file: string;
}

export interface ScrapeResponse {
  job_id: string;
  status: string;
  message: string;
  advertiser_id: string;
  region: string;
}

export interface JobStatus {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  result?: any;
  error?: string;
}
```

---

## 📍 Build Order: Feature by Feature

### **Feature 1: Dashboard with Competitor Cards (Day 1-2)**

**Why start here?**
- Simplest feature
- Tests API connection
- Gives immediate visual result
- Foundation for everything else

**What to build:**

1. **Simple layout with header**
```tsx
// app/layout.tsx
export default function RootLayout({ children }) {
  return (
    <html>
      <body className="bg-gray-50">
        <header className="bg-white border-b">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <h1 className="text-2xl font-bold">AdIntel</h1>
          </div>
        </header>
        <main className="max-w-7xl mx-auto px-4 py-8">
          {children}
        </main>
      </body>
    </html>
  );
}
```

2. **Dashboard page that fetches competitors**
```tsx
// app/page.tsx
'use client';
import { useQuery } from '@tanstack/react-query';
import { getCompetitors } from '@/lib/api';
import CompetitorCard from '@/components/CompetitorCard';

export default function Dashboard() {
  const { data: competitors, isLoading } = useQuery({
    queryKey: ['competitors'],
    queryFn: getCompetitors,
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <div>
      <h2 className="text-3xl font-bold mb-8">Competitors</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {competitors?.data.map(comp => (
          <CompetitorCard key={comp.advertiser_id} competitor={comp} />
        ))}
      </div>
    </div>
  );
}
```

3. **Simple competitor card**
```tsx
// components/CompetitorCard.tsx
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

export default function CompetitorCard({ competitor }) {
  return (
    <Card className="p-6">
      <div className="flex items-start justify-between mb-4">
        <h3 className="text-xl font-semibold">{competitor.name}</h3>
        <Badge variant="success">🟢 Active</Badge>
      </div>

      <div className="space-y-2 text-sm text-gray-600">
        <p>{competitor.total_ads} ads</p>
        <p>{competitor.region}</p>
        <p className="text-xs">
          Last updated: {new Date(competitor.last_scraped).toLocaleDateString()}
        </p>
      </div>

      <button className="w-full mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
        View Details
      </button>
    </Card>
  );
}
```

**Test:** Run `npm run dev` and see competitor cards!

---

### **Feature 2: Scraper Page (Day 3-4)**

**Why next?**
- Core functionality
- Users need to add competitors
- Tests POST endpoint and polling

**What to build:**

1. **Create scrape page**
```tsx
// app/scrape/page.tsx
'use client';
import { useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { scrapeAds } from '@/lib/api';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';

export default function ScrapePage() {
  const [url, setUrl] = useState('');
  const [maxAds, setMaxAds] = useState(400);

  const scrapeMutation = useMutation({
    mutationFn: () => scrapeAds(url, maxAds),
    onSuccess: (data) => {
      alert(`Scraping started! Job ID: ${data.data.job_id}`);
      // We'll add polling next
    },
  });

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-3xl font-bold mb-8">Scrape Competitor Ads</h2>

      <div className="bg-white rounded-lg shadow p-8 space-y-6">
        <div>
          <label className="block text-sm font-medium mb-2">
            GATC URL
          </label>
          <Input
            type="url"
            placeholder="https://adstransparency.google.com/advertiser/..."
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium mb-2">
            Max Ads
          </label>
          <select
            className="w-full border rounded px-3 py-2"
            value={maxAds}
            onChange={(e) => setMaxAds(Number(e.target.value))}
          >
            <option value={50}>50</option>
            <option value={100}>100</option>
            <option value={200}>200</option>
            <option value={400}>400</option>
          </select>
        </div>

        <Button
          onClick={() => scrapeMutation.mutate()}
          disabled={!url || scrapeMutation.isPending}
          className="w-full"
        >
          {scrapeMutation.isPending ? 'Scraping...' : 'Scrape Ads'}
        </Button>
      </div>
    </div>
  );
}
```

2. **Add navigation to header**
```tsx
// app/layout.tsx (update header)
<header className="bg-white border-b">
  <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
    <h1 className="text-2xl font-bold">AdIntel</h1>
    <nav className="flex gap-4">
      <Link href="/" className="text-gray-600 hover:text-gray-900">
        Dashboard
      </Link>
      <Link href="/scrape" className="text-gray-600 hover:text-gray-900">
        Scrape
      </Link>
    </nav>
  </div>
</header>
```

**Test:** Scrape ads and see job ID!

---

### **Feature 3: Job Status Polling (Day 5)**

**Why next?**
- Makes scraping actually useful
- Reusable for analysis later
- Shows real-time progress

**What to build:**

1. **Create polling hook**
```tsx
// hooks/useJobStatus.ts
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';

export function useJobStatus(jobId: string | null) {
  return useQuery({
    queryKey: ['job', jobId],
    queryFn: () => api.get(`/api/jobs/${jobId}`),
    enabled: !!jobId,
    refetchInterval: (data) => {
      const status = data?.data?.status;
      if (status === 'completed' || status === 'failed') {
        return false; // Stop polling
      }
      return 2000; // Poll every 2 seconds
    },
  });
}
```

2. **Update scrape page with progress**
```tsx
// app/scrape/page.tsx (add to component)
const [jobId, setJobId] = useState<string | null>(null);
const { data: jobStatus } = useJobStatus(jobId);

const scrapeMutation = useMutation({
  mutationFn: () => scrapeAds(url, maxAds),
  onSuccess: (data) => {
    setJobId(data.data.job_id);
  },
});

// Add progress UI below form
{jobId && (
  <div className="mt-8 bg-white rounded-lg shadow p-8">
    <h3 className="text-xl font-semibold mb-4">Progress</h3>

    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span>Status:</span>
        <Badge>{jobStatus?.data?.status}</Badge>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <span>Progress</span>
          <span>{jobStatus?.data?.progress}%</span>
        </div>
        <Progress value={jobStatus?.data?.progress || 0} />
      </div>

      {jobStatus?.data?.status === 'completed' && (
        <Button onClick={() => window.location.href = '/'}>
          View Competitors
        </Button>
      )}
    </div>
  </div>
)}
```

**Test:** Scrape and watch progress update in real-time!

---

### **Feature 4: Data Visualization - Charts (Day 6-7)**

**Why now?**
- Dashboard has data to visualize
- Users need insights, not just numbers
- Makes the app actually useful

**Strategy for charts:**
- **Keep it simple:** Bar charts and pie charts only
- **Use Recharts:** Easy to use, looks professional
- **Start with dummy data:** Get UI right first
- **Then connect real data:** Hook up API

**What to build:**

1. **Create reusable chart components**

```tsx
// components/charts/OfferDistributionChart.tsx
'use client';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

interface ChartData {
  name: string;
  value: number;
  color: string;
}

export default function OfferDistributionChart({ data }: { data: ChartData[] }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Offer Distribution</h3>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data}>
          <XAxis dataKey="name" />
          <YAxis />
          <Tooltip />
          <Bar dataKey="value" fill="#3B82F6" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

2. **Add to dashboard with dummy data first**

```tsx
// app/page.tsx (add below competitor cards)
const dummyOfferData = [
  { name: 'Free Delivery', value: 40, color: '#10B981' },
  { name: 'Discount', value: 25, color: '#3B82F6' },
  { name: 'BOGO', value: 15, color: '#F59E0B' },
  { name: 'No Offer', value: 20, color: '#6B7280' },
];

<div className="mt-8">
  <OfferDistributionChart data={dummyOfferData} />
</div>
```

3. **Create keyword list component**

```tsx
// components/KeywordsList.tsx
export default function KeywordsList({ keywords }) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">Top Keywords</h3>

      <div className="space-y-2">
        {keywords.map((kw, i) => (
          <div key={i} className="flex items-center justify-between">
            <span className="text-sm">{kw.word}</span>
            <div className="flex items-center gap-2">
              <div className="w-24 bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full"
                  style={{ width: `${kw.percentage}%` }}
                />
              </div>
              <Badge variant="secondary">{kw.count}</Badge>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

4. **Add to dashboard**

```tsx
const dummyKeywords = [
  { word: 'Free Delivery', count: 85, percentage: 100 },
  { word: 'Order Now', count: 62, percentage: 73 },
  { word: 'Download App', count: 45, percentage: 53 },
  { word: 'Fast', count: 38, percentage: 45 },
  { word: 'Save', count: 32, percentage: 38 },
];

<div className="mt-8 grid grid-cols-1 lg:grid-cols-2 gap-6">
  <OfferDistributionChart data={dummyOfferData} />
  <KeywordsList keywords={dummyKeywords} />
</div>
```

**Test:** See beautiful charts with dummy data!

---

### **Feature 5: Connect Real Data (Day 8)**

**Why last?**
- UI is proven to work
- Just swap dummy data for API data
- Easy to debug

**What to build:**

1. **Add insights endpoint to API client**

```typescript
// lib/api.ts (add)
export const getInsights = (csvFile: string) =>
  api.get(`/api/insights/${encodeURIComponent(csvFile)}`);
```

2. **Fetch insights on dashboard**

```tsx
// app/page.tsx (replace dummy data)
const { data: competitors } = useQuery({
  queryKey: ['competitors'],
  queryFn: getCompetitors,
});

// Get insights for all competitors
const insightsQueries = competitors?.data.map(comp =>
  useQuery({
    queryKey: ['insights', comp.csv_file],
    queryFn: () => getInsights(comp.csv_file),
    enabled: !!comp.csv_file,
  })
);

// Aggregate data from all competitors
const aggregatedOfferData = useMemo(() => {
  // Process insights and return chart data
  // This is where you'd aggregate offer_distribution from all competitors
}, [insightsQueries]);

<OfferDistributionChart data={aggregatedOfferData} />
```

**Test:** See real data in charts!

---

## 🎨 Design System: Keep It Uniform

### **1. Use a Component Library (shadcn/ui)**

**Why?**
- Components look consistent automatically
- Pre-built accessible components
- Easy to customize

**What to use:**
- `Button` - All buttons
- `Card` - All containers
- `Badge` - Status indicators
- `Input` - All text inputs
- `Progress` - Progress bars
- `Dialog` - Modals

### **2. Color Palette (Define Once, Use Everywhere)**

```css
/* app/globals.css */
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    /* Neutrals */
    --background: 250 250 250; /* #FAFAFA */
    --foreground: 26 26 26;    /* #1A1A1A */
    --muted: 107 107 107;      /* #6B6B6B */
    --border: 229 229 229;     /* #E5E5E5*/

    /* Accent */
    --primary: 37 99 235;      /* #2563EB blue */
    --success: 16 185 129;     /* #10B981 green */
    --error: 239 68 68;        /* #EF4444 red */

    /* Competitor colors */
    --talabat: 255 107 53;     /* #FF6B35 */
    --deliveroo: 0 194 168;    /* #00C2A8 */
    --keeta: 139 92 246;       /* #8B5CF6 */
    --rafiq: 245 158 11;       /* #F59E0B */
  }
}
```

**Use in components:**
```tsx
<div className="bg-background text-foreground">
<Button className="bg-primary">Click</Button>
<div className="border-border">
```

### **3. Typography Scale**

```tsx
// Use these consistently
<h1 className="text-4xl font-bold">Page Title</h1>
<h2 className="text-3xl font-bold">Section Title</h2>
<h3 className="text-xl font-semibold">Card Title</h3>
<p className="text-base">Body text</p>
<span className="text-sm text-muted">Secondary text</span>
```

### **4. Spacing System**

```tsx
// Use Tailwind's spacing consistently
gap-4      // 16px gap between items
p-6        // 24px padding
mb-8       // 32px margin bottom
space-y-4  // 16px vertical spacing between children
```

---

## 📊 Data Visualization Strategy

### **Chart Types to Use:**

**1. Bar Chart** - For comparisons
- Offer distribution
- Competitor comparison
- Category breakdown

```tsx
<BarChart data={data}>
  <XAxis dataKey="name" />
  <YAxis />
  <Tooltip />
  <Bar dataKey="value" fill="#3B82F6" radius={[4, 4, 0, 0]} />
</BarChart>
```

**2. Pie Chart** - For percentages
- Offer mix for single competitor
- Category distribution

```tsx
<PieChart>
  <Pie
    data={data}
    dataKey="value"
    nameKey="name"
    cx="50%"
    cy="50%"
    label
  />
  <Tooltip />
</PieChart>
```

**3. Progress Bars** - For lists with counts
- Keyword frequency
- Product mentions

```tsx
<div className="w-full bg-gray-200 rounded-full h-2">
  <div
    className="bg-blue-600 h-2 rounded-full"
    style={{ width: `${percentage}%` }}
  />
</div>
```

**4. Line Chart** - For trends (later)
- 30-day ad volume
- Offer strategy over time

### **Chart Best Practices:**

✅ **Keep colors consistent**
- Free Delivery → Green
- Discount → Blue
- BOGO → Orange
- No Offer → Gray

✅ **Add tooltips**
- Show exact values on hover
- Recharts does this automatically

✅ **Make responsive**
- Use `<ResponsiveContainer>`
- Set height explicitly (300px-400px)

✅ **Show empty states**
```tsx
{data.length === 0 ? (
  <div className="text-center py-12 text-gray-500">
    No data available
  </div>
) : (
  <BarChart data={data}>...</BarChart>
)}
```

✅ **Format numbers**
```tsx
import { formatNumber } from '@/lib/utils';

<Tooltip
  formatter={(value) => `${value}%`}
  labelFormatter={(label) => `Offer: ${label}`}
/>
```

---

## 🧩 Reusable Patterns

### **1. Loading States**

Create once, use everywhere:

```tsx
// components/LoadingSpinner.tsx
export default function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
    </div>
  );
}

// Usage
{isLoading ? <LoadingSpinner /> : <Content />}
```

### **2. Error States**

```tsx
// components/ErrorMessage.tsx
export default function ErrorMessage({ message, onRetry }) {
  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
      <p className="text-red-800 mb-4">{message}</p>
      <Button onClick={onRetry} variant="outline">
        Try Again
      </Button>
    </div>
  );
}
```

### **3. Empty States**

```tsx
// components/EmptyState.tsx
export default function EmptyState({ title, description, action }) {
  return (
    <div className="text-center py-12">
      <h3 className="text-lg font-semibold text-gray-900 mb-2">
        {title}
      </h3>
      <p className="text-gray-600 mb-4">{description}</p>
      {action && <Button onClick={action.onClick}>{action.label}</Button>}
    </div>
  );
}

// Usage
{competitors.length === 0 && (
  <EmptyState
    title="No competitors yet"
    description="Start by scraping your first competitor"
    action={{ label: 'Scrape Now', onClick: () => router.push('/scrape') }}
  />
)}
```

---

## 🚦 Quality Checklist (For Each Feature)

Before moving to next feature, check:

- [ ] ✅ **Works** - Feature does what it should
- [ ] 🎨 **Looks good** - Uses design system
- [ ] 📱 **Responsive** - Works on mobile
- [ ] ⏳ **Loading state** - Shows when fetching
- [ ] ❌ **Error state** - Handles failures gracefully
- [ ] 🗂️ **Empty state** - Shows when no data
- [ ] ⌨️ **Keyboard accessible** - Can use with Tab/Enter
- [ ] 🐛 **No console errors** - Clean browser console

---

## 📅 Realistic Timeline

### **Week 1: Core Features**
- Day 1-2: Setup + Dashboard with cards
- Day 3-4: Scraper page
- Day 5: Job polling
- **Deliverable:** Can scrape and see competitors

### **Week 2: Visualization**
- Day 6-7: Add charts
- Day 8: Connect real data
- Day 9-10: Polish and responsive design
- **Deliverable:** Working dashboard with insights

### **Week 3: Advanced** (Optional)
- Day 11-12: Competitor detail page
- Day 13-14: Comparison view
- Day 15: Deployment
- **Deliverable:** Full-featured app

---

## 🎯 Key Principles

### **1. Build Vertically**
Complete one feature end-to-end before starting next

### **2. Start Simple**
Dummy data → Real data → Polish

### **3. Reuse Components**
Build once, use everywhere

### **4. Test As You Go**
See it working in browser immediately

### **5. Design System First**
Set colors/spacing once, stay consistent

---

## 🚀 Start Now: First 30 Minutes

```bash
# 1. Create project (5 min)
npx create-next-app@latest adIntel-frontend --typescript --tailwind --app

# 2. Install deps (5 min)
cd adIntel-frontend
npm install @tanstack/react-query axios recharts lucide-react date-fns

# 3. Setup API client (10 min)
# Create lib/api.ts with the code above

# 4. Create first component (10 min)
# Create components/CompetitorCard.tsx

# 5. Run and see it work!
npm run dev
# Open http://localhost:3000
```

---

**That's it! You now have:**
1. ✅ Clear starting point (setup)
2. ✅ Build order (features 1-5)
3. ✅ Design system (consistent UI)
4. ✅ Chart strategy (data viz)
5. ✅ Reusable patterns (DRY)
6. ✅ Quality checklist (standards)

**Start with Feature 1 (Dashboard) and build forward!** 🚀
