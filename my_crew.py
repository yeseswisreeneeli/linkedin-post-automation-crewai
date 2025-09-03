from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool, tool
from pydantic import BaseModel, Field
import requests
import os
from dotenv import load_dotenv
load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 

@tool("perplexity tool")
def perplexity_tool(query: str) -> str:
    """Useful for searching a specific link, SEO keywords for posts, trending hashtags, latest information on the web to create relevant posts. For getting additional knowledge on certain content aspects. Input should be a single string with your query. The input must contain the link too if required."""
    
    headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        }
    payload = {
        "model": "sonar",
        "messages": [
            {"role": "system",
                "content": "You are a efficient and high skilled researcher in searching SEO keyword, finding trending hashtags & searching information on the web based on the link provided. You provide concise and relevant answers based on the query provided. If the query contains a link, you use that link to get more context and information to answer the query. You do not make up answers if you don't know them. You always try to provide the best possible answer based on the information available."},

            {"role": "user", 
                "content": query}
            ],
        "max_tokens": 4000,
        "temperature": 0.7,
        "top_p": 0.9,
        "return_citations": False,
        "return_images": False,
        "return_related_questions": False
    }
    response = requests.post(
        "https://api.perplexity.ai/chat/completions", 
        headers=headers, 
        json=payload
    )
    if response.status_code == 200:
        output = response.json()
        return output
    else:
        return f"Error: {response.status_code}, {response.text}"

llm = LLM(model="qwen/qwen3-32b", 
          api_key=GROQ_API_KEY,
          base_url="https://api.groq.com/openai/v1",
          temperature=0.1)


post_generator_agent = Agent(
              role="You are a human, a skillful content creator,a AI researcher, a freelancer, who creates best Linkedin posts in a friendly with professional tone based on the content provided to you. Your content is about latest updates in AI feild which you always want to share with your network, who are researchers, founders, AI folks, to build engagment, attraction and connections",
              goal="Create a Linkedin post based on the content provided. The post should be human written like natural, engaging and relevant to your professional network with SEO optimization for a vast reachability and you utilize very relevant and trending hashtags to the post.",
              backstory=("You are an expert AI researcher, AI Freelancer, avid reader and content creator."
                        "You love to do research and follow latest trends in the feild of AI."
                        "You love to share the same knowledge with your network to gain attraction of researchers, Founders, AI folks. You have a deep understanding of what makes"
                        "a post engaging on LinkedIn and how to tailor content to different audiences"
                        "You utilize the Perplexity_tool to get latest information on the web to create relevant posts using real time information. And also search the best hashtags & SEO keywords to suite the post."
                        "You are also given the information original link to the post that can be used over the perplexity_tool to get more context on the post along with keywords, hashtags etc. "),
              allow_delegation=False,
              tools=[perplexity_tool], 
              llm=llm, verbose=True,
              max_iter=2)

task = Task(name="Create Linkedin Post", 
            description=("Create an engaging Linkedin post based on the post content & link provided here, POST CONTENT: {content} , LINK: {link}. Follow the Dos and Donts strictly to create the post."
                         
            "### Dos:"
            "1. The post should be natural and relevant to my professional network with SEO optimization for a vast reachability."
            "2. You utilize top trending hashtags that align with most discussions on LinkedIn about this particular topic, Find using the perplexity_tool, With a max of 5 hastags that suite the SEO optimized post for better reachability."
            "3. The post must start with a engaging lines or questions, compelling hooks to grab the attention of the readers" "4. Use max of 5 to 6 bullet points to highlight key takeaways. Keep sentences short and to the point. Make use of whitespace for readability" 
            "5. Use appropriate emojis to make the post visually appealing and relatable."
            "6. Use Funny jokes, questions, narrating experiences to build emotional connections with the readers. You can start with lines like I have come across, I love to share, lately, I have been exploring, How I manage, this is Awesome, Woow crazy!, Today I read this.. etc"
            "7. The post should be like very easily consumanlble and information should seem like quick bites of large information."
            "8. The post should sound like human written."
            "9. Use the perplexity_tool to get latest information on the web to create latest facts and real time information that is requried to create realistic posts."
            ""
            "### Donts:"
            "1. Avoid large blocks of text and hard vocabulary."
            "2. Avoid excessive usage of emojis and all caps"
            "3. The post should not be too long, ideally between 100-130 words."
            "4. Do not use more than 5 hashtags and do not use hashtags in between the post. Mention all the hashtags directly at the end of post."
            "5. Do not promote any products, services and pricing structures in the post."
            "6. Do not make up any information if you dont know."
            "7. The post should not sound like AI or machine generated."
            ""
            "### Information about Tools:"
            "tool name: perplexity_tool"
            "tool input format: a single string with your query or better designed prompt. The input must contain the link too if required."
            "tool description: This tool is useful for searching latest information about the content in the web. It is also useful for finding trending hashtags on most discussion on linkedin on specific topic, SEO keywords for the linkedin post for the specific topic, find the latest information and gain more context on the web, when link is provided."
            "How to use tool: Give a better designed prompt to the tool with the link if required to get more context on the post and when you want to find the trending hashtags, SEO keywords on specific topic. example prompt: Find top 5 trending hashtags used in most discussions on linkedin related to topic called Image generation, Find top SEO keywords for the linkedin post used in top discussions on linkedin on topic: Grok-2, find latest information on the web about topic: Grok-2, link:www.examplelink.com, etc."
            ),

            expected_output="An engaging and eye-catchy Linkedin post with SEO optimized content and relevant hashtags. Do not respond with anything else other than the post content. The output post must be of short points and emojis, in short bullet points. Each point must be very consise with a max of 5 to 10 words. Mention the hashtags directly at the end of post and see to that all the hashtags are in lowercase and without any spaces. The output must contain the link '{link}' at the end of the post wherever relevant.",

            agent=post_generator_agent)  

crew = Crew(agents=[post_generator_agent], 
            tasks=[task],
            verbose=True) 

def kickoff_linkedin_post(content, link):
    crew_output = crew.kickoff(inputs={"content": content, "link": link})
    result = crew_output.raw
    return result




