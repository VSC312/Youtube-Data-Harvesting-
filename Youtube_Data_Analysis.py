import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_option_menu import option_menu
import pymongo
from googleapiclient.discovery import build
from PIL import Image
import sqlite3
import json

# SETTING PAGE CONFIGURATIONS
icon = Image.open("Youtube_logo.png")
st.set_page_config(page_title= "Youtube Data Harvesting",
                   page_icon= icon,
                   layout= "wide",
                   initial_sidebar_state= "expanded",
                   menu_items={'About': """# By Vardhan Choudhary*"""})

# CREATING OPTION MENU
with st.sidebar:
    selected = option_menu(None, ["Home","Extract & Transform","View"], 
                           icons=["house-door-fill","tools","card-text"],
                           default_index=0,
                           orientation="vertical",
                           styles={"nav-link": {"font-size": "30px", "text-align": "centre", "margin": "0px", 
                                                "--hover-color": "#C80101"},
                                   "icon": {"font-size": "30px"},
                                   "container" : {"max-width": "6000px"},
                                   "nav-link-selected": {"background-color": "#C80101"}})

# Bridging a connection with MongoDB Atlas and Creating a new database(youtube_data)
client = pymongo.MongoClient("localhost:27017")
db = client.Youtube_Data_Sam

# SQLite Connection
conn = sqlite3.connect('youtube_data.db')
cursor = conn.cursor()

# Create necessary tables if they don't exist
cursor.execute('''
CREATE TABLE IF NOT EXISTS channels (
    Channel_id TEXT PRIMARY KEY,
    Channel_name TEXT,
    Playlist_id TEXT,
    Subscribers INTEGER,
    Views INTEGER,
    Total_videos INTEGER,
    Description TEXT,
    Country TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS videos (
    Channel_name TEXT,
    Channel_id TEXT,
    Video_id TEXT PRIMARY KEY,
    Title TEXT,
    Tags TEXT,
    Thumbnail TEXT,
    Description TEXT,
    Published_date TEXT,
    Duration TEXT,
    Views INTEGER,
    Likes INTEGER,
    Comments INTEGER,
    Favorite_count INTEGER,
    Definition TEXT,
    Caption_status TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS comments (
    Comment_id TEXT PRIMARY KEY,
    Video_id TEXT,
    Comment_text TEXT,
    Comment_author TEXT,
    Comment_posted_date TEXT,
    Like_count INTEGER,
    Reply_count INTEGER
)
''')
conn.commit()

# BUILDING CONNECTION WITH YOUTUBE API
api_key = "AIzaSyC9lK5JiTsTcRPq121wKccpM6CiJe5CRgg"
youtube = build('youtube','v3',developerKey=api_key)


# FUNCTION TO GET CHANNEL DETAILS
def get_channel_details(channel_id):
    ch_data = []
    response = youtube.channels().list(part = 'snippet,contentDetails,statistics',
                                     id= channel_id).execute()

    for i in range(len(response['items'])):
        data = dict(Channel_id = channel_id[i],
                    Channel_name = response['items'][i]['snippet']['title'],
                    Playlist_id = response['items'][i]['contentDetails']['relatedPlaylists']['uploads'],
                    Subscribers = response['items'][i]['statistics']['subscriberCount'],
                    Views = response['items'][i]['statistics']['viewCount'],
                    Total_videos = response['items'][i]['statistics']['videoCount'],
                    Description = response['items'][i]['snippet']['description'],
                    Country = response['items'][i]['snippet'].get('country')
                    )
        ch_data.append(data)
    return ch_data


# FUNCTION TO GET VIDEO IDS
def get_channel_videos(channel_id):
    video_ids = []
    # get Uploads playlist id
    res = youtube.channels().list(id=channel_id, 
                                  part='contentDetails').execute()
    playlist_id = res['items'][0]['contentDetails']['relatedPlaylists']['uploads']
    next_page_token = None
    
    while True:
        res = youtube.playlistItems().list(playlistId=playlist_id, 
                                           part='snippet', 
                                           maxResults=50,
                                           pageToken=next_page_token).execute()
        
        for i in range(len(res['items'])):
            video_ids.append(res['items'][i]['snippet']['resourceId']['videoId'])
        next_page_token = res.get('nextPageToken')
        
        if next_page_token is None:
            break
    return video_ids


