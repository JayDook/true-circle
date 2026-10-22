#!/usr/bin/env python3
"""True Circle by @JayDook (MIT). https://github.com/JayDook/true-circle
Score X interactions by conversation. Usage:
score.py --me <owner_id> --data full --likes likes [--flavor fans --likers likers] [--exclude excl.json] [--out out] [--n 51]
Inputs: raw X API JSON result pages saved as *.txt (search_posts_all / likes / get_posts_by_ids)."""
import json,glob,collections,argparse,os
ap=argparse.ArgumentParser();ap.add_argument('--me',required=True);ap.add_argument('--data',default='full')
ap.add_argument('--likes',default='likes');ap.add_argument('--exclude');ap.add_argument('--out',default='out');ap.add_argument('--n',type=int,default=51);ap.add_argument('--likers',help='dir of get_posts_liking_users pages named <post_id>[_pN].txt (fans only)');ap.add_argument('--lurkers',type=int,default=12,help='fans: size of the Lurkers list (likers with no conversations)');ap.add_argument('--flavor',choices=['classic','fans','mutuals'],default='classic')
A=ap.parse_args();ME=A.me;os.makedirs(A.out,exist_ok=True)
EXCL={h.lower() for h in json.load(open(A.exclude))} if A.exclude else set()
def load(f):
    t=open(f).read();i=t.find('{')
    try: return json.loads(t[i:t.rfind('}')+1])
    except Exception: return {}
files=glob.glob(A.data+'/*.txt');lfiles=glob.glob(A.likes+'/*.txt') if A.likes else []
U={};P={};cm={}
for f in files:
    d=load(f)
    for p in (d.get('data') if isinstance(d.get('data'),list) else [])+d.get('includes',{}).get('tweets',[]):
        if 'conversation_id' in p: cm[p['id']]=p['conversation_id']
        P.setdefault(p['id'],p)
def CONV(i,dep=0):
    if i in cm: return cm[i]
    p=P.get(i)
    if not p or dep>60: return None
    r=[x['id'] for x in p.get('referenced_tweets') or [] if x['type']=='replied_to']
    if not r: return i
    c=CONV(r[0],dep+1)
    if c: cm[i]=c
    return c
seen=set();conv=collections.defaultdict(lambda:collections.defaultdict(set))
ev=collections.defaultdict(lambda:collections.defaultdict(list))
days=collections.defaultdict(set);bon=collections.defaultdict(collections.Counter);posts=collections.Counter()
for f in files+lfiles:
    d=load(f);liked=f in lfiles
    for u in d.get('includes',{}).get('users',[]): U.setdefault(u['id'],u)
    dd=d.get('data',[])
    if not isinstance(dd,list): continue
    tw={x['id']:x for x in d.get('includes',{}).get('tweets',[])}
    for p in dd:
        k=('L' if liked else '')+p['id']
        if k in seen: continue
        seen.add(k);a=p.get('author_id');day=p.get('created_at','')[:10]
        if liked:
            if a and a!=ME: bon[a]['like']+=1
            continue
        c=CONV(p['id']) or 'day:%s:%s'%(day,p.get('in_reply_to_user_id') if a==ME else a)
        txt=p.get('text','')[:140]
        if a==ME:
            r=p.get('in_reply_to_user_id')
            if r and r!=ME: conv[r][c].add('out');days[r].add(day);posts[r]+=1;ev[r][c].append((day,'out',txt))
            for rt in p.get('referenced_tweets') or []:
                if rt['type']=='quoted' and rt['id'] in tw and tw[rt['id']].get('author_id')!=ME:
                    q=tw[rt['id']]['author_id'];bon[q]['quote']+=1;days[q].add(day)
            for m in (p.get('entities') or {}).get('mentions',[]):
                if m.get('id') and m['id'] not in (ME,r): bon[m['id']]['mention']+=1
        elif a:
            days[a].add(day);posts[a]+=1;conv[a][c].add('in');ev[a][c].append((day,'in',txt))
            if p.get('in_reply_to_user_id')!=ME: bon[a]['mention_in']+=1
