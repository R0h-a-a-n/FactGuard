import praw
reddit = praw.Reddit(client_id="gl_DPpbCdXAfLj_lbDj9nw", client_secret="HFDmKLElvKpMUZ0mxBbskQbpvb9ljQ", user_agent="fact_guard")
for c in reddit.subreddit("AskReddit").hot(limit=5):
    print(c.title)
