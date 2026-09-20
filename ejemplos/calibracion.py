import numpy as np
rng = np.random.default_rng(11)
M = 300   # tareas historicas

# Verdad: duracion lognormal, mediana 4 dias, sigma 0.7
mu, sig = np.log(4.0), 0.7
real = rng.lognormal(mu, sig, M)

from scipy.stats import lognorm, norm
def quantile(med, s, p): return lognorm.ppf(p, s, scale=med)
def cdf(med, s, x):      return lognorm.cdf(x, s, scale=med)

# Tres pronosticadores, todos con la mediana CORRECTA (4 dias):
fores = {
 "Honesto (sigma=0.70)":      (4.0, 0.70),
 "Exceso de confianza (0.35)":(4.0, 0.35),
 "Vago (sigma=1.30)":         (4.0, 1.30),
}

def crps_lognorm(med, s, x, n=200000):
    # CRPS por muestreo: E|X-x| - 0.5*E|X-X'|
    X  = rng.lognormal(np.log(med), s, n)
    Xp = rng.lognormal(np.log(med), s, n)
    return np.abs(X - x).mean() - 0.5*np.abs(X - Xp).mean()

print(f"{'modelo':30s} {'cob.P50':>8s} {'cob.P80':>8s} {'cob.P95':>8s} {'ancho P50-P95':>14s} {'CRPS':>7s}")
for name,(med,s) in fores.items():
    cov = {p: (real <= quantile(med,s,p)).mean() for p in (0.5,0.8,0.95)}
    ancho = quantile(med,s,0.95) - quantile(med,s,0.50)
    crps = np.mean([crps_lognorm(med,s,x,20000) for x in real[:120]])
    print(f"{name:30s} {cov[0.5]:7.1%} {cov[0.8]:7.1%} {cov[0.95]:7.1%} {ancho:13.1f}d {crps:6.2f}")

print("\nHistograma PIT (10 bins, % esperado por bin = 10.0%)")
for name,(med,s) in fores.items():
    pit = cdf(med, s, real)
    h,_ = np.histogram(pit, bins=10, range=(0,1))
    print(f"{name:30s} " + " ".join(f"{100*x/M:4.1f}" for x in h))

# baseline "climatologico": la distribucion historica global, sin condicionar en nada
print("\n--- por que la cobertura sola no alcanza ---")
print("El 'Honesto' y un modelo que usara la MISMA distribucion para toda tarea")
print("estan ambos calibrados si las tareas son homogeneas; los separa la sharpness.")
