from pmagpy import ipmag
import numpy as np

# NOAA IGRF14 reference values calculated with the magnetic field calculator at
# https://www.ngdc.noaa.gov/geomag/calculators/magcalc.shtml
# on Feb 28, 2026. All test cases at sea level (elevation=0 km).
#
# PmagPy returns [dec, inc, intensity] where dec is 0-360.
# NOAA returns dec as -180 to 180. References below use NOAA convention.
#
# PmagPy agrees with NOAA to within:
#   Dec: ~0.05 deg, Inc: ~0.05 deg, F: ~30 nT
#
# ---- NOAA full-vector time series for 20N, 50E (1999-2029) ----
# Calculated using the IGRF model at the NOAA magnetic field calculator.
# JSON output from NOAA (model: IGRF14, labeled IGRF2025 by NOAA):
#
# Year  Dec       Inc       F (nT)    X (nT)    Y (nT)    Z (nT)
# 1999  1.23546   28.27279  40435.6   35603.5   767.8     19153.1
# 2000  1.21319   28.39540  40484.5   35605.7   754.0     19252.5
# 2001  1.23764   28.46666  40516.3   35609.4   769.3     19312.0
# 2002  1.26207   28.53780  40548.2   35613.1   784.6     19371.4
# 2003  1.28650   28.60882  40580.2   35616.8   799.9     19430.9
# 2004  1.31093   28.67972  40612.2   35620.4   815.1     19490.3
# 2005  1.33535   28.75051  40644.3   35624.1   830.4     19549.8
# 2006  1.38107   28.82664  40679.0   35627.8   858.9     19613.8
# 2007  1.42677   28.90262  40713.8   35631.5   887.5     19677.9
# 2008  1.47247   28.97846  40748.7   35635.2   916.0     19741.9
# 2009  1.51815   29.05415  40783.6   35639.0   944.5     19806.0
# 2010  1.56382   29.12969  40818.7   35642.7   973.1     19870.0
# 2011  1.60626   29.19409  40853.6   35650.1   999.7     19927.1
# 2012  1.64867   29.25837  40888.6   35657.5   1026.3    19984.2
# 2013  1.69107   29.32252  40923.7   35664.8   1052.9    20041.3
# 2014  1.73345   29.38656  40958.8   35672.2   1079.6    20098.4
# 2015  1.77581   29.45046  40994.0   35679.6   1106.2    20155.5
# 2016  1.81181   29.52712  41041.5   35693.3   1129.1    20226.7
# 2017  1.84778   29.60358  41089.1   35706.9   1151.9    20297.8
# 2018  1.88372   29.67986  41136.7   35720.5   1174.8    20369.0
# 2019  1.91963   29.75595  41184.5   35734.1   1197.7    20440.1
# 2020  1.95552   29.83186  41232.3   35747.8   1220.6    20511.3
# 2021  1.95879   29.86807  41267.0   35764.8   1223.2    20551.2
# 2022  1.96206   29.90422  41301.8   35781.9   1225.8    20591.1
# 2023  1.96533   29.94031  41336.5   35798.9   1228.4    20630.9
# 2024  1.96860   29.97634  41371.2   35815.9   1231.1    20670.8
# 2025  1.97186   30.01231  41406.0   35833.0   1233.7    20710.7
# 2026  1.96326   30.03099  41433.7   35850.4   1228.9    20736.2
# 2027  1.95467   30.04964  41461.4   35867.7   1224.1    20761.8
# 2028  1.94609   30.06827  41489.0   35885.1   1219.3    20787.3
# 2029  1.93752   30.08687  41516.7   35902.5   1214.5    20812.8
#
# ---- NOAA full-vector time series for 20S, 50E (1999-2029) ----
# Calculated using the IGRF model at the NOAA magnetic field calculator.
# JSON output from NOAA (model: IGRF14, labeled IGRF2025 by NOAA):
#
# Year  Dec        Inc        F (nT)    X (nT)    Y (nT)    Z (nT)
# 1999  -16.78186  -53.60873  34245.9   19452.7   -5866.4   -27567.4
# 2000  -16.88500  -53.55552  34279.8   19485.8   -5914.7   -27575.8
# 2001  -16.94812  -53.53056  34357.9   19535.2   -5953.2   -27629.7
# 2002  -17.01087  -53.50568  34436.0   19584.6   -5991.7   -27683.7
# 2003  -17.07327  -53.48087  34514.2   19633.9   -6030.2   -27737.6
# 2004  -17.13531  -53.45615  34592.3   19683.3   -6068.7   -27791.5
# 2005  -17.19700  -53.43151  34670.5   19732.7   -6107.1   -27845.5
# 2006  -17.19417  -53.40787  34748.5   19788.4   -6123.3   -27899.6
# 2007  -17.19136  -53.38434  34826.5   19844.1   -6139.5   -27953.7
# 2008  -17.18857  -53.36091  34904.5   19899.7   -6155.7   -28007.8
# 2009  -17.18579  -53.33758  34982.6   19955.4   -6171.8   -28061.9
# 2010  -17.18303  -53.31436  35060.6   20011.1   -6188.0   -28116.0
# 2011  -17.19361  -53.28649  35139.3   20068.0   -6209.6   -28168.8
# 2012  -17.20414  -53.25875  35217.9   20124.8   -6231.3   -28221.7
# 2013  -17.21460  -53.23113  35296.6   20181.7   -6252.9   -28274.6
# 2014  -17.22501  -53.20363  35375.3   20238.5   -6274.5   -28327.5
# 2015  -17.23535  -53.17625  35454.0   20295.4   -6296.2   -28380.3
# 2016  -17.27565  -53.13180  35537.1   20359.6   -6331.8   -28430.3
# 2017  -17.31567  -53.08754  35620.3   20423.8   -6367.4   -28480.4
# 2018  -17.35543  -53.04348  35703.5   20488.0   -6403.0   -28530.4
# 2019  -17.39492  -52.99961  35786.7   20552.2   -6438.7   -28580.4
# 2020  -17.43414  -52.95593  35870.0   20616.4   -6474.3   -28630.4
# 2021  -17.50504  -52.95473  35963.8   20662.9   -6517.0   -28704.8
# 2022  -17.57557  -52.95350  36057.6   20709.3   -6559.7   -28779.3
# 2023  -17.64572  -52.95223  36151.5   20755.8   -6602.4   -28853.7
# 2024  -17.71551  -52.95093  36245.4   20802.2   -6645.0   -28928.1
# 2025  -17.78493  -52.94959  36339.3   20848.7   -6687.7   -29002.6
# 2026  -17.85959  -52.96805  36431.8   20884.1   -6729.1   -29083.5
# 2027  -17.93393  -52.98638  36524.4   20919.5   -6770.5   -29164.4
# 2028  -18.00795  -53.00457  36617.0   20954.9   -6811.9   -29245.4
# 2029  -18.08167  -53.02261  36709.6   20990.4   -6853.3   -29326.3
#
# ---- NOAA full-vector time series for 20N, 50W (1999-2029) ----
# Calculated using the IGRF model at the NOAA magnetic field calculator.
# JSON output from NOAA (model: IGRF14, labeled IGRF2025 by NOAA):
#
# Year  Dec        Inc       F (nT)    X (nT)    Y (nT)    Z (nT)
# 1999  -17.32139  39.93747  36990.9   27076.4   -8444.4   23746.4
# 2000  -17.34447  39.71003  36877.2   27079.2   -8457.3   23560.9
# 2001  -17.29494  39.50799  36786.3   27098.7   -8437.7   23402.9
# 2002  -17.24547  39.30493  36695.8   27118.2   -8418.1   23244.9
# 2003  -17.19603  39.10084  36605.9   27137.7   -8398.5   23086.9
# 2004  -17.14664  38.89573  36516.4   27157.2   -8378.8   22928.8
# 2005  -17.09730  38.68960  36427.4   27176.6   -8359.2   22770.8
# 2006  -17.03354  38.48101  36345.3   27203.5   -8334.4   22616.0
# 2007  -16.96987  38.27143  36263.7   27230.4   -8309.5   22461.3
# 2008  -16.90628  38.06089  36182.6   27257.4   -8284.7   22306.5
# 2009  -16.84277  37.84936  36102.0   27284.3   -8259.8   22151.7
# 2010  -16.77935  37.63686  36022.0   27311.2   -8235.0   21997.0
# 2011  -16.71370  37.39962  35943.0   27347.5   -8211.8   21830.7
# 2012  -16.64819  37.16131  35864.6   27383.8   -8188.5   21664.4
# 2013  -16.58280  36.92192  35786.9   27420.1   -8165.3   21498.2
# 2014  -16.51754  36.68146  35709.9   27456.4   -8142.1   21331.9
# 2015  -16.45241  36.43993  35633.6   27492.7   -8118.9   21165.6
# 2016  -16.37980  36.18846  35566.4   27539.9   -8094.9   20999.9
# 2017  -16.30739  35.93600  35499.9   27587.0   -8070.9   20834.2
# 2018  -16.23517  35.68256  35434.2   27634.1   -8046.8   20668.6
# 2019  -16.16314  35.42814  35369.2   27681.2   -8022.8   20502.9
# 2020  -16.09131  35.17274  35305.0   27728.3   -7998.8   20337.2
# 2021  -16.02008  34.90593  35234.5   27773.4   -7974.4   20162.3
# 2022  -15.94904  34.63801  35164.9   27818.5   -7950.1   19987.3
# 2023  -15.87817  34.36900  35096.0   27863.6   -7925.7   19812.4
# 2024  -15.80748  34.09890  35028.0   27908.7   -7901.3   19637.5
# 2025  -15.73697  33.82770  34960.8   27953.8   -7876.9   19462.6
# 2026  -15.66420  33.55606  34886.7   27992.9   -7849.6   19283.7
# 2027  -15.59159  33.28323  34813.4   28032.0   -7822.2   19104.9
# 2028  -15.51912  33.00922  34741.0   28071.1   -7794.9   18926.0
# 2029  -15.44681  32.73402  34669.4   28110.1   -7767.5   18747.1


