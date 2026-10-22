# True Circle by @JayDook (MIT). https://github.com/JayDook/true-circle
# Usage: render.py --list out/list.json --handle <handle> [--flavor classic|fans|mutuals] [--days 15|30|60] --out out/inner-circle.png [--theme NAME|surprise|theme.json]
# Avatars: <username>.jpg next to list.json. Rings 8/16/27; edit `rings` to change counts.
# THEMES: --theme takes a preset name (see PRESETS), 'surprise' (default: random non-halloween preset,
#   or halloween during October), or a path to a JSON file. Missing JSON keys fall back to 'space'.
#   Colors are [r,g,b] lists. Schema:
#   bg_top, bg_bottom        vertical background gradient
#   glow, glow_alpha         soft radial glow behind the rings (alpha 0-255)
#   particles                {"style": "stars|dots|bubbles|fireflies|snow|none", "color": [r,g,b], "count": int}
#   decorations              list of: moon_bats, nebula, skyline, sun, waves, trees, grid_floor, planet, mountains
#   deco_color, deco_color2  colors used by decorations
#   ring_inner, ring_outer, center_border, lurker   avatar border colors (inner ring, outer rings, you, lurkers)
#   halo                     dark halo behind each avatar and medal
#   title, title_outline, subtitle, accent          title text, its outline, flavor label, flavor side lines
#   tag_bg, tag_text         bottom-left handle tag
import json,math,random,argparse,os
ap=argparse.ArgumentParser();ap.add_argument('--list',default='list.json');ap.add_argument('--handle',default='');ap.add_argument('--out',default='inner-circle.png');ap.add_argument('--flavor',choices=['classic','fans','mutuals'],default='classic',help='title label at top center');ap.add_argument('--notitle',action='store_true');ap.add_argument('--lurkers',help='optional lurkers.json: extra outer ring of quiet likers');ap.add_argument('--theme',default='surprise',help='preset name, surprise, or theme.json');ap.add_argument('--days',type=int,choices=[15,30,60],help='lookback window shown in the subtitle, e.g. Classic · Last 30 days');ap.add_argument('--font',help='path to a bold .ttf (default: DejaVuSans-Bold, then Arial Bold, then Pillow default)');A=ap.parse_args();AV=os.path.dirname(os.path.abspath(A.list))
from PIL import Image,ImageDraw,ImageFont,ImageFilter
W=1200;C=600;S=2  # supersample
PRESETS={
 'halloween':dict(bg_top=[40,14,70],bg_bottom=[60,20,80],glow=[110,50,150],glow_alpha=90,particles=dict(style='stars',color=[220,200,255],count=120),decorations=['moon_bats'],deco_color=[255,178,60],deco_color2=[15,5,25],ring_inner=[255,130,30],ring_outer=[235,235,245],center_border=[255,255,255],lurker=[70,190,190],halo=[25,10,40],title=[255,150,45],title_outline=[25,10,40],subtitle=[225,215,245],accent=[200,170,240],tag_bg=[30,15,50],tag_text=[225,215,245]),
 'space':dict(bg_top=[5,8,25],bg_bottom=[15,10,40],glow=[60,90,200],glow_alpha=80,particles=dict(style='stars',color=[230,235,255],count=260),decorations=['nebula','planet'],deco_color=[170,60,200],deco_color2=[40,140,220],ring_inner=[120,200,255],ring_outer=[220,225,240],center_border=[255,255,255],lurker=[150,120,230],halo=[5,5,20],title=[150,215,255],title_outline=[5,8,25],subtitle=[215,225,245],accent=[120,160,230],tag_bg=[15,20,45],tag_text=[215,225,245]),
 'neon':dict(bg_top=[12,4,28],bg_bottom=[30,5,45],glow=[220,40,200],glow_alpha=70,particles=dict(style='dots',color=[0,240,255],count=60),decorations=['skyline'],deco_color=[8,2,18],deco_color2=[0,240,255],ring_inner=[255,40,200],ring_outer=[0,230,255],center_border=[255,255,255],lurker=[160,90,255],halo=[8,2,18],title=[255,60,210],title_outline=[8,2,18],subtitle=[170,250,255],accent=[0,230,255],tag_bg=[25,5,40],tag_text=[170,250,255]),
 'sunset':dict(bg_top=[255,120,80],bg_bottom=[90,30,90],glow=[255,190,110],glow_alpha=80,particles=dict(style='none',color=[255,255,255],count=0),decorations=['sun','mountains'],deco_color=[255,220,120],deco_color2=[60,20,60],ring_inner=[255,215,90],ring_outer=[255,240,230],center_border=[255,255,255],lurker=[255,160,140],halo=[60,20,50],title=[255,245,225],title_outline=[90,25,60],subtitle=[255,240,230],accent=[255,220,180],tag_bg=[70,20,60],tag_text=[255,240,230]),
 'ocean':dict(bg_top=[10,90,140],bg_bottom=[5,25,60],glow=[60,200,220],glow_alpha=70,particles=dict(style='bubbles',color=[190,240,255],count=70),decorations=['waves'],deco_color=[20,120,170],deco_color2=[5,40,80],ring_inner=[90,240,210],ring_outer=[220,245,255],center_border=[255,255,255],lurker=[120,200,255],halo=[5,25,50],title=[200,250,255],title_outline=[5,30,60],subtitle=[220,245,255],accent=[120,220,240],tag_bg=[5,35,65],tag_text=[220,245,255]),
 'forest':dict(bg_top=[20,60,40],bg_bottom=[8,28,18],glow=[120,200,90],glow_alpha=60,particles=dict(style='fireflies',color=[230,255,120],count=70),decorations=['trees'],deco_color=[6,22,14],deco_color2=[14,40,26],ring_inner=[230,200,80],ring_outer=[225,240,215],center_border=[255,255,255],lurker=[140,200,120],halo=[6,20,12],title=[235,215,110],title_outline=[6,22,14],subtitle=[225,240,215],accent=[160,210,130],tag_bg=[10,32,20],tag_text=[225,240,215]),
 'minimal':dict(bg_top=[248,248,250],bg_bottom=[232,234,240],glow=[255,255,255],glow_alpha=0,particles=dict(style='dots',color=[205,208,218],count=50),decorations=[],deco_color=[200,200,210],deco_color2=[200,200,210],ring_inner=[40,90,220],ring_outer=[150,156,172],center_border=[30,30,40],lurker=[95,105,125],halo=[215,218,226],title=[25,28,40],title_outline=[248,248,250],subtitle=[70,75,90],accent=[160,165,180],tag_bg=[225,228,236],tag_text=[30,32,45]),
 'synthwave':dict(bg_top=[25,5,50],bg_bottom=[120,20,100],glow=[255,80,160],glow_alpha=60,particles=dict(style='stars',color=[255,210,250],count=90),decorations=['sun','grid_floor'],deco_color=[255,150,60],deco_color2=[255,60,200],ring_inner=[255,200,60],ring_outer=[255,120,220],center_border=[255,255,255],lurker=[120,220,255],halo=[30,5,45],title=[255,220,90],title_outline=[40,5,60],subtitle=[255,210,250],accent=[255,90,200],tag_bg=[40,8,60],tag_text=[255,210,250]),
}
import datetime
def load_theme(t):
    if t and os.path.isfile(t):
        u=json.load(open(t));b=dict(PRESETS['space']);b.update(u);return b
    if not t or t=='surprise':
        t='halloween' if datetime.date.today().month==10 else random.Random().choice([k for k in PRESETS if k!='halloween'])
    if t not in PRESETS: raise SystemExit(f'unknown theme {t}; choose {list(PRESETS)} or a .json path')
    return PRESETS[t]
