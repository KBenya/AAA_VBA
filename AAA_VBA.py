import spotipy
import spotipy.util as util
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import os
import numpy as np
import scipy as sp
from scipy.spatial.distance import mahalanobis
import requests
from io import BytesIO
import matplotlib as plt
# --- get_user_data
def user_information(token):
    songs=[]
    nyers=[]
    if token:
        sp = spotipy.Spotify(auth=token)
        result = sp.current_user()
        return result['display_name'], result['id']
    else:
        print ("Can't get token")

def user_library(name, token):
    songs=[]
    if token:
        limit=50
        offset=0
        sp = spotipy.Spotify(auth=token)
        max_limit=True
        print("Getting "+name+"'s tracks")
        while max_limit:
            results = sp.current_user_saved_tracks(limit=limit, offset=offset)
            for item in results['items']:
                track = item['track']
                songs.append({"playlist_owner_name": "user_library_track","playlist_owner_id": "user_library_track","artist_name":track['artists'][0]['name'],"artist_id":track['artists'][0]['id'] ,"album_name": track["album"]["name"],"album_id": track["album"]["id"],"album_release_date":track["album"]['release_date'],"track_name":track['name'], "track_id":track["id"],"track_added_at":item['added_at'], "playlist_id":"user_library_track","playlist_name":"user_library_track"})

            offset+=limit
            if len(results['items'])<limit:
                max_limit=False
        df_songs=pd.DataFrame(songs)
        print('Total number of tracks: ',df_songs.shape[0])
        return df_songs
    else:
        print ("Can't get token for", username)

def user_playlists(username,token):
    songs=[]
    if token:
        limit=50
        offset=0
        sp = spotipy.Spotify(auth=token)
        max_limit=True
        print("Getting "+username+"'s saved playlists")
        while max_limit:
            results = sp.current_user_playlists(limit=limit, offset=offset)
            for item in results['items']:
                print("Playlist: ",item["name"])
                pl_max_limit=True
                limit_pl=100
                offset_pl=0
                playlist_id=item["id"]
                playlist_owner_id=item["owner"]["id"]
                if username==item['owner']['id']:
                    if item['tracks']['total']!=0:
                        while pl_max_limit:
                            results_p = sp.user_playlist_tracks(playlist_owner_id, playlist_id, limit=limit_pl, offset=offset_pl)
                            for track in results_p['items']:
                                song=track['track']
                                songs.append({"playlist_owner_name": item['owner']['display_name'],"playlist_owner_id": item['owner']['id'],"playlist_name": item['name'],"playlist_id": item['id'], "artist_name":song['artists'][0]['name'],"artist_id":song['artists'][0]['id'] ,"album_name": song["album"]["name"],"album_id": song["album"]["id"],"album_release_date":song["album"]['release_date'] ,"track_name": song['name'], "track_id": song["id"],"track_added_at":track['added_at'] })

                            offset_pl+=limit_pl
                            if len(results_p['items'])<limit_pl:
                                pl_max_limit=False

                else:
                    if item['tracks']['total']!=0:
                        while pl_max_limit:
                            results_p = sp.user_playlist_tracks(playlist_owner_id, playlist_id, limit=limit_pl, offset=offset_pl)
                            for track in results_p['items']:
                                song=track['track']
                                songs.append({"playlist_owner_name": item['owner']['display_name'],"playlist_owner_id": item['owner']['id'],"playlist_name": item['name'],"playlist_id": item['id'], "artist_name":song['artists'][0]['name'],"artist_id":song['artists'][0]['id'] ,"album_name": song["album"]["name"],"album_id": song["album"]["id"],"album_release_date":song["album"]['release_date'] ,"track_name": song['name'], "track_id": song["id"],"track_added_at":"not_user_saved" })

                            offset_pl+=limit_pl
                            if len(results_p['items'])<limit_pl:
                                pl_max_limit=False

            offset+=limit
            if len(results['items'])<limit:
                max_limit=False
    else:
        print ("Can't get token for", username)

    df_songs=pd.DataFrame(songs)
    return df_songs

