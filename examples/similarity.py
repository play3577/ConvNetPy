# Requires nltk, nltk data, twython

from vol         import Vol
from net         import Net 
from trainers    import Trainer

from nltk        import FreqDist, RegexpTokenizer
from nltk.corpus import gutenberg as corpus #can use others like inaugural
from string      import punctuation
from operator    import mul
from math        import sqrt
from twython     import Twython, TwythonError

training_data = None
network = None
t = None
N = 0
words = None

# This list of English stop words is taken from the "Glasgow Information
# Retrieval Group". The original list can be found at
# http://ir.dcs.gla.ac.uk/resources/linguistic_utils/stop_words
ENGLISH_STOP_WORDS = frozenset([
    "a", "about", "above", "across", "after", "afterwards", "again", "against",
    "all", "almost", "alone", "along", "already", "also", "although", "always",
    "am", "among", "amongst", "amoungst", "amount", "an", "and", "another",
    "any", "anyhow", "anyone", "anything", "anyway", "anywhere", "are",
    "around", "as", "at", "back", "be", "became", "because", "become",
    "becomes", "becoming", "been", "before", "beforehand", "behind", "being",
    "below", "beside", "besides", "between", "beyond", "bill", "both",
    "bottom", "but", "by", "call", "can", "cannot", "cant", "co", "con",
    "could", "couldnt", "cry", "de", "describe", "detail", "do", "done",
    "down", "due", "during", "each", "eg", "eight", "either", "eleven", "else",
    "elsewhere", "empty", "enough", "etc", "even", "ever", "every", "everyone",
    "everything", "everywhere", "except", "few", "fifteen", "fify", "fill",
    "find", "fire", "first", "five", "for", "former", "formerly", "forty",
    "found", "four", "from", "front", "full", "further", "get", "give", "go",
    "had", "has", "hasnt", "have", "he", "hence", "her", "here", "hereafter",
    "hereby", "herein", "hereupon", "hers", "herself", "him", "himself", "his",
    "how", "however", "hundred", "i", "ie", "if", "in", "inc", "indeed",
    "interest", "into", "is", "it", "its", "itself", "keep", "last", "latter",
    "latterly", "least", "less", "ltd", "made", "many", "may", "me",
    "meanwhile", "might", "mill", "mine", "more", "moreover", "most", "mostly",
    "move", "much", "must", "my", "myself", "name", "namely", "neither",
    "never", "nevertheless", "next", "nine", "no", "nobody", "none", "noone",
    "nor", "not", "nothing", "now", "nowhere", "of", "off", "often", "on",
    "once", "one", "only", "onto", "or", "other", "others", "otherwise", "our",
    "ours", "ourselves", "out", "over", "own", "part", "per", "perhaps",
    "please", "put", "rather", "re", "same", "see", "seem", "seemed",
    "seeming", "seems", "serious", "several", "she", "should", "show", "side",
    "since", "sincere", "six", "sixty", "so", "some", "somehow", "someone",
    "something", "sometime", "sometimes", "somewhere", "still", "such",
    "system", "take", "ten", "than", "that", "the", "their", "them",
    "themselves", "then", "thence", "there", "thereafter", "thereby",
    "therefore", "therein", "thereupon", "these", "they", "thick", "thin",
    "third", "this", "those", "though", "three", "through", "throughout",
    "thru", "thus", "to", "together", "too", "top", "toward", "towards",
    "twelve", "twenty", "two", "un", "under", "until", "up", "upon", "us",
    "very", "via", "was", "we", "well", "were", "what", "whatever", "when",
    "whence", "whenever", "where", "whereafter", "whereas", "whereby",
    "wherein", "whereupon", "wherever", "whether", "which", "while", "whither",
    "who", "whoever", "whole", "whom", "whose", "why", "will", "with",
    "within", "without", "would", "yet", "you", "your", "yours", "yourself",
    "yourselves"
])

def volumize(dist):
    global words

    V = Vol(1, 1, N, 0.0)
    for i, word in enumerate(words):
        V.w[i] = dist.freq(word)
    return V

def load_data():
    global N, words

    freqs = [ FreqDist(corpus.words(fileid)) for fileid in corpus.fileids() ]
    words = list(set(word 
                    for dist in freqs 
                    for word in dist.keys()
                    if word not in ENGLISH_STOP_WORDS and
                    word not in punctuation))

    data = []
    N = len(words)
    for dist in freqs:
        x = volumize(dist)
        data.append((x, x.w))

    return data

def start():
    global training_data, network, t, N

    training_data = load_data()
    print 'Data loaded...'

    layers = []
    layers.append({'type': 'input', 'out_sx': 1, 'out_sy': 1, 'out_depth': N})
    layers.append({'type': 'fc', 'num_neurons': 50, 'activation': 'sigmoid'})
    layers.append({'type': 'fc', 'num_neurons': 10, 'activation': 'sigmoid'})
    layers.append({'type': 'fc', 'num_neurons': 50, 'activation': 'sigmoid'})
    layers.append({'type': 'regression', 'num_neurons': N})

    print 'Layers made...'

    network = Net(layers)

    print 'Net made...'
    print network

    t = Trainer(network, {'method': 'adadelta', 'batch_size': 4, 'l2_decay': 0.0001});

def train():
    global training_data, network, t

    print 'In training...'
    print 'k', 'time\t\t  ', 'loss\t  '
    print '----------------------------------------------------'
    try:
        for x, y in training_data: 
            stats = t.train(x, y)
            print stats['k'], stats['time'], stats['loss']
    except:
        return

class GetTweets(object):

    def __init__(self):
        self.APP_KEY = "###"
        self.APP_SECRET = "###"

        self.twitter = Twython(self.APP_KEY, self.APP_SECRET, oauth_version=2)
        self.ACCESS_TOKEN = self.twitter.obtain_access_token()
        self.twitter = Twython(self.APP_KEY, access_token=self.ACCESS_TOKEN)

    def get_user(self, username, count=200):
        return [ tweet['text']
                for tweet in self.twitter.get_user_timeline(screen_name=username, count=count) ]

    def get_hashtag(self, hashtag, count=200):
        query = '#{}'.format(hashtag)
        return [ tweet['text'].replace('#', '')
                for tweet in self.twitter.search(q=query, count=count)['statuses'] ]

def doc_code(v):
    global network

    network.forward(v)
    return network.layers[4].out_act.w

def cos(v1, v2):
    dot = float(sum(map(mul, v1, v2)))
    norm1 = sqrt(sum(e for e in v1))
    norm2 = sqrt(sum(e for e in v2))
    return dot / (norm1 * norm2)

def test(): 
    gt = GetTweets()
    documents = gt.get_hashtag('ferguson', count=20)
    documents += gt.get_hashtag('police', count=21)
    print 'Query:', documents[-1]

    tokenizer = RegexpTokenizer('\w+')
    vols = []
    for doc in documents:
        samples = []
        for token in tokenizer.tokenize(doc):
            word = token.lower()
            if word not in ENGLISH_STOP_WORDS and word not in punctuation:
                samples.append(word)
        vols.append(volumize(FreqDist(samples)))

    vectors = [ doc_code(v) for v in vols[:-1] ]
    query_vec = doc_code(vols[-1])

    sims = [ cos(v, query_vec) for v in vectors ]
    m = max(sims)
    print m, documents[sims.index(m)]