TH={k:(tuple(v) if isinstance(v,list) and v and isinstance(v[0],int) else v) for k,v in load_theme(A.theme).items()}
L=json.load(open(A.list))
me,rest=L[0],L[1:]
img=Image.new('RGB',(W*S,W*S))
d=ImageDraw.Draw(img)
a_,b_=TH['bg_top'],TH['bg_bottom']
for y in range(W*S):
    t=y/(W*S); d.line([(0,y),(W*S,y)],fill=tuple(int(a_[i]+(b_[i]-a_[i])*t) for i in range(3)))
def blob(cx,cy,rad,col,alpha,blur):
    global img
    m=Image.new('L',img.size);ImageDraw.Draw(m).ellipse([(cx-rad)*S,(cy-rad)*S,(cx+rad)*S,(cy+rad)*S],fill=alpha)
    img=Image.composite(Image.new('RGB',img.size,col),img,m.filter(ImageFilter.GaussianBlur(blur*S)))
if TH['glow_alpha']: blob(C,C,500,TH['glow'],TH['glow_alpha'],160)
DC,DC2=TH['deco_color'],TH['deco_color2'];DE=TH['decorations']
if 'nebula' in DE:
    for cx,cy,rr,col in [(220,260,260,DC),(980,900,300,DC2),(1000,250,180,DC),(200,950,200,DC2)]: blob(cx,cy,rr,col,110,90)
