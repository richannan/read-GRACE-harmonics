#!/usr/bin/env python
u"""
clenshaw_summation.py
Written by Tyler Sutterley (07/2020)
Calculates the spatial field for a series of spherical harmonics for a
    sequence of ungridded points

CALLING SEQUENCE:
    spatial = clenshaw_summation(clm, slm, lon, lat, UNITS=1,
        LMAX=60, LOVE=(hl,kl,ll))

INPUTS:
    clm: cosine spherical harmonic coefficients
    slm: sine spherical harmonic coefficients
    lon: longitude of points
    lat: latitude of points

OPTIONS:
    RAD: Gaussian smoothing radius (km)
    UNITS: output data units
        1: cm of water thickness
        2: mm of geoid height
        3: mm of elastic crustal deformation [Davis 2004]
        4: microGal gravitational perturbation
        5: Pa, equivalent surface pressure in Pascals
        6: cm of viscoelastic rustal uplift (GIA) [See Wahr 1995 or Wahr 2000]
    LMAX: Upper bound of Spherical Harmonic Degrees
    LOVE: input load Love numbers up to degree LMAX (hl,kl,ll)

OUTPUTS:
    spatial: spatial field for lon/lat

PYTHON DEPENDENCIES:
    numpy: Scientific Computing Tools For Python (https://numpy.org)

PROGRAM DEPENDENCIES:
    gauss_weights.py: Computes the Gaussian weights as a function of degree
    units.py: class for converting spherical harmonic data to specific units

REFERENCE:
    Holmes and Featherstone, "A Unified Approach to the Clenshaw Summation and
        the Recursive Computation of Very High Degree and Order Normalised
        Associated Legendre Functions", Journal of Geodesy (2002)
        http://dx.doi.org/10.1007/s00190-002-0216-2
    Tscherning and Poder, "Some Geodetic Applications of Clenshaw Summation",
        Bollettino di Geodesia e Scienze (1982)

UPDATE HISTORY:
    Updated 07/2020: added function docstrings
    Updated 04/2020: reading load love numbers outside of this function
        using the units class for converting normalized spherical harmonics
    Updated 03/2018: added option for output in pascals (UNITS=5)
        simplified love number extrapolation if LMAX is greater than 696
    Written 08/2017
"""
import numpy as np
from gravity_toolkit.gauss_weights import gauss_weights
from gravity_toolkit.units import units

