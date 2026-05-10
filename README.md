# Pooja Room

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?logo=css3&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?logo=javascript&logoColor=black)
![Supabase](https://img.shields.io/badge/Supabase-3ECF8E?logo=supabase&logoColor=white)
![Vercel](https://img.shields.io/badge/Vercel-000000?logo=vercel&logoColor=white)

Pooja Room is a digital library for Hindu prayers. Access prayers across 19 different languages with YouTube audios.

[![Live Demo](https://img.shields.io/badge/LIVE_WEBSITE-pooja--room.vercel.app-black?style=for-the-badge&logo=vercel)](https://pooja-room.vercel.app)

---

## A Look Inside

![Pooja Room Screenshot](./static/assets/front_image.png)

## Video Demo
[![Pooja Room Demo](https://img.shields.io/badge/YouTube-Watch_Demo-FF0000?logo=youtube&style=for-the-badge)](https://youtu.be/QUTExqvcWFI?si=LsGpG5GAycHDAQyE)

---

## Features
* **Massive Library:** 1,164 prayers ready to read.
* **19 Languages:** Read the prayers in the language you know best.
* **YouTube Audio:** Every prayer automatically plays a YouTube recitation.
* **Personal Dashboard:** Create an account to track your daily prayers and build a routine.

## Technologies
* **Frontend:** HTML, CSS, and plain JavaScript. 
* **Backend:** Supabase (for user accounts, database, and storage).
* **Hosting:** Vercel.
* **Automation:** Python (for scraping prayers in 19 different languages and assigning corresponding YouTube links).

---

## Project Structure & File Descriptions
### Frontend Pages (HTML/CSS)
* `index.html`: The landing page that introduces the app.
* `login.html`, `register.html`, `confirm-email.html`: The authentication flow. These pages connect directly to Supabase to handle sign-ups and logins.
* `dashboard.html`: The user hub. Once logged in, this page shows the user's specific prayer schedule.
* `schedule.html` & `settings.html`: Pages for users to build their daily prayer routines and manage their account preferences.
* `library.html`: A library for all 1,164 prayers from the database that users can search through.
* `prayer.html`: This is a dynamic template. Instead of making 1,164 individual HTML pages, this one file reads the URL, gets the correct prayer data from Supabase, embeds the YouTube video, and formats the lyrics into the user's chosen language.
* `style.css`: Contains all the styling for the app.

### Application Scripts (JavaScript)
* `app.js`: The JavaScript file that manages user sessions, tracks prayer schedules, and gets data from the Supabase database.
* `navbar.js`: Handles the navbar UI, making sure logged-in users see different menu options than logged-out users.
* `config.js`: Holds the Supabase keys to safely connect the frontend to the backend.

### Backend Automation (Python)
* `scraper.py`: The initial Python script used to scrape the raw prayer texts across 19 languages  and format them into JSON.
* `youtube_sync.py`: A  script that loops through the database, searches YouTube, filters the results, and assigns the best video ID to each prayer.
* `requirements.txt`: Lists the Python libraries needed to run the scripts.
* `vercel.json`: A configuration file that tells Vercel how to host the site.

---

## Design Choices and Challenges
### 1. Web Scraping and IP Bans
My first major challenge was getting the text for the prayers. I wrote `scraper.py` to pull data from online prayer archives. However, because I was requesting thousands of pages to get all 19 language translations, the server flagged my script as a bot and banned my IP address. I had to remake the scraper to act more like a human. I added sleep delays between requests and custom user-agent headers. This slowed down the scraping process significantly, but I was able to safely scrape all the prayers.

### 2. Linking Transcripts
Originally, I had an ambitious idea: I wanted the website to act like a karaoke machine. My plan was to take the AI-generated transcript from the YouTube video and match it to the prayer text. As the video played, the corresponding lines of text on my website would highlight automatically. 

After testing, I realized this was very impractical. Many YouTube videos don't have transcripts at all. For the ones that do, the auto-generated captions spell words very differently than the formal IAST (International Alphabet of Sanskrit Transliteration) text in my database. Writing an algorithm to perfectly match two completely different spelling systems was out of scope. I made the design choice to scrap the highlighting feature and go to a simpler layout where the video sits at the top and the user scrolls the text regularly.

### 3. YouTube Embedding and Strict Validation
The biggest challenge was syncing YouTube videos to the 1,164 prayers. I couldn't do this manually, so I built `youtube_sync.py`. At first, the script just searched the prayer name and grabbed the #1 result. 

This caused massive problems. First, major music channels like TSeries block embedding on their official videos, so my website was full of "Video Unavailable" errors. Second, YouTube's search algorithm often ignores the actual search term and just serves viral videos instead (e.g., getting a 400-million-view prayer video when searching for a different, lesser-known prayer).

Subsequently, I created a strict set of rules each scraped video must of adhered to.
1. **The Embed Check:** The script checks the metadata of the top 15 results and instantly discards any video where `playable_in_embed` is false.
2. **Keyword Filtering:** The script strips the prayer title down to its unique identifying words (ignoring generic terms). It then has a check against the YouTube title. If the YouTube title doesn't contain the specific unique keyword, it is discarded from the choices. 
