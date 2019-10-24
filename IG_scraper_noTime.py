import csv
import time
import html
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import timedelta
import pandas as pd
from selenium.webdriver.chrome.options import Options

# Global variables

tag = input("Provide tag : ")
filename = input("Provide filename : ")
filename = filename+'.csv'
url = "https://www.instagram.com/explore/tags/" + tag + "/"
records = int(input('Provide number of entries : '))

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


def initiate_scrolling(driver, pause, stop_count):
    print("Scraping, please wait")
    driver.get(url)

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
                # print(href)
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


def get_data(driver, href_dict, pause):  # with no timeframe
    print("Processing links......")
    index = int(read_lastline(filename))

    if index == 1:
        csv_file = open(filename, 'w',encoding="utf-8")
        csv_writer = csv.writer(csv_file, delimiter=',')
        csv_writer.writerow(['index', 'tag', 'uname', 'caption', 'time'])

    else:
        index += 1
        csv_file = open(filename, 'a',encoding="utf-8")
        csv_writer = csv.writer(csv_file, delimiter=',')

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
            datetimeObj = datetime.strptime(timestamp,'%Y-%m-%dT%H:%M:%S.%fZ')
            # print(datetimeObj, end='\n\n')
            datetimeObj1=datetimeObj
            datetimeObj1-=timedelta(hours=4)

            csv_writer.writerow([str(index), tag, username, caption_final, str(datetimeObj1)])
            print(index)
            index += 1


        except Exception as e:
            print(e)

    csv_file.close()


x = initiate_scrolling(driver, 3, records) #reduce this time########################################################
print(f"links grabbed : {len(x)}")
get_data(driver, x, 1)

driver.close()

end = time.time()

total=end-start


#sorting
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

