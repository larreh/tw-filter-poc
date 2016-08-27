#!/usr/bin/python
# -*- coding: utf-8 -*-

import tweepy, textwrap, re, json

consumer_key = ""
consumer_secret = ""

access_token = ""
access_token_secret = ""

# filter_threshold:
#   0 - off
#   1 - warn
#   2 - full
filter_threshold = 1
status_count = 5
line_length = 48

class Filter(object):
    def __init__(self, filter_message='for the lulz', min_followers=None, \
                 block_pattern=None, replace_target=None, replace_value=None):
        self.filter_message = filter_message
        self.min_followers = min_followers
        self.block_pattern = block_pattern
        self.replace_target = replace_target
        self.replace_value = replace_value

    def evaluate(self, status):
        #min_followers
        try:
            if self.min_followers is not None:
                if status.author.followers_count < self.min_followers:
                    return False, self.filter_message, status
                else:
                    return True, None, status
        except AttributeError:
            pass

        #block_pattern
        try:
            if self.block_pattern is not None:
                if re.search(self.block_pattern, status.text, re.I) is not None:
                    return False, self.filter_message, status
                else:
                    return True, None, status
        except AttributeError:
            pass

        #replace (_target, _value)
        try:
            if self.replace_target is not None and self.replace_value is not None:
                if re.search(self.replace_target, status.text, re.I) is not None:
                    status.text = re.sub(self.replace_target, self.replace_value, status.text, flags = re.I)
                    return True, self.filter_message, status
                else:
                    return True, None, status
            else:
                return True, None, status
        except AttributeError:
            pass
        return True, None, status

    @staticmethod
    def load_json(obj):
        if '__Filter__' in obj:
            f = Filter()
            if 'filter_message' in obj:
                f.filter_message = obj['filter_message']
            if 'min_followers' in obj:
                f.min_followers = obj['min_followers']
            if 'block_pattern' in obj:
                f.block_pattern = obj['block_pattern']
            if 'replace_target' in obj and 'replace_value' in obj:
                f.replace_target = obj['replace_target']
                f.replace_value = obj['replace_value']
            return f
        else:
            return None

class FilterListener(tweepy.StreamListener):
    def __init__(self, api=None):
        super(FilterListener, self).__init__()
        self.filters = []
        load_filters(self.filters)

    def on_status(self, status):
        process_status(status, self.filters)

    def on_error(self, status_code):
        if status_code == 420:
            return False

def load_filters(filters):
    with open('filters.json') as filters_json:
        filters += json.loads(filters_json.read(), object_hook=Filter.load_json)

def process_status(status, filters = []):
    passed, msgs, tweet = filter_status(status, filters)

    if filter_threshold > 1:
        if passed:
            print '-' * line_length
            print_status(status)
    elif filter_threshold > 0:
        print '-' * line_length
        if len(msgs) > 0:
            if not passed:
                print '[blocked: ',
            else:
                print '[altered: ',
            for msg in msgs:
                print msg,
            print ']'
        print_status(status)
    else:
        print '-' * line_length
        print_status(status)    
    
def filter_status(status, filters):
    msgs = []
    for filt in filters:
        result, msg, tweet = filt.evaluate(status)
        if result is False:
            return False, [msg], tweet
        else:
            if msg is not None:
                msgs.append(msg)
            status = tweet
    return True, msgs, status

def print_status(status):
    #print status._json
    fmt = '%m/%d/%y %H:%M GMT'
    spacers = 1
    j = 19
    i = line_length - spacers - j

    print ('%-' + str(i) + 's') % ('@' + status.author.screen_name[:i]),
    print ('%' + str(j) + 's') % status.created_at.strftime(fmt)

    user_attr = '['
    if status.author.verified:
        user_attr += 'v'
    if status.author.protected:
        user_attr += 'p'
    user_attr += '] ('
    
    print ('%-' + str(i) + 's') % status.author.name[:i],
    print ('%' + str(j) + 's') % (user_attr + str(status.author.followers_count) + ')')
    
    lines = textwrap.wrap(status.text, line_length, break_long_words=False)
    for line in lines:
        print line

def main():    
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.secure = True
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    
    stream = tweepy.Stream(auth = api.auth, listener = FilterListener())
    stream.userstream(encoding='utf8')    

if __name__ == '__main__':
    main()
