from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.utils import timezone

from datetime import datetime, timedelta
from decimal import Decimal
import pandas as pd
import pickle
import requests
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--incognito')
options.add_argument('--headless')
driver = webdriver.Chrome(
    "/home/ola/chrome_driver/chromedriver_linux64/chromedriver", chrome_options=options)

from .models import Hotel, HotelPrice, HotelReview


def index(request):
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    # print(yesterday)
    # for i in HotelPrice.objects.all():
    #     i.scrape_date = yesterday
    #     i.save()
    return render(request, 'index.html')

def view_hidden(url, class_name):
    print('driver')
    driver.get(url)
    more_buttons = driver.find_elements_by_class_name(class_name)
    for x in range(len(more_buttons)):
        if more_buttons[x].is_displayed():
            if more_buttons[x].find_element(By.TAG_NAME, "span").get_attribute('innerText') == 'Read all reviews':
                print('found it')
                # driver.execute_script("arguments[0].click();", more_buttons[x])
                more_buttons[x].click() 
                print(more_buttons[x]) 
                print('clicked it')
                # time.sleep(10) 
                try:
                    element = WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (By.CLASS_NAME, "review_list_new_item_block"))
                    )
                    print(element[:50])
                finally:
                    driver.quit()
                revs = driver.find_elements_by_class_name(
                    'review_list_new_item_block')
                print(revs[:10])
                print('hhh')
                page_source = driver.page_source.encode('utf-8')
                return page_source

