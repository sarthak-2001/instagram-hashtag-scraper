import csv
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
import pandas as pd
from selenium.webdriver.chrome.options import Options


# Global variables

print("EXTRACTOR WITH TIMEFRAME")
tag = input("Provide Tag : ")
filename = input("Provide filename : ")
filename = filename+'.csv'

url = "https://www.instagram.com/explore/tags/" + tag + "/"

records = int(input('Provide number of entries : '))

t1 = input("Enter starting time in format YYYY-MM-DD HH:MM:SS - ") #starting(smaller)
# t2 = "2019-10-18 15:17:32" #ending (larger)(recent)
t2 = input("Enter ending time in format YYYY-MM-DD HH:MM:SS - ") #ending (larger)(recent)
t1obj = datetime.strptime(t1,'%Y-%m-%d %H:%M:%S')
t1obj+=timedelta(hours=4)  #utc
t2obj = datetime.strptime(t2,'%Y-%m-%d %H:%M:%S')
t2obj+=timedelta(hours=4)

chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')
try:
    driver = webdriver.Chrome("./chromedriver.exe",chrome_options=chrome_options)  # chromedriver path
except:
    driver = webdriver.Chrome("./chromedriver",chrome_options=chrome_options)  # chromedriver path

# driver.get(url)


start = time.time()


def read_lastline(filename):
    try:
        with open(filename, 'r',encoding="utf-8") as f:
            last_line = f.readlines()[-1].split(',')[0]
            return last_line
    except:
        print('Creating file....')
        return 1


# newHeight=0

def initiate_scrolling(driver, pause, stop_count):
    print("Scraping, please wait")

    driver.get(url)
    # driver.execute_script("window.scrollTo(0, ${newHeight});")
    lastHeight = driver.execute_script("return document.body.scrollHeight")
    href_dict = {}
    while True:
        try:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            time.sleep(pause)

            image_list = driver.find_elements_by_class_name("v1Nh3")
            for image in image_list:
                href = image.find_element_by_tag_name("a").get_attribute("href")
                key = href.split("/")[-2]
                # print(href,key)
                href_dict[key] = href
                if (len(href_dict.keys()) >= stop_count):
                    break

            newHeight = driver.execute_script("return document.body.scrollHeight")

            if (newHeight == lastHeight) or (len(href_dict.keys()) >= stop_count):
                break

            lastHeight = newHeight




        except NoSuchElementException as e:
            print("Done Scrolling!")
            return href_dict
    print("Scraping complete")

    return href_dict


def get_data(driver,href_dict, pause, items):  # with timeframe
    print("Processing links....")
    count=0

    index = int(read_lastline(filename))

    if index == 1:
        csv_file = open(filename, 'w',encoding="utf-8")
        csv_writer = csv.writer(csv_file, delimiter=',')
        csv_writer.writerow(['index', 'tag', 'uname', 'caption', 'time'])

    else:
        index += 1
        csv_file = open(filename, 'a',encoding="utf-8")
        csv_writer = csv.writer(csv_file, delimiter=',')

    # while True:
    false_count = 0

    for ref in href_dict.values():
        # print(ref)
        driver.get(ref)
        time.sleep(pause)
        soup = BeautifulSoup(driver.page_source)

        try:
            username = soup.find('a', class_=['_2g7d5', 'notranslate', '_iadoq']).getText()
            # print(username)

            un_len = len(username)
            caption = soup.find('li', class_=['gElp9']).getText()
            caption_final = caption[un_len:]
            # print(caption[un_len:])

            timestamp = soup.find('time')["datetime"]
            datetimeObj = datetime.strptime(timestamp,'%Y-%m-%dT%H:%M:%S.%fZ')  #utc
            # datetimeObj+=timedelta(hours=5,minutes=30)   #ist
            # print(datetimeObj, end='\n\n')

            if (datetimeObj>t1obj and datetimeObj<t2obj):
                count+=1
                print(count)
                datetimeObj1=datetimeObj
                datetimeObj1-=timedelta(hours=4)   #et

                csv_writer.writerow([str(count), tag, username, caption_final, str(datetimeObj1)])
                index += 1
                if count==items:

                    break

            if(t1obj>datetimeObj):
                false_count+=1
                print("false count: ",false_count)

                if false_count==20:

                    print('Work done, no more photos in timeframe')
                    break

        except Exception as e:
            print(e)



    csv_file.close()

# change right most number below to lower if going for recent searches and increase for older ones
href = initiate_scrolling(driver, 3, 500) #***#
print(f"links grabbed : {len(href)}")
get_data(driver,href, 1, records)

driver.close()
end = time.time()

total=end-start

df = pd.read_csv(filename)
counts_series = df.uname.value_counts()
count_df = pd.DataFrame(counts_series)
count_df = count_df.reset_index()
count_df.columns = ["uname","counts"]
everything = pd.merge(df, count_df, on='uname', how='left').sort_values(by="uname",ascending=False)
everything.sort_values(['counts','uname'],ascending=[False,True],inplace=True)
everything.drop('counts',axis=1,inplace=True)
everything.drop('index',axis=1,inplace=True)
everything.to_csv(filename,index=False)

df = pd.read_csv(filename)
df.index=df.index+1
df.to_csv(filename)

print(f'TASK COMPLETED IN %.2f sec'%(total))