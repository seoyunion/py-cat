# 뉴스 크롤링 #
from bs4 import BeautifulSoup
import requests
import pandas as pd
import re
import math
import time

## 함수 정의 ##
# 날짜 분리 반환 함수
def date_slice(date_base):
    date_base1 = re.sub('[^0-9]', '', date_base)
    year = date_base1[0:4]
    month = date_base1[4:6]
    day = date_base1[6:8]
    return (year, month, day)

def clean_text(data):
    clean_text = re.sub('([a-zA-Z0-9_.+-]+@[a-zA-Z0-9]+\.[a-zA-Z0-9.]+)', '', data)
    clean_text = re.sub('([a-zA-Z0-9_.+-]+\.[a-zA-Z0-9]+\.[a-zA-Z0-9.]+)', '', clean_text)
    clean_text = re.sub('(http|ftp|https)://(?:[-\w.]|(?:%[\da-fA-F{2}]))+', '', clean_text)
    clean_text = re.sub('([ㄱ-ㅎㅏ-ㅣ]+)', '', clean_text)
    clean_text = re.sub('<[^>]*>', '', clean_text)
    clean_text = re.sub('[-=+_,#/\?;:^$@*\"※~&%ㆍ!』\\‘’“”|\(\)\[\]\<\>`\'》❤♥♡☆★▲◇△▶◆■⊙▦ⓒ●◈·]', ' ', clean_text)
    clean_text = clean_text.replace("\t", " ")
    clean_text = clean_text.replace("\r", " ")
    clean_text = clean_text.replace("\n", " ")
    clean_text = clean_text.replace("  ", " ")
    return clean_text

# [중앙일보]
def joong_crawl(header, keyword, crawl_page):
    url= 'https://news.joins.com/Search/TotalNews?page=%d&Keyword=%s&PeriodType=DirectInput&StartSearchDate=2011.01.01&EndSearchDate=2020.12.31&SortType=New&SearchCategoryType=TotalNews'% (1,keyword)
    res = requests.get(url, headers=header)

    #### 페이지 수 확인
    soup=BeautifulSoup(res.content, 'html.parser')
    page_base=soup.find("span",{'class':'total_number'}).text
    page_base1=re.split('\/',page_base)[0]
    page_end=int(re.split('-', page_base1)[1])
    #print("해당 키워드 전체 페이지 수:",page_end)

    ### 기사 링크 수집
    href_all = []
    check_list = []  # 가져오지 못한 페이지 있는지 확인하기 위해 만든 리스트

    for page in range(1, crawl_page + 1):
        #print('page :' + str(page) + '/' + str(crawl_page))
        url = 'https://news.joins.com/Search/TotalNews?page=%d&Keyword=%s&PeriodType=DirectInput&StartSearchDate=2011.01.01&EndSearchDate=2020.12.31&SortType=New&SearchCategoryType=TotalNews' % (
        page, keyword)
        res = requests.get(url, headers=header)

        # 데이터를 잘 가져오고 있는지 확인
        if res.status_code == 200:
            check_list.append('정상')
        else:
            check_list.append('에러')
            continue

        ### 2페이지 이상부터 페이지 정보 안가져와졌으면 다시 가져오기
        if page > 1:
            if soup == BeautifulSoup(res.content, 'html.parser'):
                while True:
                    res = requests.get(url, headers=header)
                    if soup != BeautifulSoup(res.content, 'html.parser'):
                        break

        ### 기사 링크 수집
        soup = BeautifulSoup(res.content, 'html.parser')
        href = soup.find_all("h2", {'class': 'headline mg'})
        for i in href:
            href_all.append(i.find('a')['href'])

        ### 페이지의 데이터를 전부 가져오지 못했으면 다시 가져오기
        if page != crawl_page:
            if len(href) != 10:
                while True:
                    res = requests.get(url, headers=header)
                    soup == BeautifulSoup(res.content, 'html.parser')
                    res = requests.get(url, headers=header)
                    soup = BeautifulSoup(res.content, 'html.parser')
                    href = soup.find_all("h2", {'class': 'headline mg'})
                    for i in href:
                        href_all.append(i.find('a')['href'])
                    if len(href) == 10:
                        break
        href = []

    ## 날짜 형식대로 만드는 함수
    def date_slice(date_base):
        date_base1 = re.sub('[^0-9]', '', date_base)
        year = date_base1[0:4]
        month = date_base1[4:6]
        day = date_base1[6:8]
        return (year, month, day)

    href_url = []
    for i in href_all:
        href_url.append('http:' + i)

    check_list_2 = []
    data_all = pd.DataFrame()
    page = 0

    for url in href_all:
        page = page + 1
        #print('page :' + str(page) + '/' + str(len(href_all)))
        res = requests.get(url, headers=header)
        if res.status_code == 200:
            check_list_2.append('정상')
        else:
            check_list_2.append('에러')
            continue

        if page > 1:
            if soup == BeautifulSoup(res.content, 'html.parser'):
                while True:
                    res = requests.get(url, headers=header)
                    if soup != BeautifulSoup(res.content, 'html.parser'):
                        break

        soup = BeautifulSoup(res.content, 'html.parser')
        title = soup.select_one('div > h1').text

        try:
            content = soup.find('div', {'class': 'article_body mg fs4'}).text
        except:
            content = soup.find('div', {'class': 'article_body fs1 mg'}).text

        date_base = soup.find('div', {'class': 'byline'}).text
        year = date_slice(date_base)[0]
        month = date_slice(date_base)[1]
        day = date_slice(date_base)[2]

        data = {"title": [title], "content": [content], "year": [year], "month": [month], "day": [day]}
        data = pd.DataFrame(data)
        data_all = pd.concat([data_all, data], axis=0)

    data_all = data_all.reset_index().drop(['index'], axis=1)

    #크롤링한 데이터 확인
    df = data_all
    df['news'] = '[보수]중앙'
    #print(df.tail())
    return df

 ##############################################################################

