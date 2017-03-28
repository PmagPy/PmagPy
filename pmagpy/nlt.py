from __future__ import division
from __future__ import print_function
from builtins import range
from past.utils import old_div
import  math
from scipy import optimize

# some functions required by non-linear TRM programs
#
#
#####   these functions require additional modules
#
###  Functions for Tanh correction of TRM data
#
def funk(p, x, y):
    """
    Function misfit evaluation for best-fit tanh curve
    f(x[:]) = alpha*tanh(beta*x[:])
        alpha = params[0]
        beta = params[1]
    funk(params) = sqrt(sum((y[:] - f(x[:]))**2)/len(y[:]))
    Output is RMS misfit
      x=xx[0][:]
      y=xx[1][:]q
    """
    alpha=p[0]
    beta=p[1]
    dev=0
    for i in range(len(x)):
      dev=dev+((y[i]-(alpha*math.tanh(beta*x[i])))**2)
    rms=math.sqrt(old_div(dev,float(len(y))))
    return rms
#
def compare(a, b):
    """
     Compare items in 2 arrays. Returns sum(abs(a(i)-b(i)))
    """
    s=0
    for i in range(len(a)):
        s=s+abs(a[i]-b[i])
    return s
#
def TRM(f,a,b):
    """
     Calculate TRM using tanh relationship
      TRM(f)=a*math.tanh(b*f)
    """
    m = float(a) * math.tanh(float(b) * float(f))
    return float(m)
#

def TRMinv(m,a,b):
    WARN = True    # Warn, rather than stop if I encounter a NaN...
    """
     Calculate applied field from TRM using tanh relationship
     TRMinv(m)=(1/b)*atanh(m/a)
    """
    if float(a)==0:
        print('ERROR: TRMinv: a==0.')
        if not WARN : sys.exit()
    if float(b)==0:
        print('ERROR: TRMinv: b==0.')
        if not WARN : sys.exit()
    x = (old_div(float(m), float(a)))
    if (1-x)<=0:
         print('ERROR:  TRMinv: (1-x)==0.')
         return -1
    if not WARN : sys.exit()
    f = (old_div(1.,float(b))) * 0.5 * math.log (old_div((1+x), (1-x)))
    return float(f)

def NRM(f,a,b,best):
    WARN = True    # Warn, rather than stop if I encounter a NaN...
    """ 
    Calculate NRM expected lab field and estimated ancient field
    NRM(blab,best)= (best/blab)*TRM(blab)
    """
    if float(f)==0:
        print('ERROR: NRM: f==0.')
    if not WARN : sys.exit()
    m = (old_div(float(best),float(f))) * TRM(f,a,b)
    return float(m)
#
def NLtrm(Bs,TRMs,best,blab,jackknife):
#    """
#    compute the tanh correction for non-linear TRM acquisition data, from Selkin et al. 2007
#    """   
# define some parameters
    FTOL = 1E-3    # Tolerance for difference in minimization routines
    MAXITER = 1E9    # Max number of iterations for fmin
    WARN = True    # Warn, rather than stop if I encounter a NaN...
    NLpars={}
#
    xi=[0,0]  # arguments for simplex
    Tmax,Bmax=0,0
    for i in range(len(TRMs)):
        if TRMs[i]>Tmax:Tmax=TRMs[i]    
        if Bs[i]>Bmax:Bmax=Bs[i]    
    xi[0]=2.0*Tmax # maximum TRM
    xi[1]=old_div(1.0,Bmax) # maximum field
# Minimize tanh function using simplex
    xopt = optimize.fmin(funk, xi, args=(Bs, TRMs),xtol=FTOL,ftol=FTOL,maxiter=MAXITER)
    xopt2= optimize.fmin(funk, xopt, args=(Bs, TRMs),xtol=FTOL,ftol=FTOL,maxiter=MAXITER)
    if (compare(xopt, xopt2) > FTOL) :     # Second run of fmin produced different parameters
        if WARN : print('WARNING: Fmin did not converge second time')
        print(xopt,xopt2,FTOL)
    try:
        n=NRM(blab,xopt2[0],xopt2[1],best)
        banc=TRMinv(n,xopt2[0],xopt2[1])
        if banc==-1:banc=-best
        bmin=-1
        bmax=-1
        rms=0
        for ix in range(len(Bs)):
            rms = rms + (TRMs[ix]-(xopt2[0]*math.tanh(xopt2[1]*Bs[ix]))**2)
        rms=math.sqrt(old_div(rms,len(Bs)))
    except ValueError:
# If no fittanh data are available, return -Best
        rms=-1
        banc,bmin,bmax=-float(best)
    NLpars['banc_npred']=TRM(banc,xopt2[0],xopt2[1])
    NLpars['best_npred']=TRM(best,xopt2[0],xopt2[1])
    NLpars['best']=best
    NLpars['blab']=blab
    NLpars['banc']=banc
    NLpars['bmin']=bmin
    NLpars['bmax']=bmax
    NLpars['xopt']=xopt2
    return  NLpars
