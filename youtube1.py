from pytube import YouTube
import requests
from googleapiclient.discovery import build
import json
import google.oauth2.credentials
import google_auth_oauthlib.flow
import db
from datetime import datetime
from collections import Counter
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly
import time
from jinja2 import Template
'''
YouTube 數據 API
https://developers.google.com/resources/api-libraries/documentation/youtube/v3/python/latest/index.html
'''

flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file('../API_KEY/client_secret_562839061912-n90l98f6ocn581r5ai1jt6a0v2kipo3u.apps.googleusercontent.com.json',
                                                               scopes=['https://www.googleapis.com/auth/youtube.force-ssl'])
flow.redirect_uri = 'https://oauth2.example.com/code'

authorization_url, state = flow.authorization_url(
    access_type='offline',
    state='sample_passthrough_value',
    login_hint='theforeverwen@gmail.com',
    prompt='consent',
    include_granted_scopes='true')


def download_video(url):
    url='https://www.youtube.com/watch?v=fPZ37t3nvco' #影片鏈結
    YouTube(url).streams.first().download() #下載影片



YOUTUBE_API_KEY = "AIzaSyCt893vHOjQVlzmaKSBXBCcsr8FFO4GK_U" #API金鑰

channel_id = 'UCmr9bYmymcBmQ1p2tLBRvwg' #櫻坂46channel
# channel_id = 'UC0SkNQXPJ60hKEFubOz0fDA' #丁特
# channel_id = 'UCUzpZpX2wRYOk3J8QTFGxDg' #乃木坂
# channel_id = 'UCR0V48DJyWbwEAdxLL5FjxA' #日向坂



youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
request = youtube.channels().list(part='contentDetails', id=channel_id)
# request = youtube.commentThreads().list(part='snippet', id=channel_id)
response = request.execute()


uploads = response['items'][0]['contentDetails']['relatedPlaylists']['uploads'] #因為items是list, 所以取出[0]後再繼續抓資料


uploads_url = 'https://www.googleapis.com/youtube/v3/channels?part=contentDetails&id={}&key={}'.format(channel_id, YOUTUBE_API_KEY)

#playlistItems (要更改path)
#playlist = 頻道裡面的播放清單
# playlist_id = 'PL0eK3gfF1BbN7E9wQOUfUxZLmbMNRrSoW'
# playlist_url = 'https://www.googleapis.com/youtube/v3/playlistItems?part=contentDetails&playlistId={}&key={}'.format(playlist_id, YOUTUBE_API_KEY)
def get_json_data(url): #解析網址=json格式
    data = requests.get(url)
    data.encoding = 'utf-8'
    data = data.text
    data = json.loads(data)
    return data
#影片資訊 (id=各影片自己的Id, 可從播放清單裡面找到)
# video_url = 'https://www.googleapis.com/youtube/v3/videos?part=snippet&id={}&key={}'.format('_ZCf_iLMwn0', YOUTUBE_API_KEY)

#channel簡介(內涵playlist)

