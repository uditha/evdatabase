import pandas as pd
import re
import itertools
import pathlib
from datetime import datetime
import time
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC 
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver import ActionChains
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument('--disable-blink-features=AutomationControlled')
chrome_options.add_argument("--disable-extensions")
#chrome_options.add_argument("--headless")
chrome_options.add_experimental_option('useAutomationExtension', False)
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])


def hasClass(el, cls):
    return  cls in el.get_attribute('class').split()

def getImageUrl(urlStr):
    return re.search(r'(https?://\S+).jpg', urlStr).group()
       

def processInfoTable(table):
    data = []
    rows = table.find_elements(By.TAG_NAME, 'tr')
    for row in rows:
        tds = row.find_elements(By.TAG_NAME, 'td')
        colName = tds[0].text.split('\n')[0]
        colData =  ', '.join(tds[1].text.split('\n')) if len(tds[1].text.split('\n')) > 1 else tds[1].text
        data.append((colName , colData ))
    
    return data


def processSpecTable(table):
    tbl_str = ''
    rows = table.find_elements(By.TAG_NAME, 'tr')
    for i,row in enumerate(rows):
        tds = row.find_elements(By.TAG_NAME, 'th' if i ==0 else 'td')
        tbl_str += ' | '.join([ td.text for td in tds]) + '\n'
        
    return tbl_str
   


def processInfoTables(tables):
    rowDict = {}
    tableArr = []
    for table in tables:
        tableArr.append(processInfoTable(table))
        
    for st in tableArr:
        for item in st:
            rowDict[item[0]] = item[1]
            
    return rowDict
        
    
def processSpecTables(tables):
    for table in tables:
        processSpecTable(table)
            

def processUrl(driver, url):
    rowDict = {}
    rowDict['url'] = url
    driver.get(url)
    
    image = driver.find_element(By.ID, 'model-image').get_attribute('style')
    rowDict['image'] = getImageUrl(image)
    
    dataArea = driver.find_element(By.XPATH,'//*[@id="main"]/div[4]')
    #get all sections
    sections = dataArea.find_elements(By.CLASS_NAME, 'header')
    # get all tables
    tables = dataArea.find_elements(By.TAG_NAME, 'table')
    
    
    for sec, tbl in zip(sections, tables ):
        if hasClass(tbl, 'model-information-table'):
            for item in processInfoTable(tbl):
                rowDict[item[0]] = item[1]
        else:
            #print(processSpecTable(tbl))
            rowDict[sec.text] = str(processSpecTable(tbl))   
            
    print('[INFO]',url, '- Completed.')
    return rowDict   


def getCarsUrls(driver):
    mainUrl = 'https://www.evspecifications.com/'  
    driver.get(mainUrl)  
    
    div = driver.find_element(By.CLASS_NAME, 'brand-listing-container-frontpage')
    urls = div.find_elements(By.TAG_NAME, 'a')
    
    brandUrls = [ url.get_attribute('href') for url in urls ]
    
    carUrls = []
    
    for brandUrl in brandUrls:
        driver.get(brandUrl)
        carSections = driver.find_elements(By.CLASS_NAME, 'model-listing-container-80')
        
        for carSection in carSections:
            cars = carSection.find_elements(By.TAG_NAME, 'a')
            for car in cars:
                if car.get_attribute('href') not in carUrls:
                    carUrls.append(car.get_attribute('href'))
                #else:
                    #print('<<<<<Duplicate>>>>')
                    #print(car.get_attribute('href'))
            
    print('[INFO] Total cars in the Website : ', len(carUrls))
    return carUrls


def saveData(path, data):
    if path.is_file():
        old = pd.read_excel(path)
        new = pd.DataFrame(data)
        frames = [old, new]
        df = pd.concat(frames)
    else:
        df = pd.DataFrame(data)
        
    with pd.ExcelWriter('cars.xlsx', engine="xlsxwriter") as writer:
        writer.book.formats[0].set_text_wrap()  # update global format with text wrap
        df.to_excel(writer, index=False)
    


def main():
    print('[INFO] Data Scraping Process is started. Please wait.')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # get all brands car urls
    urls = getCarsUrls(driver)
       
    pathToFile = "cars.xlsx"
    path = pathlib.Path(pathToFile)
    
    if path.is_file():
        OLD_FILE = pd.read_excel(pathToFile)
        oldUrls = list(OLD_FILE['url'])
        
        newlyUrls = [ url for url in urls if url not in oldUrls ]
        
        if len(newlyUrls) == 0 :
            print("[INFO] There is no new urls to be scraped.")
        else:
            print("[INFO] There are {} uls newly added to the database.".format(len(newlyUrls)))
            for url in newlyUrls[0:10]:
                carData = []
                rowDict = processUrl(driver, url) 
                carData.append(rowDict)
                saveData(path, carData)  
    else:
        for url in urls[0:5]:
            carData = []
            rowDict = processUrl(driver, url) 
            carData.append(rowDict)
            saveData(path, carData)  
       
       
    print('[INFO] Scraping process is completed.')   
    
    
    
   


if __name__ == "__main__":
    main()
