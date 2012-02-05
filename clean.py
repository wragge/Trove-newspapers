from __future__ import division
import datetime
import os
import re
import nltk
from nltk.corpus import wordnet as wn
import string

PUNCTUATION = [',','.',';',':','(',')','?','!','"','\'']

def clean_text(text):
    '''
    Does some basic cleaning up of punctuation and other stuff.
    '''
    #Insert spaces after full stops
    clean_text = re.sub(r'(\w)\.(.)', r'\1\. \2', text)
    # Join up hyphenated words across line breaks
    clean_text = re.sub(r'(\w)\-\s+(\w)', r'\1\2', clean_text)
    # Break up compound words
    clean_text = re.sub(r'(\w)\-(\w)', r'\1 \2', clean_text)
    # Remove odd punctuation
    clean_text = re.sub(r'\.(\w)', r' \1', clean_text)
    clean_text = re.sub(r'\-(\w)', r' \1', clean_text)
    clean_text = re.sub(r',(\w)', r' \1', clean_text)
    clean_text = re.sub(r'\'(\w)', r' \1', clean_text)
    #remove multiple spaces
    clean_text = re.sub(r'\s+', ' ', clean_text)
    clean_text = re.sub(r'\bHie\b', 'the', clean_text)
    return clean_text

def clean_downloads(path):
    '''
    Clean all text files from a Trove harvest.
    Saves cleaned versions in a new directory.
    '''
    output_dir = os.path.join(path, 'cleaned')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    dirs = [ dir for dir in os.listdir(path) if os.path.isdir(os.path.join(path, dir))]
    for dir in dirs:
        print 'Processing: %s' % dir
        old_dir = os.path.join(path, dir)
        new_dir = os.path.join(output_dir, dir)
        if not os.path.exists(new_dir):
            os.makedirs(new_dir)
        report_path = os.path.join(new_dir, 'accuracy.txt')
        with open(report_path, 'w') as report:
            report.write('Generated: %s\n' % datetime.datetime.now().isoformat())
        entities = []
        try:
            with open(os.path.join(path, 'entities.txt'), 'r') as entities_file:
                entities = nltk.word_tokenize(entities_file.read())
        except IOError:
            try:
                with open(os.path.join(old_dir, 'entities.txt'), 'r') as entities_file:
                    entities = nltk.word_tokenize(entities_file.read())
            except IOError:
                print 'No entities file'
        files = [ os.path.join(old_dir, text_file) for text_file in os.listdir(old_dir) if text_file[-4:] == '.txt' ]
        clean = []
        dirty = []
        total_accuracy = 0
        with open(report_path, 'a') as report:
            for text_file in files:
                print 'Cleaning %s' % text_file
                with open(text_file, 'r') as text:
                    cleaned = clean_file(text.read(), entities)
                accuracy = (cleaned['recognised'] / cleaned['total']) * 100
                print 'Accuracy: %s%%' % accuracy
                total_accuracy += accuracy
                report.write('%s: %s%%\n' % (os.path.basename(text_file), accuracy))
                #clean.extend(cleaned['clean'])
                #dirty.extend(cleaned['dirty'])
                c_text = (' ').join([ word for word in cleaned['clean']])
                c_text = adjust_punctuation(c_text)
                with open(os.path.join(new_dir, os.path.basename(text_file)), 'w') as c_file:
                    c_file.write(c_text)                    
            average_accuracy = total_accuracy / len(files)
            print 'Average accuracy: %s%%' % average_accuracy
            report.write('Average accuracy: %s%%' % average_accuracy)

def adjust_punctuation(text):
    '''
    Gets rid of space between words and puctuation.
    '''
    for punc in PUNCTUATION:
        text = re.sub(r'(\w)\s+\%s' % punc, r'\1%s' % punc, text)
    return text
                

def clean_files(path):
    '''
    Clean files in the supplied directory
    '''
    texts = [text for text in os.listdir(path) if text[-4:] == '.txt']
    try:
        with open(os.path.join(path, 'entities.txt'), 'r') as entities_file:
            entities = nltk.word_tokenize(entities_file.read())
    except AttributeError:
        print 'No entities file'
        entities = []
    clean = []
    dirty = []
    for text in texts:
        print 'Cleaning %s' % text
        with open(os.path.join(path, text), 'r') as text_file:
            cleaned = clean_file(text_file.read(), entities)
            clean.extend(cleaned['clean'])
            dirty.extend(cleaned['dirty'])
    print sorted(set(dirty))
    print sorted(set(clean))
    print 'Dirty: %s' % len(dirty)
    print 'Clean: %s' % len(clean)
    