def osszefon(df_l, df_p):
    print("Users's library + saved playlists concat")
    df_p=df_p[df_p['playlist_name']!='Discover Weekly']

    match=np.isin(df_p['track_id'], df_l['track_id'])

    matchR=[not i for i in match]
    df_tracks=pd.concat([df_l, df_p[matchR]]).reset_index().drop('index', 1)

    return df_tracks.dropna(subset=['track_id'])

def tracks_info(df, token):
    if token:
        sp = spotipy.Spotify(auth=token)
        print("Gathering user's tracks information!")
        for index in range(0,len(df),100):

            if index+99>len(df):
                track_ids=df.loc[index:len(df)-1,'track_id']
                print("100% done")
            else:
                track_ids=df.loc[index:index+99,'track_id']
                print(str(round((index+99)/len(df)*100, 2)) + "% done")

            result=sp.audio_features(tracks=track_ids)
            i=0
            for track in result:
                for key in ['danceability', 'energy','key','loudness','mode','speechiness','acousticness','instrumentalness','liveness','valence','tempo','duration_ms','time_signature','type']:

                    df.loc[index+i,key]=track[key]

                i+=1

        return df
    else:
        print("Can't get token")

def user_artists(df, token):
    if token:
        sp = spotipy.Spotify(auth=token)
        print("Gathering user's artists information!")
        df_art=df['artist_id'].value_counts()
        df_art=df_art.to_frame().reset_index().rename(index=str,columns={'artist_id': 'freq', 'index':'artist_id'})
        df_art['genres']='nincsen'
        df_art['artist_name']='nincsen'
        for index, row in df_art.iterrows():
            df_art.loc[index,'artist_name']=df['artist_name'][df['artist_id']==df_art.at[index,'artist_id']].unique()[0]

        for index in range(0,len(df_art),50):

            if index+49>len(df_art):
                track_ids=df_art.loc[str(index):str(len(df_art)-1),'artist_id']
                print("100% done")
            else:
                track_ids=df_art.loc[str(index):str(index+49),'artist_id']
                print(str(round((index+49)/len(df_art)*100, 2)) + "% done")

            result=sp.artists(track_ids)
            i=0
            for track in result['artists']:
                if len(track['genres'])==0:
                    pass
                else:
                    df_art.at[str(index+i),'genres']=track['genres']

                i+=1

        return df_art

    else:
        print("Can't get token")

def get_user_data(DATALOC='**url**'):
    print("User's profile initiated!")
    startname='aaa'
    scope_l = 'user-library-read'
    scope_p = 'playlist-read-private'

    token = util.prompt_for_user_token(startname, scope_l, client_id='ccbbd66e9120408a80ebf2a507d7e85f', client_secret='86393b63eb044dfca6f1d5d89df47794', redirect_uri='https://iloveprogramming.com/callback/')
    name, username=user_information(token)
    print(name,username)
    if len(name)==0:
        dic={"name":['nincsen'], "user_id":[username]}
    else:
        dic={"name":[name], "user_id":[username]}
    df_inf=pd.DataFrame(dic)
    requests.post(DATALOC,data={'todo':'write','df':df_inf.to_json(),'name':'data/users/'+username+"/"+username+'_info'})

    df_libra=user_library(username ,token)
    token = util.prompt_for_user_token(startname, scope_p, client_id='ccbbd66e9120408a80ebf2a507d7e85f', client_secret='86393b63eb044dfca6f1d5d89df47794', redirect_uri='https://iloveprogramming.com/callback/')
    df_plays=user_playlists(username ,token)

    df_t=osszefon(df_libra, df_plays)

    df_tracks=tracks_info(df_t, token)
    requests.post(DATALOC,data={'todo':'write','df':df_tracks.to_json(),'name':'data/users/'+username+"/"+username+'_tracks'})


    df_artists=user_artists(df_tracks, token)
    requests.post(DATALOC,data={'todo':'write','df':df_artists.to_json(),'name':'data/users/'+username+"/"+username+'_artists'})
    print("User's profile finished!")
