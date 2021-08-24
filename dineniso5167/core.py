import numpy as np

from .utils import _warningtext

# specific gas constant
Rs = 287.058  # J/kg/K
Rd = 461.523  # J/kg/K
# others:
T0_Kelvin = 273.15  # K
#mu_air = 17.24 * 10 ** (-6)  # [Pa*s]

def compute_mu_air(T):
    """from https://fluids.readthedocs.io/fluids.atmosphere.html"""
    mu_air = 1.458e-6*T**1.5/(T+110.4)
    return mu_air

def compute_density(p, T, phi=0, pv=0):
    """
    Calculates desnity acoording to ideal gas law.

    Parameters
    ----------
    p : `float or array_like`
        air pressure [Pa]
    T : `float or array_like`
        air temperature [K]
    phi : `float or array_like`, optional=0
        relative humidity phi
    pv : `float or array_like`, optional=0
        vapour pressure pv

    Returns
    -------
    rho : `float or array_like`
        Density

    """
    Rf = Rs / (1 - phi * pv / p * (1 - Rs / Rd))
    rho = p / (Rf * T)
    return rho


def Cel2Kel(T):
    """
    Converts degree celsius to kelvin
    :param T: temperature in deg cel
    :return: temperature in kelvin
    """
    return T + T0_Kelvin


def Kel2Cel(T):
    """
    Converts kelvin to degree celsius
    :param T: temperature in kelvin
    :return: temperature in deg cel
    """
    return T - T0_Kelvin


def compute_reynolds_number(u, d, nu):
    return u * d / nu


def check_beta(d, D, unit='mm', mounting_type='flange'):
    """
    verifies whether the diameter ratio beta is within the required bounds
    Note: For flange mounted orifices only!
    Note: ReD >= 5000 and ReD >= 170 beta**2*D is not checked!
    Note: Diamteres must be given in millimeters if not set
    differently using `unit` parameter!

    Parameters
    ----------
    d : `float`
        Inner diameter if the orifice in [mm]
    D : `float`
        Inner diameter of the pipe in [mm]
    unit : `str`, optional='mm
        Unit of diameters. Default is millimeters
    mounting_type : `str`, optional='flange'
        How the orifice is mounted. Currently only flange
        is implemented!

    Returns
    -------
    beta : `float`
        value for beta
    check : `bool`
        verification result
    """
    beta = d / D

    if unit == 'm':
        d *= 1000
        D *= 1000
    if mounting_type != 'flange':
        raise NotImplementedError('Only mounting type "flange" is implemented in this version!')

    if d <= 12.5:
        print(_warningtext(f'Inner orifice diameter ({d} mm) is smaller than 12.5 mm!'))
        return beta, False
    if D < 50 or D > 1000:
        print(_warningtext(f'Inner pipe diameter ({d} mm) is outside of the valid range of [50, 1000] mm!'))
        return beta, False

    if beta >= 0.10 and beta <= 0.75:
        return beta, True
    else:
        print(_warningtext(f'Value for beta ({beta}) is outside of the valid range [0.1, 0.75]!'))
        return beta, False


def compute_flow_coefficient(beta, D, Re):
    """
    Computes flow coefficient C according to equation (4)
    Note: Inner pipe diameter must be given in meters!

    Parameters
    ----------
    beta : `float`
        Diameter ratio
    D : `float`
        Inner diameter of the pipe in [m]
    Re : `float`
        Reynolds number

    Returns
    -------
    C : `float`
        Flow coefficient C
    uncertainty : `float`
        The uncertainty associated with C

    """
    L_1 = 25.4 / 1000 / D
    L_s2 = 25.4 / 1000 / D
    M_s2 = 2 * L_s2 / (1 - beta)
    A = (19000 * beta / Re) ** 0.8
    C = 0.5961 + 0.0261 * beta ** 2 - 0.216 * beta ** 8 + 0.000521 * (10 ** 6 * beta / Re) ** 0.7 + \
        (0.0188 + 0.0063 * A) * beta ** 3.5 * (10 ** 6 / Re) ** 0.3 + (0.043 + 0.080 * np.exp(-10 * L_1) -
                                                                       0.123 * np.exp(-7 * L_1)) * (1 - 0.11 * A) * (
                beta ** 4 / (1 - beta ** 4)) - 0.031 * (M_s2 - 0.8 * M_s2 ** 1.1) * beta ** 1.3

    if D < 0.7112:  # [m]
        C += 0.011 * (0.75 - beta) * (2.8 - D / 0.0254)   # note: in DIN it's 25.4 mm!

    # note: uncertainty assuming beta, D, ReD and Ra/D to be free of error
    if 0.1 <= beta < 0.2:
        uncertainty = (0.7 - beta) / 100
    elif 0.2 <= beta <= 0.6:
        uncertainty = 0.5 / 100
    elif 0.6 < beta <= 0.77:
        uncertainty = (1.667 * beta - 0.5) / 100
    else:
        uncertainty = 0
    if uncertainty > 0:
        if beta > 0.5 and np.mean(Re) < 10000:
            uncertainty += 0.5 / 100
    if D < 0.7112:
        uncertainty += 0.9 * (0.75 - beta) * (2.8 - D / 25.4) / 100
    return C, uncertainty


