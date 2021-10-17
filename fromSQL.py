import db
from youtube1 import writeBaseHtml, channel_videos_noPage, connect_Youtube, writeRankHtml
from flask import Flask, request, render_template, redirect
import google_auth_oauthlib.flow
from googleapiclient.discovery import build
from jinja2 import Template

flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
    '../API_KEY/client_secret_562839061912-n90l98f6ocn581r5ai1jt6a0v2kipo3u.apps.googleusercontent.com.json',
    scopes=['https://www.googleapis.com/auth/youtube.force-ssl'])
flow.redirect_uri = 'https://oauth2.example.com/code'

authorization_url, state = flow.authorization_url(
    access_type='offline',
    state='sample_passthrough_value',
    login_hint='theforeverwen@gmail.com',
    prompt='consent',
    include_granted_scopes='true')

YOUTUBE_API_KEY = "AIzaSyCt893vHOjQVlzmaKSBXBCcsr8FFO4GK_U"  # API金鑰
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

# app = Flask(__name__)
#
#
#
#
# @app.route('/')
# def index():
#     sql = "select title, videoUrl, imgUrl, viewCount, likeCount, dislikeCount, commentCount, published_date from youtube_videos limit 10"
#     db.cursor.execute(sql)
#     db.conn.commit()
#     result = db.cursor.fetchall()
    # writeBaseHtml('sakuRank.html')
#     for row in result:
#         data = list(row)
#         img_url = data[2]
#         return render_template('home.html', len=len(data), data=data, imgUrl=img_url)
#
#
#
# if __name__=='__main__':
#     app.run(port=3000)



def video_rank():
    sql = "select title, videoUrl, imgUrl, viewCount, likeCount, dislikeCount, commentCount, published_date from youtube_videos " \
          "order by viewCount desc limit 20"
    db.cursor.execute(sql)
    db.conn.commit()
    result = db.cursor.fetchall()
    writeRankHtml('templates/nogiRank.html')
    rank = 0
    for row in result:
        rank += 1
        title = row[0]
        videoUrl = row[1]
        imgUrl = row[2]
        viewCount = row[3]
        likeCount = row[4]
        dislikeCount = row[5]
        commentCount = row[6]
        published_date = row[7]
        html_str = """
                        <tr>
                            <td>{{ rank }}</td>
                            <td>{{ title }}</td>
                            <td><a href="{{ videoUrl }}" target="_blank">{{ videoUrl }}</td>
                            <td><img src="{{ imgUrl }}"></td>
                            <td>{{ viewCount }}</td>
                            <td>{{ likeCount }}</td>
                            <td>{{ dislikeCount }}</td>
                            <td>{{ commentCount }}</td>
                            <td>{{ published_date }}</td>
                        </tr>
                """
        comment = Template(html_str)
        with open('templates/nogiRank.html', 'a', encoding='utf-8') as f:
            f.write(comment.render(rank=rank, title=title, videoUrl=videoUrl, imgUrl=imgUrl, viewCount=viewCount,
                                   likeCount=likeCount, dislikeCount=dislikeCount, commentCount=commentCount,
                                   published_date=published_date))

    with open('templates/nogiRank.html', 'a', encoding='utf-8') as f:
        base_html = """
        </tbody>
        </table>
        </body>
        </html>
        """
        f.write(base_html)
    db.conn.close()

# sql = "select title, viewCount, published_date from youtube_videos where published_date like '%2015-12%' order by viewCount desc"
# db.cursor.execute(sql)
# db.conn.commit()
# result = db.cursor.fetchall()
# for row in result:
#     print(row)
# db.conn.close()

def channelnoPage():
    # channel_id = 'UCmr9bYmymcBmQ1p2tLBRvwg' #櫻坂46channel
    # channel_id = 'UCUzpZpX2wRYOk3J8QTFGxDg' #乃木坂
    channel_id = 'UCR0V48DJyWbwEAdxLL5FjxA' #日向坂

    data = channel_videos_noPage(channel_id=channel_id)  #type=list
    writeBaseHtml('templates/hinata_recent.html')

    for row in data:
        if type(row) is type(None):
            print('no find')
        else:
            title = row[0]
            videoUrl = row[1]
            imgUrl = row[2]
            viewCount = row[3]
            likeCount = row[4]
            dislikeCount = row[5]
            commentCount = row[6]
            published_date = row[7]
            html_str = """
                            <tr>
                                <td>{{ title }}</td>
                                <td><a href="{{ videoUrl }}" target="_blank">{{ videoUrl }}</td>
                                <td><img src="{{ imgUrl }}"></td>
                                <td>{{ viewCount }}</td>
                                <td>{{ likeCount }}</td>
                                <td>{{ dislikeCount }}</td>
                                <td>{{ commentCount }}</td>
                                <td>{{ published_date }}</td>
                            </tr>
                    """
            comment = Template(html_str)
            with open('templates/hinata_recent.html', 'a', encoding='utf-8') as f:
                f.write(comment.render(title=title, videoUrl=videoUrl, imgUrl=imgUrl, viewCount=viewCount,
                                       likeCount=likeCount, dislikeCount=dislikeCount, commentCount=commentCount,
                                       published_date=published_date))

    with open('templates/hinata_recent.html', 'a', encoding='utf-8') as f:
        base_html = """
        </tbody>
        </table>
        </body>
        </html>
        """
        f.write(base_html)

#top20觀看次數(綜合)
def mixRank():
    sql = "select * from saku_youtube union select * from nogi_youtube union select * from hinata_youtube order by viewcount desc limit 20;"

    db.cursor.execute(sql)
    db.conn.commit()
    writeBaseHtml('templates/mixRank.html')
    result = db.cursor.fetchall()
    rank = 1
    for row in result:
        row = list(row[1:])
        rank = rank
        title = row[0]
        videoUrl = row[1]
        imgUrl = row[2]
        viewCount = row[3]
        likeCount = row[4]
        dislikeCount = row[5]
        commentCount = row[6]
        published_date = row[7]
        html_str = """
                        <tr>
                            <td>{{ rank }}</td>
                            <td>{{ title }}</td>
                            <td><a href="{{ videoUrl }}" target="_blank">{{ videoUrl }}</td>
                            <td><img src="{{ imgUrl }}"></td>
                            <td>{{ viewCount }}</td>
                            <td>{{ likeCount }}</td>
                            <td>{{ dislikeCount }}</td>
                            <td>{{ commentCount }}</td>
                            <td>{{ published_date }}</td>
                        </tr>
                """
        comment = Template(html_str)
        with open('templates/mixRank.html', 'a', encoding='utf-8') as f:
            f.write(comment.render(rank=rank, title=title, videoUrl=videoUrl, imgUrl=imgUrl, viewCount=viewCount,
                                   likeCount=likeCount, dislikeCount=dislikeCount, commentCount=commentCount,
                                   published_date=published_date))
        rank += 1
    with open('templates/mixRank.html', 'a', encoding='utf-8') as f:
        base_html = """
        </tbody>
        </table>
        </body>
        </html>
        """
        f.write(base_html)
    db.conn.close()
