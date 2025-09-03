from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import base64
from watchreq_script import get_gmail_service, get_label_id, send_gmail_watch, get_message_body, get_top_news_data, download_image, get_text_content, PROJECT_ID, TOPIC_NAME, LABEL_NAME
from my_crew import kickoff_linkedin_post
from linkedin_post import markdown_to_linkedin_unicode, post_to_linkedin
from dotenv import load_dotenv
import os

load_dotenv()

linkedin_access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
linkedin_owner_urn = os.getenv("LINKEDIN_OWNER_URN")


app = FastAPI()

@app.post("/mail_payload")
async def mail_payload(request: Request):
    """
    This endpoint will receive POST requests from Pub/Sub push.
    The incoming request body will be JSON with a 'message' object.
    """
    try:
        data = await request.json()
        print("Received payload:", data)

        # ---- Example: decode Pub/Sub message if needed ----
        
        if "message" in data and "data" in data["message"]:
            # Pub/Sub sends 'data' base64 encoded
            decoded_bytes = base64.b64decode(data["message"]["data"])
            decoded_str = decoded_bytes.decode("utf-8")
            print("Decoded Pub/Sub message data:", decoded_str)

        service = get_gmail_service()
        label_id = get_label_id(service, LABEL_NAME)
        topic_full_name = f'projects/{PROJECT_ID}/topics/{TOPIC_NAME}'
        html_code = get_message_body(service, label_id)
        title, article_link, img_src = get_top_news_data(html_code)
        print(f"----------- Extracted Top News Data: Title: {title}, Link: {article_link}, Image Source: {img_src}")
        image_path = download_image(img_src) if img_src else None
        print(f"----------- Downloaded image path: {image_path}")
        text_content = get_text_content(article_link)
        print(f"----------- Extracted text content")
        agent_output = kickoff_linkedin_post(content=text_content, link=article_link)
        print(f"----------- Crew generated output successfully")
        formatted_post = markdown_to_linkedin_unicode(agent_output)
        print(f"----------- Formatted post for LinkedIn")
        print(f"----------- Posting to LinkedIn")
        linkedin_response = post_to_linkedin(access_token=linkedin_access_token, image_path=image_path, post_text=formatted_post, owner_urn=linkedin_owner_urn)
        if linkedin_response:
            print("Complete workflow successful!")
        else:
            print("Complete workflow failed")
        # Return success so Pub/Sub knows we processed it
        return JSONResponse(content={"status": "ok"}, status_code=200)

    except Exception as e:
        print("Error processing request:", e)
        # Pub/Sub will retry if not 2xx
        return JSONResponse(content={"status": "error"}, status_code=500)

@app.post("/webhooks")
async def dummy():
    return JSONResponse(content={"status": "ok"}, status_code=200)

if __name__ == "__main__":
    # Run app locally for testing
    uvicorn.run(app, host="0.0.0.0", port=8000)
