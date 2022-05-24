from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

# Create your views here.

import pandas as pd
import requests
from bs4 import BeautifulSoup

class RoomItem:
    """
    A general class to hotel data data concisely.
    """

    # def __init__(self, description, price, misc):
    #     self.description = description
    #     self.price = price
    #     self.misc = misc
    def __init__(self, name, price, manufacturer):
        self.name = name
        self.price = price
        self.manufacturer = manufacturer


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
    for pg in web_page.findAll('a', {'class':'pg'}):
        next_url = pg.get('href')
        if next_url:
            code = requests.get(f"{main_url}{next_url}")
            plain = code.text
            s = BeautifulSoup(plain, "html.parser")
            for link in s.findAll('a', {'class':'core'}):
                name = link.get('data-name')
                price = link.get('data-price')
                manufacturer = link.get('data-brand')
                item = RoomItem(name, price, manufacturer)
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
                        "name": [item.name for item in items],
                        "price": [item.price for item in items],
                        "manufacturer": [item.manufacturer for item in items],
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