# --- get_user_data
# --- comm_funcs
def available_users(DATA='**url**'):
    r=requests.post(DATA,data={'todo':'getpath','path':'/data/users/'})
    paths=eval(r.content)
    users=[]
    for path in paths:
        path=path[12:]
        if '/' not in path and len(path)>0:
            users.append(path)

    return users

def comm_ex(DATA='**url**'):
    r=requests.post(DATA,data={'todo':'getpath','path':'/data/communities/'})
    paths=eval(r.content)

    comms=[]
    for path in paths:
        path=path[18:]
        if '/' not in path and len(path)>0:
            comms.append(path)

    return comms

def files_incomm(comm,DATA='**url**'):
    r=requests.post(DATA,data={'todo':'getpath','path':'/data/communities/'})
    paths=eval(r.content)

    comms=[]
    comm_files=[]
    for path in paths:
        path=path[18:]
        if '/' not in path and len(path)>0:
            comms.append(path)

    if comm in comms:
        for path in paths:
            if path[:18+len(comm)]=='/data/communities/'+comm:
                comm_files.append(path[18+len(comm)+1:])
        return comm_files[1:]
    else:
        print(comm+' does not exist!')

def make_comm(comm_name, members ,DATA='**url**'):

    ex_comm=comm_ex()

    if comm_name not in ex_comm:
        av_users=available_users()
        dic={"user_id":[]}
        for member in members:
            if member not in av_users:
                print(member+" does not exist!")
            else:
                dic['user_id'].append(member)

        df=pd.DataFrame(dic)
        df.to_csv('proba.csv')
        requests.post(DATA,data={'todo':'write','df':df.to_json(),'name':'data/communities/'+comm_name+"/members"})
        print("Community made!")
    else:
        print(comm_name +" already exists!")

def join_comm(comm_name, members, DATA='**url**'):
    av_users=available_users()
    ex_comm=comm_ex()

    if comm_name not in ex_comm :
        print(comm_name+" does not exist!")
    else:
        r = requests.post(DATA,data={'path':'/data/communities/'+comm_name+"/members.csv",'todo':'read'})

        df =pd.read_csv(BytesIO(r.content))
        print("---")
        print("---")
        dic={"user_id":[]}
        for new_member in members:
            if new_member not in av_users:
                print(new_member+" does not exist!")
            else:
                if new_member not in df['user_id'].values:
                    dic['user_id'].append(new_member)
                    print(new_member + " added!")
                else:
                    print(new_member +" already a member!")

        if len(dic['user_id'])>0:
            df_new=pd.DataFrame(dic)
            df_ki=pd.concat([df.drop('Unnamed: 0', 1),df_new])
            requests.post(DATA,data={'todo':'write','df':df_ki.to_json(),'name':'data/communities/'+comm_name+"/members"})
            print("Community updated!")
# --- comm_funcs
# --- basic_stat
def get_community_names(comm_name, DATA='**url**', COMMDATA_LOC = '/data/communities/'):
    loc = COMMDATA_LOC + comm_name + '/'
    r = requests.post(DATA, data={'path':loc + 'members.csv','todo':'read'})
    df_members = pd.read_csv(BytesIO(r.content))
    return df_members

def create_comm_art_dict(df_members,USERDATA_LOC='/data/users/', DATA='**url**'):
    comm_art_dict = {}

    for index, row in df_members.iterrows():
        place = USERDATA_LOC + row['user_id'] + '/' + row['user_id'] + '_artists.csv'
        r = requests.post(DATA,data={'path':place, 'todo':'read'})
        comm_art_dict[row['user_id']] = pd.read_csv(BytesIO(r.content))
    return comm_art_dict

