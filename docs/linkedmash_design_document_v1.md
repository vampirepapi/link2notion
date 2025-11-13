# LinkedMash Design Document
**Version 1.0 | Build-from-Scratch Specification**

---

## 1. Executive Summary

LinkedMash is a web-based productivity tool that extracts, organizes, and activates LinkedIn saved posts. It addresses the core problem: LinkedIn's native saved posts feature is a black hole where valuable content goes to die. The application provides a searchable, labelable, exportable archive with AI-powered insights.

**Target User**: Knowledge workers, consultants, marketers, and researchers who save >20 LinkedIn posts/month.

---

## 2. Product Requirements

### 2.1 Core Features
1. **LinkedIn Import**: Extract user's saved posts (text, images, author, timestamp, URL)
2. **Search**: Full-text search across post content, author, and labels
3. **Labeling**: Manual and AI-suggested tags for categorization
4. **Export Engine**: One-click sync to Notion, Google Sheets, and Airtable
5. **AI Chat**: Conversational interface to query saved posts and extract insights
6. **Auto-Sync**: Scheduled background sync of new saved posts
7. **Mobile Responsive**: Full functionality on mobile browsers

### 2.2 User Stories
- **US1**: As a user, I can authenticate with LinkedIn and import all my saved posts in <2 minutes
- **US2**: As a user, I can search for a specific post using any keyword I remember
- **US3**: As a user, I can create custom labels and apply them to posts in batch
- **US4**: As a user, I can export labeled posts to my preferred tool (Notion/Sheets/Airtable) with one click
- **US5**: As a user, I can ask "What have I saved about AI marketing tools?" and get synthesized answers
- **US6**: As a user, I can set weekly auto-sync so new saves appear automatically

---

## 3. System Architecture

### 3.1 High-Level Architecture
```
┌─────────────────┐        ┌──────────────────┐        ┌─────────────────┐
│   Web Frontend  │───────▶│   API Gateway    │───────▶│  Backend Services│
│(React/Vue/Next) │        │ (Rate Limiter)   │        │  (Node/Python)  │
└─────────────────┘        └──────────────────┘        └─────────────────┘
        ▲                          │                            │
        │                          │                            ▼
        │                          │                    ┌─────────────────┐
        │                          │                    │  PostgreSQL DB  │
        │                          │                    │  (Primary Store)│
        │                          │                    └─────────────────┘
        │                          │                            │
        │                          │                            ▼
        │                          │                    ┌─────────────────┐
        │                          │                    │   Redis Cache   │
        │                          │                    │  (Sessions/Qs)  │
        │                          │                    └─────────────────┘
        │                          ▼
        │                    ┌──────────────────┐
        │                    │  LinkedIn Scraper│
        │                    │ (Puppeteer/Playw)│
        │                    └──────────────────┘
        ▼
┌─────────────────┐
│  AI Services    │
│ (OpenAI/Claude) │
└─────────────────┘
```

### 3.2 Technology Stack
- **Frontend**: Next.js 14 (App Router), TypeScript, Tailwind CSS, shadcn/ui
- **Backend**: Node.js/Express or Python/FastAPI
- **Database**: PostgreSQL (structured data) + Pinecone (vector embeddings)
- **Cache/Queue**: Redis (BullMQ for job processing)
- **Authentication**: NextAuth.js (LinkedIn OAuth 2.0)
- **Scraping**: Puppeteer with stealth plugins
- **AI**: OpenAI GPT-4 API / Claude 3.5 Sonnet
- **Hosting**: Vercel (frontend) + Railway/Heroku (backend)
- **Storage**: AWS S3 (for screenshots/post images)

---

## 4. Data Model

### 4.1 Core Entities

```sql
-- Users Table
CREATE TABLE users (
    id UUID PRIMARY KEY,
    linkedin_id VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    name VARCHAR(255),
    access_token TEXT, -- Encrypted LinkedIn token
    refresh_token TEXT, -- Encrypted
    token_expires_at TIMESTAMP,
    subscription_tier VARCHAR(50) DEFAULT 'free',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Saved Posts Table
CREATE TABLE saved_posts (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    linkedin_post_url VARCHAR(500) UNIQUE NOT NULL,
    author_name VARCHAR(255),
    author_profile_url VARCHAR(500),
    post_content TEXT,
    post_images TEXT[], -- Array of image URLs
    saved_at TIMESTAMP,
    scraped_at TIMESTAMP DEFAULT NOW(),
    last_synced TIMESTAMP,
    labels TEXT[], -- Array of label names
    is_exported BOOLEAN DEFAULT FALSE,
    vector_embedding_id UUID -- References vector DB
);

-- Labels Table
CREATE TABLE labels (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    name VARCHAR(100),
    color VARCHAR(7), -- Hex color
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, name)
);

-- Exports Log
CREATE TABLE export_logs (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    destination VARCHAR(50), -- 'notion', 'sheets', 'airtable'
    destination_config JSONB, -- Store API keys, sheet IDs, etc. (encrypted)
    last_exported_at TIMESTAMP,
    status VARCHAR(50),
    record_count INTEGER
);
```

