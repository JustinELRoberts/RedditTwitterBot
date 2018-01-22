# Overview
This bot takes top posts from various subreddits on Reddit and reposts on Twitter.\
It also follows and unfollows user from related accounts to try to gain followers.*\
It is meant to run many bots simultaneously on a Raspberry Pi.


# Getting Started
1. Create a Reddit application at: https://www.reddit.com/prefs/apps/
2. Create a Twitter application at: https://apps.twitter.com
3. Replace the appropriate text in "BotName" (You can rename it) in bot.py with the the ID's, keys, and access tokens from these applications
4. Find subreddits you wish to pull top posts from and replace to appropriate list in "BotName" with them
5. Replace the appropriate list in "BotName" with similar Twitter accounts which you would like to follow users from

*User following/unfollowing is still buggy and is therefore currently commented out. If you wish to use it at this time,
simply uncomment the relevant methods in the bot class. Unfortunately, if you do this after some time your Twitter access 
token will be revoked and you will have to regenerate it.