def clenshaw_summation(clm, slm, lon, lat, RAD=0, UNITS=0, LMAX=0, LOVE=None):
    """
    Calculates the spatial field for a series of spherical harmonics for a
    sequence of ungridded points

    Arguments
    ---------
    clm: cosine spherical harmonic coefficients
    slm: sine spherical harmonic coefficients
    lon: longitude of points
    lat: latitude of points

    Keyword arguments
    -----------------
    RAD: Gaussian smoothing radius (km)
    UNITS: output data units
        1: cm of water thickness
        2: mm of geoid height
        3: mm of elastic crustal deformation
        4: microGal gravitational perturbation
        5: Pa, equivalent surface pressure in Pascals
        6: cm of viscoelastic rustal uplift (GIA)
    LMAX: Upper bound of Spherical Harmonic Degrees
    LOVE: input load Love numbers up to degree LMAX (hl,kl,ll)

    Returns
    -------
    spatial: calculated spatial field for latitude and longitude
    """

    #-- check if lat and lon are the same size
    if (len(lat) != len(lon)):
        raise ValueError('Incompatable vector dimensions (lon, lat)')

    #-- calculate colatitude and longitude in radians
    th = (90.0 - lat)*np.pi/180.0
    phi = np.squeeze(lon*np.pi/180.0)
    #-- calculate cos and sin of colatitudes
    t = np.cos(th)
    u = np.sin(th)

    #-- dimensions of theta and phi
    npts = len(th)

    #-- Gaussian Smoothing
    if (RAD != 0):
        wl = 2.0*np.pi*gauss_weights(RAD,LMAX)
    else:
        #-- else = 1
        wl = np.ones((LMAX+1))

    #-- Setting units factor for output
    #-- extract arrays of kl, hl, and ll Love Numbers
    factors = units(lmax=LMAX).harmonic(*LOVE)
    #-- dfactor computes the degree dependent coefficients
    if (UNITS == 0):
        #-- 0: keep original scale
        dfactor = factors.norm
    elif (UNITS == 1):
        #-- 1: cmH2O, centimeters water equivalent
        dfactor = factors.cmwe
    elif (UNITS == 2):
        #-- 2: mmGH, mm geoid height
        dfactor = factors.mmGH
    elif (UNITS == 3):
        #-- 3: mmCU, mm elastic crustal deformation
        dfactor = factors.mmCU
    elif (UNITS == 4):
        #-- 4: micGal, microGal gravity perturbations
        dfactor = factors.microGal
    elif (UNITS == 5):
        #-- 5: Pa, equivalent surface pressure in Pascals
        dfactor = factors.Pa
    elif (UNITS == 6):
        #-- 6: cmVCU, cm viscoelastic  crustal uplift (GIA ONLY)
        dfactor = factors.cmVCU
    else:
        raise ValueError(('UNITS is invalid:\n1: cmH2O\n2: mmGH\n3: mmCU '
            '(elastic)\n4:microGal\n5: Pa\n6: cmVCU (viscoelastic)'))

    #-- calculate arrays for clenshaw summations over colatitudes
    s_m_c = np.zeros((npts,LMAX*2+2))
    for m in range(LMAX, -1, -1):
        #-- convolve harmonics with unit factors and smoothing
        s_m_c[:,2*m:2*m+2] = clenshaw_s_m(t, dfactor*wl, m, clm, slm, LMAX)

    #-- calculate cos(phi)
    cos_phi_2 = 2.0*np.cos(phi)
    #-- matrix of cos/sin m*phi summation
    cos_m_phi = np.zeros((npts,LMAX+2),dtype=np.float128)
    sin_m_phi = np.zeros((npts,LMAX+2),dtype=np.float128)
    #-- initialize matrix with values at lmax+1 and lmax
    cos_m_phi[:,LMAX+1] = np.cos(np.float128(LMAX + 1)*phi)
    sin_m_phi[:,LMAX+1] = np.sin(np.float128(LMAX + 1)*phi)
    cos_m_phi[:,LMAX] = np.cos(np.float128(LMAX)*phi)
    sin_m_phi[:,LMAX] = np.sin(np.float128(LMAX)*phi)
    #-- calculate summation for order LMAX
    s_m = s_m_c[:,2*LMAX]*cos_m_phi[:,LMAX] + s_m_c[:,2*LMAX+1]*sin_m_phi[:,LMAX]
    #-- iterate to calculate complete summation
    for m in range(LMAX-1, 0, -1):
        cos_m_phi[:,m] = cos_phi_2*cos_m_phi[:,m+1] - cos_m_phi[:,m+2]
        sin_m_phi[:,m] = cos_phi_2*sin_m_phi[:,m+1] - sin_m_phi[:,m+2]
        #-- calculate summation for order m
        a_m = np.sqrt((2.0*m+3.0)/(2.0*m+2.0))
        s_m = a_m*u*s_m + s_m_c[:,2*m]*cos_m_phi[:,m] + s_m_c[:,2*m+1]*sin_m_phi[:,m]
    #-- calculate spatial field
    spatial = np.sqrt(3.0)*u*s_m + s_m_c[:,0]
    #-- return the calculated spatial field
    return spatial