LK=collections.defaultdict(set)  # liker id -> set of owner posts they liked
if A.likers and A.flavor=='fans':
    for f in glob.glob(A.likers+'/*.txt'):
        pid=os.path.basename(f)[:-4].split('_')[0];d=load(f)
        for u in d.get('data',[]) if isinstance(d.get('data'),list) else []:
            U.setdefault(u['id'],u)
            if u['id']!=ME: LK[u['id']].add(pid)
S={}
for a in set(conv)|set(bon)|set(LK):
    cs=conv[a];two=sum(1 for v in cs.values() if len(v)==2);one=len(cs)-two;b=bon[a]
    bonus=min(3,0.75*b['quote']+0.25*(b['mention']+b['mention_in'])+0.25*b['like'])
    inc=sum(1 for v in cs.values() if 'in' in v)
    if A.flavor=='fans':   # who engages with the owner, reciprocated or not
        sc=3*inc+len(days[a])+min(3,0.5*b['mention_in'])+1.5*len(LK[a])  # each liked top post counts; quiet likers included
        if inc==0 and not LK[a]: continue
    elif A.flavor=='mutuals':  # only real back-and-forth counts
        if two==0: continue
        sc=3*two+len(days[a])+min(1,0.25*b['like'])
    else: sc=3*two+1.5*one+len(days[a])+bonus
    S[a]=(round(sc,2),two,one,len(days[a]),posts[a],dict(b,**({'liked_owner_posts':len(LK[a])} if LK[a] else {})))
rk=[(a,v) for a,v in sorted(S.items(),key=lambda x:-x[1][0]) if a in U and a!=ME and U[a]['username'].lower() not in EXCL]
LR=[]
if A.flavor=='fans':  # split: conversations -> rings; pure likers -> Lurkers
    LR=sorted([(a,v) for a,v in rk if v[1]+v[2]==0 and LK[a]],key=lambda x:(-len(LK[x[0]]),-x[1][0]))[:A.lurkers]
    rk=[(a,v) for a,v in rk if v[1]+v[2]>0]
for n,(a,v) in enumerate(rk[:20]): print(n+1,U[a]['username'],v[0],'two=%d one=%d days=%d posts=%d'%v[1:5],'|',(U[a].get('description') or '')[:60].replace('\n',' '))
top=max(posts.items(),key=lambda x:x[1]) if posts else None
if top and top[0] in U: print('most raw posts:',U[top[0]]['username'],top[1],'rank',[a for a,_ in rk].index(top[0])+1 if top[0] in [a for a,_ in rk] else 'excluded')
E=[{'rank':n+1,'username':U[a]['username'],'score':v[0],'two_way_convs':v[1],'one_way_convs':v[2],'active_days':v[3],'posts':v[4],'bonus_counts':v[5],
  'conversations':[{'conversation_id':c,'first_date':min(x[0] for x in L),'direction':'two-way' if len({x[1] for x in L})==2 else ('owner->them' if L[0][1]=='out' else 'them->owner'),'n_posts':len(L),'snippet':sorted(L)[0][2]} for c,L in sorted(ev[a].items(),key=lambda kv:min(x[0] for x in kv[1]))]} for n,(a,v) in enumerate(rk[:A.n])]
json.dump({'excluded':sorted(EXCL),'accounts':E,'lurkers':[{'rank':n+1,'username':U[a]['username'],'top_posts_liked':len(LK[a]),'of_top_posts':len({os.path.basename(f)[:-4].split('_')[0] for f in glob.glob(A.likers+'/*.txt')}) if A.likers else 0,'liked_post_ids':sorted(LK[a]),'score':v[0],'bonus_counts':v[5]} for n,(a,v) in enumerate(LR)]},open(A.out+'/evidence.json','w'),indent=1)
me=U.get(ME,{})
json.dump([{'username':me.get('username','owner'),'img':me.get('profile_image_url')}]+[{'username':U[a]['username'],'img':U[a].get('profile_image_url')} for a,v in rk[:A.n]],open(A.out+'/list.json','w'))
if A.flavor=='fans':
    json.dump([{'username':U[a]['username'],'img':U[a].get('profile_image_url')} for a,v in LR],open(A.out+'/lurkers.json','w'))
    for n,(a,v) in enumerate(LR): print('lurker',n+1,U[a]['username'],'liked',len(LK[a]),'score',v[0])
print('wrote',A.out+'/list.json and evidence.json')
