import numpy as np
from scipy.stats import lognorm
rng = np.random.default_rng(7)
M = 600

# 3 categorias con medianas distintas, misma dispersion interna
cat_med = {"C1":1.5, "C2":4.0, "C3":10.0}
cat_sig = 0.5
labels = rng.choice(list(cat_med), M)
real = np.array([rng.lognormal(np.log(cat_med[c]), cat_sig) for c in labels])

def crps_sample(muestras, x):
    n=len(muestras)//2
    A,B = muestras[:n], muestras[n:2*n]
    return np.abs(A-x).mean() - 0.5*np.abs(A-B).mean()

# Pronosticador 1: condiciona en la categoria (sabe la clase de referencia)
# Pronosticador 2: "climatologico" = usa la distribucion global de TODAS las tareas
pool = np.array([rng.lognormal(np.log(cat_med[c]), cat_sig)
                 for c in rng.choice(list(cat_med), 200000)])

res={}
# cobertura
cov_cond={}; cov_clim={}
for p in (0.5,0.8,0.95):
    q_cond=np.array([lognorm.ppf(p, cat_sig, scale=cat_med[c]) for c in labels])
    q_clim=np.quantile(pool, p)
    cov_cond[p]=(real<=q_cond).mean(); cov_clim[p]=(real<=q_clim).mean()

anch_cond=np.mean([lognorm.ppf(.95,cat_sig,scale=cat_med[c])-lognorm.ppf(.5,cat_sig,scale=cat_med[c]) for c in labels])
anch_clim=np.quantile(pool,.95)-np.quantile(pool,.5)

crps_cond=np.mean([crps_sample(rng.lognormal(np.log(cat_med[c]),cat_sig,8000), x) for c,x in zip(labels[:150],real[:150])])
crps_clim=np.mean([crps_sample(rng.choice(pool,8000), x) for x in real[:150]])

print(f"{'modelo':34s} {'P50':>7s} {'P80':>7s} {'P95':>7s} {'ancho P50-P95':>14s} {'CRPS':>7s}")
print(f"{'Condicionado en la categoria':34s} {cov_cond[.5]:6.1%} {cov_cond[.8]:6.1%} {cov_cond[.95]:6.1%} {anch_cond:13.1f}d {crps_cond:6.2f}")
print(f"{'Climatologico (todo junto)':34s} {cov_clim[.5]:6.1%} {cov_clim[.8]:6.1%} {cov_clim[.95]:6.1%} {anch_clim:13.1f}d {crps_clim:6.2f}")

print("\nPIT (10 bins, esperado 10.0% c/u)")
pit_cond=np.array([lognorm.cdf(x,cat_sig,scale=cat_med[c]) for c,x in zip(labels,real)])
pit_clim=np.array([(pool<=x).mean() for x in real])
for nm,pit in (("Condicionado",pit_cond),("Climatologico",pit_clim)):
    h,_=np.histogram(pit,bins=10,range=(0,1))
    print(f"{nm:16s} " + " ".join(f"{100*x/M:4.1f}" for x in h))