#-- PURPOSE: compute conditioned arrays for Clenshaw summation from the
#-- fully-normalized associated Legendre's function for an order m
def clenshaw_s_m(t, c, m, clm1, slm1, lmax):
    """
    Compute conditioned arrays for Clenshaw summation from the fully-normalized
    associated Legendre's function for an order m

    Arguments
    ---------
    t: elements ranging from -1 to 1, typically cos(th)
    c: degree dependent factors
    m: spherical harmonic order
    clm1: cosine spherical harmonics
    slm1: sine spherical harmonics
    lmax: maximum spherical harmonic degree

    Returns
    -------
    s_m_c: conditioned array for clenshaw summation
    """
    #-- allocate for output matrix
    N = len(t)
    s_m = np.zeros((N,2),dtype=np.float128)
    #-- scaling factor to prevent overflow
    scalef = 1.0e-280
    clm = scalef*clm1.astype(np.float128)
    slm = scalef*slm1.astype(np.float128)
    #-- convert lmax and m to float
    lm = np.float128(lmax)
    mm = np.float128(m)
    if (m == lmax):
        s_m[:,0] = c[lmax]*clm[lmax,lmax]
        s_m[:,1] = c[lmax]*slm[lmax,lmax]
    elif (m == (lmax-1)):
        a_lm = t*np.sqrt(((2.0*lm-1.0)*(2.0*lm+1.0))/((lm-mm)*(lm+mm)))
        s_m[:,0] = a_lm*c[lmax]*clm[lmax,lmax-1] + c[lmax-1]*clm[lmax-1,lmax-1]
        s_m[:,1] = a_lm*c[lmax]*slm[lmax,lmax-1] + c[lmax-1]*slm[lmax-1,lmax-1]
    elif ((m <= (lmax-2)) and (m >= 1)):
        s_mm_c_pre_2 = c[lmax]*clm[lmax,m]
        s_mm_s_pre_2 = c[lmax]*slm[lmax,m]
        a_lm = np.sqrt(((2.0*lm-1.0)*(2.0*lm+1.0))/((lm-mm)*(lm+mm)))*t
        s_mm_c_pre_1 = a_lm*s_mm_c_pre_2 + c[lmax-1]*clm[lmax-1,m]
        s_mm_s_pre_1 = a_lm*s_mm_s_pre_2 + c[lmax-1]*slm[lmax-1,m]
        for l in range(lmax-2, m-1, -1):
            ll = np.float128(l)
            a_lm=np.sqrt(((2.0*ll+1.0)*(2.0*ll+3.0))/((ll+1.0-mm)*(ll+1.0+mm)))*t
            b_lm=np.sqrt(((2.*ll+5.)*(ll+mm+1.)*(ll-mm+1.))/((ll+2.-mm)*(ll+2.+mm)*(2.*ll+1.)))
            s_mm_c = a_lm * s_mm_c_pre_1 - b_lm * s_mm_c_pre_2 + c[l]*clm[l,m]
            s_mm_s = a_lm * s_mm_s_pre_1 - b_lm * s_mm_s_pre_2 + c[l]*slm[l,m]
            s_mm_c_pre_2 = np.copy(s_mm_c_pre_1)
            s_mm_s_pre_2 = np.copy(s_mm_s_pre_1)
            s_mm_c_pre_1 = np.copy(s_mm_c)
            s_mm_s_pre_1 = np.copy(s_mm_s)
        s_m[:,0] = np.copy(s_mm_c)
        s_m[:,1] = np.copy(s_mm_s)
    elif (m == 0):
        s_mm_c_pre_2 = c[lmax]*clm[lmax,0]
        a_lm = np.sqrt(((2.0*lm-1.0)*(2.0*lm+1.0))/(lm*lm))*t
        s_mm_c_pre_1 = a_lm * s_mm_c_pre_2 + c[lmax-1]*clm[lmax-1,0]
        for l in range(lmax-2, m-1, -1):
            ll = np.float128(l)
            a_lm=np.sqrt(((2.0*ll+1.0)*(2.0*ll+3.0))/((ll+1)*(ll+1)))*t
            b_lm=np.sqrt(((2.*ll+5.)*(ll+1.)*(ll+1.))/((ll+2)*(ll+2)*(2.*ll+1.)))
            s_mm_c = a_lm * s_mm_c_pre_1 - b_lm * s_mm_c_pre_2 + c[l]*clm[l,0]
            s_mm_c_pre_2 = np.copy(s_mm_c_pre_1)
            s_mm_c_pre_1 = np.copy(s_mm_c)
        s_m[:,0] = np.copy(s_mm_c)
    #-- return s_m rescaled with scalef
    return s_m/scalef
