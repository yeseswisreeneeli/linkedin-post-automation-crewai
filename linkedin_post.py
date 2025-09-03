import requests
import json
from dotenv import load_dotenv
import os
import re

load_dotenv()

linkedin_access_token = os.getenv("LINKEDIN_ACCESS_TOKEN")
linkedin_owner_urn = os.getenv("LINKEDIN_OWNER_URN")


def register_Image(access_token, owner_urn=linkedin_owner_urn):
    """
    Register an image upload with LinkedIn API
    
    Args:
        access_token (str): LinkedIn API access token
        owner_urn (str): Owner URN (defaults to provided example)
    
    Returns:
        tuple: (asset, upload_url) if successful, (None, None) if failed
    """
    
    url = "https://api.linkedin.com/v2/assets?action=registerUpload"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    body = {
        "registerUploadRequest": {
            "recipes": [
                "urn:li:digitalmediaRecipe:feedshare-image"
            ],
            "owner": owner_urn,
            "serviceRelationships": [
                {
                    "relationshipType": "OWNER",
                    "identifier": "urn:li:userGeneratedContent"
                }
            ]
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        response_data = response.json()
        
        # Extract asset and upload URL from response
        asset = response_data["value"]["asset"]
        upload_url = response_data["value"]["uploadMechanism"]["com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"]["uploadUrl"]
        
        return asset, upload_url
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None, None
    except KeyError as e:
        print(f"Response parsing failed - missing key: {e}")
        return None, None
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        return None, None

def upload_Image(upload_url, access_token, file_path):
    """
    Upload an image file to LinkedIn using the provided upload URL
    
    Args:
        upload_url (str): The upload URL obtained from register_Image()
        access_token (str): LinkedIn API access token
        file_path (str): Path to the image file to upload
    
    Returns:
        int: HTTP status code of the upload request, or None if failed
    """
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"Error: File not found at path: {file_path}")
        return None
    
    # Determine content type based on file extension
    file_extension = os.path.splitext(file_path)[1].lower()
    content_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp'
    }
    
    content_type = content_type_map.get(file_extension, 'application/octet-stream')
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": content_type
    }
    
    try:
        # Read the image file in binary mode
        with open(file_path, 'rb') as image_file:
            image_data = image_file.read()
        
        # Make PUT request to upload the image
        response = requests.put(upload_url, headers=headers, data=image_data)
        
        # Return the status code
        return response.status_code
        
    except FileNotFoundError:
        print(f"Error: File not found: {file_path}")
        return None
    except PermissionError:
        print(f"Error: Permission denied accessing file: {file_path}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"Upload request failed: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error during upload: {e}")
        return None

def create_post(access_token, asset_urn, post_text, media_title, media_description, owner_urn=linkedin_owner_urn):
    """
    Create a LinkedIn UGC post with an image
    
    Args:
        access_token (str): LinkedIn API access token
        asset_urn (str): The asset URN from register_Image() function
        post_text (str): The text content of the post
        media_title (str): Title for the media (optional)
        media_description (str): Description for the media (optional)
        author_urn (str): Author URN (defaults to provided example)
    
    Returns:
        dict: Full response from LinkedIn API, or None if failed
    """
    
    url = "https://api.linkedin.com/v2/ugcPosts"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "X-Restli-Protocol-Version": "2.0.0"
    }
    
    body = {
        "author": owner_urn,
        "lifecycleState": "PUBLISHED",
        "specificContent": {
            "com.linkedin.ugc.ShareContent": {
                "shareCommentary": {
                    "text": post_text
                },
                "shareMediaCategory": "IMAGE",
                "media": [
                    {
                        "status": "READY",
                        "description": {
                            "text": media_description
                        },
                        "media": asset_urn,
                        "title": {
                            "text": media_title
                        }
                    }
                ]
            }
        },
        "visibility": {
            "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=body)
        response.raise_for_status()  # Raises an HTTPError for bad responses
        
        response_data = response.json()
        return response_data
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response status code: {e.response.status_code}")
            print(f"Response text: {e.response.text}")
        return None
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON response: {e}")
        return None

# Complete workflow function that combines all three steps
def post_to_linkedin(access_token, image_path, post_text, media_title="LinkedIn Post", media_description="Posted via linkedin", owner_urn=linkedin_owner_urn):
    """
    Complete workflow to post an image to LinkedIn
    
    Args:
        access_token (str): LinkedIn API access token
        image_path (str): Path to the image file
        post_text (str): Text content for the post
        media_title (str): Title for the image
        media_description (str): Description for the image
        author_urn (str): Author URN
    
    Returns:
        dict: Response from the post creation, or None if any step failed
    """
    
    print("Step 1: Registering image upload...")
    asset_urn, upload_url = register_Image(access_token, owner_urn)
    
    if not asset_urn or not upload_url:
        print("Failed to register image upload")
        return None
    
    print(f"Step 2: Uploading image from {image_path}...")
    status_code = upload_Image(upload_url, access_token, image_path)
    
    if not status_code or status_code not in [200, 201]:
        print(f"Failed to upload image. Status code: {status_code}")
        return None
    
    print("Step 3: Creating LinkedIn post...")
    response = create_post(access_token, asset_urn, post_text, media_title, media_description, owner_urn)
    
    if response:
        print("Post created successfully!")
        return response
    else:
        print("Failed to create post")
        return None

def markdown_to_linkedin_unicode(text):
    """
    Convert markdown-style formatting to LinkedIn-compatible Unicode characters
    """
    
    # Unicode character mappings for bold sans-serif
    bold_map = {
        'A': '𝗔', 'B': '𝗕', 'C': '𝗖', 'D': '𝗗', 'E': '𝗘', 'F': '𝗙', 'G': '𝗚', 'H': '𝗛', 'I': '𝗜', 'J': '𝗝',
        'K': '𝗞', 'L': '𝗟', 'M': '𝗠', 'N': '𝗡', 'O': '𝗢', 'P': '𝗣', 'Q': '𝗤', 'R': '𝗥', 'S': '𝗦', 'T': '𝗧',
        'U': '𝗨', 'V': '𝗩', 'W': '𝗪', 'X': '𝗫', 'Y': '𝗬', 'Z': '𝗭',
        'a': '𝗮', 'b': '𝗯', 'c': '𝗰', 'd': '𝗱', 'e': '𝗲', 'f': '𝗳', 'g': '𝗴', 'h': '𝗵', 'i': '𝗶', 'j': '𝗷',
        'k': '𝗸', 'l': '𝗹', 'm': '𝗺', 'n': '𝗻', 'o': '𝗼', 'p': '𝗽', 'q': '𝗾', 'r': '𝗿', 's': '𝘀', 't': '𝘁',
        'u': '𝘂', 'v': '𝘃', 'w': '𝘄', 'x': '𝘅', 'y': '𝘆', 'z': '𝘇',
        '0': '𝟬', '1': '𝟭', '2': '𝟮', '3': '𝟯', '4': '𝟰', '5': '𝟱', '6': '𝟲', '7': '𝟳', '8': '𝟴', '9': '𝟵'
    }
    
    # Unicode character mappings for italic sans-serif  
    italic_map = {
        'A': '𝘈', 'B': '𝘉', 'C': '𝘊', 'D': '𝘋', 'E': '𝘌', 'F': '𝘍', 'G': '𝘎', 'H': '𝘏', 'I': '𝘐', 'J': '𝘑',
        'K': '𝘒', 'L': '𝘓', 'M': '𝘔', 'N': '𝘕', 'O': '𝘖', 'P': '𝘗', 'Q': '𝘘', 'R': '𝘙', 'S': '𝘚', 'T': '𝘛',
        'U': '𝘜', 'V': '𝘝', 'W': '𝘞', 'X': '𝘟', 'Y': '𝘠', 'Z': '𝘡',
        'a': '𝘢', 'b': '𝘣', 'c': '𝘤', 'd': '𝘥', 'e': '𝘦', 'f': '𝘧', 'g': '𝘨', 'h': '𝘩', 'i': '𝘪', 'j': '𝘫',
        'k': '𝘬', 'l': '𝘭', 'm': '𝘮', 'n': '𝘯', 'o': '𝘰', 'p': '𝘱', 'q': '𝘲', 'r': '𝘳', 's': '𝘴', 't': '𝘵',
        'u': '𝘶', 'v': '𝘷', 'w': '𝘸', 'x': '𝘹', 'y': '𝘺', 'z': '𝘻'
    }
    
    def convert_to_bold(match):
        text_inside = match.group(1)
        return ''.join(bold_map.get(char, char) for char in text_inside)
    
    def convert_to_italic(match):
        text_inside = match.group(1) 
        return ''.join(italic_map.get(char, char) for char in text_inside)
    
    # Convert **bold** to Unicode bold
    if "<think>" in text:
        text = text.split("</think>")[-1]
        
    text = re.sub(r'\*\*(.*?)\*\*', convert_to_bold, text)
    
    # Convert *italic* to Unicode italic 
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', convert_to_italic, text)
    
    # Convert bullet points
    text = re.sub(r'^\* ', '• ', text, flags=re.MULTILINE)
    text = re.sub(r'\n\* ', '\n• ', text)
    
    # Handle line breaks
    text = text.replace('\\n', '\n')
    
    return text