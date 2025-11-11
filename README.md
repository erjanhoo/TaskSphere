# 🎯 TaskSphere - Gamified Task Management API

A feature-rich task management REST API built with Django REST Framework that gamifies productivity through karma points, badges, streaks, and leaderboards.

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Django](https://img.shields.io/badge/Django-5.2+-green.svg)
![DRF](https://img.shields.io/badge/DRF-3.14+-red.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

---

## 🌟 Overview

TaskSphere transforms task management into an engaging experience. Users earn karma points and badges for completing tasks, maintain daily completion streaks, and compete on leaderboards. The system includes automated email notifications, recurring task generation, and advanced filtering—all powered by Celery for background processing and Redis for caching.

---

## ✨ Key Features

### 🎯 **Task Management**
- **Full CRUD Operations** - Create, read, update, delete tasks
- **Subtasks** - Break down complex tasks with progress tracking
- **Priority System** - 5 levels: Low → Extremely Important
- **Organization** - Custom categories and multiple tags
- **Smart Scheduling** - Due dates, reminders, recurring tasks (daily/weekly/monthly)
- **Calendar View** - Visualize tasks by date range
- **Advanced Filtering** - Search by title, filter by status/priority/category/tag/due date

### 🏆 **Gamification System**

**Karma Point System:**
- Task completion: **5-25 karma** (based on priority)
- Subtask completion: **+5 karma** each
- All subtasks done: **+50 karma** bonus
- Daily streak: **+20 karma**
- 7-day streak: **+350 karma**
- 30-day streak: **+1000 karma**

**8-Tier Badge System:**
1. 🥉 **Beginner** (0-499 karma)
2. 🥈 **Novice** (500-2,499)
3. 🥇 **Intermediate** (2,500-4,999)
4. 💼 **Professional** (5,000-7,499)
5. 🎓 **Expert** (7,500-9,999)
6. 👑 **Master** (10,000-19,999)
7. 💎 **Grand Master** (20,000-49,999)
8. ✨ **Enlightened** (50,000+)

**Additional Features:**
- Daily completion streak tracking
- Global leaderboard ranking
- Karma transaction history
- Progress analytics & charts
- User profile dashboard

### 📧 **Notifications & Automation**
- **Email Notifications:**
  - OTP verification (registration & 2FA)
  - Password reset codes
  - Task reminders
  - Daily summaries (8 AM)
  - Evening progress reports (6 PM)
  - Weekly productivity reports
- **Automated Background Tasks:**
  - Recurring task generation
  - Streak calculation
  - Expired task cleanup
  - All emails sent asynchronously via Celery

### 🔐 **Authentication & Security**
- JWT authentication with refresh tokens
- Optional 2FA via email OTP
- Token blacklisting on logout
- Rate limiting on sensitive endpoints
- Password hashing & CSRF protection

---

## 🛠 Tech Stack

**Backend:**
- Django 5.2+ & Django REST Framework
- SimpleJWT (authentication)
- Celery (async task queue)
- Redis (cache & message broker)
- django-filter (advanced filtering)

**Database:**
- PostgreSQL / SQLite

**Infrastructure:**
- Docker & Docker Compose
- Gunicorn (WSGI server)
- SMTP (email delivery)

---

## 📁 Project Structure

```
TaskSphere/
├── TaskSphere/              # Main project configuration
│   ├── settings.py          # Django settings
│   ├── celery.py            # Celery configuration
│   └── urls.py              # Main URL routing
│
├── task/                    # Task management app
│   ├── models.py            # Task, SubTask, Category, Tag, RecurrenceRule
│   ├── views.py             # API endpoints
│   ├── serializers.py       # Data serialization
│   ├── filters.py           # Search & filtering logic
│   └── tasks.py             # Celery background tasks
│
├── user/                    # User & gamification app
│   ├── models.py            # MyUser, Badges, UserBadge, KarmaTransaction
│   ├── views.py             # Auth & gamification endpoints
│   ├── services.py          # Karma & badge business logic
│   ├── tasks.py             # Email background tasks
│   └── throttling.py        # API rate limiting
│
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## 🎮 Gamification Details

### How Karma Works
Users earn karma by completing tasks. Higher priority tasks yield more karma. Streaks provide bonus rewards at milestones. Uncompleting a task deducts karma (5-25 points based on priority).

### Badge Progression
Badges are automatically awarded as users accumulate karma. Users can earn multiple badges as they progress through levels. The system tracks both current badge level and all earned badges.

### Streak System
Complete at least one task every day to maintain a streak. Streaks are calculated at midnight. Missing a day resets the current streak but preserves the highest streak achieved.

### Karma Transaction History
All karma changes are logged with timestamps and reasons (e.g., "Completed task: Buy groceries", "7-day streak bonus"). Users can view their complete karma history and statistics.

---

## 🚦 Performance & Optimization

- **Redis Caching** - User profiles cached (5 min TTL)
- **Database Indexing** - Optimized queries for karma/badges
- **Query Optimization** - select_related/prefetch_related to reduce N+1 queries
- **Async Processing** - Long operations (emails, streak calculations) handled by Celery
- **Efficient Filtering** - django-filter for performant API queries

---

## 🔒 Security

- JWT token authentication with refresh tokens
- Password hashing (Django's built-in PBKDF2)
- OTP-based 2FA support
- Rate limiting on auth endpoints
- Token blacklisting on logout
- CSRF & XSS protection
- SQL injection prevention (Django ORM)

---

## 🐳 Docker Support

Includes `Dockerfile` and `docker-compose.yml` for easy deployment with PostgreSQL, Redis, Celery worker, and Celery beat scheduler.

---

## 📄 License

MIT License

---

## 👨‍💻 Author

**Erjan Hoo**  
GitHub: [@erjanhoo](https://github.com/erjanhoo)

---

**⭐ Star this project if you find it useful!**