# [한겨레]
def han_crawl(header, keyword, crawl_page):
    url = 'http://search.hani.co.kr/Search?command=query&keyword=%s&media=news&submedia=&sort=d&period=all&datefrom=2011.01.01&dateto=2020.12.31&pageseq=%d'%(keyword,1)
    res = requests.get(url, headers=header)

    #### 페이지 수 확인
    soup=BeautifulSoup(res.content, 'html.parser')
    page_base=soup.find("span",{'class':'total'}).text
    page_base1 = int(re.sub('[^0-9]','',page_base))
    page_end=math.ceil(page_base1/10)
    #print("해당 키워드 전체 페이지 수:",page_end)

    ### 기사 링크 수집
    href_all = []
    check_list = []  # 가져오지 못한 페이지 있는지 확인하기 위해 만든 리스트
    for page in range(1, crawl_page + 1):
        #print('page :' + str(page) + '/' + str(crawl_page))
        url = 'http://search.hani.co.kr/Search?command=query&keyword=%s&media=news&submedia=&sort=d&period=all&datefrom=2011.01.01&dateto=2020.12.31&pageseq=%d' % (
        keyword, page)
        res = requests.get(url, headers=header)
        # 데이터를 잘 가져오고 있는지 확인
        if res.status_code == 200:
            check_list.append('정상')
        else:
            check_list.append('에러')
            continue
        ### 2페이지 이상부터 페이지 정보 안가져와졌으면 다시 가져오기
        if page > 1:
            if soup == BeautifulSoup(res.content, 'html.parser'):
                while True:
                    res = requests.get(url, headers=header)
                    if soup != BeautifulSoup(res.content, 'html.parser'):
                        break
        ### 기사 링크 수집
        href_base = []
        soup = BeautifulSoup(res.content, 'html.parser')
        href = soup.find_all('dt')
        for i in href:
            href_base.append(i.find('a'))
        href_base = [item for item in href_base if item != None]
        for i in href_base:
            href_all.append(i['href'])
        ### 페이지의 데이터를 전부 가져오지 못했으면 다시 가져오기
        if page != page_end:
            if len(href_base) != 10:
                while True:
                    res = requests.get(url, headers=header)
                    href_base = []
                    soup = BeautifulSoup(res.content, 'html.parser')
                    href = soup.find_all('dt')
                    for i in href:
                        href_base.append(i.find('a'))
                    href_base = [item for item in href_base if item != None]
                    for i in href_base:
                        href_all.append(i['href'])
                    if len(href) == 10:
                        break
        href = []
    # 날짜 형식 반환 함수
    def date_slice(date_base):
        date_base1 = re.sub('[^0-9]', '', date_base)
        year = date_base1[0:4]
        month = date_base1[4:6]
        day = date_base1[6:8]
        return (year, month, day)
    ### href를 url 형식으로 바꿔주기
    href_url = []
    for i in href_all:
        href_url.append('http:' + i)
    check_list_2 = []
    data_all = pd.DataFrame()
    page = 0

    for url in href_url:
        page = page + 1
        #print('page :' + str(page) + '/' + str(len(href_url)))
        res = requests.get(url, headers=header)
        if res.status_code == 200:
            check_list_2.append('정상')
        else:
            check_list_2.append('에러')
            continue
        if page > 1:
            if soup == BeautifulSoup(res.content, 'html.parser'):
                while True:
                    res = requests.get(url, headers=header)
                    if soup != BeautifulSoup(res.content, 'html.parser'):
                        break
        soup = BeautifulSoup(res.content, 'html.parser')
        title = soup.select_one('#article_view_headline > h4').text
        content = soup.find('div', {'class': 'text'}).text
        date_base = soup.find('p', {'class': 'date-time'}).text
        year = date_slice(date_base)[0]
        month = date_slice(date_base)[1]
        day = date_slice(date_base)[2]

        data = {"title": [title], "content": [content], "year": [year], "month": [month], "day": [day]}
        data = pd.DataFrame(data)
        data_all = pd.concat([data_all, data], axis=0)
    data_all = data_all.reset_index().drop(['index'], axis=1)
    df = data_all
    df['news'] = '[진보]한겨레'

    return df


