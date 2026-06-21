import json, numpy as np, geopandas as gpd, pyproj, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
from shapely.ops import unary_union
from shapely import contains_xy
from scipy.spatial import cKDTree
from collections import defaultdict
import pulp

R=((30-5)/60.0)*250*1000.0
pol=gpd.read_file(str(HERE / "geo" / "gadm41_POL_2.json")).to_crs("EPSG:2180")
land=unary_union(pol.geometry).buffer(0); minx,miny,maxx,maxy=land.bounds
tr=pyproj.Transformer.from_crs("EPSG:4326","EPSG:2180",always_xy=True)
xy=lambda la,lo: tr.transform(lo,la)
d=json.load(open(HERE / "loc28.json")); f=lambda s:float(str(s).replace(',','.'))
CRL=[(r[1],f(r[8]),f(r[9])) for r in d if r[0]=="CRL"]
CT =[(r[1],f(r[8]),f(r[9])) for r in d if r[0]=="CT" and "Rzeszów" not in r[1]]
named=np.array([xy(la,lo) for _,la,lo in CRL+CT])

D=5000
xs=np.arange(minx,maxx,D);ys=np.arange(miny,maxy,D);gx,gy=np.meshgrid(xs,ys)
P=np.column_stack([gx.ravel(),gy.ravel()]); dem=P[contains_xy(land,P[:,0],P[:,1])]
C=18000
xs2=np.arange(minx,maxx,C);ys2=np.arange(miny,maxy,C);gx2,gy2=np.meshgrid(xs2,ys2)
Q=np.column_stack([gx2.ravel(),gy2.ravel()]); cand=Q[contains_xy(land,Q[:,0],Q[:,1])]
crl=np.array([xy(la,lo) for _,la,lo in CRL]); cand=np.vstack([crl,cand]); NF=7
tree=cKDTree(cand); neigh=tree.query_ball_point(dem,R)
cand2dem=defaultdict(list)
for i,nb in enumerate(neigh):
    for j in nb: cand2dem[j].append(i)
NTOT=len(dem); print(f"demand={NTOT} candidates={len(cand)} fixed={NF}")

# greedy incremental curve (record coverage as bases added 7..21)
covered=np.zeros(NTOT,bool); open_set=set(range(NF))
for j in open_set:
    if cand2dem[j]: covered[cand2dem[j]]=True
gcurve={NF:covered.sum()/NTOT*100}
while len(open_set)<21:
    best,bg=None,-1; unc=~covered
    for j in range(len(cand)):
        if j in open_set or not cand2dem[j]: continue
        g=unc[cand2dem[j]].sum()
        if g>bg: bg,best=g,j
    open_set.add(best); covered[cand2dem[best]]=True
    gcurve[len(open_set)]=covered.sum()/NTOT*100

def milp(P_TOT):
    pr=pulp.LpProblem("m",pulp.LpMaximize)
    y={j:pulp.LpVariable(f"y{j}",cat="Binary") for j in range(len(cand))}
    x={i:pulp.LpVariable(f"x{i}",0,1) for i in range(NTOT)}
    pr+=pulp.lpSum(x.values())
    for j in range(NF): pr+=y[j]==1
    pr+=pulp.lpSum(y.values())<=P_TOT
    for i,nb in enumerate(neigh):
        pr+= x[i]<=(pulp.lpSum(y[j] for j in nb) if nb else 0)
    pr.solve(pulp.PULP_CBC_CMD(msg=0,timeLimit=200,gapRel=0.0002))
    return pulp.value(pr.objective)/NTOT*100, pulp.LpStatus[pr.status]

ps=[9,11,13,15,17,19,21]
rows=[]
for p in ps:
    t0=time.time(); mc,st=milp(p); rows.append((p,gcurve[p],mc,mc-gcurve[p],st,time.time()-t0))
    print(f"p={p:2d}  greedy={gcurve[p]:7.3f}  MILP={mc:7.3f}  gap={mc-gcurve[p]:.3f}pp  {st} {time.time()-t0:.0f}s")

ntree=cKDTree(named); named_cov=sum(1 for p in dem if ntree.query_ball_point(p,R))/NTOT*100
print(f"named-21 on this grid: {named_cov:.3f}%")
maxgap=max(r[3] for r in rows)
print(f"MAX greedy-MILP gap across p: {maxgap:.3f} pp ; at p=21 gap={rows[-1][3]:.3f} pp")
np.save("curve_rows.npy",np.array([(r[0],r[1],r[2]) for r in rows]))
json.dump({"gcurve":gcurve,"rows":[list(r[:4]) for r in rows],"named":named_cov},open(HERE / "curve.json", "w"))
