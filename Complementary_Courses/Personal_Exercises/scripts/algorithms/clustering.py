

import numpy as np
import pandas as pd
from collections import defaultdict

from sklearn.cluster import KMeans
from scipy.cluster.hierarchy import linkage, dendrogram, pdist, fcluster

import requests
from PIL import Image
import matplotlib.pyplot as plt
from wordcloud import WordCloud


'''
UTILS
=====
'''

def subsample_tfidf_by_cluster(model,words):
    ''' Return a sample version of a TFIDF for the words of a cluster '''
    return model[words]

def get_tf_idf_of_word_from_tfidf_matrix(model,k,v):
    ''' Get the TF vector and IDF float of an specific term '''
    return model.representation[[k]].values, model.mapping.idf_[v]

def compute_word_importance(model,words_of_cluster=None):
    ''' Compute the importance of a word given the TFIDF for a bunch of
    importance methods '''
    scores = defaultdict(list)
    if not words_of_cluster: words_of_cluster = model.token2id.keys()
    print('[INFO]: Computing word importance for each cluster')
    for k,v in model.token2id.items():
        # With this comparison we save a lot of time
        if k in words_of_cluster:
            scores['words'].append(k)
            t,i = get_tf_idf_of_word_from_tfidf_matrix(model,k,v)
            scores['idf'].append(i)
            scores['max_tf_idf'].append(np.max(t)*i)
            scores['avg_tf_idf'].append(np.max(t)*i)
            scores['norm_tf_idf'].append(np.linalg.norm(t)*i)
    return scores


'''
REGULAR CLUSTERING 
==================
'''

''' ALGORITHM '''

def kmean_clustering(
    model, #:Model
    num_clusters:int=4, 
    words_per_cluster:int=None):
    '''
    TODO: Consider MiniBatchKMeans
    
    Clusters using k-mean with k words per cluster
    ----------------------------------------------
        The k-words are the k closest to the centroid of that cluster
        Equivalently: the words are the ones most present in the 'fake'
        document represented by the centroid of the cluster

    Inputs:
    -------
        - model: Trained instance of class Model
        - num_clusters: Number of Clusters to look for
        - words_per_cluster: K parameter above

    Returns:
    -------- 
        - Dict key='cluster id', value=k_words_closest_to_centroid
    '''
    # 1. Performs K-Means algorithm to identify clusters
    km = KMeans(
        n_clusters=num_clusters) #,
        #n_jobs=-1)
    km.fit_transform(model.representation)
    # clusters = km.labels_.tolist()

    # Bring K most similar words to centroid
    closests_words_to_centroids = km.cluster_centers_.argsort()[:, :-words_per_cluster:-1] 
    
    cluster_words = defaultdict(list)
    for i in range(num_clusters):
        for idx in closests_words_to_centroids[i, :words_per_cluster]:
            cluster_words[i].append(model.id2token[idx])
    return cluster_words


''' PLOTS  '''

def mask_(url="https://image.shutterstock.com/image-illustration/flask-word-cloud-artwork-isolated-260nw-185529119.jpg"):
    return np.array(
        Image.open(
            requests.get(url,stream=True).raw))

def cluster_to_wordcloud(
    df, method='idf', max_words=100, use_mask=False):
    ''' Convert 1 cluster into a WordCloud given:
        - The TFIDF for the cluster
        - The Score Method that give imporance to the word '''
    # Create the wordcloud attending to the inverse of idf
    wordcloud = WordCloud(
        max_words=max_words, 
        mask=mask_ if use_mask else None,
        background_color="white").generate_from_frequencies(
            frequencies=dict(zip(df.words, df[method])))
    return wordcloud

