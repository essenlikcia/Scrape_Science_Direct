import os
import re
import csv
import fitz
import requests
from django.contrib import messages

from dotenv import load_dotenv
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Record, Author
from .utils.soup_helper import get_parsed_html


load_dotenv()
api_key = os.getenv('API_KEY')


def home(request):
    """
    Render the home page.
    """
    return render(request, 'home.html', {})


def search(request):
    """
    Handle search requests and fetch articles from the API based on the query.
    """
    if request.method == 'POST':
        query = request.POST.get('query')
        if not query:
            return render(request, 'home.html', {'error': 'Please enter a search query.'})

        articles_number = int(request.POST.get('articles', 25))
        custom_articles_number = request.POST.get('custom_articles')
        Record.objects.all().delete()
        Author.objects.all().delete()

        if custom_articles_number:
            articles_number = int(custom_articles_number)

        articles = []
        for i in range(0, articles_number, 100):
            count = min(100, articles_number - i)
            url = (f"https://api.elsevier.com/content/search/sciencedirect?query={query}&count={count}"
                   f"&offset={i}&apiKey={api_key}")

            response = requests.get(url)
            data = response.json()
            articles.append(data)

        papers = extract_papers(articles, articles_number)
        save_papers_to_db(papers)

        records = Record.objects.all()
        sort_by = request.POST.get('sort_by', 'relevance')
        records = show_articles_by_date(records, sort_by)

        return render(request, 'search_results.html', {'records': records})
    else:
        return render(request, 'home.html', {})


def extract_papers(articles, articles_number):
    """
    Extract paper details from the API response.
    """
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
            corresponding_author_email = "Upload PDF file to scan"

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

    return papers


def save_papers_to_db(papers):
    """
    Save the extracted paper details into the database.
    """
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


def search_results(request):
    """
    Render the search results page with all records.
    """
    records = Record.objects.all()
    context = {'records': records}

    return render(request, 'search_results.html', context)


def upload_pdf(request):
    """
    Handle the PDF upload and extract the corresponding author's email.
    """
    if request.method == 'POST' and request.FILES.get('pdf'):
        record_id = request.POST.get('record_id')
        pdf = request.FILES['pdf']
        fs = FileSystemStorage()
        filename = fs.save(pdf.name, pdf)
        email = extract_email_from_pdf(fs.path(filename))

        if email:
            record = Record.objects.get(id=record_id)
            record.corresponding_author_email = email
            record.save()
            messages.success(request, 'Email extracted and record updated successfully.')
        else:
            messages.error(request, 'Email extraction failed. Please check the PDF.')

        records = Record.objects.all()

        return render(request, 'search_results.html',
                      {'records': records, 'corresponding_author_email': email})

    return render(request, 'search_results.html', {'records': Record.objects.all()})


def extract_email_from_pdf(file_path):
    """
    Extract the corresponding author's email from the PDF.
    """
    doc = fitz.open(file_path)
    email_pattern = re.compile(
        r'Corresponding author\.\s*E-mail addresses?:\s*\S+\s*\(\S+\.\s+\S+\),\s*(\S+@\w+\.\w+)\s*\(\S+\.\s+\S+\)'
    )
    email = None

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text = page.get_text("text")
        match = email_pattern.search(text)
        if match:
            email = match.group(1)
            break

    return email


def download_csv(request):
    """
    Download all records as a CSV file.
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="articles.csv"'

    writer = csv.writer(response)
    writer.writerow(['Id', 'Created At', 'Title', 'Authors', 'Corresponding Author',
                     'Corresponding Author Email', 'Date', 'PII'])

    records = Record.objects.all()
    for record in records:
        authors = ", ".join([author.name for author in record.authors.all()])
        writer.writerow([record.id, record.created_at, record.title, authors, record.corresponding_author,
                         record.corresponding_author_email, record.date, record.pii])

    return response


def search_corresponding_author_name(pii):
    """
    Search for the corresponding author's name using the PII.
    """
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
    """
    Search for the corresponding author's ORCID ID using the PII.
    """
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


def show_articles_by_date(records, sort_by):
    """
    Sort the records by date.
    """
    if sort_by == 'newest':
        records = records.order_by('-date')
    elif sort_by == 'oldest':
        records = records.order_by('date')

    return records