def scrape_hotels(request):
    if request.method == "POST":
        # items = list()
        url = 'https://www.booking.com/country/nl.en-gb.html?label=gen173nr-1DCAIoqQE4F0gzWARopwGIAQGYAQm4ARnIAQzYAQPoAQGIAgGoAgO4Apmfs5QGwAIB0gIkMDJmZTNiOTAtZjg3ZS00ZjQ5LTgwZmEtZDliNzZhMTFmZjEw2AIE4AIB&sid=ab2dc835adae11bafb9a0def6023959d&keep_landing=1&'
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
                        item_url = hotel.find('div', {
                            'class': 'sr__card_main'
                        }).find('a').get('href')
                        reviews = []
                        features = [] 
                        room_price = []
                        new_hotel, created = Hotel.objects.get_or_create(
                            name=description,
                            location=location,
                            defaults={
                                'description': title,
                                'features': features,
                                'average_price': price,
                                'average_rating': Decimal(ratings)
                            } 
                        )
                        new_price = HotelPrice.objects.create(
                            hotel=new_hotel,
                            room='Average',
                            price=price,
                            availability=-100
                        )
                        today = timezone.now()
                        month = today.month
                        day = today.day
                        year = today.year
                        next_three_days = today + timedelta(days=3)
                        month_3 = next_three_days.month
                        day_3 = next_three_days.day
                        year_3 = next_three_days.year
                        url_add = (f"&checkin_month={month}&checkin_monthday={day}"
                            f"&checkin_year={year}&checkout_month={month_3}"
                            f"&checkout_monthday={day_3}&checkout_year={year_3}"
                            f"&dist=0&do_availability_check=1&group_adults=2"
                            f"&group_children=0&hp_avform=1&hp_group_set=0&hp_sbox=1"
                            f"&no_rooms=1&origin=hp&sb_price_type=total&src=hotel"
                            f"&stay_on_hp=1&type=total")
                        # url_add = '&checkin_month=6&checkin_monthday=15&checkin_year=2022&checkout_month=6&checkout_monthday=16&checkout_year=2022&dist=0&do_availability_check=1&group_adults=2&group_children=0&hp_avform=1&hp_group_set=0&hp_sbox=1&no_rooms=1&origin=hp&sb_price_type=total&src=hotel&stay_on_hp=1&type=total'
                        # two_weeks = requests.get(f"{main_url}{item_url}{url_add}")

 
                        if new_hotel: 
                            if item_url:
                                # print(f"{main_url}{item_url}?{url_add}")
                                item_code = requests.get(f"{main_url}{item_url}?{url_add}")
                                item_plain = item_code.text
                                the_hotel = BeautifulSoup(item_plain, "html.parser")
                                # html = the_hotel.prettify()
                                # print('start')
                                # with open("out.txt", "w", encoding='utf-8') as out:
                                #     for i in range(0, len(html)):
                                #         try:
                                #             out.write(html[i])
                                #         except Exception:
                                #             1+1
                                #             pass 
                                # print('stop')
                                for feature in the_hotel.findAll('div', {'class': 'important_facility'}):
                                    features.append((feature.contents[2]).strip())
                                new_hotel.features = features
                                new_hotel.save()
                                # print('features') 
                                # kkk = the_hotel.findAll(
                                #     'li', {'class': 'review_list_new_item_block'})
                                # print(len(kkk)) 
                                # # get hidden reviews
                                # page_source = view_hidden(
                                #     f"{main_url}{item_url}", 'bui-button--secondary')
                                # # print(page_source)
                                # soup = BeautifulSoup(page_source, 'lxml')
                                # print('soup')
                                # ll = soup.findAll(
                                #     'li')
                                # print(len(ll)) 
                                # # print(ll[:500]) 
                                # for review in soup.findAll('li', {'class': 'review_list_new_item_block'}):
                                #     print(review)
                                #     score = review.find(
                                #         'span', {'class': 'bui-review-score__badge'})
                                #     the_comment = []
                                #     for i in review.findAll(
                                #         'span', {'class': 'c-review__body'}):
                                #         the_comment.append(i.string)
                                #     # reviews.append({'score': score, 'comments': the_comment})
                                #     print('here')
                                #     print(the_comment)
                                #     ll = HotelReview.objects.create(
                                #         hotel=new_hotel,
                                #         rating=Decimal(score),
                                #         review=the_comment
                                #     ) 
                                #     print(ll)
                                #     # reviews = f"{reviews}\n{review}"
                                for review in the_hotel.findAll('div', {'data-testid': 'featuredreview'}):
                                    score = review.find(
                                        'span', {'class': 'bui-review-score__badge'})
                                    if score is None:
                                        score = -100.0
                                    the_comment = []
                                    for i in review.findAll(
                                            'div', {'data-testid': 'featuredreview-text'}):
                                        the_comment.append(i.get_text())
                                    # print('here')
                                    ll = HotelReview.objects.create(
                                        hotel=new_hotel,
                                        rating=Decimal(score),
                                        review=the_comment
                                    )
                                    # print(ll)
                                no_avail = the_hotel.find(
                                    'div', {'id': 'no_availability_msg'})
                                if no_avail:
                                    new_price.room='fully booked'
                                    new_price.availability=0
                                    new_price.save() 
                                # lll = the_hotel.findAll(
                                #     'tr', {'class': 'e2e-hprt-table-row'})
                                # print('rooms')
                                # print(len(lll))
                                for room in the_hotel.findAll('tr', {'class': 'e2e-hprt-table-row'}):
                                    name = room.find(
                                        'span', {'class': 'hprt-roomtype-icon-link'}).string
                                    print('name')
                                    print(name)
                                    price = room.find('div', {
                                                    'class': 'bui-price-display__value'}).find('span').string
                                    rooms_left = room.find('div', {
                                        'class': 'bui-price-display__value'}).find('span').string
                                    room_price.append({'room': name, 'price': price, 'availability': rooms_left})
                                    HotelPrice.objects.create(
                                        hotel=new_hotel,
                                        room=name,
                                        price=price,
                                        availability=rooms_left
                                    )
        # messages.add_message(request, messages.INFO, 'Hello world.')
        return HttpResponseRedirect('/')