def clean_file(text, entities):
    clean = []
    recognised = 0
    dirty = []
    ctext = clean_text(text)
    tokens = nltk.word_tokenize(ctext)
    unusual = unusual_words(tokens)
    for token in tokens:
        ltoken = token.lower().strip()
        if ltoken in PUNCTUATION:
            clean.append(token)
            recognised += 1
        else:
            if len(ltoken) > 1 or ltoken in ['a', 'i']:
                if ltoken in unusual:
                    stem = wn.morphy(ltoken)
                    if stem:
                        clean.append(token)
                        recognised += 1
                    else:
                        if ltoken in entities:
                           clean.append(token)
                           recognised += 1
                        else:
                            dirty.append(token)
                            clean.append('[?]')
                else:
                    clean.append(token)
                    recognised += 1
            else:
                dirty.append(token)
    return {'clean': clean, 'dirty': dirty, 'recognised': recognised, 'total': len(tokens)}
        
def unusual_words(text):
    '''
    Returns a list of words in the supplied text than don't occur in NLTK's wordlist.
    '''
    #print text
    text_vocab = set(w.lower() for w in text)
    english_vocab = set(w.lower() for w in nltk.corpus.words.words())
    unusual = text_vocab.difference(english_vocab)
    return sorted(unusual)
    
def extract_entity_names(t):
    '''
    Extract named entities from the supplied chunk.
    Returns a list of entity names.
    '''
    entity_names = []
    if hasattr(t, 'node') and t.node:
        if t.node == 'NE':
            entity_names.append(' '.join([child[0] for child in t]))
        else:
            for child in t:
                entity_names.extend(extract_entity_names(child))        
    return entity_names

def get_entities(text):
    '''
    Extracts named entities from the supplied text.
    Returns a list of entity names.
    '''
    sentences = nltk.sent_tokenize(text)
    tokenized_sentences = [nltk.word_tokenize(sentence) for sentence in sentences]
    tagged_sentences = [nltk.pos_tag(sentence) for sentence in tokenized_sentences]
    chunked_sentences = nltk.batch_ne_chunk(tagged_sentences, binary=True)
    entity_names = []
    for tree in chunked_sentences:
        entity_names.extend(extract_entity_names(tree))
    return entity_names

def make_all_entity_lists(path):
    '''
    Loop through all subdirectories in the given folder extracting entities from enclosed files.
    Writes out a raw list of entities and a list of unique values with a frequency greater
    than 1.
    '''
    entity_names = []
    dirs = [ os.path.join(path, dir) for dir in os.listdir(path) if os.path.isdir(os.path.join(path, dir))]
    for dir in dirs:
        print 'Extracting entities from: %s' % dir
        entity_names.extend(make_entity_list(dir))
    with open(os.path.join(path, 'all_entities.txt'), 'w') as entities_file:
        for entity in sorted(entity_names):
            entities_file.write('%s\n' % entity)
    fdist = nltk.FreqDist(entity_names)
    # Adjust frequency value as required.
    unique_entities = sorted(set([ entity for entity in entity_names if fdist[entity] > 1 ]))
    with open(os.path.join(path, 'entities.txt'), 'w') as entities_file:
        for entity in unique_entities:
            entities_file.write('%s\n' % entity)
   
def make_entity_list(path):
    '''
    Extract named entities from files in the given folder.
    Write out a text file with unique values.
    Return raw list of entities for aggregation.
    '''
    texts = [text for text in os.listdir(path) if text[-4:] == '.txt']
    entity_names = []
    for text in texts:
        with open(os.path.join(path, text), 'r') as text_file:
            c_text = clean_text(text_file.read())
            entity_names.extend(get_entities(c_text))
    #fdist = nltk.FreqDist(entity_names)
    #print fdist
    #entity_names = sorted(set([ entity for entity in entity_names if fdist[entity] > 1 and entity.istitle() and entity.isalpha() ]))
    entities = []
    entity_names = [ entity for entity in entity_names if entity.istitle() and entity.isalpha() ]
    for entity in entity_names:
        for name in entity.split():
            entities.append(name.lower())
    unique_entities = sorted(set(entities))
    with open(os.path.join(path, 'entities.txt'), 'w') as entities_file:
        for entity in unique_entities:
            entities_file.write('%s\n' % entity)
    print unique_entities
    return entities