def _vfr(C_0, beta, d, eps, dp, rho):
    """
    Calculates volume flow rate according to DIN EN ISO 5167
    :param C_0:
    :param beta:
    :param d:
    :param eps:
    :param dp:
    :param rho:
    :return:
    """
    return C_0 / (np.sqrt(1 - beta ** 4)) * eps * np.pi / 4 * d ** 2 * np.sqrt(2 * dp / rho)  # [m^3/s]


def compute_expansion_number(beta, p1, p2, kappa):
    """computes expansion number epsilon and relative uncertainty according to equation (5)"""
    eps = 1 - (0.351 + 0.256 * beta ** 4 + 0.93 * beta ** 8) * (1 - (p2 / p1) ** (1 / kappa))
    dp = p2 - p1
    rel_uncertainty = 3.5 * dp / kappa / p1 / 100
    return eps, rel_uncertainty


def compute_volume_flow_rate(dp, d, D, length_unit, p1, T, phi=0,
                             kappa=1.4, Cguess=0.62, residuum=0.1,
                             verbose=False):
    """
    Computes the volume flow rate according to ISO 5167-2 Eq. (1)

    Parameters
    ----------
    dp : `array_like`
    d : `float`
        Diameter
    Cguess : `float`, optional=0.62
        Initial guess for flow coefficient

    Returns
    -------
    qv : `array_linke`
        Volume flow rate in [m3/s]
    """
    if length_unit == 'mm':
        d /= 1000
        D /= 1000
    beta, _ = check_beta(d, D, length_unit)
    A_D = D ** 2 / 4 * np.pi  # [m2]
    if T < 100:
        T = Cel2Kel(T)
    rho_air = compute_density(p=p1, T=T, phi=phi)  # p [Pa], T [K], phi [-]
    mu_air = compute_mu_air(T)
    nu_air = mu_air / rho_air  # [m**2/s]
    p2 = p1 + dp

    eps, eps_runcertainty = compute_expansion_number(beta, p1, p2, kappa)

    _str_count = 32
    if verbose:
        print(f' (i) > {"Inner diameter orifice d: ":>{_str_count}} {d} mm')
        print(f' (i) > {"Inner diameter pipe D: ":>{_str_count}} {D} mm')
        print(f' (c) > {"beta=d/D: ":>{_str_count}} {beta}')
        print(f' (i) > {"Temperature: ":>{_str_count}} {T} K')
        print(f' (i) > {"Pressure Difference: ":>{_str_count}} {dp} Pa')
        print(f' (i) > {"Absolute Pressure p1: ":>{_str_count}} {p1} Pa')
        print(f' (i) > {"Rel. humidity phi: ":>{_str_count}} {phi * 100} %')
        print(f' (i) > {"Density of air: ":>{_str_count}} {rho_air:5.2f} kg/m^3')
        print(f' (i) > {"viscosity of air nu: ":>{_str_count}} {nu_air:5.2e} m^2/s')
    eps_res = 10 ** (-4)
    j = 0
    while np.mean(residuum) > eps_res:
        vfr_value = _vfr(Cguess, beta, d, eps, dp, rho_air)  # [m^3/s]
        Re = compute_reynolds_number(vfr_value / A_D, D, nu_air)
        C, C_err = compute_flow_coefficient(beta, D, Re)
        vfr_value_max = _vfr(Cguess + C_err, beta, d, eps + eps_runcertainty, dp, rho_air)
        vfr_value_min = _vfr(Cguess - C_err, beta, d, eps - eps_runcertainty, dp, rho_air)
        residuum = abs(C - Cguess)
        Cguess = C
        j += 1
        if j > 999:
            print(_warningtext('maximum iterations reached/exiting while loop to calculate C'))
            break

    dp_loss = ((np.sqrt(1 - beta ** 4 * (1 - C ** 2)) - C * beta ** 2) / (
            np.sqrt(1 - beta ** 4 * (1 - C ** 2)) + C * beta ** 2) * dp)

    if verbose:
        print(f' (c) > {"flow velocity in pipe: ":>{_str_count}} {vfr_value / A_D:>3.2} m/s')
        print(f' (c) > {"flow coefficient C: ":>{_str_count}} {C:>3.2} (it took {j} iterations to converge)')
        print(f' (c) > {"Reynolds number Re: ":>{_str_count}} {Re:>1.1e}')
        print('------')
        print(f' (c) > {"volume flow rate qv: ":>{_str_count}} {vfr_value:>7.4f} m^3/s '
              f'({vfr_value * 3600:.1f} m^3/h)')
        print(f' (c) > {"mass flow rate qm: ":>{_str_count}} {vfr_value * rho_air:>7.4f} kg/s '
              f' ({vfr_value * rho_air * 3600:.1f} kg/h)')
        print(f' (c) > {"Pressure loss of orifice: ":>{_str_count}} {dp_loss:>3.1f} Pa')


    return vfr_value, vfr_value_min, vfr_value_max, dp_loss