d=ImageDraw.Draw(img)
P=TH['particles'];rnd=random.Random(3)
for _ in range(P.get('count',0) if P.get('style')!='none' else 0):
    x,y=rnd.randint(0,W),rnd.randint(0,W);st=P['style'];col=tuple(P['color'])
    if st=='stars': r=rnd.choice([1,1,1,2,3]);d.ellipse([(x-r/2)*S,(y-r/2)*S,(x+r/2)*S,(y+r/2)*S],fill=col)
    elif st=='dots': r=rnd.choice([2,3,4]);d.ellipse([(x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S],fill=col)
    elif st=='bubbles': r=rnd.randint(4,14);d.ellipse([(x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S],outline=col,width=2*S)
    elif st=='snow': r=rnd.randint(2,5);d.ellipse([(x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S],fill=col)
    elif st=='fireflies':
        r=rnd.randint(2,4);g=Image.new('L',img.size);ImageDraw.Draw(g).ellipse([(x-r*4)*S,(y-r*4)*S,(x+r*4)*S,(y+r*4)*S],fill=90)
        img=Image.composite(Image.new('RGB',img.size,col),img,g.filter(ImageFilter.GaussianBlur(6*S)));d=ImageDraw.Draw(img)
        d.ellipse([(x-r)*S,(y-r)*S,(x+r)*S,(y+r)*S],fill=col)
if 'planet' in DE:
    blob(1080,1080,120,DC2,120,40);d=ImageDraw.Draw(img)
    d.ellipse([990*S,990*S,1170*S,1170*S],fill=DC2);d.arc([930*S,1050*S,1230*S,1110*S],start=160,end=380,fill=DC,width=6*S)
if 'sun' in DE:
    sy=1010 if 'grid_floor' in DE else 980
    blob(C,sy,260,DC,150,60);d=ImageDraw.Draw(img)
    d.ellipse([(C-200)*S,(sy-200)*S,(C+200)*S,(sy+200)*S],fill=DC)
    for k in range(5): yy=sy+30+k*30;d.rectangle([(C-210)*S,yy*S,(C+210)*S,(yy+6+k*2)*S],fill=a_ if 'grid_floor' in DE else b_)
if 'grid_floor' in DE:
    hz=1050;d.rectangle([0,hz*S,W*S,W*S],fill=TH['bg_top'])
    for k in range(-12,13): d.line([((C+k*40)*S,hz*S),((C+k*220)*S,W*S)],fill=DC2,width=2*S)
    for k in range(8): yy=hz+(k**1.7)*6;d.line([(0,yy*S),(W*S,yy*S)],fill=DC2,width=2*S)
if 'mountains' in DE:
    d.polygon([(0,W*S),(0,1020*S),(180*S,900*S),(380*S,1030*S),(560*S,920*S),(760*S,1060*S),(950*S,890*S),(W*S,1010*S),(W*S,W*S)],fill=DC2)
if 'skyline' in DE:
    x=0;rb=random.Random(9)
    while x<W:
        w=rb.randint(40,90);h=rb.randint(60,200);d.rectangle([x*S,(W-h)*S,(x+w)*S,W*S],fill=DC)
        for wy in range(W-h+12,W-10,22):
            for wx in range(x+8,x+w-8,16):
                if rb.random()<0.35: d.rectangle([wx*S,wy*S,(wx+6)*S,(wy+8)*S],fill=DC2)
        x+=w+rb.randint(0,8)
if 'waves' in DE:
    for k,col in enumerate([DC,DC2]):
        base=1060+k*60;pts=[(0,W*S)]+[(x*S,(base+18*math.sin(x/70+k))*S) for x in range(0,W+10,10)]+[(W*S,W*S)];d.polygon(pts,fill=col)
if 'trees' in DE:
    rt=random.Random(5)
    for k in range(26):
        x=k*48+rt.randint(-10,10);h=rt.randint(110,230);col=DC if k%2 else DC2
        d.polygon([(x*S,(W-h)*S),((x-45)*S,W*S),((x+45)*S,W*S)],fill=col)
if 'moon_bats' in DE:
    mx,my,mr=1090*S,105*S,62*S
    blob(1090,105,99,(255,170,70),120,30);d=ImageDraw.Draw(img)
    d.ellipse([mx-mr,my-mr,mx+mr,my+mr],fill=DC)
    for cx,cy,cr in [(-20,-15,12),(18,20,9),(25,-25,6)]:
        d.ellipse([mx+cx*S-cr*S,my+cy*S-cr*S,mx+cx*S+cr*S,my+cy*S+cr*S],fill=(238,155,45))
    def bat(x,y,s):
        x*=S;y*=S;s*=S
        pts=[(0,0),(-.3,-.25),(-.6,-.45),(-1,-.3),(-.85,-.1),(-.7,.05),(-.5,-.05),(-.35,.1),(-.15,0),(0,.2),(.15,0),(.35,.1),(.5,-.05),(.7,.05),(.85,-.1),(1,-.3),(.6,-.45),(.3,-.25)]
        d.polygon([(x+px*s,y+py*s) for px,py in pts],fill=DC2)
        d.ellipse([x-.12*s,y-.3*s,x+.12*s,y+.1*s],fill=DC2)
    for b in [(985,60,34),(1150,190,26),(1020,170,22),(80,1080,30),(150,1140,20),(70,90,28),(140,50,18),(1130,1060,24)]: bat(*b)
d=ImageDraw.Draw(img)
def avatar(name,cx,cy,r,border,bw):
    try: a=Image.open(os.path.join(AV,name+'.jpg')).convert('RGB')
    except: a=Image.new('RGB',(400,400),(90,60,120))
    D=int(2*r*S);a=a.resize((D,D),Image.LANCZOS)
    m=Image.new('L',(D,D));ImageDraw.Draw(m).ellipse([0,0,D-1,D-1],fill=255)
    R=(r+bw)*S
    d.ellipse([cx*S-R-4*S,cy*S-R-4*S,cx*S+R+4*S,cy*S+R+4*S],fill=TH['halo'])
    d.ellipse([cx*S-R,cy*S-R,cx*S+R,cy*S+R],fill=border)
    img.paste(a,(int(cx*S-r*S),int(cy*S-r*S)),m)
def F(s):
    for p in [A.font,'DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/Library/Fonts/Arial Bold.ttf','/System/Library/Fonts/Supplemental/Arial Bold.ttf','arialbd.ttf']:
        if p:
            try: return ImageFont.truetype(p,s*S)
            except OSError: pass
    return ImageFont.load_default(size=s*S)
rings=[(8,225,62,TH['ring_inner'],6,-90),(16,372,49,TH['ring_outer'],5,-90+11.25),(27,518,39,TH['ring_outer'],4,-90)]
LU=json.load(open(A.lurkers)) if A.lurkers else []
K=0.9 if LU else 1.0  # shrink main rings to make room for the Lurkers ring
T=not A.notitle  # title band: shrink and drop the layout to free the top ~120px
G=(0.88 if LU else 0.9) if T else 1.0;CY=C+40 if T else C
rings=[(n,rad*K*G,r*(0.92 if LU else 1)*G,col,bw,off) for n,rad,r,col,bw,off in rings]
i=0;pos=[]
for n,rad,r,col,bw,off in rings:
    for k in range(n):
        ang=math.radians(off+360*k/n)
        x,y=C+rad*math.cos(ang),CY+rad*math.sin(ang)
        avatar(rest[i]['username'],x,y,r,col,bw);pos.append((x,y,r));i+=1
avatar(me['username'],C,CY,112*(0.92 if LU else 1)*G,TH['center_border'],8)
if LU:  # Lurkers: dim teal ring, gap at the top for the label
    LR_,lr=548*G,24*G;n=len(LU);step=(360-40)/max(n-1,1) if n>1 else 0
    d.arc([(C-LR_)*S,(CY-LR_)*S,(C+LR_)*S,(CY+LR_)*S],start=-70,end=250,fill=TH['lurker'],width=2*S)
    for k,u in enumerate(LU):
        ang=math.radians(-70+step*k);x,y=C+LR_*math.cos(ang),CY+LR_*math.sin(ang)
        avatar(u['username'],x,y,lr,TH['lurker'],3)
        ov=Image.new('RGBA',img.size,(0,0,0,0));R=(lr+3)*S
        ImageDraw.Draw(ov).ellipse([x*S-R,y*S-R,x*S+R,y*S+R],fill=TH['halo']+(90,))
        img.paste(ov,(0,0),ov)
    d=ImageDraw.Draw(img)
    d.text((C*S,(CY-LR_)*S),'LURKERS',font=F(17),fill=TH['subtitle'],stroke_width=3*S,stroke_fill=TH['title_outline'],anchor='mm')
for j,(c,fc) in enumerate([((255,200,40),(90,60,0)),((205,210,220),(60,60,70)),((205,127,50),(70,35,5))]):
    x,y,r=pos[j];bx,by,br=x+r*0.72,y-r*0.72,17
    d.ellipse([(bx-br-2)*S,(by-br-2)*S,(bx+br+2)*S,(by+br+2)*S],fill=TH['halo'])
    d.ellipse([(bx-br)*S,(by-br)*S,(bx+br)*S,(by+br)*S],fill=c)
    d.text((bx*S,by*S),str(j+1),font=F(19),fill=fc,anchor='mm')
if T:
    d.text((C*S,48*S),'INNER CIRCLE',font=F(40),fill=TH['title_outline'],anchor='mm',stroke_width=6*S,stroke_fill=TH['title_outline'])
    d.text((C*S,48*S),'INNER CIRCLE',font=F(40),fill=TH['title'],anchor='mm')
    fl={'classic':'Classic','fans':'Fans','mutuals':'Mutuals'}[A.flavor]+(' · Last %d days'%A.days if A.days else '')
    tw=d.textlength(fl,font=F(22))/S
    for sx in (-1,1): d.line([((C+sx*(tw/2+14))*S,90*S),((C+sx*(tw/2+64))*S,90*S)],fill=TH['accent'],width=2*S)
    d.text((C*S,90*S),fl,font=F(22),fill=TH['subtitle'],anchor='mm',stroke_width=3*S,stroke_fill=TH['title_outline'])
tx,ty=30,1160
hd='@'+(A.handle or me['username']);tw2=d.textlength(hd,font=F(22))/S
d.rounded_rectangle([(tx-12)*S,(ty-22)*S,(tx+tw2+12)*S,(ty+18)*S],radius=10*S,fill=TH['tag_bg'])
d.text(((tx-2)*S,ty*S),hd,font=F(22),fill=TH['tag_text'],anchor='lm')
img.resize((W,W),Image.LANCZOS).save(A.out)