### 4.2 Vector Database Schema (Pinecone)
```json
{
  "namespace": "user_{user_id}",
  "vectors": [
    {
      "id": "post_{post_id}",
      "values": [/* 1536-dimensional embedding */],
      "metadata": {
        "author": "John Doe",
        "labels": ["ai-marketing", "saas"],
        "saved_at": "2024-01-15",
        "content_preview": "First 200 chars..."
      }
    }
  ]
}
```

---

## 5. Frontend Design

### 5.1 Page Structure
- **/dashboard**: Main view with searchable post grid
- **/import**: LinkedIn connection and sync management
- **/labels**: Label management interface
- **/exports**: Export configuration and history
- **/ai-chat**: Conversational interface
- **/settings**: Account, billing, preferences

### 5.2 Key Components
1. **PostCard**: Display post content, author, preview image, labels
2. **SearchBar**: Real-time search with filters (author, date range, labels)
3. **LabelManager**: Drag-and-drop labeling, bulk actions
4. **ExportWizard**: Step-by-step destination setup
5. **AIChatPanel**: Sidebar chat interface with context awareness

### 5.3 State Management
- Use React Query for server state
- Zustand for frontend UI state (search filters, selected posts)
- WebSocket connection for real-time sync progress

---

## 6. Backend Design

### 6.1 API Endpoints

```typescript
// Authentication
POST /api/auth/linkedin/callback

// Posts
GET    /api/posts?search=&labels=&page=
POST   /api/posts/sync (triggers background job)
PUT    /api/posts/:id/labels
DELETE /api/posts/:id

// Labels
GET    /api/labels
POST   /api/labels
PUT    /api/labels/:id
DELETE /api/labels/:id

// Exports
POST   /api/exports/notion (body: { filters })
POST   /api/exports/sheets
GET    /api/exports/history

// AI
POST   /api/ai/chat (body: { question, context_posts[] })
POST   /api/ai/classify (auto-label posts)
```

### 6.2 Background Workers (BullMQ on Redis)
- **scrape-linkedin-job**: Scrapes saved posts from LinkedIn
  - Rate: 1 request/5 seconds (to avoid detection)
  - Retry: 3 attempts with exponential backoff
- **export-job**: Handles exports to third-party tools
  - Batch size: 100 posts per batch
  - Rate limits per destination API
- **embed-generate-job**: Creates vector embeddings for search/AI
  - Processed asynchronously to avoid blocking

---

## 7. Integration Deep Dive

### 7.1 LinkedIn Scraping (Critical Path)
Since LinkedIn has no public API for saved posts, use **Puppeteer Stealth**:

```javascript
// Pseudocode for scraper
async function scrapeSavedPosts(linkedinCredentials) {
  const browser = await puppeteer.launch({ headless: true });
  const page = await browser.newPage();
  
  // Use stealth plugin to avoid detection
  await page.goto('https://www.linkedin.com/login');
  await page.type('#username', linkedinCredentials.email);
  await page.type('#password', linkedinCredentials.password); // Or use session cookie
  
  // Navigate to saved posts
  await page.goto('https://www.linkedin.com/my-items/saved-posts/');
  
  // Infinite scroll to load all posts
  let previousHeight = 0;
  while (true) {
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await page.waitForTimeout(2000);
    const newHeight = await page.evaluate(() => document.body.scrollHeight);
    if (newHeight === previousHeight) break;
    previousHeight = newHeight;
  }
  
  // Extract post data
  const posts = await page.evaluate(() => {
    return Array.from(document.querySelectorAll('.saved-post')).map(el => ({
      url: el.querySelector('a').href,
      content: el.querySelector('.feed-shared-text').innerText,
      // ... other fields
    }));
  });
  
  await browser.close();
  return posts;
}
```

**Security**: Never store raw LinkedIn passwords. Use session cookies or encrypted OAuth tokens.

### 7.2 Export Destinations
- **Notion**: Use Notion API v2, create database pages with post content as blocks
- **Google Sheets**: Use Google Sheets API, append rows with hyperlinks
- **Airtable**: Use Airtable API, map fields to table schema

Each export should be idempotent—rerunning exports only adds new/updated posts.

---