# --- Epoch boundary tests (NOAA-verified) ---

def test_igrf_2000_arabian_sea():
    """2000, 20N, 50E — DGRF epoch boundary"""
    result = ipmag.igrf([2000, 0, 20, 50])
    # NOAA IGRF14: Dec=1.213, Inc=28.395, F=40484.5
    noaa_ref = np.array([1.213, 28.395, 40484.5])
    pmagpy_dec = result[0] if result[0] < 180 else result[0] - 360
    assert abs(pmagpy_dec - noaa_ref[0]) < 0.1
    assert abs(result[1] - noaa_ref[1]) < 0.1
    assert abs(result[2] - noaa_ref[2]) < 50


def test_igrf_2000_north_atlantic():
    """2000, 60N, 10W — high latitude, large declination, DGRF epoch"""
    result = ipmag.igrf([2000, 0, 60, -10])
    # NOAA IGRF14: Dec=-10.085, Inc=72.626, F=50651.7
    pmagpy_dec = result[0] if result[0] < 180 else result[0] - 360
    assert abs(pmagpy_dec - (-10.085)) < 0.1
    assert abs(result[1] - 72.626) < 0.1
    assert abs(result[2] - 50651.7) < 50


def test_igrf_2000_south_africa():
    """2000, 30S, 30E — southern hemisphere, DGRF epoch"""
    result = ipmag.igrf([2000, 0, -30, 30])
    # NOAA IGRF14: Dec=-22.516, Inc=-63.827, F=28089.7
    pmagpy_dec = result[0] if result[0] < 180 else result[0] - 360
    assert abs(pmagpy_dec - (-22.516)) < 0.1
    assert abs(result[1] - (-63.827)) < 0.1
    assert abs(result[2] - 28089.7) < 50