# FUNCTION TO GET VIDEO DETAILS
def get_video_details(v_ids):
    video_stats = []
    
    for i in range(0, len(v_ids), 50):
        response = youtube.videos().list(
                    part="snippet,contentDetails,statistics",
                    id=','.join(v_ids[i:i+50])).execute()
        for video in response['items']:
            video_details = dict(Channel_name = video['snippet']['channelTitle'],
                                Channel_id = video['snippet']['channelId'],
                                Video_id = video['id'],
                                Title = video['snippet']['title'],
                                Tags = video['snippet'].get('tags'),
                                Thumbnail = video['snippet']['thumbnails']['default']['url'],
                                Description = video['snippet']['description'],
                                Published_date = video['snippet']['publishedAt'],
                                Duration = video['contentDetails']['duration'],
                                Views = video['statistics']['viewCount'],
                                Likes = video['statistics'].get('likeCount'),
                                Comments = video['statistics'].get('commentCount'),
                                Favorite_count = video['statistics']['favoriteCount'],
                                Definition = video['contentDetails']['definition'],
                                Caption_status = video['contentDetails']['caption']
                               )
            video_stats.append(video_details)
    return video_stats


# FUNCTION TO GET COMMENT DETAILS
def get_comments_details(v_id):
    comment_data = []
    try:
        next_page_token = None
        while True:
            response = youtube.commentThreads().list(part="snippet,replies",
                                                    videoId=v_id,
                                                    maxResults=100,
                                                    pageToken=next_page_token).execute()
            for cmt in response['items']:
                data = dict(Comment_id = cmt['id'],
                            Video_id = cmt['snippet']['videoId'],
                            Comment_text = cmt['snippet']['topLevelComment']['snippet']['textDisplay'],
                            Comment_author = cmt['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                            Comment_posted_date = cmt['snippet']['topLevelComment']['snippet']['publishedAt'],
                            Like_count = cmt['snippet']['topLevelComment']['snippet']['likeCount'],
                            Reply_count = cmt['snippet']['totalReplyCount']
                           )
                comment_data.append(data)
            next_page_token = response.get('nextPageToken')
            if next_page_token is None:
                break
    except:
        pass
    return comment_data


# FUNCTION TO GET CHANNEL NAMES FROM SQLite
def channel_names():
    cursor.execute("SELECT Channel_name FROM channels")
    return [row[0] for row in cursor.fetchall()]


# HOME PAGE
if selected == "Home":
    # Title Image
    st.image("title.png")
    col1,col2 = st.columns(2,gap= 'medium')
    col1.markdown("## :blue[Domain] : Social Media")
    col1.markdown("## :blue[Technologies used] : Python,MongoDB, Youtube Data API, SQLite, Streamlit")
    col1.markdown("## :blue[Overview] : Retrieving the Youtube channels data from the Google API, storing it in a MongoDB as data lake, migrating and transforming data into a SQLite database, then querying the data and displaying it in the Streamlit app.")
    col2.markdown("#   ")
    col2.markdown("#   ")
    col2.markdown("#   ")

# EXTRACT AND TRANSFORM PAGE
if selected == "Extract & Transform":
    st.markdown("#    ")
    st.write("### Enter YouTube Channel_ID below :")
    ch_id = st.text_input("Hint : Goto channel's home page > Right click > View page source > Find channel_id").split(',')

    if ch_id and st.button("Extract Data"):
        ch_details = get_channel_details(ch_id)
        st.write(f'#### Extracted data from :green["{ch_details[0]["Channel_name"]}"] channel')
        st.table(ch_details)

    if st.button("Upload to MongoDB"):
        with st.spinner('Please Wait for it...'):
            ch_details = get_channel_details(ch_id)
            v_ids = get_channel_videos(ch_id)
            vid_details = get_video_details(v_ids)
            
            def comments():
                com_d = []
                for i in v_ids:
                    com_d += get_comments_details(i)
                return com_d
            comm_details = comments()

            # Insert new data into MongoDB
            collections1 = db.channel_details
            collections1.insert_many(ch_details)

            collections2 = db.video_details
            collections2.insert_many(vid_details)

            collections3 = db.comments_details
            collections3.insert_many(comm_details)
            st.success("Upload to MongoDB successful !!")

    if st.button("Submit"):
        with st.spinner('Please Wait for it...'):
            # Insert new data into SQLite
            collections = db.channel_details
            query = """INSERT OR IGNORE INTO channels (Channel_id, Channel_name, Playlist_id, Subscribers, Views, Total_videos, Description, Country)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)"""
            for i in collections.find({}, {'_id': 0}):
                values = [str(val) if isinstance(val, list) else val for val in i.values()]
                cursor.execute(query, tuple(values))
            conn.commit()

            collections1 = db.video_details
            query1 = """INSERT OR IGNORE INTO videos (Channel_name, Channel_id, Video_id, Title, Tags, Thumbnail, Description, Published_date, Duration, Views, Likes, Comments, Favorite_count, Definition, Caption_status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"""
            for i in collections1.find({}, {'_id': 0}):
                values = [json.dumps(val) if isinstance(val, list) else str(val) for val in i.values()]
                cursor.execute(query1, tuple(values))
            conn.commit()

            collections2 = db.comments_details
            query2 = """INSERT OR IGNORE INTO comments (Comment_id, Video_id, Comment_text, Comment_author, Comment_posted_date, Like_count, Reply_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?)"""
            for vid in collections1.find({}, {'_id': 0}):
                for i in collections2.find({'Video_id': vid['Video_id']}, {'_id': 0}):
                    values = [str(val) if isinstance(val, list) else val for val in i.values()]
                    cursor.execute(query2, tuple(values))
            conn.commit()

            st.success("Transformation to SQLite successful !!")




# VIEW PAGE
if selected == "View":
    st.write("## :orange[Select any question to get Insights]")
    
    questions = st.selectbox('Questions',
        ['1. What are the names of all the videos and their corresponding channels?',
        '2. Which channels have the most number of videos, and how many videos do they have?',
        '3. What are the top 10 most viewed videos and their respective channels?',
        '4. How many comments were made on each video, and what are their corresponding video names?',
        '5. Which videos have the highest number of likes, and what are their corresponding channel names?',
        '6. What is the total number of likes for each video, and what are their corresponding video names?',
        '7. What is the total number of views for each channel, and what are their corresponding channel names?',
        '8. What are the names of all the channels that have published videos in the year 2022?',
        '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?',
        '10. Which videos have the highest number of comments, and what are their corresponding channel names?'])

    if questions == '1. What are the names of all the videos and their corresponding channels?':
        cursor.execute("""SELECT Title AS Video_Title, Channel_name AS Channel_Name
                            FROM videos
                            ORDER BY Channel_name""")
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        st.write(df)

    elif questions == '2. Which channels have the most number of videos, and how many videos do they have?':
        cursor.execute("""SELECT Channel_name AS Channel_Name, Total_videos AS Total_Videos
                            FROM channels
                            ORDER BY Total_videos DESC""")
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        st.write(df)

    elif questions == '3. What are the top 10 most viewed videos and their respective channels?':
        cursor.execute("""SELECT Title AS Video_Title, Channel_name AS Channel_Name, Views AS View_Count
                            FROM videos
                            ORDER BY Views DESC
                            LIMIT 10""")
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        st.write(df)

    elif questions == '4. How many comments were made on each video, and what are their corresponding video names?':
        cursor.execute("""SELECT Title AS Video_Title, Comments AS Comment_Count
                            FROM videos
                            ORDER BY Comments DESC""")
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        st.write(df)

    elif questions == '5. Which videos have the highest number of likes, and what are their corresponding channel names?':
        cursor.execute("""SELECT Title AS Video_Title, Channel_name AS Channel_Name, Likes AS Like_Count
                            FROM videos
                            ORDER BY Likes DESC""")
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        st.write(df)

    elif questions == '6. What is the total number of likes for each video, and what are their corresponding video names?':
        cursor.execute("""SELECT Title AS Video_Title, Likes AS Like_Count
                            FROM videos
                            ORDER BY Likes DESC""")
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        st.write(df)

    elif questions == '7. What is the total number of views for each channel, and what are their corresponding channel names?':
        cursor.execute("""SELECT Channel_name AS Channel_Name, Views AS View_Count
                            FROM channels
                            ORDER BY Views DESC""")
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        st.write(df)

    elif questions == '8. What are the names of all the channels that have published videos in the year 2022?':
        cursor.execute("""SELECT DISTINCT Channel_name AS Channel_Name
                            FROM videos
                            WHERE Published_date LIKE '2022%'""")
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        st.write(df)

    elif questions == '9. What is the average duration of all videos in each channel, and what are their corresponding channel names?':
        cursor.execute("""SELECT Channel_name AS Channel_Name, AVG(Duration) AS Average_Duration
                            FROM videos
                            GROUP BY Channel_name""")
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        st.write(df)

    elif questions == '10. Which videos have the highest number of comments, and what are their corresponding channel names?':
        cursor.execute("""SELECT Title AS Video_Title, Channel_name AS Channel_Name, Comments AS Comment_Count
                            FROM videos
                            ORDER BY Comments DESC""")
        df = pd.DataFrame(cursor.fetchall(), columns=[desc[0] for desc in cursor.description])
        st.write(df)