def create_comm_track_dict(df_members,USERDATA_LOC='/data/users/',DATA='**url**'):
    comm_track_dict = {}
    for index, row in df_members.iterrows():
        place = USERDATA_LOC + row['user_id'] + '/' + row['user_id'] + '_tracks.csv'
        r = requests.post(DATA,data={'path':place, 'todo':'read'})
        comm_track_dict[row['user_id']] = pd.read_csv(BytesIO(r.content))
    for user in comm_track_dict:
        df = comm_track_dict[user]
        for attribute in ['tempo','loudness']:
            df[attribute] = (df[attribute] - df[attribute].min())/ (df[attribute].max() - df[attribute].min())
    return comm_track_dict

def fav_artist_plot(num,comm_name,DATA='**url**',COMMDATA_LOC = '/data/communities/',USERDATA_LOC = '/data/users/'):
    comm_art_dict = create_comm_art_dict(get_community_names(comm_name),USERDATA_LOC)
    loc = COMMDATA_LOC + comm_name + '/'
    r = requests.post(DATA,data={'path':loc + 'comm_artists.csv', 'todo':'read'})
    if r.status_code==200:
        pd.read_csv(BytesIO(r.content), index_col=0, header=None, names = ['artist', 'freq']).tail(num).plot(kind='bar', title = 'Favourite artists')
    elif r.status_code==500:
        favs = pd.concat(comm_art_dict.values()).groupby('artist_name')['freq'].sum().sort_values()
        requests.post(DATA,data={'todo':'write','df':favs.to_json(),'name': loc + 'comm_artists.csv'})
        favs.tail(num).plot(kind='bar', title = 'Favourite artists')

def fav_genre_plot(num,comm_name,DATA='**url**',COMMDATA_LOC = '/data/communities/',USERDATA_LOC = '/data/users/'):
    comm_art_dict = create_comm_art_dict(get_community_names(comm_name),USERDATA_LOC)
    loc = COMMDATA_LOC + comm_name + '/'
    r = requests.post(DATA,data={'path':loc + 'comm_genres.csv', 'todo':'read'})
    if r.status_code==200:
        pd.read_csv(BytesIO(r.content), index_col=0, header = None, names = ['genre', 'freq']).head(num).plot(kind='bar', title = 'Favourite genres')
    elif r.status_code==500:
        dftt = pd.concat(comm_art_dict.values())['genres']
        def parselist(l):
            try:
                return pd.Series(eval(l))
            except:
                return pd.Series([])
        favs = dftt.apply(parselist).unstack().value_counts()
        requests.post(DATA,data={'todo':'write','df':favs.to_json(),'name': loc + 'comm_genres.csv'})
        favs.head(num).plot(kind='bar', title = 'Favourite genres')

def comm_track_attributes(comm_name,DATA='**url**',COMMDATA_LOC = '/data/communities/',USERDATA_LOC = '/data/users/'):
    comm_track_dict = create_comm_track_dict(get_community_names(comm_name),USERDATA_LOC)
    attributes = ['acousticness', 'danceability', 'energy', 'instrumentalness','liveness','loudness','speechiness','tempo','valence']
    loc = COMMDATA_LOC + comm_name + '/'
    r = requests.post(DATA,data={'path':loc + 'comm_attributes.csv', 'todo':'read'})
    if r.status_code==200:
        pd.read_csv(BytesIO(r.content), index_col=0).mean(axis=1).plot(kind='bar',title='Means of attributes')
        print(pd.read_csv(BytesIO(r.content), index_col=0))
    elif r.status_code==500:
        attr_dict = {}
        for attribute in attributes:
            subdict = {}
            for user in comm_track_dict:
                subdict[user] = comm_track_dict[user][attribute].mean()
            attr_dict[attribute] = subdict
        attrs = pd.DataFrame(list(attr_dict.values()),index=list(attr_dict.keys()))
        requests.post(DATA,data={'todo':'write','df':attrs.to_json(),'name': loc + 'comm_attributes.csv'}) # ITT ÍR
        attrs.mean(axis=1).plot(kind='bar', title='Means of attributes')
        print(pd.DataFrame(list(attr_dict.values()),index=list(attr_dict.keys())))
