import re
import os
import tweepy
import MeCab

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


class StreamListener(tweepy.StreamListener):
    def __init__(self, api):
        self.api = api
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
            statuses = self.api.statuses_lookup(self.lookup_ids)
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
    AT = os.getenv("TW_AT")
    AS = os.getenv("TW_AS")
    CK = os.getenv("TW_CK")
    CS = os.getenv("TW_CS")
    auth = tweepy.OAuthHandler(CK, CS)
    auth.set_access_token(AT, AS)
    api = tweepy.API(auth)
    listener = StreamListener(api)
    streaming = tweepy.Stream(auth, listener)
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
