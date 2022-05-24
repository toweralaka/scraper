from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

import pandas as pd
import requests
from bs4 import BeautifulSoup

class RoomItem:
    """
    A general class to hotel data data concisely.
    """

    def __init__(self, title, location, description, price, ratings, comments):
        self.title = title
        self.location = location
        self.description = description
        self.price = price
        self.ratings = ratings
        self.comments = comments


def web(WebUrl):
    items = list()
    url = WebUrl
    url_split = url.split('/')
    protocol = url_split[0]
    domain = url_split[2]
    main_url = f"{protocol}//{domain}"
    code = requests.get(url)
    plain = code.text
    web_page = BeautifulSoup(plain, "html.parser")
    for heading in web_page.findAll('div', {'class': 'lp-bui-section'}):
        try:
            title = heading.find('h2').string
        except AttributeError:
            title = 'Nil'
        list_items = heading.findAll('a', {'class': 'bui-card'})
        for card in list_items:
            try:
                location = card.find('h3', {'class': 'bui-card__title'}).string
            except AttributeError:
                location = 'Nil'
            next_url = card.get('href')
            if next_url:
                code = requests.get(f"{main_url}{next_url}")
                plain = code.text
                s = BeautifulSoup(plain, "html.parser")
                for hotel in s.findAll('div', {'class':'sr__card'}):
                    try:
                        description = hotel.find('span', {'class': 'bui-card__title'}).string
                    except AttributeError:
                        description = 'Nil'
                    try:
                        price = hotel.find('div', {'class': 'bui-price-display__value'}).string
                    except AttributeError:
                        price = 'Nil'
                    try:
                        ratings = hotel.find('div', {'class': 'bui-review-score__badge'}).string
                    except AttributeError:
                        ratings = 'Nil'
                    try:
                        comment1 = hotel.find('p',{'class': 'bui-card__text'}).string
                    except AttributeError:
                        comment1 = 'Nil'
                    try:
                        comment2 = hotel.find('span',{'class': 'hotel-card__text_review'}).string
                    except AttributeError:
                        comment2 = 'Nil'
                    comments = f"{comment1}/n{comment2}"
                    item = RoomItem(title, location, description, price, ratings, comments)
                    items.append(item)
    return items


def index(request):
    if request.method == "POST":
        url = request.POST.get('url')
        if url[0:4] == 'http':
            try:
                items = web(url) 
                df = pd.DataFrame(
                    {
                        "LOCATION": [item.location for item in items],
                        "NAME": [item.description for item in items],
                        "PRICE": [item.price for item in items],
                        "RATINGS": [item.ratings for item in items],
                        "REVIEWS": [item.comments for item in items],
                        "RANKING": [item.title for item in items]
                    }
                )
                response = HttpResponse(headers={
                        'Content-Type': 'text/csv',
                        'Content-Disposition': 'attachment; filename="scraped.csv"',
                    })
                df.to_csv(path_or_buf=response, index=False)
                return response
            except Exception as e:
                print(e)
                return HttpResponseRedirect('/')
        else:
            return HttpResponseRedirect('/')
    return render(request, 'index.html')
