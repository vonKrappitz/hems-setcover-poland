import json, numpy as np, geopandas as gpd, pyproj, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
from shapely.ops import unary_union
from shapely import contains_xy
from scipy.spatial import cKDTree
import pulp

T_BUDGET,T_STARTUP,V=30,5,250
R=((T_BUDGET-T_STARTUP)/60.0)*V*1000.0   # 104 km

# --- land ---
pol=gpd.read_file(str(HERE / "geo" / "gadm41_POL_2.json")).to_crs("EPSG:2180")
land=unary_union(pol.geometry).buffer(0)
minx,miny,maxx,maxy=land.bounds
tr=pyproj.Transformer.from_crs("EPSG:4326","EPSG:2180",always_xy=True)
def xy(la,lo): return tr.transform(lo,la)

# --- named solution (model coords) ---
d=json.load(open(HERE / "loc28.json")); f=lambda s:float(str(s).replace(',','.'))
CRL=[(r[1],f(r[8]),f(r[9])) for r in d if r[0]=="CRL"]                       # 7 fixed
CT =[(r[1],f(r[8]),f(r[9])) for r in d if r[0]=="CT" and "Rzeszów" not in r[1]]  # 14 primary
assert len(CRL)==7 and len(CT)==14, (len(CRL),len(CT))
named=[xy(la,lo) for _,la,lo in CRL+CT]

# --- demand grid (6 km centroids in land) ---
D=6000
xs=np.arange(minx,maxx,D); ys=np.arange(miny,maxy,D)
gx,gy=np.meshgrid(xs,ys); P=np.column_stack([gx.ravel(),gy.ravel()])
dem=P[contains_xy(land,P[:,0],P[:,1])]
# --- candidate grid (18 km in land) + 7 CRL forced ---
C=18000
xs2=np.arange(minx,maxx,C); ys2=np.arange(miny,maxy,C)
gx2,gy2=np.meshgrid(xs2,ys2); Q=np.column_stack([gx2.ravel(),gy2.ravel()])
cand=Q[contains_xy(land,Q[:,0],Q[:,1])]
crl_xy=np.array([xy(la,lo) for _,la,lo in CRL])
cand=np.vstack([crl_xy,cand])           # first 7 are the fixed CRL
n_fixed=7
print(f"demand={len(dem)}  candidates={len(cand)} (fixed CRL={n_fixed})  R={R/1000:.0f} km")

# --- coverage neighbours (candidate within R of demand) ---
tree=cKDTree(cand)
neigh=tree.query_ball_point(dem,R)      # for each demand: list of candidate idx
P_TOT=21

def cover_of(open_idx):
    s=set()
    for j in open_idx: pass
    op=set(open_idx)
    c=0
    for nb in neigh:
        if op.intersection(nb): c+=1
    return c/len(dem)*100

# --- GREEDY (7 CRL fixed, add to 21) on same candidate set ---
t0=time.time()
open_set=set(range(n_fixed))
covered=np.array([bool(set(nb)&open_set) for nb in neigh])
# precompute candidate->demand incidence for speed
from collections import defaultdict
cand2dem=defaultdict(list)
for i,nb in enumerate(neigh):
    for j in nb: cand2dem[j].append(i)
while len(open_set)<P_TOT:
    best,bestgain=None,-1
    unc=~covered
    for j in range(len(cand)):
        if j in open_set: continue
        g=unc[cand2dem[j]].sum() if cand2dem[j] else 0
        if g>bestgain: bestgain,best=g,j
    open_set.add(best)
    idx=cand2dem[best]
    covered[idx]=True
greedy_cov=covered.sum()/len(dem)*100
t_greedy=time.time()-t0

# --- MILP: MCLP, x continuous in [0,1], y binary, 7 fixed, <=21 open ---
t0=time.time()
prob=pulp.LpProblem("MCLP",pulp.LpMaximize)
y={j:pulp.LpVariable(f"y{j}",cat="Binary") for j in range(len(cand))}
x={i:pulp.LpVariable(f"x{i}",lowBound=0,upBound=1) for i in range(len(dem))}
prob += pulp.lpSum(x.values())
for j in range(n_fixed): prob += y[j]==1
prob += pulp.lpSum(y.values())<=P_TOT
for i,nb in enumerate(neigh):
    if nb: prob += x[i] <= pulp.lpSum(y[j] for j in nb)
    else:  prob += x[i] <= 0
prob.solve(pulp.PULP_CBC_CMD(msg=0,timeLimit=400,gapRel=0.0005))
milp_cov=pulp.value(prob.objective)/len(dem)*100
status=pulp.LpStatus[prob.status]
t_milp=time.time()-t0
# bound (best possible) if not proven optimal
try:    bound=prob.solverModel.getBestPossibleObjValue()/len(dem)*100
except Exception: bound=None

# --- named-21 coverage on same demand grid (sanity) ---
ntree=cKDTree(np.array(named))
ncov=sum(1 for p in dem if ntree.query_ball_point(p,R)) # any named base within R
named_cov=ncov/len(dem)*100

print(f"GREEDY (21): {greedy_cov:.3f}%  [{t_greedy:.1f}s]")
print(f"MILP   (21): {milp_cov:.3f}%  status={status} [{t_milp:.1f}s]  bound={bound}")
print(f"named 21   : {named_cov:.3f}%  (manuscript coords on this grid)")
gap = milp_cov-greedy_cov
print(f"greedy gap vs MILP: {gap:.3f} pp ; greedy/MILP = {greedy_cov/milp_cov*100:.3f}%")
