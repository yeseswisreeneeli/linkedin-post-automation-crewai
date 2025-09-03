import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

import base64
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
import requests
load_dotenv()  

# The same SCOPES used during your quickstart
SCOPES = [os.getenv('GMAIL_SCOPE')]

# Set these for your setup:
PROJECT_ID = os.getenv("GOOGLE_PROJECT_ID") # <-- replace with your Project ID
TOPIC_NAME = os.getenv("GMAIL_TOPIC_NAME")  # <-- replace with your Pub/Sub topic name (not subscription)
LABEL_NAME = os.getenv("TARGET_LABEL_NAME")  # <-- your Gmail label's name

def get_gmail_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            raise Exception("You must authorize the app and have a valid token.json file.")
    return build('gmail', 'v1', credentials=creds)

def get_label_id(service, label_name): 
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])
    for label in labels:
        if label['name'] == label_name:
            return label['id']
    raise Exception(f"Label '{label_name}' not found. Please check spelling or create it in Gmail.")

def send_gmail_watch(service, label_id, topic_name):
    body = {
        'labelIds': [label_id],
        'topicName': topic_name,
        'labelFilterBehavior': 'INCLUDE'
    }
    response = service.users().watch(userId='me', body=body).execute()
    print("Watch response from Gmail API:")
    print(response)


def get_message_body(service, label_id): #returns html content
    response = service.users().messages().list(userId='me', labelIds=[label_id]).execute()
    message_id = response['messages'][0]['id']
    message = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    body_content = None
    if "payload" in message:
        payload = message['payload']
        if 'body' in payload and 'data' in payload['body']:
            data = payload['body']['data']
            decoded_bytes = base64.urlsafe_b64decode(data.encode('UTF-8'))
            body_content = decoded_bytes.decode('UTF-8')
        elif 'parts' in payload:
            for part in payload['parts']:
                # if part['mimeType'] == 'text/plain' and 'body' in part and 'data' in part['body']:
                #     data = part['body']['data']
                #     decoded_bytes = base64.urlsafe_b64decode(data.encode('UTF-8'))
                #     body_content = decoded_bytes.decode('UTF-8')
                #     break
                if part['mimeType'] == 'text/html' and 'body' in part and 'data' in part['body']:
                    data = part['body']['data']
                    decoded_bytes = base64.urlsafe_b64decode(data.encode('UTF-8'))
                    body_content = decoded_bytes.decode('UTF-8')
    return body_content 

def get_top_news_data(mail_html_content):
    title, content_page_link, img_src = None, None, None
    soup = BeautifulSoup(mail_html_content, 'lxml')
    top_news_strong = soup.find('strong', string="Top News")
    top_news_tr = top_news_strong.find_parent("tr") if top_news_strong else print("Top News not found")
    next_tr = top_news_tr.find_next_sibling() if top_news_tr else print("top_news_tr not found")
    a_tag = next_tr.find('a') if next_tr else print("Next sibling not found")
    if a_tag:
        content_page_link = a_tag.get('href')
        title = a_tag.get_text(strip=True)
    img_list = soup.find_all('img')
    img_src = img_list[1].get('src') if len(img_list) > 1 else None
    return title, content_page_link, img_src

def download_image(img_url):
    image_path = None
    response = requests.get(img_url)
    # Extract filename from URL, or set your own
    filename = "post_image."+img_url.split(".")[-1] if img_url else "default_image.jpg" 

    # Write the image content to a file
    with open(filename, 'wb') as f:
        f.write(response.content)
    image_path = f'./{filename}'
    print(f"Image saved in path {image_path}")
    return image_path

def get_text_content(page_url: str):
    response = requests.get(page_url)
    response.raise_for_status() 
    soup = BeautifulSoup(response.text, 'lxml')
    page_text = soup.get_text(separator='\n', strip=True)
    return page_text
         

if __name__ == '__main__':
    # Initialize gmail API client
    service = get_gmail_service()

    # Find label ID for your "Alpha Signal" label
    label_id = get_label_id(service, LABEL_NAME)
    print(f"Label '{LABEL_NAME}' ID is: {label_id}")

    # Pub/Sub topic full name (expected format)
    topic_full_name = f'projects/{PROJECT_ID}/topics/{TOPIC_NAME}'

    # Send the watch request
    send_gmail_watch(service, label_id, topic_full_name)
