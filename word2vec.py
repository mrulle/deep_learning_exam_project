# %%
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.autograd import Variable
import matplotlib.pyplot as plt
import pandas as pd
import torchtext as tt
import spacy
import time
from datetime import datetime
import re


dtype = torch.FloatTensor

# 3 Words Sentence (to semplify)
# All them form our text corpus

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
sentences = ''
play = False

start_time = datetime.fromtimestamp(time.time())
print(f'<{start_time}> training started on {device}')

if play:
    sentences = [ "i like dog", "i like cat", "i like animal", 
              "dog cat animal", "apple cat dog like", "dog fish milk like",
              "dog cat eyes like", "i like apple", "apple i hate",
              "apple i movie", "book music like", "cat dog hate", "cat dog like"]
else:
    df = pd.read_csv("./data/True.csv")
    nlp = spacy.load('en_core_web_sm')
    tokenizer = tt.data.utils.get_tokenizer('spacy')
    np_array = df['text'].values
    txt_array = np_array.tolist()
    sentences = '\n'.join(txt_array[0:10000])
    sentences = sentences.lower()

number_match = re.compile('\b.*[0-9].*\b')
punctuation_match = re.compile('\b.*(\.|\\|\/|,\/|\(|\)).*\b')
match_all = re.compile('\b.*![a-z].*\b')

print(sentences[0:100])
for sentence in sentences:
    match_all.sub(repl="",string=sentence)
    # sentence = number_match.sub(repl="", string=sentence)
    # sentence = punctuation_match.sub(repl="", string=sentence)

print(sentences[0:100])
print(f'number of articles: {len(txt_array)}')
print(f'length of sentences: {len(sentences)}')


# list all the words present in our corpus
word_sequence = tokenizer(sentences)
word_list = list(set(word_sequence))

print(f'{len(word_list)} unique tokens')

# word_list = [word for word in word_list if not number_match.match(word)]
# print(f'{len(word_list)} unique tokens after removing numbers')
# word_list = [word for word in word_list if not punctuation_match.match(word)]
# print(f'{len(word_list)} unique tokens after removing special characters')


# print(word_sequence)
# build the vocabulary
print(f'final length of word list: {len(word_list)}')
word_dict = {w: i for i, w in enumerate(word_list)}

# print(word_dict)

# Word2Vec Parameter
batch_size = 10  # To show 2 dim embedding graph
embedding_size = 2  # To show 2 dim embedding graph
voc_size = len(word_list)

# %%
# input word
# j = 1
# print("Input word : ")
# print(word_sequence[j], word_dict[word_sequence[j]])

# context words
# print("Context words : ")
# print(word_sequence[j - 1], word_sequence[j + 1])
# print([word_dict[word_sequence[j - 1]], word_dict[word_sequence[j + 1]]])

# %%
# Make skip gram of one size window
window_size = 2
skip_grams = []
for i in range(1, len(word_sequence) - window_size):
    input = word_dict[word_sequence[i]]
    context = [word_dict[word_sequence[i - window_size]], word_dict[word_sequence[i + window_size]]]
    for w in context:
        skip_grams.append([input, w])


#lets plot some data
# skip_grams[:6]

# %%
np.random.seed(172)

def random_batch(data, size):
    random_inputs = []
    random_labels = []
    random_index = np.random.choice(range(len(data)), size, replace=False)

    for i in random_index:
        # one-hot encoding of words
        random_inputs.append(np.eye(voc_size)[data[i][0]])  # input
        random_labels.append(data[i][1])  # context word

    return random_inputs, random_labels

# random_batch(skip_grams[:6], size=3)

# inputs: like , i, dog , context: i, dog, i

# %%
# Model
class Word2Vec(nn.Module):
    def __init__(self):
        super(Word2Vec, self).__init__()

        # parameters between -1 and + 1
        self.W = nn.Parameter(-2 * torch.rand(voc_size, embedding_size) + 1).type(dtype).to(device) # voc_size -> embedding_size Weight
        self.V = nn.Parameter(-2 * torch.rand(embedding_size, voc_size) + 1).type(dtype).to(device) # embedding_size -> voc_size Weight

    def forward(self, X):
        hidden_layer = torch.matmul(X, self.W) # hidden_layer : [batch_size, embedding_size]
        output_layer = torch.matmul(hidden_layer, self.V) # output_layer : [batch_size, voc_size]
        #return output_layer 
        return output_layer

model = Word2Vec()
# Set the model in train mode
model.train()

criterion = nn.CrossEntropyLoss() # Softmax (for multi-class classification problems) is already included
optimizer = optim.Adam(model.parameters(), lr=0.001)

# %%
# Training
epochs = 1
print_freq = (epochs // 20) or 1

for epoch in range(epochs):

    input_batch, target_batch = random_batch(skip_grams, batch_size)

    # new_tensor(data, dtype=None, device=None, requires_grad=False)
    input_batch = torch.Tensor(input_batch)
    target_batch = torch.LongTensor(target_batch)

    optimizer.zero_grad()
    output = model(input_batch)

    # output : [batch_size, voc_size], target_batch : [batch_size] (LongTensor, not one-hot)
    loss = criterion(output, target_batch)
    if (epoch + 1)%print_freq == 0:
        epoch_time = datetime.fromtimestamp(time.time())
        print('<', epoch_time, '> Epoch:', '%04d' % (epoch + 1), 'cost =', '{:.6f}'.format(loss))

    loss.backward()
    optimizer.step()

# %%
# Learned W
W, _= model.parameters()
print(W.detach())

# %%
file_path = f'./models/w2v_wsize_{window_size}_epocs_{epochs}.model'
torch.save(model.state_dict(), file_path)

end_time = datetime.fromtimestamp(time.time())
print(f'training finished at: {end_time}')

# %%
# for i, word in enumerate(word_list):
#     W, _= model.parameters()
#     W = W.detach()
#     x,y = float(W[i][0]), float(W[i][1])
#     plt.scatter(x, y)
#     plt.annotate(word, xy=(x, y), xytext=(5, 2), textcoords='offset points', ha='right', va='bottom')
# plt.show()


