import cPickle as pk
import os
import re
import time

import numpy as np
import scipy.sparse as spr

letters = {'\'': 1, '<s>': 2, 'a': 3, 'b': 4, 'c': 5, 'd': 6, 'e': 7, 'f': 8, 'g': 9, 'h': 10, 'i': 11, 'j': 12,
           'k': 13, 'l': 14, 'm': 15, 'n': 16, 'o': 17, 'p': 18, 'q': 19, 'r': 20, 's': 21, 't': 22, 'u': 23, 'v': 24,
           'w': 25, 'x': 26, 'y': 27, 'z': 28}
letters_num = len(letters) + 1
word_length = 30


def split_train(train_set, alpha=0.1):
    import random
    with open(train_set, 'r') as fin:
        with open(train_set + '.part1', 'w') as out1:
            with open(train_set + '.part2', 'w') as out2:
                for line in fin:
                    line = line.strip()
                    if random.random() <= alpha:
                        out1.write(line + '\n')
                    else:
                        out2.write(line + '\n')


def is_ascii(s):
    return all(ord(c) < 128 for c in s)


def make_sens():
    with open('raw/corpus', 'r') as fin:
        with open('raw/corpus.sens', 'w') as fout:
            for line in fin:
                if is_ascii(line):
                    for sen in re.findall("[a-z ']+", line.lower().strip()):
                        sen = sen.strip()
                        if len(sen) > 0:
                            fout.write(sen + '\n')


def make_word_vector(word):
    if word == '<s>':
        return [letters[word]]

    vect = []
    for c in word[:word_length]:
        if c in letters:
            vect.append(letters[c])
        else:
            vect.append(0)
    return vect


def clean_sens(dict_in, corpus_out):
    with open('raw/corpus.sens', 'r') as corpus_in:
        with open(corpus_out, 'w') as corpus_out:
            dict = set(np.loadtxt(dict_in, dtype=str))

            for line in corpus_in:
                line = line.strip()
                flag = True
                for word in line.split():
                    if word not in dict:
                        flag = False
                        break
                if flag:
                    corpus_out.write(line + '\n')


def count_word_length():
    # 42 23 23 -> 30
    with open('raw/train', 'r') as fin:
        with open('raw/log', 'w') as log_out:
            len1 = 0
            len2 = 0
            len3 = 0
            dict = []
            for line in fin:
                line = line.strip().lower()
                index1 = line.rfind(' ')
                label = line[index1 + 1:]
                index2 = line.rfind(' ', 0, index1)
                last = line[index2 + 1:index1]
                index3 = line.rfind(' ', 0, index2)
                if index3 != -1:
                    last2 = line[index3 + 1: index2]
                else:
                    last2 = '<s>'

                len1 = max(len1, len(last2))
                len2 = max(len2, len(last))
                len3 = max(len3, len(label))

                dict.append(last2)

            dict = sorted(set(dict), key=lambda x: -len(x))
            for word in dict:
                log_out.write(word + '\n')

        print len1, len2, len3


def count_word():
    with open('raw/corpus.sens', 'r') as fin:
        dict = {}
        for line in fin:
            for word in re.findall("[a-z']+", line.strip()):
                if word in dict:
                    dict[word] += 1
                else:
                    dict[word] = 1

        print 'dict size', len(dict)

        with open('raw/corpus.words', 'w') as fout:
            for key, value in sorted(dict.items(), key=lambda (term, freq): -freq):
                fout.write(key + '\t' + str(value) + '\n')


def count_ngram(N, fin, fout):
    import pynlpl.textprocessors as proc

    with open(fin, 'r') as corpus_in:
        ngrams = {}
        for line in corpus_in:
            words = proc.tokenize(line)
            for ngram in proc.Windower(words, N, '<s>', None):
                key = '\t'.join(ngram)
                if key in ngrams:
                    ngrams[key] += 1
                else:
                    ngrams[key] = 1

        with open(fout, 'w') as ngrams_out:
            for key, value in sorted(ngrams.items(), key=lambda (term, freq): (term, -freq)):
                ngrams_out.write(key + '\t' + str(value) + '\n')


def load_dictionary(dict):
    import pandas as pd
    return pd.read_csv(dict, names=['word'], dtype={'word': str})


def load_bigrams(bigram_path):
    bigrams_bin_path = bigram_path + '.bin'
    if os.path.isfile(bigrams_bin_path):
        return pk.load(open(bigrams_bin_path, 'r'))

    bigrams = {}
    with open(bigram_path, 'r') as bigram_in:
        for line in bigram_in:
            arr = line.strip().split()
            if arr[0] in bigrams:
                bigrams[arr[0]].append((arr[1], int(arr[2])))
            else:
                bigrams[arr[0]] = [(arr[1], int(arr[2]))]

    for key in bigrams.keys():
        bigrams[key].sort(reverse=True, key=lambda (a, b): b)

    pk.dump(bigrams, open(bigrams_bin_path, 'w'))
    return bigrams


def load_bigrams2(bigram_path):
    bigram_bin_path = bigram_path + '.bin2'
    if os.path.isfile(bigram_bin_path):
        return pk.load(open(bigram_bin_path, 'r'))

    bigrams = {}
    with open(bigram_path, 'r') as bigram_in:
        for line in bigram_in:
            arr = line.strip().split()
            if arr[0] in bigrams:
                bigrams[arr[0]][arr[1]] = int(arr[2])
            else:
                bigrams[arr[0]] = {arr[1]: int(arr[2])}

    for key in bigrams.keys():
        counter = 0
        for key2 in bigrams[key]:
            counter += bigrams[key][key2]
        bigrams[key]['#total#'] = counter

    pk.dump(bigrams, open(bigram_bin_path, 'w'))
    return bigrams


