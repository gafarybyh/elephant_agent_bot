from twikit import Client, TooManyRequests, NotFound
import os
from datetime import datetime
from random import randint
import asyncio
from config.app_config import X_USERNAME, X_EMAIL, X_PASSWORD, logger
from helpers.api_helpers import get_gemini_response_v2

# !IMPORTANT FOR PYTHONANYWHERE
# !CHANGE THIS line on twikit library at /home/yourusername/.local/lib/python3.x/site-packages/twikit/client.py
# !self.http = AsyncClient(proxy=proxy, **kwargs)
# to this: 
# !self.http = AsyncClient(proxies={"http://": proxy, "https://": proxy}, **kwargs)

# Untuk path pythonanywhere
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
cookies_file = os.path.join(BASE_DIR, 'cookies.json')

# TODO* GET MULTIPLE PAGE TWEETS
async def get_multiple_pages_of_tweets(search_query: str = "#btc", min_tweets = 30):
    all_tweets = []
    max_retries = 3
    retry_count = 0
    
    # Buat client dengan cara yang lebih aman
    client = None
    try:
        # Coba inisialisasi client dengan parameter minimal
        client = Client(language='en-US')
        logger.info(f'{datetime.now()} - Client initialized successfully')
    except Exception as e:
        logger.error(f'{datetime.now()} - Error initializing client: {str(e)}')
        return []
    
    # Login sekali di awal
    try:
        # Check if cookies file exists and has content
        if os.path.exists(cookies_file) and os.path.getsize(cookies_file) > 0:
            # Load cookies from file
            client.load_cookies(cookies_file)
            logger.info(f'{datetime.now()} - Successfully loaded cookies')
        else:
            # Login with credentials
            await client.login(
                auth_info_1=X_USERNAME,
                auth_info_2=X_EMAIL,
                password=X_PASSWORD
            )
            # Save cookies for future use
            client.save_cookies(cookies_file)
            logger.info(f'{datetime.now()} - Login successful, cookies saved')
    except Exception as e:
        logger.error(f'{datetime.now()} - Error during login: {str(e)}')
        return []
    
    #* GET FIRST PAGE TWEETS with max_entries
    while retry_count < max_retries:
        try:
            logger.info(f'{datetime.now()} - Getting initial tweets...')
            tweets = await client.search_tweet(query=search_query, product='Top', count=20)
            
            # Tambahkan tweets ke daftar
            for tweet in tweets:
                all_tweets.append(tweet)
            
            logger.info(f'{datetime.now()} - Collected {len(all_tweets)} tweets so far')
            
            #* GET NEXT PAGE TWEETS UNTIL min_tweets
            page_count = 1
            
            while len(all_tweets) < min_tweets:
                page_count += 1
                
                # Tambahkan jeda untuk menghindari rate limiting
                wait_time = randint(5, 10)
                logger.info(f'{datetime.now()} - Waiting {wait_time} seconds before fetching page {page_count}...')
                await asyncio.sleep(wait_time)
                
                # Gunakan tweets.next() untuk mendapatkan halaman berikutnya
                try:
                    tweets = await tweets.next()
                    
                    if not tweets or len(tweets) == 0:
                        logger.info(f'{datetime.now()} - No more tweets available')
                        break
                    
                    # Tambahkan tweets ke daftar
                    for tweet in tweets:
                        all_tweets.append(tweet)
                    
                    logger.info(f'{datetime.now()} - Collected {len(all_tweets)} tweets so far')
                    
                except TooManyRequests as e:
                    # Handle rate limiting specifically
                    wait_time = 120  # Default wait time of 2 minutes
                    if hasattr(e, 'rate_limit_reset') and e.rate_limit_reset:
                        # Calculate wait time based on rate limit reset if available
                        current_time = datetime.now().timestamp()
                        wait_time = max(e.rate_limit_reset - current_time + 5, 60)
                    
                    logger.error(f'{datetime.now()} - Rate limit exceeded. Waiting {wait_time} seconds before retrying...')
                    await asyncio.sleep(wait_time)
                    continue
                except NotFound as e:
                    logger.error(f'{datetime.now()} - 404 Not Found error: {str(e)}')
                    # If we get a 404, we might have an invalid cursor or the search is no longer valid
                    # Best to return what we have so far
                    break
                except Exception as e:
                    logger.error(f'{datetime.now()} - Error fetching next page: {str(e)}')
                    # Tunggu lebih lama jika terjadi error
                    await asyncio.sleep(30)
                    continue
            
            # If we got here, we either collected enough tweets or ran out of pages
            break  # Exit the retry loop
        
        except TooManyRequests as e:
            wait_time = 120  # Default wait time of 2 minutes
            if hasattr(e, 'rate_limit_reset') and e.rate_limit_reset:
                current_time = datetime.now().timestamp()
                wait_time = max(e.rate_limit_reset - current_time + 5, 60)
            
            logger.info(f'{datetime.now()} - Rate limit exceeded during initial fetch. Waiting {wait_time} seconds before retrying...')
            await asyncio.sleep(wait_time)
            retry_count += 1
            continue
        except NotFound as e:
            logger.error(f'{datetime.now()} - 404 Not Found error during initial fetch: {str(e)}')
            # Try a different search approach or wait before retrying
            logger.info(f'{datetime.now()} - Waiting 30 seconds before retry {retry_count+1}/{max_retries}...')
            await asyncio.sleep(30)
            retry_count += 1
            continue
        except Exception as e:
            logger.error(f'{datetime.now()} - Error during tweet collection: {str(e)}')
            # Try again after a delay
            logger.info(f'{datetime.now()} - Waiting 30 seconds before retry {retry_count+1}/{max_retries}...')
            await asyncio.sleep(30)
            retry_count += 1
            continue
    
    print(f'{datetime.now()} - Finished collecting {len(all_tweets)} tweets')
    return all_tweets


