"""
Figure 1 (Part I / Socio-Economic Planning Sciences): publication-style network map.
White background, country + voivodeship outlines, 30-minute coverage as light shading,
CRL stars / primary CT circles / supporting locations in grey by shape, side symbol key,
NO title or statistics panel on the figure (these go to the caption), Liberation Sans
(Arial-equivalent) embedded, vector PDF + PNG. Colourblind-safe.
"""
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.ops import unary_union
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import pyproj

plt.rcParams["font.family"] = "Liberation Sans"
plt.rcParams["pdf.fonttype"] = 42
plt.rcParams["ps.fonttype"] = 42

T_BUDGET, T_STARTUP, V_KMH = 30, 5, 250
RADIUS_M = ((T_BUDGET - T_STARTUP) / 60.0) * V_KMH * 1000  # 104 km

C_CRL = "black"; C_CT = "#0072B2"; C_SUP = "#6E6E6E"; C_COV = "#0072B2"

HUBS = [("Warsaw",52.2297,21.0122),("Kraków",50.0647,19.9450),("Wrocław",51.1079,17.0385),
        ("Gdańsk",54.3520,18.6466),("Lublin",51.2465,22.5684),("Poznań",52.4064,16.9252),
        ("Olsztyn",53.7784,20.4801)]
CT = [("Mirosławiec",53.3963,16.0833),("Białystok",53.0942,23.1700),("Sanok",49.5917,22.2106),
      ("Łask",51.5519,19.1789),("Zielona Góra",52.1356,15.7986),("Toruń",53.0451,18.5556),
      ("Ełk",53.8636,22.1681),("Gliwice",50.2378,18.6722),("Stargard",53.308,14.973),
      ("Lubomierz",51.296,15.367),("Zamość",50.7142,23.1986),("Bytów",54.1719,17.4978),
      ("Kielce",50.8979,20.7167),("Biała Podlaska",52.0344,23.1469)]
SUP = [("Rzeszów",50.1100,22.0190,"s"),("Drawsko",53.4730,15.7640,"D"),
       ("Suwałki",54.078,22.890,"v"),("Płock-Łąck",52.519,19.626,"v"),
       ("Polska Nowa Wieś",50.674,17.797,"v"),("Sokołów Podlaski",52.408,22.245,"v"),
       ("Krępa Słupska",54.467,17.075,"P"),("Zakopane (TOPR)",49.299,19.949,"^")]

LBL = {  # label offsets in points; 3rd item "right" => right-aligned (label sits to the left)
 "Warsaw":(15,2),"Kraków":(15,-3),"Wrocław":(11,-11),"Gdańsk":(14,-7),
 "Lublin":(13,-2),"Poznań":(13,-2),"Olsztyn":(12,7),"Mirosławiec":(10,7),
 "Białystok":(-11,2,"right"),"Sanok":(-9,2,"right"),"Łask":(13,-7),"Zielona Góra":(11,-8),
 "Toruń":(15,1),"Ełk":(-9,5,"right"),"Gliwice":(-11,8,"right"),"Stargard":(0,-13,"center"),
 "Lubomierz":(11,-6),"Zamość":(-9,2,"right"),"Bytów":(11,-8),
 "Kielce":(13,-8),"Biała Podlaska":(-11,2,"right")}

poland = gpd.read_file("/home/claude/geo/gadm41_POL_2.json").to_crs("EPSG:2180")
voiv = (poland.dissolve(by="NAME_1") if "NAME_1" in poland.columns else poland).reset_index(drop=True)
land = unary_union(voiv.geometry).buffer(0)
def drop_holes(g):
    if g.geom_type=="Polygon": return Polygon(g.exterior)
    if g.geom_type=="MultiPolygon": return MultiPolygon([Polygon(p.exterior) for p in g.geoms])
    return g
country = drop_holes(land)
minx,miny,maxx,maxy = country.bounds
tr = pyproj.Transformer.from_crs("EPSG:4326","EPSG:2180",always_xy=True)
def xy(lat,lon): return tr.transform(lon,lat)

# coverage: union of 21 primary base circles, clipped to land
primary = HUBS + CT
covers = [Point(*xy(la,lo)).buffer(RADIUS_M) for _,la,lo in primary]
cover_union = unary_union(covers).intersection(land)

