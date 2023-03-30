import numpy as np
import seaborn as sns
import sklearn.cluster as cluster
from sklearn import metrics
import pandas as pd
import time
sns.set_context('poster')
sns.set_color_codes()
plot_kwds = {'alpha' : 0.25, 's' : 80, 'linewidths':0}

df = pd.read_csv("pubg stats dataset/agg_5_days.csv")

tmp = df['match_id'].unique()
dic_id = dict(zip(range(len(tmp)),tmp))
dic1_id = dict(zip(tmp,range(len(tmp))))
df['match_id']=df['match_id'].apply(lambda x: dic1_id[x])
tmp = df['match_mode'].unique()
dic_mode = dict(zip(range(len(tmp)),tmp))
dic1_mode = dict(zip(tmp,range(len(tmp))))
df['match_mode']=df['match_mode'].apply(lambda x: dic1_mode[x])
tmp = df['player_name'].unique()
dic_name = dict(zip(range(len(tmp)),tmp))
dic1_name = dict(zip(tmp,range(len(tmp))))
df['player_name']=df['player_name'].apply(lambda x: dic1_name[x])
df1 = df
def kmeans(df,k):
    km = cluster.KMeans(n_clusters=k)
    tmp = df[df.columns[1:-1]].values
    km = km.fit(tmp)
    t = km.labels_
    print(set(t),[(i,np.count_nonzero(t == i)) for i in set(t)])
    return {"eps":e,"min_samples":s,"error":km.inertia_}

def dbscan(df,e,s):
    km = cluster.DBSCAN(eps=e,min_samples=s)
    tmp = df[df.columns[1:-1]].values
    km = km.fit(tmp)
    t = km.labels_
    print(set(t),[(i,np.count_nonzero(t == i)) for i in set(t)])
    if len(set(t))==1:
        t=-1
    else:
        t = metrics.davies_bouldin_score(tmp, km.labels_)
    return {"eps":e,"min_samples":s,"error":t}

Sum_of_squared_distances_kmeans = []
K = range(2,41)
for k in K:
    Sum_of_squared_distances_kmeans.append(kmeans(df,k))

df1 = df[df.party_size==4]
Sum_of_squared_distances_kmeans_4 = []
K = range(2,41)
for k in K:
    Sum_of_squared_distances_kmeans_4.append(kmeans(df,k))

df1 = df[df.party_size==2]
Sum_of_squared_distances_kmeans_2 = []
K = range(2,41)
for k in K:
    Sum_of_squared_distances_kmeans_2.append(kmeans(df,k))

df1 = df[df.party_size==1]
Sum_of_squared_distances_kmeans_1 = []
K = range(2,41)
for k in K:
    Sum_of_squared_distances_kmeans_1.append(kmeans(df,k))

Sum_of_squared_distances_DBSCAN = []
ms = range(500,3000,100)
eps = [10,30,60,100,125,150,175,200,250,300,400,500]
for s in ms:
    for e in eps:
        Sum_of_squared_distances_DBSCAN.append(dbscan(df,e,s))