def test_igrf_2000_indian_ocean():
    """2000, 20S, 50E — southern hemisphere, DGRF epoch"""
    result = ipmag.igrf([2000, 0, -20, 50])
    # NOAA IGRF14: Dec=-16.885, Inc=-53.556, F=34279.8
    pmagpy_dec = result[0] if result[0] < 180 else result[0] - 360
    assert abs(pmagpy_dec - (-16.885)) < 0.1
    assert abs(result[1] - (-53.556)) < 0.1
    assert abs(result[2] - 34279.8) < 50


def test_igrf_2020_arabian_sea():
    """2020, 20N, 50E — DGRF epoch boundary (newly definitive in IGRF14)"""
    result = ipmag.igrf([2020, 0, 20, 50])
    # NOAA IGRF14: Dec=1.956, Inc=29.832, F=41232.3
    pmagpy_dec = result[0] if result[0] < 180 else result[0] - 360
    assert abs(pmagpy_dec - 1.956) < 0.1
    assert abs(result[1] - 29.832) < 0.1
    assert abs(result[2] - 41232.3) < 50


def test_igrf_2025_arabian_sea():
    """2025, 20N, 50E — current IGRF epoch boundary"""
    result = ipmag.igrf([2025, 0, 20, 50])
    # NOAA IGRF14: Dec=1.972, Inc=30.012, F=41406.0
    pmagpy_dec = result[0] if result[0] < 180 else result[0] - 360
    assert abs(pmagpy_dec - 1.972) < 0.1
    assert abs(result[1] - 30.012) < 0.1
    assert abs(result[2] - 41406.0) < 50