# surface coverage % on a 1 km grid (reported in caption)
xs = np.arange(minx,maxx,1000); ys=np.arange(miny,maxy,1000)
gx,gy = np.meshgrid(xs,ys)
from shapely import contains_xy
pts = np.column_stack([gx.ravel(),gy.ravel()])
mask = contains_xy(land,pts[:,0],pts[:,1]); grid=pts[mask]
covered = np.zeros(len(grid),dtype=bool)
for _,la,lo in primary:
    bx,by = xy(la,lo); d=np.hypot(grid[:,0]-bx,grid[:,1]-by); covered|=(d<=RADIUS_M)
pct = covered.sum()/len(grid)*100

fig = plt.figure(figsize=(10,7))
ax = fig.add_axes([0.01,0.02,0.72,0.96]); ax.set_facecolor("white")
ax_leg = fig.add_axes([0.74,0.05,0.25,0.9]); ax_leg.axis("off")

try:
    voiv.geometry.apply(drop_holes).simplify(250).boundary.plot(ax=ax,color="#CBCBCB",linewidth=0.5,zorder=2)
except Exception: pass
gpd.GeoSeries([country.boundary]).plot(ax=ax,color="black",linewidth=1.1,zorder=4)
# coverage shading
gpd.GeoSeries([cover_union]).plot(ax=ax,facecolor=C_COV,edgecolor=C_COV,linewidth=0.4,alpha=0.16,zorder=3)

# supporting (grey, by shape), with labels for verification
SUP_LBL = {
 "Rzeszów":(10,2),"Drawsko":(-6,9,"right"),"Suwałki":(-9,-7,"right"),
 "Płock-Łąck":(-9,5,"right"),"Polska Nowa Wieś":(9,-7),"Sokołów Podlaski":(0,11,"center"),
 "Krępa Słupska":(0,-10,"center"),"Zakopane (TOPR)":(0,28,"center")}
for name,la,lo,mk in SUP:
    bx,by=xy(la,lo)
    if mk=="s":
        ax.scatter(bx,by,s=100,marker="s",facecolors="none",edgecolors=C_SUP,linewidths=1.5,zorder=8)
    else:
        ax.scatter(bx,by,s=95,marker=mk,c=C_SUP,edgecolors="white",linewidths=0.8,zorder=8)
    o=SUP_LBL.get(name,(9,5)); ha=o[2] if len(o)>2 else "left"
    ax.annotate(name,(bx,by),xytext=(o[0],o[1]),textcoords="offset points",
                fontsize=7.4,ha=ha,va="center",color=C_SUP,zorder=13)
# primary CT (blue circles)
for name,la,lo in CT:
    bx,by=xy(la,lo)
    ax.scatter(bx,by,s=150,marker="o",c=C_CT,edgecolors="white",linewidths=1.1,zorder=10)
# CRL (black stars)
for name,la,lo in HUBS:
    bx,by=xy(la,lo)
    ax.scatter(bx,by,s=430,marker="*",c=C_CRL,edgecolors="white",linewidths=1.2,zorder=12)
# labels for the 21 primary
for name,la,lo in primary:
    bx,by=xy(la,lo); o=LBL.get(name,(10,6)); ha=o[2] if len(o)>2 else "left"
    ax.annotate(name,(bx,by),xytext=(o[0],o[1]),textcoords="offset points",
                fontsize=8.3,ha=ha,va="center",color="black",zorder=14)

ax.set_xlim(minx-25000,maxx+25000); ax.set_ylim(miny-25000,maxy+25000)
ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
for s in ax.spines.values(): s.set_visible(False)