## 8. AI Features Implementation

### 8.1 Vector Search & Embeddings
```python
# Generate embeddings for each post
def generate_embedding(post_content, author, labels):
    text = f"{post_content} by {author} about {', '.join(labels)}"
    response = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response['data'][0]['embedding']

# Semantic search
def semantic_search(user_id, query, top_k=10):
    query_embedding = generate_embedding(query, "", [])
    results = pinecone.query(
        namespace=f"user_{user_id}",
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True
    )
    return results.matches
```

### 8.2 AI Chat Context
When user asks question, retrieve top 20 relevant posts via vector search, then:
```python
context = "\n\n".join([f"Post {i}: {post.content}" for i, post in enumerate(relevant_posts)])
prompt = f"""
Based on these saved LinkedIn posts, answer the user's question.
Posts: {context}

Question: {user_question}
Answer concisely with citations if possible.
"""
```

### 8.3 Auto-Labeling (Coming Soon Feature)
- Use GPT-4 to suggest 3-5 labels per post based on content
- Store suggestions in a `suggested_labels` array
- User approves/rejects via UI

---

## 9. Security & Privacy

### 9.1 Data Protection
- **Encryption at Rest**: AES-256 for all tokens, API keys in PostgreSQL
- **Encryption in Transit**: TLS 1.3 for all connections
- **OAuth Only**: No LinkedIn password storage; use official OAuth 2.0
- **Session Management**: JWT with httpOnly cookies, 24-hour expiry
- **Rate Limiting**: 60 req/min per user, 1,000 req/day per free user

### 9.2 LinkedIn Account Safety
- **Human-like Scraping**: Random delays, viewport variations, user-agent rotation
- **Session Refresh**: Auto-refresh LinkedIn session every 7 days
- **Backup Auth**: Warn users if session expires; provide re-auth flow
- **Scrape Frequency**: Max 1 sync per hour per user (configurable)

### 9.3 Compliance
- GDPR/CCPA compliant data deletion (cascade delete user data)
- Clear privacy policy: "We never sell your data"
- Data retention: Delete inactive accounts after 12 months

---

## 10. Deployment Infrastructure

### 10.1 Vercel Deployment (Frontend)
```json
// vercel.json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "environment": {
    "NEXTAUTH_URL": "https://linkedlmash.com",
    "NEXTAUTH_SECRET": "@nextauth_secret"
  }
}
```

### 10.2 Backend Scaling
- **Web Server**: 2-4 instances (Node.js cluster mode)
- **Workers**: Separate worker dyno/process for BullMQ
- **Database**: PostgreSQL on Neon/Supabase (serverless)
- **Redis**: Upstash Redis (for queues)
- **Monitoring**: Sentry for errors, Datadog for metrics

---

## 11. Development Roadmap

### Phase 1: MVP (Weeks 1-3)
- [ ] LinkedIn OAuth + basic scraper
- [ ] Dashboard with post grid
- [ ] Manual labeling
- [ ] Export to Google Sheets
- [ ] Vector search with basic embeddings

### Phase 2: Core Features (Weeks 4-6)
- [ ] Export to Notion & Airtable
- [ ] AI chat interface
- [ ] Auto-sync scheduling
- [ ] Bulk labeling
- [ ] Mobile UI polish

### Phase 3: AI Power (Weeks 7-9)
- [ ] Auto-labeling suggestions
- [ ] AI summarization of post collections
- [ ] Email digest feature
- [ ] Advanced filters (date, author, engagement)

### Phase 4: Scale & Monetize (Weeks 10-12)
- [ ] Payment integration (Stripe)
- [ ] Rate limit handling improvements
- [ ] Performance optimizations
- [ ] Admin dashboard for support

---

## 12. AI Agent Implementation Prompt

When you give this document to your AI agent, use this condensed prompt:

```
Build LinkedMash: A LinkedIn saved posts manager. Use Next.js 14, TypeScript, Tailwind, shadcn/ui for frontend. Backend: Node.js/Express, PostgreSQL, Redis BullMQ for queues. 

Core features:
1. LinkedIn OAuth + Puppeteer scraper for saved posts (respect rate limits)
2. Dashboard: Search, label, filter posts
3. One-click export to Notion/Sheets/Airtable via their APIs
4. AI chat using OpenAI + vector search (Pinecone) over posts
5. Auto-sync background jobs

Start with MVP: implement LinkedIn auth, basic scraper, post display, and manual labeling. Deploy on Vercel + Railway. Follow the design document provided for data models and API structure.
```

This document provides the blueprint—your AI agent now has the architectural decisions, tech stack, data models, and sequencing needed to build LinkedMash from zero to production.
