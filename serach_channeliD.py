from selenium import webdriver
import requests
from bs4 import BeautifulSoup
url = 'https://www.youtube.com/results?search_query=%E8%8C%84%E5%AD%90%E8%9B%8B'

driver = webdriver.Chrome('C:/Users/user/PycharmProjects/pythonProject_autoEXE/chromedriver')

driver.implicitly_wait(3)

driver.get(url)

html = driver.page_source
header = {'user-agent': 'ECC=Googlebot', 'cookie': 'Googlebot'}
resp = requests.get(url, headers=header)
resp = resp.text
soup = BeautifulSoup(resp, 'html.parser')
print(soup)

#尚未完成...