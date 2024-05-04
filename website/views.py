import os
import requests

from django.shortcuts import render
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from .models import Record, Author
from .utils.soup_helper import get_parsed_html


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

        if not query:
            return render(request, 'home.html', {'error': 'Please enter a search query.'})

        articles_number = int(request.POST.get('articles', 25))
        custom_articles_number = request.POST.get('custom_articles')
        Record.objects.all().delete()
        Author.objects.all().delete()
        url = f"https://api.elsevier.com/content/search/sciencedirect?query={query}&apiKey={api_key}"

        if custom_articles_number:
            articles_number = int(custom_articles_number)

        articles = []
        for i in range(0, articles_number, 100):
            if articles_number == 25:
                url = url
            elif articles_number == 50:
                url += f"&count=50&offset={i}&apiKey={api_key}"
            elif articles_number == 100:
                url += f"&count=100&offset={i}&apiKey={api_key}"

            response = requests.get(url)
            data = response.json()
            articles.append(data)

        papers = []
        article_count = 0
        for data in articles:
            for item in data['search-results']['entry']:
                if article_count >= articles_number:
                    break

                title = item['dc:title']
                authors = ', '.join(
                    author.get('$', '') if isinstance(author, dict) else '' for author in item['authors']['author']) \
                    if isinstance(item['authors'], dict) and 'author' in item['authors'] else 'N/A'
                date = item['prism:coverDate']
                pii = item['pii']

                print(f"searching article {article_count}...")
                article_count += 1

                corresponding_author_name = search_corresponding_author_name(pii)
                corresponding_author_email = search_corresponding_author_email(corresponding_author_name)

                papers.append({
                    'title': title,
                    'authors': authors,
                    'date': date,
                    'corresponding_author': corresponding_author_name,
                    'corresponding_author_email': corresponding_author_email,
                    'pii': pii
                })
            if article_count >= articles_number:
                break

        for paper in papers:
            authors_list = paper['authors'].split(', ')
            authors_objs = []
            pii = paper['pii']
            for author_name in authors_list:
                orcid_id = None
                if author_name == paper['corresponding_author']:
                    orcid_id = search_corresponding_author_orcid_id(pii)
                author, created = Author.objects.get_or_create(name=author_name.strip(), defaults={'orcid_id': orcid_id})
                authors_objs.append(author)
            record = Record.objects.create(
                title=paper['title'],
                corresponding_author=paper['corresponding_author'],
                corresponding_author_email=paper['corresponding_author_email'],
                date=paper['date'],
                pii=paper['pii']
            )
            record.authors.add(*authors_objs)

        records = Record.objects.all()
        sort_by = request.POST.get('sort_by', 'relevance')
        records = show_articles_by_date(records, sort_by)

        return render(request, 'search_results.html', {'records': records})
    else:
        return render(request, 'home.html', {})


def search_corresponding_author_name(pii):
    pii_url = f"https://api.elsevier.com/content/article/pii/{pii}?apiKey={api_key}"
    soup = get_parsed_html(pii_url)

    author_tags = soup.find_all('ce:author')

    for author_tag in author_tags:
        if author_tag.find('ce:cross-ref', {'refid': "cor1"}) or author_tag.find('ce:cross-ref', {'refid': "cr0005"}):
            given_name = author_tag.find('ce:given-name').text
            surname = author_tag.find('ce:surname').text
            corresponding_author_name = f"{given_name} {surname}"
            return corresponding_author_name

    author_tag = soup.find('ce:author')
    if author_tag is not None:
        return author_tag.find('ce:given-name').text + ' ' + author_tag.find('ce:surname').text
    else:
        return "Author not found."


def search_corresponding_author_orcid_id(pii):
    pii_url = f"https://api.elsevier.com/content/article/pii/{pii}?apiKey={api_key}"
    soup = get_parsed_html(pii_url)

    author_tags = soup.find_all('ce:author')

    for author_tag in author_tags:
        if author_tag.find('ce:cross-ref', {'refid': "cor1"}) or author_tag.find('ce:cross-ref', {'refid': "cr0005"}):
            orcid_id = author_tag.get('orcid')
            if orcid_id:
                return orcid_id
            else:
                return soup.find('ce:author').get('orcid')


def search_corresponding_author_email(corresponding_author_name):
    return "Email not found."


def show_articles_by_date(records, sort_by):
    if sort_by == 'newest':
        records = records.order_by('-date')
    elif sort_by == 'oldest':
        records = records.order_by('date')
    return records
