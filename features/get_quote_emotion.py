#Written by: Anusha Balakrishnan
#Date: 4/18/14
from collections import defaultdict
import json
import pickle
import urllib
import urllib2


class SentimentAnalyzer:
    def __init__(self, rel="./"):
        self.MOVIEQUOTE = '%scorpus_polarities.pkl' % rel
        self.ADS = '%sadvert_polarities.pkl' % rel
        self.POLITICS = '%spolitical_polarities.pkl' % rel
        self.MNEMONIC = '%smnemonic_polarities.pkl' % rel
        self.polarity_mappings = defaultdict(dict)

    def save_corpus_polarities(self, in_file, path):
        read_file = file(in_file, 'r')
        polarity_info = []
        line = read_file.readline()
        while line:
            try:
                line = line.strip().split('\t')
                quote = line[0].strip()
                mem = line[1].strip()
            except IndexError as ie:
                # print "ERROR HERE:",line
                quote = line[0].strip()
                mem = quote[-1]
                quote = quote[0:-1]

                if mem!='M' and mem!='N':
                    mem = 'N'
                print "MODIFIED QUOTE: %s, MEM: %s" % (quote, mem)
            response = self.call_sentiment_analysis_api(quote)
            json_response = json.loads(response)
            if json_response==None:
                break
            packaged_data = (quote, mem, json_response)
            print packaged_data
            polarity_info.append(packaged_data)
            line = read_file.readline()

        pickle.dump(polarity_info, file(path, 'wb'))
    def load_emotion_mappings(self):
        all_data = [self.MOVIEQUOTE, self.ADS, self.MNEMONIC, self.POLITICS]
        for filename in all_data:
            data = pickle.load(file(filename, 'rb'))
            for item in data:
                slogan = item[0]
                info = item[2]
                self.polarity_mappings[slogan] = info

    def call_sentiment_analysis_api(self,sentence):
        url = "http://text-processing.com/api/sentiment/"
        param = {"text":sentence}
        data = urllib.urlencode(param)

        try:
            req = urllib2.Request(url, data)
            response = urllib2.urlopen(req)
            page = response.read()
            return page
        except urllib2.HTTPError as e:
            print e.code
            print e.read()
            return None

    '''
    Returns the polarity of a sentence.
    Returns 1 if positive, 0 if neutral, -1 if negative.
    '''
    def get_polarity(self,quote):
        if len(self.polarity_mappings.keys())==0:
            raise AttributeError("Mappings from slogan to emotion polarity haven't been loaded."
                                 "Run the load_emotion_mappings() function on the SentAnalyzer object.")
        else:
            quote = quote.strip()
            if self.polarity_mappings.has_key(quote):
                response = self.polarity_mappings[quote]
            else:
                print "Had to call sentiment analysis API"
                response = self.call_sentiment_analysis_api(quote)
                response = json.loads(response)
            label = response['label']
            if label=="neutral" :
                return 0
            elif label=="pos":
                return 1
            elif label=="neg":
                return -1
        return -9

    def __get_quote_polarity(self, quote):
        response = self.call_sentiment_analysis_api(quote)
        if response==None:
            return -9
        try:
            json_response = json.loads(response)
            polarity = self.get_polarity(json_response)
            return polarity
        except ValueError as v:
            print v
            return -9

    def get_emotion_strength(self, quote):
        if len(self.polarity_mappings.keys())==0:
            raise AttributeError("Mappings from slogan to emotion polarity haven't been loaded."
                                 "Run the load_emotion_mappings() function on the SentAnalyzer object.")
        else:
            quote = quote.strip()
            if self.polarity_mappings.has_key(quote):
                response = self.polarity_mappings[quote]
            else:
                print "Had to call sentiment analysis API:\t (%s)" %quote
                response = self.call_sentiment_analysis_api(quote)
                response = json.loads(response)
            label = response['label']
            probabilities = response['probability']
            pos = float(probabilities['pos'])
            neg = float(probabilities['neg'])
            neutral = float(probabilities['neutral'])

            if label=="neutral":
                return 1-neutral
            elif label=="pos":
                return pos
            elif label=="neg":
                return neg
        return -9


    def compare_polarities(self, first, second):
        """
        Returns 1 if the first quote is emotionally stronger than the second quote
        Returns -1 if the second quote is emotionally stronger than the first quote
        :param first: dictionary containing emotion probabilites for the first quote
        :param second: dictionary containing emotoion probabilities for the second quote
        """
        first_label = self.get_polarity(first)
        second_label = self.get_polarity(second)
        first_pol = self.get_emotion_strength(first)
        second_pol = self.get_emotion_strength(second)
        # If one quote is neutral and the other isn't, the one that isn't is stronger emotionally
        if first_label==0 and second_label!=0:
            return -1
        elif first_label!=0 and second_label==0:
            return 1
        # If both quotes are neutral, the one that's less neutral is stronger emotionally
        elif first_label==0 and second_label==0:
            if first_pol==second_pol:
                return 0
            if max(first_pol, second_pol) == first_pol:
                return 1
            else:
                return -1
        # Else if both quotes are not neutral, then the one with higher polarity is stronger,
        # irrespective of whether they are negative or positive
        else:
            if first_pol==second_pol:
                return 0
            if max(first_pol, second_pol)== first_pol:
                return 1
            else:
                return -1

def test_corpus_polarity():
    sentAnalysis = SentimentAnalyzer()
    corpus = file('../quotes.dat', 'r')
    line = corpus.readline()
    pos = {'M':0, 'N':0}
    neg = {'M':0, 'N':0}
    neut = {'M':0, 'N':0}
    total = {'M':0, 'N':0}
    while line:

        line = line.split('\t')
        sentence = line[0]
        mem = line[1].strip()
        polarity = sentAnalysis.get_quote_polarity(sentence)
        total[mem]+=1
        if polarity==1:
            pos[mem] +=1
        elif polarity==0:
            neut[mem]+=1
        elif polarity==-1:
            neg[mem]+=1
        line = corpus.readline()

        if (total['M']+total['N'])%500==0:
            print "Polarized %d quotes" %(total['M']+total['N'])


    print "MEMORABLE QUOTES"
    print "Percent positive: %f" % (float(pos['M'])/total['M'])
    print "Percent negative: %f" % (float(neg['M'])/total['M'])
    print "Percent neutral: %f" % (float(neut['M'])/total['M'])

    print "NON-MEMORABLE QUOTES"
    print "Percent positive: %f" % (float(pos['N'])/total['N'])
    print "Percent negative: %f" % (float(neg['N'])/total['N'])
    print "Percent neutral: %f" % (float(neut['N'])/total['N'])

def compare_quote_strengths(corpus_polarities, sentAnalyzer=None):
    if sentAnalyzer==None:
        sentAnalyzer = SentimentAnalyzer()
        sentAnalyzer.load_emotion_mappings()
    corpus = pickle.load(file(corpus_polarities, 'rb'))
    i=0
    mem = 0
    nonmem = 0
    total = 0
    while i<len(corpus):
        mem_info = corpus[i]
        nonmem_info = corpus[i+1]

        total += 1
        comparison = sentAnalyzer.compare_polarities(mem_info[0], nonmem_info[0])
        if comparison==1:
            mem +=1
        elif comparison==-1:
            nonmem+=1
        elif comparison==0:
            total-=1
        i+=2

    print "Percentage of pairs where the memorable quote was emotionally stronger: %f" % (float(mem)/total)
    print "Percentage of pairs where the non-memorable quote was emotionally stronger: %f" % (float(nonmem)/total)
