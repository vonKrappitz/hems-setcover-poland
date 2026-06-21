import json, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"]="Liberation Sans"; plt.rcParams["pdf.fonttype"]=42; plt.rcParams["ps.fonttype"]=42
c=json.load(open("curve.json"))
g={int(k):v for k,v in c["gcurve"].items()}
gx=sorted(g); gy=[g[k] for k in gx]
mp=[r[0] for r in c["rows"]]; mv=[r[2] for r in c["rows"]]
C_G="#0072B2"; C_M="#D55E00"
fig,ax=plt.subplots(figsize=(7.2,4.6))
ax.plot(mp,mv,"--o",color=C_M,lw=1.8,ms=6,mfc="white",mec=C_M,mew=1.6,label="MILP global optimum (MCLP)",zorder=5)
ax.plot(gx,gy,"-s",color=C_G,lw=1.8,ms=4.5,label="Greedy heuristic",zorder=6)
ax.axhline(95,ls=":",color="#666666",lw=1.2)
ax.text(9.1,95.4,"95% threshold (H1)",fontsize=8.5,color="#444444")
ax.axvline(21,ls="-",color="#BBBBBB",lw=0.9,zorder=1)
ax.annotate("operating point\n21 primary bases",xy=(21,99.808),xytext=(17.4,90.5),
            fontsize=8.5,color="#222222",ha="center",
            arrowprops=dict(arrowstyle="->",color="#888888",lw=1))
ax.set_xlabel("Number of bases (7 Regional Centres pre-seeded, fixed)",fontsize=10)
ax.set_ylabel("Surface coverage within 30 min (%)",fontsize=10)
ax.set_xlim(8.4,21.8); ax.set_ylim(74,101.5)
ax.set_xticks(range(9,22,2))
ax.grid(True,axis="y",ls="-",lw=0.4,color="#E6E6E6",zorder=0)
ax.tick_params(labelsize=9)
for s in ["top","right"]: ax.spines[s].set_visible(False)
ax.legend(loc="lower right",fontsize=9,framealpha=1,edgecolor="#999999")
pdf="/mnt/user-data/outputs/Figure2_optimality_gap_EN.pdf"
png="/mnt/user-data/outputs/Figure2_optimality_gap_EN.png"
plt.tight_layout(); plt.savefig(pdf,bbox_inches="tight"); plt.savefig(png,dpi=300,bbox_inches="tight"); plt.close()
import os
print("Figure2:",round(os.path.getsize(pdf)/1024,1),"kB PDF |",round(os.path.getsize(png)/1024,1),"kB PNG")
