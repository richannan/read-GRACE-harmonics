#!/usr/bin/env python
u"""
plm_colombo.py
Written by Tyler Sutterley (07/2020)

Computes fully-normalized associated Legendre Polynomials
    for a vector of x values (can also be singular)
Uses the Colombo (1981) recursion relation
    Listed in the Geoid Cookbook and Holmes-Featherstone (2002)
    as the most popular recursive algorithm used for computing
    fully-normalized Legendre Polynomials in Geodesy
This is a Standard forward column method

CALLING SEQUENCE:
    plm,dplm = plm_colombo(LMAX, np.cos(theta))

INPUTS:
    LMAX: Upper bound of Spherical Harmonic Degrees
    x: elements ranging from -1 to 1
        typically cos(theta), where theta is the colatitude in radians

OUTPUT:
    plms: Legendre polynomials of x (geodesy normalization)
    dplms: first differentials of Legendre polynomials of x

OPTIONS:

PYTHON DEPENDENCIES:
    numpy: Scientific Computing Tools For Python (https://numpy.org)

REFERENCES:
    Geoid Cookbook: http://mitgcm.org/~mlosch/geoidcookbook.pdf

UPDATE HISTORY:
    Updated 07/2020: added function docstrings
    Updated 07/2017: output first differential of legendre polynomials
    Updated 09/2013: new format for file headers
    Written 03/2013
"""
import numpy as np

def plm_colombo(LMAX, x, ASTYPE=np.float):
    """
    Computes fully-normalized associated Legendre Polynomials and
    their first derivative using a Standard forward column method

    Arguments
    ---------
    LMAX: Upper bound of Spherical Harmonic Degrees
    x: elements ranging from -1 to 1

    Keyword arguments
    -----------------
    ASTYPE: output variable data type

    Returns
    -------
    plms: fully-normalized Legendre polynomials
    dplms: first differentials of Legendre polynomials
    """

    #-- Verify LMAX as integer
    LMAX = np.int(LMAX)

    if (np.ndim(x) > 0):
        #-- length of the x array
        jm = np.shape(x)[0]
    else:
        jm = 1

    #-- allocating for the plm matrix and differentials
    plm = np.zeros((LMAX+1,LMAX+1,jm))
    dplm = np.zeros((LMAX+1,LMAX+1,jm))
    #-- removing singleton dimensions of x
    x = np.squeeze(x)
    u = np.sqrt(1.0 - x**2)#-- for x=cos(th): u=sin(th)

    #-- Calculating the initial polynomials for the recursion
    plm[0,0,:] = 1.0
    plm[1,0,:] = np.sqrt(3.0)*x
    plm[1,1,:] = np.sqrt(3.0)*u
    #-- calculating first derivatives for harmonics of degree 1
    dplm[1,0,:] = (1.0/u)*(x*plm[1,0,:] - np.sqrt(3)*plm[0,0,:])
    dplm[1,1,:] = (x/u)*plm[1,1,:]
    for l in range(2, LMAX+1):
        for m in range(0, l):#-- Zonal and Tesseral harmonics (non-sectorial)
            #-- Computes the non-sectorial terms from previously computed
            #-- sectorial terms.
            alm = np.sqrt(((2.0*l-1.0)*(2.0*l+1.0))/((l-m)*(l+m)))
            blm = np.sqrt(((2.0*l+1.0)*(l+m-1.0)*(l-m-1.0))/((l-m)*(l+m)*(2.0*l-3.0)))
            #-- if (m == l-1): plm[l-2,m,:] will be 0
            plm[l,m,:] = alm*x*plm[l-1,m,:] - blm*plm[l-2,m,:]
            #-- calculate first derivatives
            flm = np.sqrt(((l**2.0 - m**2.0)*(2.0*l + 1.0))/(2.0*l - 1.0))
            dplm[l,m,:] = (1.0/u)*(l*x*plm[l,m,:] - flm*plm[l-1,m,:])

        #-- Sectorial harmonics
        #-- The sectorial harmonics serve as seed values for the recursion
        #-- starting with P00 and P11 (outside the loop)
        plm[l,l,:] = u*np.sqrt((2.0*l+1.0)/(2.0*l))*np.squeeze(plm[l-1,l-1,:])
        #-- calculate first derivatives for sectorial harmonics
        dplm[l,l,:] = np.float128(l)*(x/u)*plm[l,l,:]

    #-- return the legendre polynomials and their first derivative
    return plm,dplm