# --- basic_stat
# --- comm_search
def total_unique_tracks():
    communities=comm_ex()
    total_unique_tracks=pd.DataFrame()
    for i in communities:
            files=files_incomm(i)

            search_string=i+'_unique.csv'

            if search_string in files:

                r=requests.post('**url**',data={'path':'/data/communities'+"/" +i+"/"+i+'_unique.csv','todo':'read'})
                unique_tracks=pd.read_csv(BytesIO(r.content))
                total_unique_tracks=total_unique_tracks.append(unique_tracks, ignore_index=True)

            else:
                r=requests.post('**url**',data={'path':'/data/communities'+"/" +i+"/"+'members.csv','todo':'read'})
                members=pd.read_csv(BytesIO(r.content))
                unique_tracks=un_tracks(members, i)
                r=requests.post('**url**',data={'path':'/data/communities'+"/" +i+"/"+i+'_unique.csv','todo':'read'})
                unique_tracks=pd.read_csv(BytesIO(r.content))
                total_unique_tracks=total_unique_tracks.append(unique_tracks, ignore_index=True)

    return total_unique_tracks

def inv_covariance():
    test=total_unique_tracks()
    invcovmx=sp.linalg.inv(test[["acousticness", "danceability", "energy", "speechiness", "instrumentalness", "valence","loudness", "tempo"]].cov())
    return invcovmx

def un_tracks(users, community):
    first=True
    for i in users["user_id"]:

        r=requests.post('**url**',data={'path':'/data/users'+"/" +str(i)+"/"+str(i)+'_tracks.csv','todo':'read'})
        df_egy=pd.read_csv(BytesIO(r.content))


        a=pd.Series(np.zeros([len(df_egy['track_id'])]))
        a[:]=i
        df_egy["names"]=a

        if first:
            df_un=pd.DataFrame(columns=df_egy.columns)
            first=False

        match=np.isin(df_egy['track_id'], df_un['track_id'])
        matchR=[not i for i in match]
        try:
            df_un=pd.concat([df_un, df_egy[matchR]]).reset_index().drop('index', 1).drop('Unnamed: 0', 1)
        except:
            df_un=pd.concat([df_un, df_egy[matchR]]).reset_index().drop('index', 1)

        DATALOC='**url**'
        requests.post(DATALOC,data={'todo':'write','df':df_un.to_json(),'name':'data/communities'+"/" +community+"/"+community+'_unique'})

    return df_un

def calculate_similarity(community,invcovmx=inv_covariance()):
    r=requests.post('**url**',data={'path':'/data/communities'+"/" +community+"/"+'members.csv','todo':'read'})
    users=pd.read_csv(BytesIO(r.content))

    sim=pd.DataFrame(np.zeros([len(users),len(users)]),columns=users["user_id"],index=users["user_id"])

    k=0
    for i in users['user_id']:
        for j in users[k:len(users)]['user_id']:

            if j==i:
                sim.loc[i,j]=0
            else:
                sum_has=0

                r= requests.post('**url**',data={'path':'/data/users/'+i+"/"+i+'_tracks.csv','todo':'read'})
                e=pd.read_csv(BytesIO(r.content))

                r= requests.post('**url**',data={'path':'/data/users/'+j+"/"+j+'_tracks.csv','todo':'read'})
                n=pd.read_csv(BytesIO(r.content))

                df_e=e[["acousticness", "danceability", "energy", "speechiness","instrumentalness", "valence","loudness", "tempo"]].dropna().values
                df_k=n[["acousticness", "danceability", "energy", "speechiness","instrumentalness", "valence","loudness", "tempo"]].dropna().values

                for row_e in df_e:
                    for row_k in df_k:
                        sum_has+=mahalanobis(row_e,row_k,invcovmx)

                sim.loc[i,j]=sim.loc[j,i]=sum_has/(len(df_k)*len(df_k))
                k=k+1

        DATALOC='**url**'
        requests.post(DATALOC,data={'todo':'write','df':sim.to_json(),'name':'data/communities'+"/" +community+"/"+community+'_sim'})

    return sim