# TODO* SEARCH TWEET
async def extract_tweets(search_query: str, minimum_tweets: int = 30) -> list:
    
    all_tweets = await get_multiple_pages_of_tweets(search_query=search_query, min_tweets=minimum_tweets)
    
    if not all_tweets:
        print(f'{datetime.now()} - No tweets found for query: {search_query}')
        return []
    
    list_tweet = []
    
    for i, tweet in enumerate(all_tweets):
        tweet_count = i + 1 
        tweet_data = { 
            "tweet_count": tweet_count,
            "username": tweet.user.name,
            "text": tweet.text,
            "created_at": tweet.created_at,
            "retweets": tweet.retweet_count,
            "favorites": tweet.favorite_count
        }
        
        list_tweet.append(tweet_data)
        
    return list_tweet


# TODO* GENERATE TWEET PROMPT
def generate_tweet_prompt(tweets_data: list = None, user_query = "#btc"):
    """Generate a prompt for the Gemini model to analyze tweets sentiment."""
    
    all_tweets = "\n".join([f"{tweet['tweet_count']}. @{tweet['username']}: {tweet['text']}, rt: {tweet['retweets']}, likes: {tweet['favorites']} ({tweet['created_at']})" for tweet in tweets_data])
    
    return f"""
You are an expert crypto sentiment analyst focusing on **early signal detection** for crypto traders.

Given a list of tweets about a cryptocurrency (e.g., Bitcoin), generate a concise, actionable sentiment report in **Telegram format**, focusing on whether there's an early momentum or notable sentiment shift.

The report should contain:

1. Title: “🔥 {user_query.upper()} Tweets Sentiment Report 🔥”
2. Total tweets analyzed: “📊 Total tweets: [count]”
3. Sentiment breakdown:  
    ✅ Positive: [count] (avg score: [score])  
    ❌ Negative: [count] (avg score: [score])  
    ⚪ Neutral: [count]
4. Dominant sentiment: “🏆 Dominant sentiment: [positive/neutral/negative]”

5. **Momentum analysis:**
    - Write 1-2 lines indicating whether sentiment is **building up**, **flat**, or **cooling down**, based on the tweet content and engagement (likes/retweets/trending words).

6. **Key emerging narratives:**
    List **3-5 bullet points** summarizing the trending topics (e.g., ETF inflow, memecoin surge, regulatory news, big influencer tweet).

7. **Notable influencer activity:**
    Mention if any **influencer account (high retweet count and favorites)** is posting or boosting sentiment.

8. **Top tweets:**
    List 1-2 highest engagement tweets in this format:
    - “@username: “[tweet text]” (RT: [retweets], ❤️: [likes])”

👉 Format should be clear, readable, and friendly for Telegram crypto trader audience.

Only output the report text, no extra explanation.

Tweets:
{all_tweets}
"""

# TODO* ANALYZE TWEETS
async def analyze_tweets(user_query = None):
    try:
        if not user_query or user_query.strip() == "":
            return "Please provide a search query. Example: /tweets #bitcoin"
            
        tweets = await extract_tweets(user_query)
        
        if not tweets:
            return "No tweets found or error fetching tweets. Please try again later..."
        
        prompt = generate_tweet_prompt(tweets, user_query)
        
        response = get_gemini_response_v2(prompt)
        
        # Ensure we never return None
        if not response:
            return "Failed to generate analysis. Please try again later."
            
        return response
    except Exception as e:
        logger.error(f"Error in analyze_tweets: {e}")
        return f"Error analyzing tweets: {str(e)[:100]}... Please try again later."