## main ##
# 전역변수 선언
header = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.220 Whale/1.3.51.7 Safari/537.36',
}
#keyword = input("검색할 키워드를 입력하세요: ")

#crawl_page = int(input("분석 할 뉴스 기사 페이지 수를 입력하세요(한 페이지당 보수10+진보10 >> 총20건): "))

# 뉴스 기사 크롤링
# 긁어온 기사 제목, 본문, 날짜, 종류 확인
joong_data = joong_crawl(header, keyword, crawl_page)
print('[보수]중앙일보\n', joong_data)
han_data = han_crawl(header, keyword, crawl_page)
print('[진보]한겨레일보\n', han_data)
from news_preprocessing import clean_text
news = ""
for i in range(crawl_page*10):
    news += "["+str(joong_data['title'][i])+"]"+"    "+str(joong_data['news'][i])+"\n"+clean_text(str(joong_data['content'][i]))+"\n"+"*"*50+"\n\n"
    news += "["+str(han_data['title'][i])+"]"+"    "+str(han_data['news'][i])+"\n"+clean_text(str(han_data['content'][i]))+"\n""*"*50+"\n\n"
print(news)
########################################################################
'''
#데이터 전처리 및 분석
def content_data(joong_data, han_data):
    j = joong_data['content']
    h = han_data['content']

    js = ""
    hs = ""
    for s in j:
        js += s
    for s in h:
        hs += s
    return js, hs, js+hs
# 문자열로 변환
js, hs, jh = content_data(joong_data, han_data)

#print(joong_data.isnull().sum())
#print(han_data.isnull().sum())
'''


