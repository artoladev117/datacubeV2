#!/usr/bin/env python
# -*- coding: utf8 -*-
import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt
from matplotlib import rc, rcParams
import scipy.optimize

##Functions definition

def gaussian(param):
	(v0,I0,sig) = param
	func = I0*prt/sig*np.exp(-0.5*((vel_array-v0)/float(sig))**2)
	return func

def chi2(param):
	(v0,I0,sig) = param
	return np.sum(((gaussian(param)-obs_spec)/cerr)**2)/float(ncont-3)


print ("Setting constants & co")
########################################################################
# Define some constants used throughout the code
########################################################################
light = 2.99792458e5
prt = 1./np.sqrt(2.*np.pi)
obsfile = "../../data/paws-pdbi+30m-12co10-1as-cube.fits"
refpix = (501,506)

########################################################################
# Now reads the data
########################################################################
print ("Now reading the files...")
hdu_data = fits.open(obsfile)
obs = hdu_data[0].data
obs_head = hdu_data[0].header

nx = obs_head["NAXIS1"]
ny = obs_head["NAXIS2"]
nv = obs_head["NAXIS3"]
Dv = obs_head["CDELT3"]
vmin = obs_head["CRVAL3"]			#velocity is in m/s
pref = obs_head["CRPIX3"]
res_nu = obs_head["RESTFREQ"]
refv = np.abs(obs_head["ALTRPIX"])
bmaj =  1.6155e-3
bmin =  1.5437e-3
beam = np.sqrt(bmaj*bmin)*60.*1.442   #in arcminutes plus the 1.442 factor to go from a circle to a gaussian
velocity = np.zeros(nv)
for x in range(nv):
	velocity[x] = vmin + float(x-pref+1)*Dv
# here the velocity is in m/s, hence:
velocity = velocity*1e-3 # 1e-3 Para transforma a de m/s a km/s

# here uses some keywords defined in the header to convert velocity to frequency
freq = res_nu/(1.+velocity/light)/1e9 # 1e9 tranforma de Hz a GHz
cube = obs[0,:,:,:]

nd = 10  #how many channels before and after the maximum to fit a gaussian?
## Here ask what pixel you want to fit
#xx = 450 #input("X pixel ")
#yy = 450 #input("Y pixel ")
resultados=np.zeros([4,ny,nx])

# Declarando variables necesarias

intentsity_guess=150
int_inf=0
int_sup=10000

sigma_guess=10
sig_inf=1
sig_sup=150


for _x in range(nx):
    for _y in range(ny):
    	
		# Here Units convwersion: from Jy/beam to K
		spec = cube[:,_y,_x] #*1e3/2.95*beam**(-2)*freq**(-2)

		# at which velocity (frequency) do we see a maximum in intensity?
		maxi = np.argmax(spec)
		vmax = velocity[maxi]
		
		vel_array = velocity[maxi-nd:maxi+nd]
		obs_spec = spec[maxi-nd:maxi+nd]
		ncont = len(vel_array)
		cont = np.concatenate((spec[maxi-2*nd:maxi-nd],spec[maxi+nd:maxi+2*nd]))
		cerr = np.std(cont)

		Iave= np.sum(spec[maxi-1:maxi+2])/3.

		if (Iave>(3.*cerr)):

			## Change this to what you think is reasonable
			velocity_guess=0
			
			x0 = [velocity_guess, intentsity_guess, sigma_guess]
			## Change this to what you think is reasonable

			vel_inf=-300
			vel_sup=vmax
			limits = [(vel_inf,vel_sup), (int_inf,int_sup), (sig_inf,sig_sup)]
			fit = scipy.optimize.minimize(chi2,x0,method='TNC',bounds=limits)

			resultados[0,_y,_x]=fit.fun
			resultados[1,_y,_x]=fit.x[0]
			resultados[2,_y,_x]=fit.x[1]
			resultados[3,_y,_x]=fit.x[2]

newheader = obs_head.copy()
newheader["NAXIS"]=3
newheader["NAXIS3"]=4
del newheader[37:]
del newheader[6:27]
newheader["PLANE00"]="chi2"
newheader["PLANE01"]="velocity"
newheader["PLANE02"]="IO"
newheader["PLANE03"]="sigma"
newHdu = fits.PrimaryHDU(resultados,header=newheader)
newHdu.writeto("resultadosfit_co.fits")

"""
print "Best chi2: ",fit.fun
print "Best velocity ",fit.x[0]
print "Best intensity ",fit.x[1]
print "Best sigma ",fit.x[2]
## Use this to find values for the x0 and limits variables
bfit = (velocity_guess, intentsity_guess, sigma_guess)
model_guess = gaussian(bfit)
model = gaussian(fit.x)

## Plotting Part

yma = max(spec)*1.2
ymi = min(spec)*1.2
xma = max(velocity)*1.01
xmi = min(velocity)*0.97
plt.figure(figsize=(15,10))
plt.plot(velocity,spec,linestyle='-',color='black')
plt.plot(vel_array,model,linestyle='-',color='blue')
plt.plot(vel_array,model_guess,linestyle='-',color='green')
plt.xlabel(r'Velocity  [km s$^{-1}$]',fontsize=20)
plt.ylabel(r'T  [K]',fontsize=20)
plt.tick_params(labelsize=20)
tstring = 'Pixel coordinates: x=' + str(_x)+' y='+str(_y)
plt.title(tstring)
plt.xlim(xmi,xma)
plt.ylim(ymi,yma)
fig = plt.gcf()
plt.show()
"""