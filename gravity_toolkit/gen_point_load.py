#!/usr/bin/env python
u"""
gen_point_load.py
Written by Tyler Sutterley (07/2020)
Calculates gravitational spherical harmonic coefficients for point masses

CALLING SEQUENCE:
    Ylms = gen_point_load(data, lon, lat, LMAX=LMAX)

INPUTS:
    data: data magnitude
    lon: longitude of points
    lat: latitude of points

OUTPUTS:
    clm: cosine spherical harmonic coefficients (geodesy normalization)
    slm: sine spherical harmonic coefficients (geodesy normalization)
    l: spherical harmonic degree to LMAX
    m: spherical harmonic order to MMAX

OPTIONS:
    LMAX: Upper bound of Spherical Harmonic Degrees
    MMAX: Upper bound of Spherical Harmonic Orders
    UNITS: input data units
        1: grams of mass (default)
        2: gigatonnes of mass
    LOVE: input load Love numbers up to degree LMAX (hl,kl,ll)

PYTHON DEPENDENCIES:
    numpy: Scientific Computing Tools For Python (https://numpy.org)
    scipy: Scientific Tools for Python (https://docs.scipy.org/doc/)

PROGRAM DEPENDENCIES:
    legendre.py: Computes associated Legendre polynomials for degree l
    units.py: class for converting spherical harmonic data to specific units

UPDATE HISTORY:
    Updated 07/2020: added function docstrings
    Written 05/2020
"""
import numpy as np
from gravity_toolkit.legendre import legendre
from gravity_toolkit.units import units

def gen_point_load(data, lon, lat, LMAX=60, MMAX=None, UNITS=1, LOVE=None):
    """
    Calculates spherical harmonic coefficients for point masses

    Arguments
    ---------
    data: data magnitude
    lon: longitude of points
    lat: latitude of points

    Keyword arguments
    -----------------
    LMAX: Upper bound of Spherical Harmonic Degrees
    MMAX: Upper bound of Spherical Harmonic Orders
    UNITS: input data units
        1: grams of mass (default)
        2: gigatonnes of mass
    LOVE: input load Love numbers up to degree LMAX (hl,kl,ll)

    Returns
    -------
    clm: cosine spherical harmonic coefficients
    slm: sine spherical harmonic coefficients
    l: spherical harmonic degree to LMAX
    m: spherical harmonic order to MMAX
    """

    #-- upper bound of spherical harmonic orders (default == LMAX)
    if MMAX is None:
        MMAX = np.copy(LMAX)

    #-- number of input data points
    npts = len(data.flatten())
    #-- convert output longitude and latitude into radians
    phi = np.pi*lon.flatten()/180.0
    theta = np.pi*(90.0 - lat.flatten())/180.0

    #-- SH Degree dependent factors to convert into geodesy normalized SH's
    #-- use splat operator to extract arrays of kl, hl, and ll Love Numbers
    factors = units(lmax=LMAX).spatial(*LOVE)
    #-- Average Radius of the Earth [cm]
    rad_e = factors.rad_e
    #-- extract degree dependent factor for specific units
    int_fact = np.zeros((npts))
    if (UNITS == 1):
        #-- Default Parameter: Input in g
        dfactor = factors.cmwe/(factors.rad_e**2)
        int_fact[:] = 1.0
    elif (UNITS == 2):
        #-- Input in gigatonnes (Gt)
        dfactor = factors.cmwe/(factors.rad_e**2)
        int_fact[:] = 1e15
    #-- flattened form of data converted to units
    D = int_fact*data.flatten()

    #-- output harmonics
    Ylms = {}
    Ylms['clm'] = np.zeros((LMAX+1,MMAX+1))
    Ylms['slm'] = np.zeros((LMAX+1,MMAX+1))
    Ylms['l'] = np.arange(LMAX+1)
    Ylms['m'] = np.arange(MMAX+1)
    #-- for each degree l
    for l in range(LMAX+1):
        m1 = np.min([l,MMAX]) + 1
        SPH = spherical_harmonic_matrix(l,D,phi,theta,dfactor[l])
        #-- truncate to spherical harmonic order and save to output
        Ylms['clm'][l,:m1] = SPH.real[:m1]
        Ylms['slm'][l,:m1] = SPH.imag[:m1]
    #-- output harmonics
    return Ylms

#-- calculate spherical harmonics of degree l evaluated at (theta,phi)
def spherical_harmonic_matrix(l,data,phi,theta,coeff):
    """
    Calculates spherical harmonics of degree l evaluated at coordinates

    Arguments
    ---------
    l: spherical harmonic degree
    data: data magnitude in grams
    phi: longitude of points in radians
    theta: colatitude of points in radians
    coeff: degree-dependent factor for converting units

    Returns
    -------
    Ylms: spherical harmonic coefficients in Eulerian form
    """
    #-- calculate normalized legendre polynomials (points, order)
    Pl = legendre(l, np.cos(theta), NORMALIZE=True).T
    #-- spherical harmonic orders up to degree l
    m = np.arange(0,l+1)
    #-- calculate Euler's of spherical harmonic order multiplied by azimuth phi
    mphi = np.exp(1j*np.dot(np.squeeze(phi)[:,np.newaxis],m[np.newaxis,:]))
    #-- reshape data to order
    D = np.kron(np.ones((1,l+1)), data[:,np.newaxis])
    #-- calculate spherical harmonics and multiply by coefficients and data
    Ylms = coeff*D*Pl*mphi
    #-- calculate the sum over all points and return harmonics for degree l
    return np.sum(Ylms,axis=0)