handles=[
 Line2D([0],[0],marker="*",color="w",markerfacecolor=C_CRL,markeredgecolor="white",markersize=17,lw=0,label="Regional Centre (CRL), 7"),
 Line2D([0],[0],marker="o",color="w",markerfacecolor=C_CT,markeredgecolor="white",markersize=11,lw=0,label="Primary Transfer Centre (CT), 14"),
 Line2D([0],[0],marker="s",color="w",markerfacecolor="none",markeredgecolor=C_SUP,markersize=11,lw=0,markeredgewidth=1.4,label="Transport base (CT-LST)"),
 Line2D([0],[0],marker="D",color="w",markerfacecolor=C_SUP,markeredgecolor="white",markersize=9,lw=0,label="Training and integration centre"),
 Line2D([0],[0],marker="v",color="w",markerfacecolor=C_SUP,markeredgecolor="white",markersize=10,lw=0,label="Support base (4)"),
 Line2D([0],[0],marker="P",color="w",markerfacecolor=C_SUP,markeredgecolor="white",markersize=11,lw=0,label="Seasonal base"),
 Line2D([0],[0],marker="^",color="w",markerfacecolor="#444444",markeredgecolor="white",markersize=11,lw=0,label="External partner"),
 Line2D([0],[0],marker="s",color="w",markerfacecolor=C_COV,markeredgecolor=C_COV,markersize=13,lw=0,alpha=0.35,label="30-minute coverage (104 km)"),
]
leg = ax_leg.legend(handles=handles,loc="center left",fontsize=8.6,framealpha=1.0,
                    facecolor="white",edgecolor="#888888",borderpad=0.8,labelspacing=0.9,
                    handletextpad=0.6,title="Location type",title_fontsize=9.6)
leg.get_title().set_fontweight("bold")

# --- automated collision check: labels vs base markers and national border ---
from shapely.geometry import Point as _P
import math as _m
fig.canvas.draw(); _r=fig.canvas.get_renderer(); _inv=ax.transData.inverted()
_dpi=fig.dpi
def _rpx(s): return (_m.sqrt(s)/2.0)*(_dpi/72.0)
_pts=[]   # (name, px, py, radius_px)
for nm,la,lo in HUBS: dx,dy=ax.transData.transform(xy(la,lo)); _pts.append((nm,dx,dy,_rpx(430)))
for nm,la,lo in CT:   dx,dy=ax.transData.transform(xy(la,lo)); _pts.append((nm,dx,dy,_rpx(150)))
for nm,la,lo,_mk in SUP: dx,dy=ax.transData.transform(xy(la,lo)); _pts.append((nm,dx,dy,_rpx(100)))
_iss=[]
for t in ax.texts:
    lbl=t.get_text(); bb=t.get_window_extent(renderer=_r)
    for nm,px,py,r in _pts:
        if nm==lbl: continue
        ddx=max(bb.x0-px,0,px-bb.x1); ddy=max(bb.y0-py,0,py-bb.y1)
        if _m.hypot(ddx,ddy) <= r+1.5:
            _iss.append(f"napis '{lbl}' nachodzi na baze '{nm}'")
    for cx,cy in [(bb.x0,bb.y0),(bb.x1,bb.y0),(bb.x0,bb.y1),(bb.x1,bb.y1),((bb.x0+bb.x1)/2,(bb.y0+bb.y1)/2)]:
        gx_,gy_=_inv.transform((cx,cy))
        if not country.buffer(500).contains(_P(gx_,gy_)):
            _iss.append(f"napis '{lbl}' wychodzi poza granice panstwa"); break
# label vs label
_tx=[(t.get_text(),t.get_window_extent(renderer=_r)) for t in ax.texts if not t.get_text().strip().isdigit() and len(t.get_text())<=60]
for _i in range(len(_tx)):
    for _j in range(_i+1,len(_tx)):
        a=_tx[_i][1]; b=_tx[_j][1]
        if a.x0<b.x1 and b.x0<a.x1 and a.y0<b.y1 and b.y0<a.y1:
            _iss.append(f"napisy '{_tx[_i][0]}' i '{_tx[_j][0]}' nachodza na siebie")
print("KOLIZJE:", "brak" if not _iss else "WYKRYTE")
for i in sorted(set(_iss)): print("  -",i)

pdf="/mnt/user-data/outputs/Figure1_HEMS_network_EN.pdf"
png="/mnt/user-data/outputs/Figure1_HEMS_network_EN.png"
plt.savefig(pdf,bbox_inches="tight",facecolor="white")
plt.savefig(png,dpi=300,bbox_inches="tight",facecolor="white")
plt.close()
import os
print(f"surface coverage (21 primary): {pct:.3f}%")
print("PDF kB:",round(os.path.getsize(pdf)/1024,1),"| PNG MB:",round(os.path.getsize(png)/1024/1024,2))
