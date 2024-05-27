# Scrape Science Direct 🕵️‍♂️

A web scraping project based on the Django framework. The aim of the project is to scrape article information from sciencedirect.com

## Tech Stack 🚀

- Django Framework
- MySQL
- Docker

## Features 🌟

- 📜 Fetch the amount of articles desired from Science Direct, optionally sort them by date
- 🔗 Go to the corresponding author's ORCID page from results
- 📧 Get the email of the corresponding author by uploading the PDF file of the article from the Science Direct website
- 📥 Download results as CSV
- 🌙 Dark mode

## Requirements 📋

- 🔑 API key from Elsevier Developer Portal
- 🏫 Academic institution Network

## Installation 🛠️

1. Clone the repository:
    ``` Powershell
    git clone https://github.com/essenlikcia/Scrape_Science_Direct.git
    cd Scrape_Science_Direct
    ```
2. Add your API Key and Database Info to your `.env` file. The file should be in project root and look like this:
	``` .env
    MYSQL_ROOT_PASSWORD=your_mysql_root_password
    
    DATABASE_ENGINE=django.db.backends.mysql
    DATABASE_NAME=webscraperdb
    DATABASE_USER=your_database_user
    DATABASE_PASSWORD=your_database_password
    DATABASE_HOST=db
    DATABASE_PORT=3306
    
    API_KEY=your_elsevier_api_key
	```

## How To Run ▶️

1. Build the Docker container:
    `docker-compose build`
2. Start the application:
    `docker-compose up`

## Usage 💻

1. Open http://localhost:8080/ in your browser
2. Enter article title that you want to search

