# Telegram Hiring Bot 🤖💼

**Telegram Hiring Bot** is an intelligent automated solution for publishing job vacancies and managing the initial recruitment stages. The main goal of this project is to save HR managers' time by delegating the routine first-step candidate screening to an AI Agent.

### 💡 How does it help HR?
The moment a candidate responds to a vacancy, the **AI Agent** steps in to conduct the initial screening. The agent automatically discovers and structures key information, including:
- 📍 Location & preferred work mode (Remote, Office, Hybrid)
- ⏳ Years of experience
- 💻 GitHub profile link
- 🛠 Key skills & technology stack

This allows HR managers to skip the basic back-and-forth and jump straight to reviewing pre-screened, structured candidate profiles.

---

## 🛠 Tech Stack

This project is built using an asynchronous Telegram bot framework and advanced AI agent orchestration:
- **Core:** Python 🐍[
- **Telegram Bot API:** `aiogram` (v3 async framework)
- **AI & Agents:** `OpenAI` API, `LangGraph` (for complex agent state workflows), `LangChain`
- **Database:** PostgreSQL (Data persistence) & `psycopg2` (Database adapter)
- **Caching & State Management:** Redis (FSM state handling and caching)
- **Data Validation:** Pydantic (Strict typing and candidate data parsing)

---

## ✨ Features

The bot provides dedicated interfaces and distinct workflows for two roles:

### 🧑‍💼 For HR Managers
- **Vacancy Management:** Easily add and publish new job vacancies.
- **Application Tracking:** Receive and view real-time applications from candidates.
- **Decision Making:** Directly respond to or reject candidates through button interfaces.
- **Talent Pool:** Save promising candidates to a talent pool for future opportunities.

### 👨‍💻 For Candidates
- **Smart Search:** Search for jobs easily by typing keywords or text descriptions.
- **Browse Vacancies:** View all currently open job positions.
- **Instant Feedback:** Receive real-time updates and direct messages from HR.
- **Application History:** Keep track of previously applied vacancies.

## 📸 User Flow & Screenshots

Here is a comprehensive visual demonstration of the bot's workflow, showcasing both the candidate's screening journey and the HR management interface.

---
![HR Welcome Window](https://github.com/cApitanYARE/telegram-hiring-bot-/blob/943851b1dfb4ceac56a62b0f18e82d2b6ed3ba35/img/welcome_window.png?raw=true)
### 👨‍💻 Candidate Journey

#### 1. Welcome Screen & Main Menu
Upon launching the bot, users are greeted with a clean welcome interface providing quick-access buttons tailored to their role.
![Welcome Screen](https://github.com/cApitanYARE/telegram-hiring-bot-/blob/943851b1dfb4ceac56a62b0f18e82d2b6ed3ba35/img/welcome_user.png?raw=true)

#### 2. Job Search by Description
Candidates can perform a text-based query, describing what kind of job or position they are looking for using simple natural language.
![Search Vacancy](https://github.com/cApitanYARE/telegram-hiring-bot-/blob/943851b1dfb4ceac56a62b0f18e82d2b6ed3ba35/img/search_vacancy_by_query.png?raw=true)

#### 3. Relevant Vacancy Found
The bot processes the candidate's query and suggests matching results, displaying vacancy card details with interactive option buttons.
![Vacancy Found](https://github.com/cApitanYARE/telegram-hiring-bot-/blob/943851b1dfb4ceac56a62b0f18e82d2b6ed3ba35/img/found_1.png?raw=true)

#### 4. AI Screening Process (Interview Round 1)
When applying, the dynamic AI Agent activates to engage the candidate, initiating a smart interview to systematically request details about their background, location, and key skills.
![AI Interview Phase 1](https://github.com/cApitanYARE/telegram-hiring-bot-/blob/943851b1dfb4ceac56a62b0f18e82d2b6ed3ba35/img/1_interview.png?raw=true)

#### 5. Detailed Technical Discovery (Interview Round 2)
The AI Agent continues the dialog seamlessly, extracting further necessary artifacts like a GitHub profile link and specific framework knowledge while keeping the interaction natural.
![AI Interview Phase 2](https://github.com/cApitanYARE/telegram-hiring-bot-/blob/943851b1dfb4ceac56a62b0f18e82d2b6ed3ba35/img/interview_2.png?raw=true)
![HR Response Action](https://github.com/cApitanYARE/telegram-hiring-bot-/blob/943851b1dfb4ceac56a62b0f18e82d2b6ed3ba35/img/answear_to_c.png?raw=true)

---

### 🧑‍💼 HR Management & Communication Flow

#### 6. HR Dashboard & Welcome Window
The main entry point for recruiters, offering a structured control panel to add vacancies, check applications, or manage the talent pool.
![Welcome Screen](https://github.com/cApitanYARE/telegram-hiring-bot-/blob/5e4fd2abce8a0c25c43da4e8de0fb3520335dd6b/img/welcome_hr.png)

#### 7. Reviewing Candidate Submissions
HR managers receive structured summaries generated from the AI screening process, allowing them to review parsed skills, profiles, and logs before making a decision.
![Review Candidate](https://github.com/cApitanYARE/telegram-hiring-bot-/blob/943851b1dfb4ceac56a62b0f18e82d2b6ed3ba35/img/response_to_hr.png?raw=true)
![Review Details](https://github.com/cApitanYARE/telegram-hiring-bot-/blob/943851b1dfb4ceac56a62b0f18e82d2b6ed3ba35/img/response_to_hr_2.png?raw=true)

#### 8. Sending Feedback to Candidates
Recruiters can accept, reject, or message the candidate directly from the Telegram interface.

**HR Input View:**
The recruiter inputs their decision or commentary for the specific applicant:
![Candidate Notification](https://github.com/cApitanYARE/telegram-hiring-bot-/blob/943851b1dfb4ceac56a62b0f18e82d2b6ed3ba35/img/from_hr_to_c.png?raw=true)

**Candidate Notification View:**
The candidate instantly receives a cleanly formatted notification containing the vacancy details and the HR's feedback:
![HR Response Action](https://github.com/cApitanYARE/telegram-hiring-bot-/blob/943851b1dfb4ceac56a62b0f18e82d2b6ed3ba35/img/answear_to_c.png?raw=true)

## 📦 Getting Started

### Prerequisites
Make sure you have the following installed on your machine:
- Python 3.10+
- PostgreSQL
- Redis

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/cApitanYARE/telegram-hiring-bot-
   cd telegram-hiring-bot-
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/macOS
   # Or on Windows: venv\Scripts\activate
   ```

3. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   Create a `.env` file in the root directory and populate it with your credentials:
   ```env
   BOT_TOKEN=your_telegram_bot_token
   OPENAI_API_KEY=your_openai_api_key
   DATABASE_URL=postgresql://user:password@localhost:5432/db_name
   REDIS_HOST=localhost
   REDIS_PORT=6379
   ```

---

## 🚀 Usage
To start the Telegram bot, run the following command from the root directory:

```bash
python -m bot.aiogram_run
```