def search_engine(self,community,similarity="None", user="None",artist="None",genre="None",acousticness="None", danceability="None", energy="None", speechiness="None", instrumentalness="None", valence="None",loudness="None", tempo="None" ,sort="None", length=10):

    files=files_incomm(community)

    search_string=community+"_sim.csv"


    if search_string in files:

        if user =="None":
            r= requests.post('**url**',data={'path':'/data/communities'+"/" +community+"/"+community+'_unique.csv','todo':'read'})
            return_list=pd.read_csv(BytesIO(r.content))

            r=requests.post('**url**',data={'path':'/data/communities'+"/" +community+"/"+'members.csv','todo':'read'})
            members=pd.read_csv(BytesIO(r.content))

            if similarity!="None":
                for i in members.values:
                    if i==self:
                        return_list=return_list
                    else:

                        r= requests.post('**url**',data={'path':'/data/communities/'+community+"/"+community+'_sim.csv','todo':'read'})
                        sim_matrix=pd.read_csv(BytesIO(r.content))
                        print(sim_matrix)
                        sim_matrix.index=sim_matrix.columns

                        print(np.where(sim_matrix.loc[i,:]>0.1))
                        print(sim_matrix.columns[[np.where(sim_matrix.loc[i,:]>0.1)]])
                        print(sim_matrix.loc[self,i])
                        if sim_matrix.loc[self,i].values>similarity:
                            return_list=return_list
                        else:
                            return_list=return_list.drop(df.index==i)

        else:

            r= requests.post('**url**',data={'path':'/data/users/'+self+"/"+self+'_tracks.csv','todo':'read'})
            self_df=pd.read_csv(BytesIO(r.content))
            a=pd.Series(np.zeros([len(self_df['track_id'])]))
            a[:]=self
            self_df["names"]=a

            r= requests.post('**url**',data={'path':'/data/users/'+user+"/"+user+'_tracks.csv','todo':'read'})
            user_df=pd.read_csv(BytesIO(r.content))
            a=pd.Series(np.zeros([len(user_df['track_id'])]))
            a[:]=user
            user_df["names"]=a

            return_list=matching_tracks(self_df,user_df)

            if similarity!="None":
                r= requests.post('**url**',data={'path':'/data/communities/'+community+"/"+community+'_sim.csv','todo':'read'})
                sim_matrix=pd.read_csv(BytesIO(r.content))
                print(sim_matrix)
                sim_matrix.index=sim_matrix.columns
                print(sim_matrix)
                names=sim_matrix.loc[user,sim_matrix.loc[user,:]>similarity].index
                return_list=return_list[np.isin(return_list["names"],names)]

        attributes=[acousticness, danceability, energy, speechiness, instrumentalness, valence,loudness, tempo]
        attributes_str=["acousticness", "danceability", "energy", "speechiness", "instrumentalness", "valence","loudness", "tempo"]

        if artist !="None":
            return_list=return_list[return_list["artist_name"]==artist]

        if return_list.empty:
            return "There is no match for these arguments"
        else:

            for i in range(len(attributes)):
                if attributes[i] is not "None":
                    return_list=return_list[return_list[attributes_str[i]]>attributes[i]]

        if return_list.empty:
            return "There is no match for these arguments"
        else:
            if sort!="None":
                t=[attributes[i] !="None" for i in range(len(attributes))]
                k=[attributes_str[i] for i,x in enumerate(t) if x]
                if sort in k:
                    return_names=["artist_name","track_name","album_name",'album_release_date']+k
                    return return_list[return_names].sort_values(sort,ascending=0)[0:min(length,len(return_list['artist_name']))]
                else:
                    return_names=["artist_name","track_name","album_name",'album_release_date',sort]+k
                    return return_list[return_names].sort_values(sort,ascending=0)[0:min(length,len(return_list['artist_name']))]
            else:
                t=[attributes[i] !="None" for i in range(len(attributes))]
                k=[attributes_str[i] for i,x in enumerate(t) if x]
                return_names=["artist_name","track_name","album_name",'album_release_date']+k
                return return_list[return_names][1:min(length,len(return_list['artist_name']))]

    else:

       if user =="None":
            r= requests.post('**url**',data={'path':'/data/communities'+"/" +community+"/"+community+'_unique.csv','todo':'read'})
            return_list=pd.read_csv(BytesIO(r.content))
            r=requests.post('**url**',data={'path':'/data/communities'+"/" +community+"/"+'members.csv','todo':'read'})
            members=pd.read_csv(BytesIO(r.content))

            if similarity!="None":
                for i in members.values:
                    if i==self:
                        return_list=return_list
                    else:

                        calculate_similarity(members)
                        r= requests.post('**url**',data={'path':'/data/communities/'+community+"/"+community+'_sim.csv','todo':'read'})
                        sim_matrix=pd.read_csv(BytesIO(r.content))
                        print(sim_matrix)
                        sim_matrix.index=sim_matrix.columns

                        print(np.where(sim_matrix.loc[i,:]>0.1))
                        print(sim_matrix.columns[[np.where(sim_matrix.loc[i,:]>0.1)]])
                        print(sim_matrix.loc[self,i])
                        if sim_matrix.loc[self,i].values>similarity:
                            return_list=return_list
                        else:
                            return_list=return_list.drop(df.index==i)
            else:
                return_list=return_list
       else:

            r= requests.post('**url**',data={'path':'/data/users/'+self+"/"+self+'_tracks.csv','todo':'read'})
            self_df=pd.read_csv(BytesIO(r.content))
            a=pd.Series(np.zeros([len(self_df['track_id'])]))
            a[:]=self
            self_df["names"]=a

            r= requests.post('**url**',data={'path':'/data/users/'+user+"/"+user+'_tracks.csv','todo':'read'})
            user_df=pd.read_csv(BytesIO(r.content))
            a=pd.Series(np.zeros([len(user_df['track_id'])]))
            a[:]=user
            user_df["names"]=a

            return_list=matching_tracks(self_df,user_df)

            if similarity!="None":
                r= requests.post('**url**',data={'path':'/data/communities/'+community+"/"+community+'_sim.csv','todo':'read'})
                sim_matrix=pd.read_csv(BytesIO(r.content))
                print(sim_matrix)
                sim_matrix.index=sim_matrix.columns
                print(sim_matrix)

                print(sim_matrix.index)
                names=sim_matrix.loc[user,sim_matrix.loc[user,:]>similarity].index

                return_list=return_list[np.isin(return_list["names"],names)]

       attributes=[acousticness, danceability, energy, speechiness, instrumentalness, valence,loudness, tempo]
       attributes_str=["acousticness", "danceability", "energy", "speechiness", "instrumentalness", "valence","loudness", "tempo"]

       if artist !="None":
           return_list=return_list[return_list["artist_name"]==artist]

       if return_list.empty:
            return "There is no match for these arguments"
       else:

            for i in range(len(attributes)):
                if attributes[i] is not "None":
                    return_list=return_list[return_list[attributes_str[i]]>attributes[i]]

       if return_list.empty:
            return "There is no match for these arguments"
       else:
            if sort!="None":
                t=[attributes[i] !="None" for i in range(len(attributes))]
                k=[attributes_str[i] for i,x in enumerate(t) if x]
                if sort in k:
                    return_names=["artist_name","track_name","album_name",'album_release_date']+k
                    return return_list[return_names].sort_values(sort,ascending=0)[0:min(length,len(return_list['artist_name']))]
                else:
                    return_names=["artist_name","track_name","album_name",'album_release_date',sort]+k
                    return return_list[return_names].sort_values(sort,ascending=0)[0:min(length,len(return_list['artist_name']))]
            else:
                t=[attributes[i] !="None" for i in range(len(attributes))]
                k=[attributes_str[i] for i,x in enumerate(t) if x]
                return_names=["artist_name","track_name","album_name",'album_release_date']+k
                return return_list[return_names][1:min(length,len(return_list['artist_name']))]

def matching_tracks(self,dt2):
    match=self[np.isin(self['track_id'], dt2['track_id'])]
    return match

# --- comm_search
