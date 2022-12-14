from bs4 import BeautifulSoup
import requests
import json
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

def save_locally(df):
    df.to_excel('leetcode_problems.xlsx', index=False)
    print('dataframe saved locally')

def push_to_gsheet(df):
    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    credentials = Credentials.from_service_account_file(
        'secret/key_google.json',
        scopes=scopes
    )

    gc = gspread.authorize(credentials)
    sheet = gc.open_by_url('https://docs.google.com/spreadsheets/d/1X2pQyaEXwmCnopdkDCP-zzl2L6tq0J3CYoQCV3Ze8Zk/edit#gid=0')
    worksheet = sheet.get_worksheet(0)
    worksheet.clear()
    worksheet.update([df.columns.values.tolist()] + df.values.tolist(), value_input_option='USER_ENTERED')    

    print('pushed to gsheet')

def get_scraped_attributes(title_slug):
    if not title_slug:
        return None

    url = 'https://leetcode.com/problems/' + title_slug
    
    while True:
        page = requests.get(url)
        soup = BeautifulSoup(page.text, 'html.parser')
        obj = json.loads(soup.find(id = '__NEXT_DATA__').string)

        try:
            ob = obj['props']['pageProps']['dehydratedState']['queries'][0]['state']['data']['question']
            break
        except:
            continue

    return ob

def main():
    page = requests.get('https://leetcode.com/api/problems/algorithms/')
    obj = json.loads(page.text)
    ob = obj['stat_status_pairs']

    ob = ob[ : 2]

    total = len(ob)
    counter = 0

    frontend_question_id = []
    question_title = []
    title_slug = []
    total_acs = []
    total_submitted = []
    difficulty = []
    paid_only = []
    likes = []
    dislikes = []
    like_dislike_ratio = []
    
    for item in ob:
        counter = counter + 1
        print('pulling ' + item['stat']['question__title'], str(counter) + '/' + str(total))

        # if not item['stat']['question__title_slug']:
        #     continue
        
        frontend_question_id.append(item['stat']['frontend_question_id'])
        question_title.append(item['stat']['question__title'])
        title_slug.append(item['stat']['question__title_slug'])
        total_acs.append(item['stat']['total_acs'])
        total_submitted.append(item['stat']['total_submitted'])
        difficulty.append(item['difficulty']['level'])
        paid_only.append(item['paid_only'])
        
        ob_scraped = get_scraped_attributes(title_slug[-1])

        if not ob_scraped:
            likes.append(None)
            dislikes.append(None)
            like_dislike_ratio.append(None)
        else:
            likes.append(ob_scraped['likes'])
            dislikes.append(ob_scraped['dislikes'])
            like_dislike_ratio.append(likes[-1] / max(dislikes[-1], 1))
    
    name_link = []
    for i in range(total):
        name_link.append(question_title[i] + '#https://leetcode.com/problems/' + title_slug[i])

    data = {
        'id' : frontend_question_id,
        'title' : name_link,
        'ACs' : total_acs,
        'total_submitted' : total_submitted,
        'difficulty' : difficulty,
        'paid_only' : paid_only,
        'likes' : likes,
        'dislikes' : dislikes,
        'like_dislike_ratio' : like_dislike_ratio
    }

    df = pd.DataFrame(data)
    def make_clickable(val):
        title, url = val.split('#')
        return "=HYPERLINK(\"{}\", \"{}\")".format(url, title)
    df['title'] = df['title'].apply(lambda x: make_clickable(x))
    df = df.sort_values(by=['id'])

    # save_locally(df)
    push_to_gsheet(df)

if __name__ == '__main__':
    main()