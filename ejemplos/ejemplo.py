import numpy as np
rng = np.random.default_rng(20260906)
N = 20000

# ---------- PARTE A: un proyecto, 12 capabilities, 2 tracks ----------
# Categorias inventadas, medianas en dias habiles, sigma en escala log
cats = {"C1-S":(1.0,0.45),"C2-S":(3.5,0.55),"C3-S":(5.0,0.65),"C4-S":(8.0,0.75)}
# (nombre, categoria, depende_de)
caps = [("A","C1-S",[]),("B","C1-S",[]),("C","C2-S",["A"]),("D","C2-S",["A"]),
        ("E","C3-S",["B"]),("F","C2-S",["C"]),("G","C4-S",["E"]),("H","C1-S",["D"]),
        ("I","C3-S",["F","H"]),("J","C2-S",["G"]),("K","C1-S",["I"]),("L","C4-S",["I","J"])]
names=[c[0] for c in caps]; idx={n:i for i,n in enumerate(names)}

def sample_durations():
    d = np.zeros((N,len(caps)))
    for i,(n,c,_) in enumerate(caps):
        med,sig = cats[c]
        d[:,i] = rng.lognormal(np.log(med), sig, N)
    return d

def schedule(dur, W):
    """list scheduling con W tracks; devuelve fecha de fin por trial"""
    n=len(caps); finish=np.zeros((N,n)); out=np.zeros(N)
    for t in range(N):
        done={}; free=np.zeros(W); pend=list(range(n))
        while pend:
            ready=[i for i in pend if all(idx[p] in done for p in caps[i][2])]
            ready.sort(key=lambda i:-dur[t,i])
            k=int(np.argmin(free)); i=ready[0]
            start=max(free[k], max([done[idx[p]] for p in caps[i][2]], default=0.0))
            end=start+dur[t,i]; done[i]=end; free[k]=end; pend.remove(i)
        out[t]=max(done.values())
    return out

dur = sample_durations()
for W in (1,2,3,4):
    T = schedule(dur, W)
    print(f"W={W}  P50={np.percentile(T,50):5.1f}  P80={np.percentile(T,80):5.1f}  P95={np.percentile(T,95):5.1f}  min={T.min():4.1f}")

# piso: tracks ilimitados = camino critico
T_inf = schedule(dur, len(caps))
print(f"W=inf P50={np.percentile(T_inf,50):5.1f}  P80={np.percentile(T_inf,80):5.1f}  P95={np.percentile(T_inf,95):5.1f}")
T2 = schedule(dur,2)
print(f"\nP(<=55 dias) con W=2: {(T2<=55).mean():.1%}   con W=3: {(schedule(dur,3)<=55).mean():.1%}")
