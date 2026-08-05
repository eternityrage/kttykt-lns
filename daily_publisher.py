import os
import json
import glob
import random
import requests
import shutil
import sys
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
from pathlib import Path
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path, override=True)

# Import upload functions
try:
    from upload.upload_instagram import upload_to_instagram
    from upload.upload_threads import upload_to_threads
    from upload.upload_facebook import upload_to_facebook, upload_to_facebook_story
    from upload.upload_to_youtube import upload_to_youtube
except ImportError as e:
    print(f"Error importing upload modules: {e}")
    # Still want to proceed or stop?
    pass

PROCESSED_DIR = "Processed_Videos"
PUBLISHED_LOG = "published_videos.json"

def get_already_published():
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []


def get_repost_counts():
    """Count how many times each video has been posted."""
    published = get_already_published()
    counts = {}
    for entry in published:
        vname = entry.get("video_name", "")
        counts[vname] = counts.get(vname, 0) + 1
    return counts

def mark_as_published(video_name, metadata):
    published = get_already_published()
    published.append({
        "video_name": video_name,
        "metadata": metadata
    })
    with open(PUBLISHED_LOG, 'w', encoding='utf-8') as f:
        json.dump(published, f, indent=4)

def select_video(specific_video=None):
    published = [item["video_name"] for item in get_already_published()]
    all_videos = sorted(glob.glob(os.path.join(PROCESSED_DIR, "*.mp4")))

    if specific_video:
        # specific_video might be a full path or just a filename
        if os.path.exists(specific_video):
            # It's a full path
            vid_path = specific_video
            name = os.path.basename(specific_video)
        else:
            # It's just a filename, join with PROCESSED_DIR
            vid_path = os.path.join(PROCESSED_DIR, specific_video)
            name = specific_video

        if os.path.exists(vid_path):
            if name in published:
                post_count = sum(1 for p in published if p == name)
                print(f"ðŸ”„ Video {name} was already published ({post_count}x) - Re-publishing (recycling)")
            return vid_path, name
        else:
            print(f"âŒ Error: Specific video {name} not found")
            return None, None

    # Find unpublished videos first
    unpublished = [(vid, os.path.basename(vid)) for vid in all_videos if os.path.basename(vid) not in published]

    if unpublished:
        vid, name = unpublished[0]
        return vid, name

    # All videos published - use weighted random selection (less posted = more likely)
    if all_videos:
        repost_counts = get_repost_counts()
        weights = []
        for vid in all_videos:
            name = os.path.basename(vid)
            count = repost_counts.get(name, 0)
            weight = max(1, 1000 // (3 ** min(count, 6)))
            weights.append(weight)

        selected_vid = random.choices(all_videos, weights=weights, k=1)[0]
        name = os.path.basename(selected_vid)
        post_count = repost_counts.get(name, 0)
        print(f"ðŸŽ² All videos published. Weighted random reuse (posted {post_count}x): {name}")
        return selected_vid, name

    return None, None

def generate_caption():
    import random
    import time

    api_key = os.getenv("POLLINATIONS_API_KEY")
    model = os.getenv("AI_MODEL", "openai")

    fallback_titles = [
        "Jane Seymour's Most Iconic Red Carpet Looks of All Time",
        "Jane Seymour as Solitaire in Live and Let Die \u2014 The Bond Girl Who Stole Hearts",
        "Jane Seymour's Best Dr. Quinn Moments That Made Television History",
        "Jane Seymour in Somewhere in Time \u2014 The Performance That Defined a Generation",
        "Jane Seymour Interview Moments That Proved She's a True Star",
        "Jane Seymour on the Red Carpet \u2014 Hollywood's Timeless Elegance",
        "Jane Seymour's Funniest Talk Show Moments Compilation",
        "The Rise of Jane Seymour \u2014 From Bond Girl to Hollywood Legend",
        "Jane Seymour's Most Emotional On-Screen Moments You Need to See",
        "Jane Seymour Behind the Scenes \u2014 She's So Real",
        "Jane Seymour at the Oscars \u2014 A Legacy of Glamour",
        "Jane Seymour's Best Fashion Moments You Need to See",
        "Why Jane Seymour Is One of Hollywood's Most Beloved Actresses",
        "Jane Seymour's Throwback Moments \u2014 Pure Timeless Magic",
        "Jane Seymour: The Iconic Roles That Made Her a Legend",
    ]

    fallback_descriptions = [
        "Jane Seymour doesn't just walk red carpets \u2014 she owns them. From her legendary turn as Solitaire in the Bond classic Live and Let Die to the timeless elegance she brings to every appearance, she is the definition of Old Hollywood glamour. She is the kind of star who makes every moment feel iconic, and her fans can't get enough of it. Drop a \U0001F525 if you think Jane Seymour is one of the most elegant actresses of all time! #janeseymour #liveandletdie #bondgirl #hollywood #classiccinema #actress #janeseymourfan #redcarpet #fashionicon #timeless #icon",
        "When Jane Seymour stepped onto the screen as Solitaire in Live and Let Die, she didn't just play a Bond girl \u2014 she became a legend. Her elegance, her mystery, and that unforgettable presence turned a supporting role into cinema history. She has been captivating audiences ever since, from Dr. Quinn Medicine Woman to Somewhere in Time. Like if you still get chills watching her classic scenes! \U0001F3AC #janeseymour #liveandletdie #bondgirl #007 #jamesbond #classicmovies #hollywood #janeseymourfan #cinema #legend #actress",
        "Jane Seymour's portrayal of Dr. Michaela Quinn in Dr. Quinn, Medicine Woman is one of the most beloved performances in television history. For years she brought strength, compassion, and heart to the role, becoming a role model for a generation of viewers. She proved that a woman could lead a prime-time drama with grace and power. Share this if you grew up watching Dr. Quinn! \U0001F4FA #janeseymour #drquinn #drquinnmedicinewoman #tvhistory #hollywood #actress #janeseymourfan #classicTV #rolemodel #strongwomen",
        "When Jane Seymour starred in Somewhere in Time, she created one of the most romantic films ever made. Her chemistry with Christopher Reeve, her timeless beauty, and the haunting score made it a classic that still moves audiences today. It is the kind of love story they don't make anymore. Comment below with your favorite Jane Seymour movie! \U0001F48D #janeseymour #somewhereintime #christopherreeve #romance #classicmovies #hollywood #janeseymourfan #timelesslove #cinema #icon",
        "Jane Seymour on the interview circuit is an absolute joy to watch. Whether she's telling stories about working with Roger Moore, sharing her thoughts on Hollywood, or being wonderfully charming and witty, she lights up every room. She's funny, sharp, thoughtful, and endlessly elegant \u2014 the kind of star who makes you feel like you're chatting with a friend. Like if you could watch Jane Seymour interviews all day! \U0001F399\uFE0F #janeseymour #interviews #talkshow #hollywood #celebrity #bondgirl #classicactress #janeseymourfan #elegance #timeless",
        "From Bond girl to Emmy-winning icon, Jane Seymour's career is a masterclass in timeless elegance. Every red carpet appearance is pure class, every role is unforgettable, and every interview reminds us why she's one of the most beloved actresses in Hollywood history. She has played queens, doctors, and spies \u2014 and she made them all legendary. Follow for more Jane Seymour content! \U0001F483 #janeseymour #hollywood #elegance #actress #liveandletdie #drquinn #classiccinema #janeseymourfan #redcarpet #timeless #icon",
        "Jane Seymour's talk show appearances are comedy gold! From her delightful stories about playing a Bond girl to her charming chemistry with every host she meets, she always brings the class and the laughs. Her wit, her warmth, and her legendary poise make her one of the most entertaining guests in television history. Like if Jane Seymour's laugh is your favorite sound! \U0001F602 #janeseymour #funnymoments #fallon #kimmel #talkshow #comedy #hollywood #celebrity #laughter #elegance #janeseymourfan #entertainment",
        "Jane Seymour's journey from a young actress in London to a Hollywood legend is nothing short of inspirational. She became a Bond girl, won an Emmy for Dr. Quinn Medicine Woman, and starred in some of the most beloved films of all time. She has shown grace, resilience, and incredible talent at every step. Her story proves that class and hard work never go out of style. Share this if Jane Seymour inspires you! \u2B50 #janeseymour #inspiration #hollywood #successstory #emmywinner #bondgirl #drquinn #actress #legend #janeseymourfan #journey #timeless",
        "There is something about Jane Seymour's emotional scenes that stays with you forever. Whether it's the heartbreaking romance of Somewhere in Time or the powerful moments in Dr. Quinn Medicine Woman, she brings a depth and vulnerability that few actresses can match. She doesn't just perform \u2014 she makes you feel every single moment. Like if Jane Seymour's performances have ever moved you! \U0001F495 #janeseymour #emotional #acting #somewhereintime #drquinn #hollywood #cinema #janeseymourfan #legend #performance #awardworthy",
        "There's something about Jane Seymour behind the scenes that makes her even more lovable. The way she treats her co-stars, the grace she shows on set, the kindness she radiates \u2014 she's the real deal. Everyone who works with her says she's one of the most professional, humble, and talented people they've ever met. Hollywood needs more stars like Jane Seymour. Like if you agree! \U0001F49B #janeseymour #bts #behindthescenes #real #authentic #hollywood #kindness #humble #talent #setlife #janeseymourfan #wholesome",
        "Jane Seymour at the Oscars is appointment viewing. Year after year, she delivers some of the most elegant, talked-about looks in awards history. She brings Old Hollywood glamour to every single appearance, and she always looks absolutely timeless. Her commitment to her craft and her grace on the red carpet are unmatched. Comment your favorite Jane Seymour look! \U0001F3AC #janeseymour #oscars #awards #fashion #elegance #redcarpet #hollywood #classicglamour #janeseymourfan #timeless #icon",
        "Jane Seymour's fashion is the definition of timeless elegance. From her iconic Bond girl era to the classic glamour of the red carpet, she has always dressed like a true Hollywood star. She is not afraid of risk, she always looks graceful, and every single look tells a story. Follow for style inspiration from the queen herself! \U0001F48E #janeseymour #fashion #style #elegance #redcarpet #classicglamour #hollywood #bondgirl #janeseymourstyle #icon #fashionista #timeless",
        "Why do we love Jane Seymour? Because she is the complete package \u2014 a Bond girl, an Emmy winner, a timeless beauty, and one of the most genuine people in Hollywood. From Live and Let Die to Dr. Quinn Medicine Woman to Somewhere in Time, she has given us decades of unforgettable performances. She is truly one of the most beloved actresses of all time. Like if you love Jane Seymour! \U0001F496 #janeseymour #hollywood #actress #bondgirl #emmywinner #liveandletdie #drquinn #somewhereintime #janeseymourfan #legend #timeless #cinema",
        "Take a trip down memory lane with Jane Seymour's most iconic throwback moments! From her legendary Bond girl days to her Emmy-winning run on Dr. Quinn Medicine Woman, she has been dazzling audiences for decades. Her elegance, her talent, and her warmth are pure timeless magic. Like if you love Jane Seymour throwbacks! \U0001F5A4 #janeseymour #throwback #bondgirl #drquinn #liveandletdie #classiccinema #hollywood #janeseymourfan #nostalgia #legend #icon #timeless",
        "Jane Seymour's career is a masterclass in staying iconic. She was a Bond girl when Bond was at its best, she led her own Emmy-winning TV series, and she starred in some of the most romantic films ever made. She has done it all with elegance, talent, and grace. Here's to a true Hollywood legend \u2014 comment your favorite Jane Seymour role below! \U0001F37F #janeseymour #hollywood #actress #bondgirl #emmywinner #drquinn #liveandletdie #somewhereintime #janeseymourfan #legend #career #icon #cinema",
    ]
    if not api_key:
        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        print("Warning: POLLINATIONS_API_KEY not found. Using fallback captions.")
        return chosen_title, chosen_desc

    vibes = [
        "exciting and celebratory â€” hype up Jane Seymour's talent, style, and iconic moments",
        "fun and engaging â€” make it feel like you're talking about your favorite celebrity with a friend",
        "inspiring and uplifting â€” highlight how Jane Seymour's journey motivates her fans",
        "glamorous and stylish â€” focus on her incredible fashion and red carpet looks",
        "emotional and heartfelt â€” showcase her powerful acting and the moments that move us",
        "funny and lighthearted â€” capture her amazing personality and hilarious interview moments",
        "nostalgic and throwback â€” celebrate her journey from Disney to Hollywood superstardom",
    ]
    chosen_vibe = random.choice(vibes)

    prompt = (
        f"Write a completely unique, long, and captivating title and description for a short video "
        f"about Jane Seymour for the Facebook page 'Jane Seymour Daily'. "
        f"The page posts the best Jane Seymour moments â€” red carpet looks, interviews, acting scenes, "
        f"fashion, behind-the-scenes, and everything that makes Jane Seymour a Hollywood icon. "
        f"Speak as a passionate Jane Seymour fan who loves celebrating her talent and style. "
        f"Make the vibe {chosen_vibe}. "
        f"The description should be LONG (4-6 sentences minimum), deeply engaging, and fun. "
        f"Include engagement calls-to-action such as: "
        f"- Like if you love Jane Seymour! "
        f"- Comment your favorite Jane Seymour movie or role! "
        f"- Share this with another Jane Seymour fan! "
        f"- Follow Jane Seymour Daily for the best Jane Seymour content! "
        f"Include relevant hashtags in ALL LOWERCASE such as #janeseymour #hollywood #liveandletdie #bondgirl #drquinn #somewhereintime #classiccinema #fashion #celebrity #redcarpet #janeseymourfan #actress #emmywinner #elegance #timeless. "
        f"Return ONLY a valid JSON object in this format: {{\"title\": \"<title>\", \"description\": \"<description>\"}} "
        f"Do not include any other text or markdown block backticks."
    )

    url = "https://gen.pollinations.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "seed": random.randint(1, 999999)
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)

        chosen_title = random.choice(fallback_titles)
        chosen_desc = random.choice(fallback_descriptions)
        return result.get("title", chosen_title), result.get("description", chosen_desc)
    except Exception as e:
        print(f"Error generating caption: {e}")
        return random.choice(fallback_titles), random.choice(fallback_descriptions)

