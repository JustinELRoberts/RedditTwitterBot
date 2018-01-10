# These bots take weekly top posts from various subreddits and posts them on Twitter
import tweepy, requests, threading, datetime, random, imghdr, praw, time, os, re


# Class which controls bots
class Bot:

    def __init__(self, folder_name, subreddits, similar_accounts, reddit_id, reddit_secret, twitter_key, twitter_secret,
                 twitter_token, twitter_token_secret):

        # Path where bot's folder will exist
        self.path = os.path.dirname(os.path.realpath(__file__)) + '/' + folder_name + '/'

        # Subreddits to get posts from
        self.subreddits = subreddits

        # Twitter accounts to use to follow users
        self.accounts = similar_accounts

        # Self explanatory
        self.reddit_id = reddit_id
        self.reddit_secret = reddit_secret
        self.twitter_key = twitter_key
        self.twitter_secret = twitter_secret
        self.twitter_token = twitter_token
        self.twitter_token_secret = twitter_token_secret

        # Make a folder for the bot if it doesnt already exist
        if not os.path.exists(self.path):
            os.mkdir(self.path)

    # This method downloads posts from the list of subreddits associated with a particular bot
    def download(self):
        # Begin the Reddit session
        reddit = praw.Reddit(client_id=self.reddit_id, client_secret=self.reddit_secret, user_agent='MemeRetriever')

        # Iterate through each subreddit in the list
        for subreddit in self.subreddits:

            # Find the first (limit = ) N top weekly posts
            for submission in reddit.subreddit(subreddit).top(time_filter='week', limit=10):

                # Pull the image data
                img = requests.get(submission.url)

                # Make sure there is no errors
                if img.status_code == 200:

                    # This is the handle errors in the title of the submission
                    try:
                        # Write the binary image file
                        with open(self.path + submission.title, 'wb') as f:

                            # Default writes in 128 Byte increments
                            for chunk in img:
                                f.write(chunk)
                            f.close()

                            # First delete memes that talk about mods or Reddit
                            if re.search("mod", submission.title, re.IGNORECASE) or \
                               re.search("reddit", submission.title, re.IGNORECASE) or \
                               re.search("r/", submission.title, re.IGNORECASE):
                                os.remove(self.path + submission.title)

                            # Next delete unrecognized file types (typically videos)
                            # TODO: Figure out how to download videos
                            elif imghdr.what(self.path + submission.title) is None:
                                os.remove(self.path + submission.title)

                            # If it isn't deleted, use the correct file extension
                            else:
                                os.rename(self.path + submission.title, self.path + submission.title +
                                          '.' + str(imghdr.what(self.path + submission.title)))

                    # Error handling
                    except:
                        print('"{}" failed to download from "{}"'.format(submission.title, subreddit))
                        pass

    # This method posts (on Twitter) one of the posts downloaded in the previous method (from Reddit)
    def post(self):
        # Choose a random post from the folder
        post = random.choice(os.listdir(self.path))

        # Extract the title
        title = os.path.splitext(post)[0]

        # Create the OAuth instance
        auth = tweepy.OAuthHandler(self.twitter_key, self.twitter_secret)
        auth.set_access_token(self.twitter_token, self.twitter_token_secret)

        # Login
        api = tweepy.API(auth)

        # Post tweet
        api.update_with_media(self.path + post, title)

        # Delete the posted tweet from the folder
        os.remove(self.path + post)

    # This method follows users from the list of Twitter accounts
    def follow(self):
        # Create the OAuth instance
        auth = tweepy.OAuthHandler(self.twitter_key, self.twitter_secret)
        auth.set_access_token(self.twitter_token, self.twitter_token_secret)

        # Login
        api = tweepy.API(auth)

        # Find some users. j exists for debugging purposes
        j = 0
        for account in self.accounts:
            users = tweepy.Cursor(api.followers, screen_name=account).items()

            # Follow the 10 most recent followers in each Twitter account
            for x in range(10):
                j += 1

                # This is to prevent Twitter from revoking the token for "mass following"
                time.sleep(random.randrange(10, 120))

                # Self explanatory
                try:
                    user = next(users)
                except tweepy.TweepError:
                    pass
                except StopIteration:
                    break

                # Follow the user
                try:
                    api.create_friendship(user.screen_name)
                except:
                    print('Failed to follow {} after {} users'.format(user.screen_name, j))
                    break

    # This method unfollows users who do not follow back
    def unfollow(self):
        # Create the OAuth instance
        auth = tweepy.OAuthHandler(self.twitter_key, self.twitter_secret)
        auth.set_access_token(self.twitter_token, self.twitter_token_secret)

        # Login
        api = tweepy.API(auth)

        # Loop through pages of the bot's followers
        for page in tweepy.Cursor(api.friends, count=100).pages():

            # Get all the user ID's
            user_ids = [user.id for user in page]

            # Check to see if they follow the bot
            for user in api._lookup_friendships(user_ids):
                if not user.is_followed_by:
                    # Prevent Twitter from revoking the token for "mass unfollowing"
                    if random.uniform(0, 1) <= 0.75:
                        try:
                            # Unfollow
                            api.destroy_friendship(user.id)
                        except tweepy.error.TweepError:
                            print('Error unfollowing.')
                            break

                # This is to prevent Twitter from revoking the token for "mass unfollowing"
                # However, I don't believe it always works
                # TODO: Find a more reliable method for unfollowing users
                time.sleep(random.randrange(10, 120))


    # This method fills the directory, posts, and follows
    def run(self):
        # Check how many posts are currently in the directory
        self.num = len([f for f in os.listdir(self.path) if os.path.isfile(os.path.join(self.path, f))])

        # Refill if necessary
        if self.num == 0:
            self.download()

        # Post
        self.post()

        # Follow some users in a seperate thread
        follow_thread = threading.Thread(target=self.follow)
        follow_thread.start()


# Initialize bots
BotName = Bot('BotName',
             ['Subreddits to pull posts from'],
             ['Twitter accounts to follow users from'],
              'Reddit account ID', 'Reddit Account Secret', 'Twitter Account Key',
              'Twitter Account Secret',
              'Twitter Account Token',
              'Twitter Account Token Secret')

# I create this list to make scaling easier in the future (i.e. run more bots)
bots = [BotName]


# Boolean used to unfollow once every day
toggle = False
day = datetime.datetime.today().day

# Indefinitely run bots
while True:
    # Unfollow users I follow that don't follow me back in a new thread every other day.
    if toggle:
        toggle = False
        for bot in bots:
            unfollow_thread = threading.Thread(target=bot.unfollow)
            unfollow_thread.start()

    # This toggle value is simply to make sure it only unfollows once on even days
    if day != datetime.datetime.today().day and not toggle:
        toggle = True
        day = datetime.datetime.today().day

    # Wait a random amount of time until posting
    pause_length = random.randrange(3600 * 2, 3600 * 12)

    print('Next post at: {}'.format(datetime.timedelta(seconds=pause_length) + datetime.datetime.now()))
    time.sleep(pause_length)

    # Post and follow
    # TODO: Make this more scalable by iterating through "bots" and creating seperate threads
    BotName.run()
