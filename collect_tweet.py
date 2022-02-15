import re
import os
import tweepy
import MeCab
from math import inf

INFILE = "./data/input.txt"
OUTFILE = "./data/output.txt"
MAX_TW = 10000


def parseja(text):
    wakati = MeCab.Tagger('-Owakati')
    return wakati.parse(text)


class Tweet:
    def __init__(self, status):
        self.in_reply_to_status_id = status.in_reply_to_status_id
        self.text = status.text
        self.created_at = status.created_at
        self.screen_name = status.user.screen_name
        self.username = status.user.name
        self.user_id = status.user.id


class Stream(tweepy.Stream):
    def __init__(self, consumer_key, consumer_secret, access_token,
                 access_token_secret, *, chunk_size=512, daemon=False,
                 max_retries=inf, proxy=None, verify=True):
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.access_token = access_token
        self.access_token_secret = access_token_secret
        self.chunk_size = chunk_size
        self.daemon = daemon
        self.max_retries = max_retries
        self.proxies = {"https": proxy} if proxy else {}
        self.verify = verify

        self.running = False
        self.session = None
        self.thread = None
        self.user_agent = (
            f"Python "
            f"Requests "
            f"Tweepy/{tweepy.__version__}"
        )
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)
        self.saved = 0
        self.lookup_ids = []
        self.replies = {}

    def on_status(self, status):
        # is not reply
        if not status.in_reply_to_status_id:
            return
        # filter
        if not self.is_valid_tweet(status):
            return
        # append lookup id
        self.lookup_ids.append(status.in_reply_to_status_id)
        self.replies[status.in_reply_to_status_id] = Tweet(status)
        # collect 100 tweets
        if len(self.lookup_ids) >= 100:
            statuses = self.api.lookup_statuses(self.lookup_ids)
            for status in statuses:
                if not self.is_valid_tweet(status):
                    continue
                reply = self.replies[status.id]
                # is same user
                if status.user.id == reply.user_id:
                    continue
                intext = re.sub(r"@([A-Za-z0-9_]+)", "", status.text)
                outtext = re.sub(r"@([A-Za-z0-9_]+)", "", reply.text)
                with open(INFILE, "a") as f:
                    print(parseja(intext), file=f)
                with open(OUTFILE, "a") as f:
                    print(parseja(outtext), file=f)
                self.saved += 1
                print("\r" + str(self.saved), end="")
                if self.saved > MAX_TW:
                    exit()
            self.lookup_ids = []
            self.reply_list = {}

    def is_valid_tweet(self, status):
        # is not ja
        if status.lang != "ja":
            return False
        # is bot
        if "bot" in status.user.screen_name:
            return False
        # include URL
        if re.search(r"https?://", status.text):
            return False
        # is hashtag
        if re.search(r"#(\w+)", status.text):
            return False
        # reply to multi user
        tweet = re.sub(r"@([A-Za-z0-9_]+)", "<unk>", status.text)
        if tweet.split().count("<unk>") > 1:
            return False
        # too long
        if len(tweet.replace("<unk>", "")) > 30:
            return False
        return True


def main():
    CK = os.getenv("TW_CK")
    CS = os.getenv("TW_CS")
    AT = os.getenv("TW_AT")
    AS = os.getenv("TW_AS")
    streaming = Stream(CK, CS, AT, AS)
    while True:
        try:
            streaming.sample()
        except KeyboardInterrupt:
            streaming.disconnect()
            break
        except Exception as e:
            streaming.disconnect()
            print(e)


if __name__ == "__main__":
    main()