def plot_clusters_as_wordclouds(
    tfidf:pd.DataFrame, 
    cluster_words:dict,
    method:str='idf',
    max_words_per_cloud=100, use_mask=False, n_cols=2):
    '''
    Arguments:
        - tfidf: TFIDF of the entire Corpus
        - cluster_words: Dict {'cluster_id': [list of important words]}
        - methods: the Score Method that give imporance to the word in that cluster
    Steps:
        - Iterate for each cluster
        - Subsample the TFIDF to the Cluster TDIDF (reduce the columns to increase performance)
        - Get the scores of the chosen methods to give importance to the words --> Not needed ???
        - Call cluster_to_wordcloud() for that cluster to get its corresponding wordcloud
    '''
    n_rows = len(cluster_words)//n_cols
    _, axs = plt.subplots(nrows=n_rows, ncols=n_cols,figsize=(n_cols*5,n_rows*5))
    
    for cluster,words in cluster_words.items():

        cluster_word_scores = pd.DataFrame(compute_word_importance(tfidf,words))
        print(cluster_word_scores.head())
        print(cluster_word_scores.shape)
        # cluster_tfidf = sort_scores(scores, 'norm_tf_idf')
        wordcloud = cluster_to_wordcloud(
            df=cluster_word_scores,
            method='norm_tf_idf',
            max_words=max_words_per_cloud,
            use_mask=use_mask)
        
        # Plot the resulting wordcloud
        axs[cluster // n_cols, cluster % n_cols].imshow(wordcloud)
        axs[cluster // n_cols, cluster % n_cols].axis('off')
    plt.tight_layout()
    plt.show()
    return




'''
HIERARCHICAL CLUSTERING 
=======================
'''

# def plot_dendogram_from_catalog(
#     model, 
#     n_terms:int,
#     truncate_mode=None,
#     clusters:int=5):
#     linkage_matrix = ward_clustering(model=model,n_terms=n_terms)
#     terms = get_most_relevant_terms(tfidf_df=model,n_terms=n_terms)
#     plot_dendogram_from_linkage_matrix(
#         linkage_matrix=linkage_matrix,
#         truncate_mode=truncate_mode,
#         clusters=clusters,
#         labels=terms)
#     return

def compute_dist_matrix(df,metric='cosine'):
    return pdist(df, metric=metric)


def hca_document_clustering(
    model, # Model
    method:str='ward',
    distance_metric:str='cosine'):
    '''
    Performs Hierarchical Cluster
    Arguments:
        - model: Model instance representation
        - methods: How the distance between clusters is minimized
        - distance_metric: How to measure the distance between 2 clusters
    NOTE: 
        Filtering by terms is breaking the whole thing when plotting ??
        Does it make sense to run it on all and then truncate the plot rather than
        subsampling the TFIDF by the most important words (columns)?
    '''
    X = model.representation
    print('[INFO]: Computing Distance Matrix using {} distance'.format(distance_metric))
    d = compute_dist_matrix(X,distance_metric)
    print('[INFO]: Performing Hierarchical Clustering using {} linkage'.format(method))
    linkage_matrix = linkage(y=d, method=method)
    return linkage_matrix


def plot_dendogram_from_linkage_matrix(
    linkage_matrix, 
    truncate_mode:str=None,
    p:int=None,
    labels:list=None,
    orientation='right',
    show_leaf_counts=True,
    leaf_rotation=0.,
    leaf_font_size=12,
    figsize=None):
    ''' Plot a dendogram out of its linkage matrix '''
    
    _, ax = plt.subplots(figsize=figsize) 

    dendrogram(
        Z=linkage_matrix,
        p=p,                            
        truncate_mode=truncate_mode,    
        orientation=orientation, 
        show_leaf_counts=show_leaf_counts,
        leaf_rotation=leaf_rotation,
        leaf_font_size=leaf_font_size,
        labels=labels, 
        ax=ax)

    plt.tick_params(
        axis= 'x',          
        which='both',      
        bottom='off',     
        top='off',       
        labelbottom='off')

    plt.tight_layout() #show plot with tight layout
    plt.show()
    return


if __name__ == '__main__':

    '''
    PIPELINE UNTIL THE TFIDF
    ------------------------
    '''    
    import sys
    sys.path.append('../../utils')
    sys.path.append('../../scripts')
    from nltk.corpus import stopwords
    from utils.general import parse_yaml
    from scripts.catalog import load_catalog, Catalog
    from sklearn.feature_extraction.text import TfidfVectorizer

    config = parse_yaml('config.yaml')
    paths = config['paths']

    catalog = Catalog()
    catalog = load_catalog(path=paths['catalog'], name='spacy_pipeline_on_US_corpus')
    catalog.collect_corpus(attr='processed_text', form=list)

    ''' TFIDF '''
    vectorizer = TfidfVectorizer(
        min_df=.1,
        max_df=.7,
        norm='l2',
        use_idf=True,
        smooth_idf=True,
        max_features=3000,
        ngram_range=(1,3),
        lowercase=True,
        stop_words=stopwords.words('english'))

    tfidf = catalog.to_matrix(
        vectorizer=vectorizer,
        modelname='TFIDF',
        max_docs=50)

    tfidf.representation.head()

    '''
    FLAT CLUSTERING
    ---------------
    '''
    NUM_CLUSTERS = 4
    EMBED_SIZE = 10000
    WORDS_PER_CLUSTER = 50

    clustered_words = kmean_clustering(
        model=catalog.models['TFIDF'],
        num_clusters=NUM_CLUSTERS, 
        words_per_cluster=WORDS_PER_CLUSTER)

    ''' Clustering2WordCloud '''
    plot_clusters_as_wordclouds(tfidf, clustered_words, method='idf')




    # '''
    # HIERARCHICAL CLUSTERING
    # -----------------------
    # '''
    # # Alternative 1 - Computing everything in advanced
    # MAX_TERMS = 500
    # terms = tfidf_df.sort_values(
    #     by='idf',ascending=False).iloc[:MAX_TERMS,:]['word'].tolist()

    # X = catalog.models['TFIDF'].representation
    # X = X[terms]
    # X.head(5)

    # dist = 1 - cosine_similarity(X)
    # linkage_matrix = ward(dist)
    # plot_dendogram_from_linkage_matrix(linkage_matrix, terms)



    # # Aternative 2 - Directly from the catalog.models['TFIDF']
    # matrix = ward_clustering(
    #     model=catalog.models['TFIDF'],
    #     tfidf_df=tfidf_df,
    #     terms = terms)

    # ''' Clustering to Dendogram ''' 
    # plot_dendogram_from_linkage_matrix(matrix, clusters=5)
    # # plot_dendogram_from_linkage_matrix(catalog.models['TFIDF'])
