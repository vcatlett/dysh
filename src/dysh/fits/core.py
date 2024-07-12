"""
Core functions for FITS/SDFITS
"""

import numpy as np
from astropy.io.fits.column import _convert_format


def default_sdfits_columns():
    """The default column names for GBT SDFITS.

    Returns
    -------
        colnames : list
        A list of the GBT SDFITS column names
    """
    colnames = [
        "OBJECT",
        "BANDWID",
        "DATE-OBS",
        "DURATION",
        "EXPOSURE",
        "TSYS",
        "TDIM7",
        "TUNIT7",
        "CTYPE1",
        "CRVAL1",
        "CRPIX1",
        "CDELT1",
        "CTYPE2",
        "CRVAL2",
        "CTYPE3",
        "CRVAL3",
        "CRVAL4",
        "OBSERVER",
        "OBSID",
        "SCAN",
        "OBSMODE",
        "FRONTEND",
        "TCAL",
        "VELDEF",
        "VFRAME",
        "RVSYS",
        "OBSFREQ",
        "LST",
        "AZIMUTH",
        "ELEVATIO",
        "TAMBIENT",
        "PRESSURE",
        "HUMIDITY",
        "RESTFREQ",
        "DOPFREQ",
        "FREQRES",
        "EQUINOX",
        "RADESYS",
        "TRGTLONG",
        "TRGTLAT",
        "SAMPLER",
        "FEED",
        "SRFEED",
        "FEEDXOFF",
        "FEEDEOFF",
        "SUBREF_STATE",
        "SIDEBAND",
        "PROCSEQN",
        "PROCSIZE",
        "PROCSCAN",
        "PROCTYPE",
        "LASTON",
        "LASTOFF",
        "TIMESTAMP",
        "QD_XEL",
        "QD_EL",
        "QD_BAD",
        "QD_METHOD",
        "VELOCITY",
        "FOFFREF1",
        "ZEROCHAN",
        "ADCSAMPF",
        "VSPDELT",
        "VSPRVAL",
        "VSPRPIX",
        "SIG",
        "CAL",
        "CALTYPE",
        "TWARM",
        "TCOLD",
        "CALPOSITION",
        "BACKEND",
        "PROJID",
        "TELESCOP",
        "SITELONG",
        "SITELAT",
        "SITEELEV",
        "IFNUM",
        "PLNUM",
        "FDNUM",
        "INT",
        "INTNUM",  # not all SDFITS files have INT, so we always create INTNUM
        "NSAVE",
        # The following are added by the GBTFITSLoad constructor.
        # Arguable whether they should be included or not.
        "HDU",
        "BINTABLE",
        "ROW",
        "PROC",
        "_OBSTYPE",
        "_SUBOBSMODE",
    ]
    return colnames


# def FITScol_format(key, meta):
#    a = np.array(meta[key].values)
#    if meta[key].dtype == np.dtype("O"):
# a = a.astype(str)
#       print(f"{key}={a[0]}, {a.dtype} {len(a[0])}A")
#       return f"{len(a[0])}A"
#   # if a.dtype == np.dtype("O"):
#    return "A"
# else:
#   return _convert_format(a.dtype, reverse=True)