def update_prices(request):
    if request.method == "POST":
        url = 'https://www.booking.com/country/nl.en-gb.html?label=gen173nr-1DCAIoqQE4F0gzWARopwGIAQGYAQm4ARnIAQzYAQPoAQGIAgGoAgO4Apmfs5QGwAIB0gIkMDJmZTNiOTAtZjg3ZS00ZjQ5LTgwZmEtZDliNzZhMTFmZjEw2AIE4AIB&sid=ab2dc835adae11bafb9a0def6023959d&keep_landing=1&'
        url_split = url.split('/')
        protocol = url_split[0]
        domain = url_split[2]
        main_url = f"{protocol}//{domain}"
        code = requests.get(url)
        plain = code.text
        web_page = BeautifulSoup(plain, "html.parser")
        for heading in web_page.findAll('div', {'class': 'lp-bui-section'}):
            list_items = heading.findAll('a', {'class': 'bui-card'})
            for card in list_items:
                try:
                    location = card.find(
                        'h3', {'class': 'bui-card__title'}).string
                except AttributeError:
                    location = 'Nil'
                next_url = card.get('href')
                if next_url:
                    code = requests.get(f"{main_url}{next_url}")
                    plain = code.text
                    s = BeautifulSoup(plain, "html.parser")
                    for hotel in s.findAll('div', {'class': 'sr__card'}):
                        try:
                            description = hotel.find(
                                'span', {'class': 'bui-card__title'}).string
                        except AttributeError:
                            description = 'Nil'
                        try:
                            price = hotel.find(
                                'div', {'class': 'bui-price-display__value'}).string
                        except AttributeError:
                            price = 'Nil'
                        item_url = hotel.find('a').get('href')
                        room_price = []
                        try:
                            new_hotel = Hotel.objects.get(
                                name=description,
                                location=location,
                            )  
                            HotelPrice.objects.create(
                                hotel=new_hotel,
                                room='Average',
                                price=price,
                                availability=-100
                            )
                            if item_url:
                                item_code = requests.get(
                                    f"{main_url}{item_url}")
                                item_plain = item_code.text
                                the_hotel = BeautifulSoup(
                                    item_plain, "html.parser")
                                for room in the_hotel.findAll('tr', {'class': 'js-rt-block-row e2e-hprt-table-row'}):
                                    name = room.find(
                                        'span', {'class': 'hprt-roomtype-icon-link'}).string
                                    price = room.find('div', {
                                        'class': 'bui-price-display__value'}).find('span').string
                                    rooms_left = room.find('div', {
                                        'class': 'bui-price-display__value'}).find('span').string
                                    room_price.append(
                                        {'room': name, 'price': price, 'availability': rooms_left})
                                    HotelPrice.objects.create(
                                        hotel=new_hotel,
                                        room=name,
                                        price=price,
                                        availability=rooms_left
                                    )
                        except Hotel.DoesNotExist:
                            pass
        return HttpResponseRedirect('/')

def hotel_summary(request):
    labels = []
    data_price = []
    data_rating = []
    today = timezone.now().date()
    yesterday = today - timedelta(days=2)
    stripped_price = sorted(HotelPrice.objects.filter(
        scrape_date__gte=yesterday).exclude(price='Nil'), key=lambda t: t.strip_price)
    stripped_price_reverse = sorted(HotelPrice.objects.filter(
        scrape_date__gte=yesterday).exclude(price='Nil'), key=lambda t: t.strip_price, reverse=True)

    # queryset = stripped_price_reverse[:100]
    for hotel_price in stripped_price_reverse[:25]:
        if not hotel_price.hotel.name in labels:
            labels.append(hotel_price.hotel.name)
            data_price.append(int(hotel_price.price[1:]))
            data_rating.append(float(hotel_price.hotel.average_rating))
    for hotel_price in stripped_price[:25]:
        if not hotel_price.hotel.name in labels:
            labels.append(hotel_price.hotel.name)
            data_price.append(int(hotel_price.price[1:]))
            data_rating.append(float(hotel_price.hotel.average_rating))
    highest_rate = stripped_price_reverse[0:5]
    lowest_rate = stripped_price[0:5]
    context = {
        'labels': labels,
        'data_price': data_price,
        'data_rating': data_rating,
        # 'object_list': queryset,
        'highest_rate': highest_rate,
        'lowest_rate': lowest_rate,
    }
    return render(request, 'summary.html', context)