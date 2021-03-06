import requests
import os
from bs4 import BeautifulSoup
import json

WIDTH = "226"
IMAGES_PER_PAGE = 30
REST_PER_PAGE = 10
new_city_url = "https://en.yelp.com.hk/search?find_loc=urbana&start="
s = requests.session()


def find_page_number(webpage):
    num_pages = webpage.find("div", {"class": "page-of-pages"})
    if num_pages:
        num_pages = int(str(num_pages).split("Page 1 of ")[1].strip("</div>"))
    elif "404" in str(webpage.find("title")):
        num_pages = 0
    else:
        num_pages = 1
    return num_pages


def fetch_restaurant(url):
    links = []
    r = s.get(url)
    webpage = BeautifulSoup(r.content, 'lxml')
    num_pages = find_page_number(webpage)

    for i in range(1, num_pages + 1):
        for link in webpage.find_all('img'):
            source = str(link.get('src'))
            if str(link.get('width')) == WIDTH:
                links.append(source)
        next_page = url + "?start=" + str(i * IMAGES_PER_PAGE)
        r = s.get(next_page)
        webpage = BeautifulSoup(r.content, 'lxml')
    return links


def save_file(filename, link):
    r = s.get(link)
    f = open(filename, 'wb')
    f.write(r.content)
    f.close()


def search_city(city_url):
    restaurants = []
    r = s.get(city_url)
    webpage = BeautifulSoup(r.content, 'lxml')
    num_pages = find_page_number(webpage)

    for i in range(1, num_pages + 1):
        for link in webpage.find_all('a'):
            if str(link.get('data-analytics-label')) == "biz-name":
                restaurants.append(str(link.get('href')))
        next_page = new_city_url + str(i * REST_PER_PAGE)
        r = s.get(next_page)
        webpage = BeautifulSoup(r.content, 'lxml')

        print("finish searching restaurant urls on page: {}/{}".format(i, num_pages))
    return restaurants


def save_from_url(url):
    restaurants = search_city(url)
    fout = open("restaurant_url.txt", "w")
    for item in restaurants:
        fout.write("%s\n" % item)
    fout.close()
    print("============ finish writing restaurant URLs ============")
    return restaurants


def save_from_file(filename):
    return open(filename).readlines()

def getName(name):
    name = name.lower().split(' ')
    name = [x for x in name if x != '']
    name = '-'.join(name)
    name = name.replace('&', "and").replace("'", "").replace(",", "").replace(".", "")
    return name

def generateResNames(city):
    restaurantsNames = []
    cityName = getName(city)
    with open("../data/" + city + ".json", 'r') as fileHandle:
        restaurants = json.load(fileHandle)
        for restaurant in restaurants:
            joinedName = '-'.join([getName(restaurant["name"]), cityName])
            restaurantsNames.append({"name": joinedName, "id": restaurant["business_id"]})
    return restaurantsNames

def main(city, counter = 0, restaurantNum = 0):
    restaurants = generateResNames(city)
    total_num_restaurants = len(restaurants)
    current_restaurant = restaurantNum
    mapping = dict()
    folder_name = city + "_photos"
    photo_file_handle = open(city + "_photos_info.json", "a+")
    problem_file_handle = open(city+"problems.json", "a+")
    os.makedirs(folder_name)
    for restaurant in restaurants[restaurantNum:]:
        mapping[restaurant["id"]] = []
        current_restaurant += 1
        print("save photos progress: {}/{}".format(current_restaurant, total_num_restaurants))
        # folder_name = restaurant["id"]
        # if not os.path.exists(folder_name):
        #     os.makedirs(folder_name)
        # else:
        #     print("find restaurant exists!")
        #     continue

        biz_photo_url = "https://en.yelp.com.hk/biz_photos/" + restaurant["name"] + "?tab=food"
        urls = fetch_restaurant(biz_photo_url)
        if len(urls) == 0:
            problem_file_handle.write(json.dumps(restaurant, indent = 4))
            problem_file_handle.write(",\n")
            print "No information for " + restaurant["name"]
        else:
            for link in urls:
                fileName = restaurant["id"] + str(counter) + '.jpg'
                mapping[restaurant["id"]].append(fileName)
                filePath = folder_name + '/' + fileName
                save_file(filePath, link)
                photo_file_handle.write(json.dumps([restaurant["id"], fileName], indent = 4))
                photo_file_handle.write(",\n")
                counter += 1
    photo_file_handle.close()
    problem_file_handle.close()
    with open(city + "mapping" + ".json", 'w') as writeFile:
        strData = json.dumps(mapping, indent = 4)
        writeFile.write(strData)
    print "finish"

if __name__ == "__main__":
    # main(cityName, imageSequenceNumber, resaurantSequenceNumber), in case the program stopped unexpectedly
    # you can resume at a specific restaurant
    main(city = "Cleveland", counter = 1, restaurantNum = 0)

