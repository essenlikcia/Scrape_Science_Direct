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
api_key = os.getenv('API_KEY')


def search(request):
    if request.method == 'POST':
        query = request.POST.get('query')
        articles_number = int(request.POST.get('articles'))
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
        article_count = 1
        for data in articles:
            for item in data['search-results']['entry']:
                title = item['dc:title']
                authors = ', '.join(
                    author.get('$', '') if isinstance(author, dict) else '' for author in item['authors']['author']) \
                    if isinstance(item['authors'], dict) and 'author' in item['authors'] else 'N/A'
                date = item['prism:coverDate']
                article_url = item['link'][1]['@href']
                pii = item['pii']

                print(f"searching article {article_count}...")
                article_count += 1

                corresponding_author_name = search_corresponding_author_name(pii)
                corresponding_author_email = "N/A"

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


def search_corresponding_author_name(pii):
    url = f"https://api.elsevier.com/content/article/pii/{pii}?apiKey={api_key}"
    response = requests.get(url)
    data = response.text
    soup = BeautifulSoup(data, "lxml")

    author_tags = soup.find_all('ce:author')

    for author_tag in author_tags:
        if author_tag.find('ce:cross-ref', {'refid': "cor1"}) or author_tag.find('ce:cross-ref', {'refid':"cr0005"}):
            given_name = author_tag.find('ce:given-name').text
            surname = author_tag.find('ce:surname').text
            corresponding_author_name = f"{given_name} {surname}"
            return corresponding_author_name

    author_tag = soup.find('ce:author')
    return author_tag.find('ce:given-name').text + ' ' + author_tag.find('ce:surname').text


def search_corresponding_author_email():
    pass