def get_channel_videos(channel_id): #取得影片名稱, 鏈結, 上傳時間...並插入資料庫
    base_url = 'https://www.googleapis.com/youtube/v3/'
    resp = youtube.channels().list(part='contentDetails', id=channel_id).execute()
    playlist_id = resp['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    next_page_token = None
    page = 1
    while 1:
        if page == 1:
            playlist_url = base_url + 'playlistItems?part={}&playlistId={}&maxResults={}&key={}'.format('snippet',
                                                                                                        playlist_id,
                                                                                                        50,
                                                                                                        YOUTUBE_API_KEY)
            data = get_json_data(playlist_url)
            next_page_token = data['nextPageToken']
            for row in data['items']:

                title = row['snippet']['title']
                img = row['snippet']['thumbnails']['default']['url']
                video_url = 'https://www.youtube.com/watch?v=' + \
                            row['snippet']['resourceId']['videoId']
                videoId = row['snippet']['resourceId']['videoId']
                video_desc = get_videos_statistics(videoId) #呼叫影片detail的內容
                viewCount = video_desc[0]
                likeCount = video_desc[1]
                dislikeCount = video_desc[2]
                commentCount = video_desc[3]

                published_data = publishedTime(videoId) #影片發布時間
                publishedAt = published_data[:10]


                uploadDate = row['snippet']['publishedAt'][:10].replace("T", "").replace("Z", "")
                # published = datetime.strptime(published, '%Y-%m-%d')
                print('標題:{}, 影片鏈結:{}, 圖片鏈結:{}, 上傳時間:{}'.format(title, video_url, img, uploadDate))
                sql = "select * from youtube_videos where videoUrl='{}'".format(video_url)
                db.cursor.execute(sql)
                db.conn.commit()
                if db.cursor.rowcount == 0:
                    getdate = datetime.today()
                    getdate = getdate.strftime('%Y-%m-%d')
                    sql = "insert into youtube_videos(title, videoUrl, imgUrl, uploadDate, viewCount, likeCount, dislikeCount, commentCount, published_date) " \
                          "values ('{}', '{}', '{}', '{}','{}', '{}', '{}', '{}', '{}')".format(title.replace("'", ""),
                                                                                          video_url, img, uploadDate,
                                                                                          viewCount, likeCount,
                                                                                          dislikeCount, commentCount,
                                                                                          publishedAt)
                    db.cursor.execute(sql)
                    db.conn.commit()
                else:
                    result = db.cursor.fetchone()
                    if viewCount != result[5]:
                        sql = "update youtube_videos set title = '{}', videoUrl = '{}', imgUrl = '{}', uploadDate = '{}', viewCount = '{}', " \
                              "likeCount = '{}', dislikeCount = '{}', commentCount = '{}', published_date = '{}' where id = '{}'".\
                            format(title.replace("'", ""),video_url, img, uploadDate,viewCount, likeCount
                                   ,dislikeCount, commentCount,publishedAt, result[0])
                        db.cursor.execute(sql)
                        db.conn.commit()

            page += 1
        else:
            playlist_url = base_url + 'playlistItems?part={}&playlistId={}&maxResults={}&key={}&pageToken={}'.format('snippet',
                                                                                                        playlist_id,
                                                                                                        50,
                                                                                                        YOUTUBE_API_KEY,
                                                                                                        next_page_token)
            data = get_json_data(playlist_url)
            if 'nextPageToken' not in data.keys(): #最後一頁不會有nextPageToken
                for row in data['items']:
                    title = row['snippet']['title']
                    img = row['snippet']['thumbnails']['default']['url']

                    video_url = 'https://www.youtube.com/watch?v=' + \
                                row['snippet']['resourceId']['videoId']
                    videoId = row['snippet']['resourceId']['videoId']

                    video_desc = get_videos_statistics(videoId)  # 呼叫影片detail的內容
                    viewCount = video_desc[0]
                    likeCount = video_desc[1]
                    dislikeCount = video_desc[2]
                    commentCount = video_desc[3]

                    published_data = publishedTime(videoId)  # 影片發布時間
                    publishedAt = published_data[:10]

                    uploadDate = row['snippet']['publishedAt'][:10]
                    # published = datetime.strptime(published, '%Y-%m-%d')
                    print('標題:{}, 影片鏈結:{}, 圖片鏈結:{}, 上傳時間:{}'.format(title, video_url, img, uploadDate))
                    sql = "select * from youtube_videos where videoUrl='{}'".format(video_url)
                    db.cursor.execute(sql)
                    db.conn.commit()
                    if db.cursor.rowcount == 0:
                        # getdate = datetime.today()
                        # getdate = getdate.strftime('%Y-%m-%d')
                        sql = "insert into youtube_videos(title, videoUrl, imgUrl, uploadDate, viewCount, likeCount, dislikeCount, commentCount, published_date) " \
                              "values ('{}', '{}', '{}', '{}','{}', '{}', '{}', '{}', '{}')".format(title.replace("'", ""),
                                                                                              video_url, img,
                                                                                              uploadDate,
                                                                                              viewCount, likeCount,
                                                                                              dislikeCount,
                                                                                              commentCount, publishedAt)
                        db.cursor.execute(sql)
                        db.conn.commit()
                    else:
                        result = db.cursor.fetchone()
                        if viewCount != result[5]:
                            sql = "update youtube_videos set title = '{}', videoUrl = '{}', imgUrl = '{}', uploadDate = '{}', viewCount = '{}', " \
                                  "likeCount = '{}', dislikeCount = '{}', commentCount = '{}', published_date = '{}' where id = '{}'". \
                                format(title.replace("'", ""), video_url, img, uploadDate, viewCount, likeCount
                                       , dislikeCount, commentCount, publishedAt, result[0])
                            db.cursor.execute(sql)
                            db.conn.commit()
                break
            else:
                next_page_token = data['nextPageToken']
                for row in data['items']:
                    title = row['snippet']['title']
                    img = row['snippet']['thumbnails']['default']['url']
                    video_url = 'https://www.youtube.com/watch?v=' + \
                                row['snippet']['resourceId']['videoId']
                    videoId = row['snippet']['resourceId']['videoId']

                    video_desc = get_videos_statistics(videoId)  # 呼叫影片detail的內容
                    viewCount = video_desc[0]
                    likeCount = video_desc[1]
                    dislikeCount = video_desc[2]
                    commentCount = video_desc[3]

                    published_data = publishedTime(videoId)  # 影片發布時間
                    publishedAt = published_data[:10]

                    uploadDate = row['snippet']['publishedAt'][:10]
                    # published = datetime.strptime(published, '%Y-%m-%d')
                    print('標題:{}, 影片鏈結:{}, 圖片鏈結:{}, 上傳時間:{}'.format(title, video_url, img, uploadDate))
                    sql = "select * from youtube_videos where videoUrl='{}'".format(video_url)
                    db.cursor.execute(sql)
                    db.conn.commit()
                    if db.cursor.rowcount == 0:
                        # getdate = datetime.today()
                        # getdate = getdate.strftime('%Y-%m-%d')
                        sql = "insert into youtube_videos(title, videoUrl, imgUrl, uploadDate, viewCount, likeCount, dislikeCount, commentCount, published_date) " \
                              "values ('{}', '{}', '{}', '{}','{}', '{}', '{}', '{}', '{}')".format(title.replace("'", ""),
                                                                                              video_url, img,
                                                                                              uploadDate,
                                                                                              viewCount, likeCount,
                                                                                              dislikeCount,
                                                                                              commentCount, publishedAt)
                        db.cursor.execute(sql)
                        db.conn.commit()
                    else:
                        result = db.cursor.fetchone()
                        if viewCount != result[5]:
                            sql = "update youtube_videos set title = '{}', videoUrl = '{}', imgUrl = '{}', uploadDate = '{}', viewCount = '{}', " \
                                  "likeCount = '{}', dislikeCount = '{}', commentCount = '{}', published_date = '{}' where id = '{}'". \
                                format(title.replace("'", ""), video_url, img, uploadDate, viewCount, likeCount
                                       , dislikeCount, commentCount, publishedAt, result[0])
                            db.cursor.execute(sql)
                            db.conn.commit()
            page += 1
    db.conn.close()



def get_videos_statistics(videoId): #觀看次數, 讚數, 倒讚數, 留言數
    base_url = 'https://www.googleapis.com/youtube/v3/'
    video_desc = base_url + 'videos?part=statistics&id={}&key={}'.format(videoId, YOUTUBE_API_KEY)
    video_desc = get_json_data(video_desc)
    for row in video_desc['items']:
        if 'commentCount' not in row['statistics']:
            viewCount = row['statistics']['viewCount']
            likeCount = row['statistics']['likeCount']
            dislikeCount = row['statistics']['dislikeCount']
            commentCount = 'no comment'
            video_dlist = [viewCount, likeCount, dislikeCount, commentCount]
            # print('觀看次數:{}, 讚數:{}, 倒讚數:{}, 評論數:{}'.format(viewCount, likeCount, dislikeCount, commentCount))
            return video_dlist
        else:
            viewCount = row['statistics']['viewCount']
            likeCount = row['statistics']['likeCount']
            dislikeCount = row['statistics']['dislikeCount']
            commentCount = row['statistics']['commentCount']
            video_dlist = [viewCount, likeCount, dislikeCount, commentCount]
            # print('觀看次數:{}, 讚數:{}, 倒讚數:{}, 評論數:{}'.format(viewCount, likeCount, dislikeCount, commentCount))
            return video_dlist


def publishedTime(videoId): #影片發布日期  (不一定等於上傳日期)
    base_url = 'https://www.googleapis.com/youtube/v3/'
    video_desc = base_url + 'videos?part=snippet&id={}&key={}'.format(videoId, YOUTUBE_API_KEY)
    video_desc = get_json_data(video_desc)
    for row in video_desc['items']:
        publishedTime = row['snippet']['publishedAt']
        return publishedTime

def get_commentsThreads(videoId, title): #影片評論
    base_url = 'https://www.googleapis.com/youtube/v3/'
    video_desc = base_url + 'commentThreads?part=snippet&videoId={}&key={}&maxResults=100'.format(videoId, YOUTUBE_API_KEY)

    next_page_token = None
    page = 1

    # writeBaseHtml(filename) #先寫好網頁架構
    sql = "create table if not exists `{}` (id INT NOT NULL auto_increment, playName varchar(255), " \
          "playerChannel varchar(255), textDisplay longtext, likeCount int, primary key(id))".format(title)
    db.cursor.execute(sql)
    db.conn.commit()
    while 1:
        if page == 1: #第一頁
            video_comments = get_json_data(video_desc)
            next_page_token = video_comments['nextPageToken'] #抓取nextPageToken
            # writeIntoHtml(video_comments, filename)
            for row in video_comments['items']:
                playName = row['snippet']['topLevelComment']['snippet']['authorDisplayName'] #留言者名字
                playerChannel = row['snippet']['topLevelComment']['snippet']['authorChannelUrl']
                textDisplay = row['snippet']['topLevelComment']['snippet']['textDisplay']  # 留言內容
                likeCount = row['snippet']['topLevelComment']['snippet']['likeCount'] #留言按讚數
                data_list = [playName, playerChannel, textDisplay, likeCount]
                # print("留言者:{}, 頻道:{}, 內容:{}, 按讚:{}".format(playName, playerChannel, textDisplay, likeCount))
                print(data_list)
                sql = "select likeCount from `{}` where playName = '{}'".format(title, playName)
                db.cursor.execute(sql)
                db.conn.commit()
                if db.cursor.rowcount == 0:
                    sql = "insert into `{}`(playName, playerChannel, textDisplay, likeCount) values " \
                          "('{}', '{}', '{}', '{}')".format(title, playName, playerChannel, textDisplay.isalnum(), likeCount)
                    db.cursor.execute(sql)
                    db.conn.commit()
            page += 1
            time.sleep(1)
        else:
            video_comment_url = video_desc + "&pageToken='{}'".format(next_page_token)
            video_comments = get_json_data(video_comment_url)
            if 'nextPageToken' not in video_comments.keys(): #最後一頁不會有nextPageToken
                # writeIntoHtml(video_comments, filename)
                for row in video_comments['items']:
                    playName = row['snippet']['topLevelComment']['snippet']['authorDisplayName']  # 留言者名字
                    playerChannel = row['snippet']['topLevelComment']['snippet']['authorChannelUrl']
                    textDisplay = row['snippet']['topLevelComment']['snippet']['textDisplay']  # 留言內容
                    likeCount = row['snippet']['topLevelComment']['snippet']['likeCount']  # 留言按讚數
                    data_list = [playName, playerChannel, textDisplay, likeCount]
                    # print("留言者:{}, 頻道:{}, 內容:{}, 按讚:{}".format(playName, playerChannel, textDisplay, likeCount))
                    print(data_list)
                    sql = "select likeCount from `{}` where playName = '{}'".format(title, playName)
                    db.cursor.execute(sql)
                    db.conn.commit()
                    if db.cursor.rowcount == 0:
                        sql = "insert into `{}`(playName, playerChannel, textDisplay, likeCount) values " \
                              "('{}', '{}', '{}', '{}')".format(title, playName, playerChannel, textDisplay.isalnum(), likeCount)
                        db.cursor.execute(sql)
                        db.conn.commit()

                break
            else:
                next_page_token = video_comments['nextPageToken']  # 抓取nextPageToken
                # writeIntoHtml(video_comments, filename)
                for row in video_comments['items']:
                    playName = row['snippet']['topLevelComment']['snippet']['authorDisplayName']  # 留言者名字
                    playerChannel = row['snippet']['topLevelComment']['snippet']['authorChannelUrl']
                    textDisplay = row['snippet']['topLevelComment']['snippet']['textDisplay']  # 留言內容
                    likeCount = row['snippet']['topLevelComment']['snippet']['likeCount']  # 留言按讚數
                    data_list = [playName, playerChannel, textDisplay, likeCount]
                    # print("留言者:{}, 頻道:{}, 內容:{}, 按讚:{}".format(playName, playerChannel, textDisplay, likeCount))
                    print(data_list)
                    sql = "select likeCount from '{}' where playName = '{}'".format(title, playName)
                    db.cursor.execute(sql)
                    db.conn.commit()
                    if db.cursor.rowcount == 0:
                        sql = "insert into '{}'(playName, playerChannel, textDisplay, likeCount) values " \
                              "('{}', '{}', '{}', '{}')".format(title, playName, playerChannel, textDisplay.isalnum(), likeCount)
                        db.cursor.execute(sql)
                        db.conn.commit()

                    # writeIntoHtml(video_comments, filename)
                page += 1
                time.sleep(1)
    db.conn.close()
    # with open(filename, 'a', encoding='utf-8') as f:  #完成網頁底部架構
    #     base_html = """
    #     </tbody>
    #     </body>
    #     </html>
    #     """
    #     f.write(base_html)

def writeBaseHtml(filename): #基本網頁架構
    with open(filename, 'w+', encoding='utf-8') as f:
        base_html = """
        <html>
        <head>
            <meta charset='utf-8'>
            <style>#tds table,#tds tr,#tds td{border:1px solid #000;}</style>
        </head>
        <body>
        <table id="tds">
            <thead>
                <tr role='row'>
                <th>影片標題</th>
                <th>鏈結</th>
                <th>圖片</th>
                <th>觀看次數</th>
                <th>喜歡</th>
                <th>不喜歡</th>
                <th>留言數</th>
                <th>發布日期</th>
                </tr>
            </thead>
            <tbody>
        """
        f.write(base_html)

def writeRankHtml(filename): #基本網頁架構
    with open(filename, 'w+', encoding='utf-8') as f:
        base_html = """
        <html>
        <head>
            <meta charset='utf-8'>
            <style>#tds table,#tds tr,#tds td{border:1px solid #000;}</style>
        </head>
        <body>
        <table id="tds">
            <thead>
                <tr role='row'>
                <th>排名</th>
                <th>影片標題</th>
                <th>鏈結</th>
                <th>圖片</th>
                <th>觀看次數</th>
                <th>喜歡</th>
                <th>不喜歡</th>
                <th>留言數</th>
                <th>發布日期</th>
                </tr>
            </thead>
            <tbody>
        """
        f.write(base_html)

def writeIntoHtml(video_comments, filename):
    for row in video_comments['items']:
        playName = row['snippet']['topLevelComment']['snippet']['authorDisplayName']  # 留言者名字
        playerChannel = row['snippet']['topLevelComment']['snippet']['authorChannelUrl']
        textDisplay = row['snippet']['topLevelComment']['snippet']['textDisplay']  # 留言內容
        likeCount = row['snippet']['topLevelComment']['snippet']['likeCount']  # 留言按讚數
        html_str = """
                <tr>
                    <td>{{ playName }}</td>
                    <td>{{ playerChannel }}</td>
                    <td>{{ textDisplay }}</td>
                    <td>{{ likeCount }}</td>
                </tr>
        """
        comment = Template(html_str)
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(comment.render(textDisplay=textDisplay, playName=playName, playerChannel=playerChannel, likeCount=likeCount))

    # with open('sakurazaka_comment.html', 'a', encoding='utf-8') as f:
    #     base_html = """
    #     </body>
    #     </html>
    #     """
    #     f.write(base_html)

    #     publishedTime = row['snippet']['publishedAt']
    #     return publishedTime


# sql = "select * from youtube_videos order by viewCount desc limit 20" #查詢觀看次數最多的前20筆
def get_TotalviewCount():
    publishedAt_list = []
    sql = "select title, viewCount, published_date from youtube_videos"
    db.cursor.execute(sql)
    result = db.cursor.fetchall()
    for row in result:
        data = list(row)
        # print(data)
        publishedAt_list.append(data[-1][:-3])
    db.conn.commit()

    data = Counter(publishedAt_list) #統整日期清單  (根據同年同月份發布的影片, day不看)
    data_dict = list(data)
    p_date_list = []
    m_vc_list = []
    m_videos_list = []
    for d in range(len(data_dict)):  #計算當月總共有發布多少影片, 月分按讚數, 倒讚數, 留言數
        viewCount_sum_sql = "select published_date, sum(viewCount), count(published_date) from youtube_videos where published_date like '%{}%'".format(data_dict[d])
        db.cursor.execute(viewCount_sum_sql)
        result = db.cursor.fetchall()
        for row in result:
            print(row)
            p_date = str(list(row)[0])
            month_viewCount = int(list(row)[1])
            month_videos = int(list(row)[2])
            sql = "select id, totalVideos from youtube_vcount where totalViewCount = '{}'".format(month_viewCount)
            db.cursor.execute(sql)
            db.conn.commit()
            if db.cursor.rowcount == 0:
                sql = "insert into youtube_vcount(publishedMonth, totalViewCount, totalVideos) values ('{}', '{}', '{}')".format(
                    p_date, month_viewCount, month_videos)
                db.cursor.execute(sql)
                db.conn.commit()
            p_date_list.append(datetime.strptime(p_date[:-3], "%Y-%m"))
            m_vc_list.append(month_viewCount)
            m_videos_list.append(-month_videos)
    df = pd.DataFrame({'publishedMonth': p_date_list, 'TotalViewCount': m_vc_list, 'TotalVideos': m_videos_list})
    df.to_csv('templates/Hinatazaka46.csv')
    print(df)
    db.conn.close()

def get_plotly_line():
    # df = pd.DataFrame({'publishedMonth':p_date_list, 'TotalViewCount':m_vc_list, 'TotalVideos':m_videos_list})
    df = pd.read_csv('templates/Hinatazaka46.csv')
    fig = make_subplots(rows=2, cols=1)
    fig.add_trace(go.Bar(x=df['publishedMonth'], y=df['TotalViewCount'], name='日向坂46總觀看次數', text=df['TotalViewCount'],
                        textfont=dict(size=20),
                         marker=dict(color='#2EFAEB')), row=1, col=1)

    fig.add_trace(go.Bar(x=df['publishedMonth'], y=-df['TotalVideos'], name='日向坂46影片發布數',
                         textfont=dict(size=20),
                         marker=dict(color='#2EFAEB')), row=2, col=1)

    fig.update_layout(title_text='日向坂_YouTube觀看月份統計/影片數', font=dict(size=20))
    plotly.offline.plot(fig, filename='templates/Hinatazaka46.html', auto_open=False)
    fig.show()
def migrate_Barline():
    df1 = pd.read_csv('templates/Hinatazaka46.csv')
    df2 = pd.read_csv('templates/Nogizaka46.csv')
    df3 = pd.read_csv('templates/sakurazaka46.csv')
    fig = make_subplots(rows=2, cols=1)

    fig.add_trace(go.Bar(x=df1['publishedMonth'], y=df1['TotalViewCount'], name='日向坂46影片總觀看次數', text=df1['TotalViewCount'],
                        textfont=dict(size=20),
                         marker=dict(color='#2EFAEB')), row=1, col=1)

    fig.add_trace(go.Bar(x=df1['publishedMonth'], y=-df1['TotalVideos'], name='日向坂46影片發布數',
                        textfont=dict(size=20),
                         marker=dict(color='#2EFAEB')), row=2, col=1)

    fig.add_trace(go.Bar(x=df2['publishedMonth'], y=df2['TotalViewCount'], name='乃木坂46影片總觀看次數', text=df2['TotalViewCount'],
                        textfont=dict(size=20),
                         marker=dict(color='#E74AF4')), row=1, col=1)

    fig.add_trace(go.Bar(x=df2['publishedMonth'], y=-df2['TotalVideos'], name='乃木坂46影片發布數',
                        textfont=dict(size=20),
                         marker=dict(color='#E74AF4')), row=2, col=1)

    fig.add_trace(go.Bar(x=df3['publishedMonth'], y=df3['TotalViewCount'], name='櫻坂46總觀看次數',text=df3['TotalViewCount'],
                        textfont=dict(size=20),
                         marker=dict(color='#FCA2DB')), row=1, col=1)

    fig.add_trace(go.Bar(x=df3['publishedMonth'], y=-df3['TotalVideos'], name='櫻坂46影片發布數',
                         textfont=dict(size=20),
                         marker=dict(color='#FCA2DB')), row=2, col=1)

    fig.update_layout(title_text='YouTube觀看月份統計/影片數', font=dict(size=20))
    plotly.offline.plot(fig, filename='templates/sakamichi.html', auto_open=False)
    fig.show()

def get_videoId(channel_id): #抓取videoId
    base_url = 'https://www.googleapis.com/youtube/v3/'
    resp = youtube.channels().list(part='contentDetails', id=channel_id).execute()
    playlist_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    playlist_url = base_url + 'playlistItems?part={}&playlistId={}&maxResults={}&key={}'.format('snippet',
                                                                                                playlist_id,
                                                                                                50,
                                                                                                YOUTUBE_API_KEY)
    data = get_json_data(playlist_url)
    next_page_token = data['nextPageToken']
    for row in data['items']:

        title = row['snippet']['title']
        img = row['snippet']['thumbnails']['default']['url']
        video_url = 'https://www.youtube.com/watch?v=' + \
                    row['snippet']['resourceId']['videoId']
        videoId = row['snippet']['resourceId']['videoId']
    #     get_commentsThreads(videoId)
    # print('*'*100)

# get_commentsThreads(videoId='DWDVNjqaX4o')
# get_commentsThreads(videoId='Lx4xRBmhoKQ', filename='FutariSaion.html')

def read_htmlfile():
    from bs4 import BeautifulSoup
    with open('FutariSaion.html', 'r', encoding='utf-8') as file:

        soup = BeautifulSoup(file, 'html.parser')
        data = soup.find_all('tr')
        for row in data[1:]:
            playName = row[0]
            channel_url = row[1]
            comment = row[2]
            likeComment = row[3]
            print(playName, channel_url, comment, likeComment)
        print('*'*100)


def dataIntoSQL():
    sql = "select title, viewCount, likeCount, videoUrl from youtube_videos order by likeCount desc limit 5" #觀看次數TOP5
    db.cursor.execute(sql)
    db.conn.commit()

    result = db.cursor.fetchall()
    for row in result:
        title = row[0].replace(' ', '')
        print(title)
        videoId = row[-1].split('?')[1].replace('v=', '')
        get_commentsThreads(videoId, title)

    db.conn.close()



def channel_videos_noPage(channel_id): #沒有換頁版本
    base_url = 'https://www.googleapis.com/youtube/v3/'
    resp = youtube.channels().list(part='contentDetails', id=channel_id).execute()
    playlist_id = resp['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    playlist_url = base_url + 'playlistItems?part={}&playlistId={}&maxResults={}&key={}'.format('snippet',
                                                                                                playlist_id,
                                                                                                20,
                                                                                                YOUTUBE_API_KEY)
    data = get_json_data(playlist_url)
    data_list = []
    for row in data['items']:

        title = row['snippet']['title']
        img = row['snippet']['thumbnails']['default']['url']
        video_url = 'https://www.youtube.com/watch?v=' + \
                    row['snippet']['resourceId']['videoId']
        videoId = row['snippet']['resourceId']['videoId']
        video_desc = get_videos_statistics(videoId) #呼叫影片detail的內容
        viewCount = video_desc[0]
        likeCount = video_desc[1]
        dislikeCount = video_desc[2]
        commentCount = video_desc[3]

        published_data = publishedTime(videoId) #影片發布時間
        publishedAt = published_data[:10]
        # uploadDate = row['snippet']['publishedAt'][:10].replace("T", "").replace("Z", "")

        data_list.append([title, video_url, img, viewCount, likeCount, dislikeCount, commentCount, publishedAt])
    return data_list
        # print('標題:{}, 影片鏈結:{}, 圖片鏈結:{}, 觀看次數:{}, 喜歡:{}, 不喜歡:{}, 留言數:{}, 發布時間:{}'.format(title,
        #                                                                                 video_url, img, viewCount,
        #                                                                                 likeCount, dislikeCount,
        #                                                                                 commentCount, publishedAt))




def connect_Youtube():
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file('client_secret_562839061912-n90l98f6ocn581r5ai1jt6a0v2kipo3u.apps.googleusercontent.com.json',
                                                                   scopes=['https://www.googleapis.com/auth/youtube.force-ssl'])
    flow.redirect_uri = 'https://oauth2.example.com/code'

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        state='sample_passthrough_value',
        login_hint='theforeverwen@gmail.com',
        prompt='consent',
        include_granted_scopes='true')

    YOUTUBE_API_KEY = "AIzaSyCt893vHOjQVlzmaKSBXBCcsr8FFO4GK_U"  # API金鑰

# get_TotalviewCount()
# get_plotly_line()