def test_igrf_2025_indian_ocean():
    """2025, 20S, 50E — current IGRF epoch boundary, southern hemisphere"""
    result = ipmag.igrf([2025, 0, -20, 50])
    # NOAA IGRF14: Dec=-17.785, Inc=-52.950, F=36339.3
    pmagpy_dec = result[0] if result[0] < 180 else result[0] - 360
    assert abs(pmagpy_dec - (-17.785)) < 0.1
    assert abs(result[1] - (-52.950)) < 0.1
    assert abs(result[2] - 36339.3) < 50


# --- Between-epoch tests (NOAA-verified) ---

def test_igrf_1999_arabian_sea():
    """1999, 20N, 50E — between DGRF epochs (1995-2000)"""
    result = ipmag.igrf([1999, 0, 20, 50])
    # NOAA IGRF14: Dec=1.235, Inc=28.273, F=40435.6
    pmagpy_dec = result[0] if result[0] < 180 else result[0] - 360
    assert abs(pmagpy_dec - 1.235) < 0.1
    assert abs(result[1] - 28.273) < 0.1
    assert abs(result[2] - 40435.6) < 50


def test_igrf_2007_indian_ocean():
    """2007, 20S, 50E — between DGRF epochs (2005-2010), southern hemisphere"""
    result = ipmag.igrf([2007, 0, -20, 50])
    # NOAA IGRF14: Dec=-17.191, Inc=-53.384, F=34826.5
    pmagpy_dec = result[0] if result[0] < 180 else result[0] - 360
    assert abs(pmagpy_dec - (-17.191)) < 0.1
    assert abs(result[1] - (-53.384)) < 0.1
    assert abs(result[2] - 34826.5) < 50


def test_igrf_2012_western_atlantic():
    """2012, 20N, 50W — between DGRF epochs (2010-2015)"""
    result = ipmag.igrf([2012, 0, 20, -50])
    # NOAA IGRF14: Dec=-16.648, Inc=37.161, F=35864.6
    pmagpy_dec = result[0] if result[0] < 180 else result[0] - 360
    assert abs(pmagpy_dec - (-16.648)) < 0.1
    assert abs(result[1] - 37.161) < 0.1
    assert abs(result[2] - 35864.6) < 50


def test_igrf_2017_arabian_sea():
    """2017, 20N, 50E — between DGRF epochs (2015-2020)"""
    result = ipmag.igrf([2017, 0, 20, 50])
    # NOAA IGRF14: Dec=1.848, Inc=29.604, F=41089.1
    pmagpy_dec = result[0] if result[0] < 180 else result[0] - 360
    assert abs(pmagpy_dec - 1.848) < 0.1
    assert abs(result[1] - 29.604) < 0.1
    assert abs(result[2] - 41089.1) < 50


def test_igrf_2022_arabian_sea():
    """2022, 20N, 50E — between DGRF epochs (2020-2025)"""
    result = ipmag.igrf([2022, 0, 20, 50])
    # NOAA IGRF14: Dec=1.962, Inc=29.904, F=41301.8
    pmagpy_dec = result[0] if result[0] < 180 else result[0] - 360
    assert abs(pmagpy_dec - 1.962) < 0.1
    assert abs(result[1] - 29.904) < 0.1
    assert abs(result[2] - 41301.8) < 50


def test_igrf_2027_indian_ocean():
    """2027, 20S, 50E — SV extrapolation (2025-2030), southern hemisphere"""
    result = ipmag.igrf([2027, 0, -20, 50])
    # NOAA IGRF14: Dec=-17.934, Inc=-52.986, F=36524.4
    pmagpy_dec = result[0] if result[0] < 180 else result[0] - 360
    assert abs(pmagpy_dec - (-17.934)) < 0.1
    assert abs(result[1] - (-52.986)) < 0.1
    assert abs(result[2] - 36524.4) < 50


def test_igrf_2027_western_atlantic():
    """2027.5, 20N, 50W — SV extrapolation (2025-2030)"""
    result = ipmag.igrf([2027.5, 0, 20, -50])
    # NOAA IGRF14 (interpolated from 2027 and 2028 yearly values):
    # Dec=-15.555, Inc=33.146, F=34777.2
    pmagpy_dec = result[0] if result[0] < 180 else result[0] - 360
    assert abs(pmagpy_dec - (-15.555)) < 0.1
    assert abs(result[1] - 33.146) < 0.1
    assert abs(result[2] - 34777.2) < 50
