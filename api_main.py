import requests
import time
import csv
import pymongo
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

HOMEPAGE = "https://www.truepeoplesearch.com"
USERNAME = os.getenv("username")
PASSWORD = os.getenv("password")
DB = os.getenv("db")
proxies = {
  'http': 'http://USERNAME:PASSWORD@unblock.oxylabs.io:60000',
  'https': 'http://USERNAME:PASSWORD@unblock.oxylabs.io:60000',
}
headers = {
    "x-oxylabs-geo-location": "United States"
}

server = pymongo.MongoClient(DB)
sdb = server["mydatabase"]
server = sdb["beenverified"]


def filter_arr(array):
    arr = []
    for it in array:
        if it != "":
            arr.append(it)
    return arr
def getfinaldata(link, first, last):
    while 1:
        try:
            response = requests.get(HOMEPAGE + link, headers = headers, proxies = proxies)
            break
        except Exception as e:
            print(e)
            time.sleep(20)

    soup = BeautifulSoup(response.content, 'html.parser')

    jsondata = {}
    try:
        name = soup.find("h1", {"class" : "oh1"}).text
    except:
        name = ""
    
    try:
        div = soup.find("div",{"id" : "personDetails"})
        age_dob = div['data-age']
    except:
        age_dob = ""

    try:
        street = soup.find("span", {"itemprop" : "streetAddress"}).text
        city = soup.find("span", {"itemprop" : "addressLocality"}).text
        state = soup.find("span", {"itemprop" : "addressRegion"}).text
        zip = soup.find("span", {"itemprop" : "postalCode"}).text
    except:
        street = ""
        city = ""
        state = ""
        zip = ""

    email_arr = []
    phone = []
    # items = soup.find_all("div", {"class" : ["col-12", "col-sm-11"]})
    try:
        items = soup.select(".col-12.col-sm-11")
        for item in items:
            text = item.text
            if text.find("Email Addresses") != -1:
                res = text.replace("Email Addresses", "")
                res = res.strip()
                email_arr = res.split("\n")
                email_arr = filter_arr(email_arr)
            elif text.find("Phone Numbers") != -1:
                phs = item.select(".col-12.col-md-6.mb-3")
                for ph in phs:
                    jso = {}
                    number = ph.findChild("span", {'itemprop':'telephone'}).text
                    type = ph.findChild("span", {'class':'smaller'}).text
                    carr = ph.findChildren("span", {'class':'dt-sb'})
                    carrier = carr[len(carr) - 1].text
                    jso["Phone Number"] = number
                    jso["Line Type"] = type
                    jso["Carrier"] = carrier
                    phone.append(jso)
    except:
        email_arr = []
        phone = []

    detail = {}
    try:
        dts = soup.select(".col-6.col-md-3.mb-2")
        for dt in dts:
            res = dt.contents
            attr = res[0].replace("\n","").strip()
            valu = res[2].text
            detail[attr] = valu
    except:
        detail = {}

    jsondata["First Name"] = first
    jsondata["Last Name"] = last
    jsondata["Full Name"] = name
    jsondata["Age"] = age_dob
    jsondata["Phone Detail"] = phone
    jsondata["Street"] = street
    jsondata["City"] = city
    jsondata["State"] = state
    jsondata["PostalCode"] = zip
    jsondata["Email Addresses"] = email_arr
    jsondata["Property Detail"] = detail

    if name != "":
        server.insert_one(jsondata)
        print(jsondata)
    else:
        print("None")
        # getfinaldata(link, first, last)

def getURL(first, last):
    res = server.find_one({"First Name" : first, "Last Name" : last})
    if res != None:
        print("Existing")
        return
    url = "https://www.truepeoplesearch.com/results?name=" + first + "%20" + last + "&page="
    index = 1
    url_array = []
    while 1:
        new_url = url + str(index)
        while 1:
            try:
                response = requests.get(new_url, headers = headers, proxies = proxies)
                if response.status_code != 550:
                    break
            except Exception as e:
                print(e)
                time.sleep(20)
        soup = BeautifulSoup(response.content, 'html.parser')
        results = soup.findAll("div", {"class" : "card-summary"})
        if len(results) == 0:
            break
        for result in results:
            url_array.append(result['data-detail-link'])
        index += 1

    for link in url_array:
        getfinaldata(link, first, last)

def parseList(list):
    for item in list:
        arr = item.split(" ")
        getURL(arr[0], arr[1])
        print(arr[0] + " " + arr[1])

def main():
    names = open('names.csv', 'r', encoding='utf8')
    read = csv.reader(names)
    
    list = []
    for x in read:
        full_name = x[0] + " " + x[1]
        list.append(full_name)

    parseList(list)

if __name__ == '__main__':
    main()    
