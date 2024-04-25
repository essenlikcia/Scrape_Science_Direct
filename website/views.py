import os
import requests

from django.shortcuts import render
from dotenv import load_dotenv
from bs4 import BeautifulSoup

from .models import Record, Author


def home(request):
    return render(request, 'home.html', {})


'''def search(request):
    records = Record.objects.all()
    return render(request, 'search_results.html', {'records': records})'''


load_dotenv()


def search(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        articles_number = int(request.POST.get('articles'))
        api_key = os.getenv('API_KEY')

        # Delete all records from the tables (assuming you want fresh data)
        Record.objects.all().delete()
        Author.objects.all().delete()

        url = f"https://api.elsevier.com/content/search/sciencedirect?query={query}&apiKey={api_key}"

        articles = []
        for i in range(0, articles_number, 100):
            if articles_number == 25:
                url = url
            elif articles_number == 50:
                url += f"&count=50&offset={i}&apiKey={api_key}"
            elif articles_number >= 100:
                url += f"&count=100&offset={i}&apiKey={api_key}"

            response = requests.get(url)
            data = response.json()
            articles.append(data)

        papers = []
        for data in articles:
            for item in data['search-results']['entry']:
                title = item['dc:title']
                authors = ', '.join(
                    author.get('$', '') if isinstance(author, dict) else '' for author in item['authors']['author']) \
                    if isinstance(item['authors'], dict) and 'author' in item['authors'] else 'N/A'
                date = item['prism:coverDate']
                article_url = item['link'][1]['@href']

                # Scrape corresponding author details using BeautifulSoup
                response = requests.get(article_url)
                soup = BeautifulSoup(response.content, 'html.parser')

                # Find the author information div
                author_div = soup.find('div', class_='author-group')

                # Extract author names (assuming one author per button)
                corresponding_author_names = []
                if author_div:
                    for button in author_div.find_all('button'):
                        button_link_text_span = button.find('span', class_='button-link-text')  # Find the outer span
                        if button_link_text_span:
                            author_name_element = button_link_text_span.find('span', class_='react-xocs-alternative-link')  # Find the inner span
                            if author_name_element:
                                author_name = author_name_element.text.strip()
                                corresponding_author_names.append(author_name)

                corresponding_author_name = ', '.join(
                    corresponding_author_names) if corresponding_author_names else 'N/A'

                corresponding_author_email = None
                email_element = soup.select_one("#side-panel-author > div.e-address > a > span")
                if email_element:
                    corresponding_author_email = email_element.text.strip()
                else:
                    corresponding_author_email = 'N/A'
                papers.append({
                    'title': title,
                    'authors': authors,
                    'date': date,
                    'url': article_url,
                    'corresponding_author': corresponding_author_name,
                    'corresponding_author_email': corresponding_author_email,
                })

        for paper in papers:
            authors_list = paper['authors'].split(', ')
            authors_objs = []
            for author_name in authors_list:
                author, created = Author.objects.get_or_create(name=author_name.strip())
                authors_objs.append(author)
            record = Record.objects.create(
                title=paper['title'],
                corresponding_author=paper['corresponding_author'],
                corresponding_author_email=paper['corresponding_author_email'],
                date=paper['date']
            )
            record.authors.add(*authors_objs)

        records = Record.objects.all()
        return render(request, 'search_results.html', {'records': records})
    else:
        return render(request, 'home.html', {})