def main():
    print("=" * 60)
    print("ðŸš€ DAILY AUTOMATION STARTING")
    print("=" * 60)
    
    specific_video = sys.argv[1] if len(sys.argv) > 1 else None
    video_path, video_name = select_video(specific_video)
    if not video_path:
        print("âœ… No new videos found to publish. Exiting.")
        return
        
    print(f"ðŸ‘‰ Selected Video: {video_name}")
    print("ðŸ§  Generating caption via Pollination AI...")
    title, description = generate_caption()
    
    print(f"ðŸ“ Title: {title}")
    print(f"ðŸ“ Description:\n{description}")
    
    # Combined caption for platforms that use a single text field
    combined_caption = f"{title}\n\n{description}"
    
    success_flags = {
        "instagram_reel": False,
        "instagram_story": False,
        "facebook_reel": False,
        "facebook_story": False,
        "threads": False,
        "youtube": False
    }
    
    # Instagram Reels
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=False)
        if result and result.get('status') == 'skipped':
            print(f"âš ï¸  Instagram Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_reel"] = True
    except Exception as e:
        print(f"âŒ Instagram Reel upload failed: {e}")
        
    # Instagram Stories
    try:
        result = upload_to_instagram(video_path, combined_caption, is_story=True)
        if result and result.get('status') == 'skipped':
            print(f"âš ï¸  Instagram Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["instagram_story"] = True
    except Exception as e:
        print(f"âŒ Instagram Story upload failed: {e}")
        
    # Facebook Reels
    try:
        result = upload_to_facebook(video_path, description, title=title)
        if result and result.get('status') == 'skipped':
            print(f"âš ï¸  Facebook Reel: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_reel"] = True
    except Exception as e:
        print(f"âŒ Facebook Reel upload failed: {e}")
        
    # Facebook Stories
    try:
        result = upload_to_facebook_story(video_path)
        if result and result.get('status') == 'skipped':
            print(f"âš ï¸  Facebook Story: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["facebook_story"] = True
    except Exception as e:
        print(f"âŒ Facebook Story upload failed: {e}")
        
    # Threads
    try:
        result = upload_to_threads(video_path, combined_caption)
        if result and result.get('status') == 'skipped':
            print(f"âš ï¸  Threads: Skipped ({result.get('reason', 'No credentials')})")
        else:
            success_flags["threads"] = True
    except Exception as e:
        print(f"âŒ Threads upload failed: {e}")
        
    # YouTube Shorts
    try:
        upload_to_youtube(video_path, title, description, tags=["janeseymour", "hollywood", "liveandletdie", "bondgirl", "drquinn", "somewhereintime", "janeseymourstyle", "fashion", "celebrity", "red carpet", "janeseymour fan", "actress", "emmy winner", "classiccinema", "timeless", "janeseymour daily"])
        success_flags["youtube"] = True
    except Exception as e:
        print(f"âŒ YouTube upload failed: {e}")
        
    # Record as published regardless of partial success,
    # to avoid repeating the same video. Alternatively, only record if fully successful.
    print("\nâœ… Marking video as published.")
    
    # Check if this is a recycled video (already in published_videos.json)
    published_list = get_already_published()
    is_recycled = any(item["video_name"] == video_name for item in published_list)
    
    if is_recycled:
        print(f"   ðŸ”„ This is a recycled video (re-publishing)")
    
    mark_as_published(video_name, {
        "title": title,
        "description": description,
        "success_flags": success_flags,
        "recycled": is_recycled
    })
    
    # Move the published video to Published_Videos folder
    published_dir = "Published_Videos"
    if not os.path.exists(published_dir):
        os.makedirs(published_dir)
        
    try:
        dest_path = os.path.join(published_dir, video_name)
        shutil.move(video_path, dest_path)
        print(f"ðŸ“¦ Moved published video to {dest_path}")
    except Exception as e:
        print(f"âŒ Failed to move published video: {e}")
    
    print("ðŸŽ‰ DAILY AUTOMATION COMPLETE")

if __name__ == "__main__":
    main()
