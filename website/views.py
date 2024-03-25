import os
import requests

from django.shortcuts import render
from dotenv import load_dotenv

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
        api_key = os.getenv('API_KEY')

        # Delete all records from the tables
        Record.objects.all().delete()
        Author.objects.all().delete()

        articles = []
        for i in range(0, 25, 100):
            url = f"https://api.elsevier.com/content/search/sciencedirect?query={query}&apiKey={api_key}"
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
                papers.append({'title': title, 'authors': authors, 'date': date, 'url': article_url})

        for paper in papers:
            authors_list = paper['authors'].split(', ')
            authors_objs = []
            for author_name in authors_list:
                author, created = Author.objects.get_or_create(name=author_name.strip())
                authors_objs.append(author)

            record = Record.objects.create(
                title=paper['title'],
                corresponding_author=authors_objs[0].name if authors_objs else '',  # Use the first author as the corresponding author
                corresponding_author_email='',
                date=paper['date']
            )

            record.authors.add(*authors_objs)

        records = Record.objects.all()
        return render(request, 'search_results.html', {'records': records})
    else:
        return render(request, 'home.html', {})