def get_bifreq(bigrams, key, key2, norm=True):
    if key in bigrams:
        # if count_edit == 0:
        #     count_edit = count_total * 1.0 / (len(bigrams[key]) + 1)
        if key2 in bigrams[key]:
            if norm:
                return bigrams[key][key2] * 1.0 / bigrams[key]['#total#']
            else:
                return bigrams[key][key2]
    return 0


def make_feature(corpus, train_set):
    from SymSpell import SymSpell
    sp = SymSpell(corpus)

    print 'make feature', corpus, train_set
    with open(train_set, 'r') as train_in:
        with open(train_set + '.feature', 'w') as feature_out:
            bigrams = load_bigrams(corpus + '.bigram')

            count_total = 0
            count_feature = 0
            stime = time.time()

            for line in train_in:
                line = line.strip().lower()
                index1 = line.rfind(' ')
                label = line[index1 + 1:]
                index2 = line.rfind(' ', 0, index1)
                last = line[index2 + 1:index1]
                index3 = line.rfind(' ', 0, index2)
                if index3 != -1:
                    last2 = line[index3 + 1: index2]
                else:
                    last2 = '<s>'

                count_total += 1

                if count_total % 1000 == 0:
                    etime = time.time()
                    print count_total, count_feature, etime - stime
                    stime = etime

                if sp.get_index(label) == 0:
                    continue

                sug_list = sp.get_suggestions(last, True)
                for edit, value in sug_list:
                    # label
                    # [0-len]:last2
                    # [len+1 - 2*len+1]:edit
                    # 2*len+2:is_prefix
                    # 2*len+3:edit distance
                    # 2*len+4:freq
                    # 2*len+5: bi_freq
                    count_feature += 1

                    if edit == label:
                        feature_out.write('1 ')
                    else:
                        feature_out.write('0 ')
                    feature_out.write(str(sp.get_index(last2)) + ':1 ')
                    feature_out.write(str(sp.unique_word_count + 1 + sp.get_index(edit)) + ':1 ')
                    feature_out.write(str(2 * sp.unique_word_count + 1) + ':1 ')
                    if edit.startswith(last):
                        feature_out.write(str(2 * sp.unique_word_count + 2) + ':1 ')
                    else:
                        feature_out.write(str(2 * sp.unique_word_count + 2) + ':0 ')
                    feature_out.write(str(2 * sp.unique_word_count + 3) + ':' + str(value[1]) + ' ')
                    feature_out.write(str(2 * sp.unique_word_count + 4) + ':' + str(value[0]) + ' ')
                    term = last2 + '\t' + edit
                    if term in bigrams:
                        feature_out.write(str(2 * sp.unique_word_count + 5) + ':' + str(bigrams[term]) + '\n')
                    else:
                        feature_out.write(str(2 * sp.unique_word_count + 5) + ':0\n')


def get_feature_word_vector(last2, last, edit, label, freq, bi_freq):
    # label
    # last2
    # last
    # edit
    # freq
    # bi_freq
    foo = ''
    st = 0

    vect_last2 = make_word_vector(last2)
    for i in range(len(vect_last2)):
        foo += str(st + i * letters_num + vect_last2[i]) + ':1 '
    st += word_length * letters_num
    vect_last = make_word_vector(last)
    for i in range(len(vect_last)):
        foo += str(st + i * letters_num + vect_last[i]) + ':1 '
    st += word_length * letters_num
    vect_edit = make_word_vector(edit)
    for i in range(len(vect_edit)):
        foo += str(st + i * letters_num + vect_edit[i]) + ':1 '
    st += word_length * letters_num
    foo += str(st) + ':' + str(freq) + ' '
    st += 1
    foo += str(st) + ':' + str(bi_freq) + '\n'

    return foo


def foo_2_csr(foos):
    r = 0
    data = []
    row_ind = []
    col_ind = []
    for foo in foos:
        for fea in foo.split():
            x, y = fea.split(':')
            data.append(float(y))
            col_ind.append(int(x))
            row_ind.append(r)
        r += 1
    return spr.csr_matrix((data, (row_ind, col_ind)))


def make_feature_word_vector(corpus, train_set):
    from SymSpell import SymSpell
    sp = SymSpell(corpus)

    print 'make feature word vector', corpus, train_set
    with open(train_set, 'r') as train_in:
        with open(train_set + '.vfeature2', 'w') as feature_out:
            bigrams = load_bigrams2(corpus + '.bigram')

            count_total = 0
            count_feature = long(0)
            stime = time.time()
            for line in train_in:
                line = line.strip().lower()
                index1 = line.rfind(' ')
                label = line[index1 + 1:]
                index2 = line.rfind(' ', 0, index1)
                last = line[index2 + 1:index1]
                index3 = line.rfind(' ', 0, index2)
                if index3 != -1:
                    last2 = line[index3 + 1: index2]
                else:
                    last2 = '<s>'

                count_total += 1

                # if sp.get_index(last):
                #     continue

                if count_total % 10000 == 0:
                    etime = time.time()
                    print count_total, count_feature, etime - stime
                    stime = etime

                sug_list = sp.get_suggestions(last, True)
                for edit, _ in sug_list:
                    count_feature += 1

                    if edit == label:
                        feature_out.write('1 ')
                    else:
                        feature_out.write('0 ')
                    feature_out.write(get_feature_word_vector(last2, last, edit, label, sp.get_freq(edit),
                                                              get_bifreq(bigrams, last2, edit)))
