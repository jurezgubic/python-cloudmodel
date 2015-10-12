import matplotlib.pyplot as plot
import matplotlib.gridspec as gridspec
import numpy as np

try:
    from tephigram_python.tephigram_plotter import Tephigram
except ImportError:
    Tephigram = None

import utils
from common import Var

def profile_plot(F, z, Te):
    r = F[:,Var.r]
    w = F[:,Var.w]
    T = F[:,Var.T]

    plot.figure(figsize=(16,6))
    plot.subplot(131)
    plot.plot(r, z, marker='x')
    plot.ylabel('height [m]')
    plot.xlabel('radius [m]')
    plot.grid(True)
    plot.xlim(0., None)
    plot.subplot(132)
    plot.plot(T, z, marker='x', label='in-cloud')
    plot.plot(Te(z), z, marker='x', label='environment')
    plot.legend()
    plot.xlabel('temperature [K]')
    plot.ylabel('height [m]')
    plot.grid(True)
    plot.subplot(133)
    plot.plot(w, z, marker='x')
    plot.ylabel('height [m]')
    plot.xlabel('vertical velocity [m/s]')
    plot.grid(True)

    return plot

def hydrometeor_profile_plot(F, z, Te, p_e):
    p = p_e
    r = F[:,Var.r]
    w = F[:,Var.w]
    T = F[:,Var.T]
    q_v = F[:,Var.q_v]
    q_l = F[:,Var.q_l]
    q_r = F[:,Var.q_r]

    T = [float(t_) for t_ in T]

    q_v__sat = utils.qv_sat(T=T, p=p)

    plot.figure(figsize=(16,6))
    plot.subplot(131)
    plot.plot(q_v, z, marker='x', label='in-cloud')
    plot.plot(q_v__sat, z, marker='x', label='saturation (in-cloud temp)')
    plot.ylabel('height [m]')
    plot.xlabel('water vapor specific concentration [kg/kg]')
    plot.legend()
    plot.grid(True)
    plot.subplot(132)
    plot.plot(q_l, z, marker='x', label='in-cloud')
    plot.ylabel('height [m]')
    plot.xlabel('liquid water specific concentration [kg/kg]')
    plot.grid(True)
    plot.subplot(133)
    plot.plot(q_r, z, marker='x', label='in-cloud')
    plot.ylabel('height [m]')
    plot.xlabel('rain water specific concentration [kg/kg]')
    plot.grid(True)


def plot_profiles(profiles, vars=['r', 'w', 'T', 'q_v', 'q_l', 'T__tephigram']):
    if len(vars) > 6:
        raise NotImplementedError

    n = len(vars)
    c = n > 3 and 3 or n
    r = n/c

    gs = gridspec.GridSpec(r, c)

    fig = plot.figure(figsize=(6*c,7*r))

    lines = []
    for n, (v, s) in enumerate(zip(vars, list(gs))):

        tephigram = None
        if v == 'T__tephigram':
            tephigram = Tephigram(fig=fig, subplotshape=(r, c, n+1))
            v = 'T'
        else:
            plot.subplot(s)

        try:
            i = Var.names.index(v)
        except ValueError:
            i = None

        ref_plot_func = None
        ref_lines = []

        scale_by_max = False
        d_max = 0.0

        for n_profile, profile in enumerate(profiles):
            if v == 'mse':
                profile_data = utils.Utils(profile.cloud_model.constants).moist_static_energy(profile.F, profile.z)/1.e3
                if n_profile == 0:
                    def ref_plot_func():
                        z = profile.z
                        Te = profile.cloud_model.environment.temp(z)
                        F_e = np.zeros((profile.F.shape))
                        F_e[...,Var.T] = Te
                        environment_mse = utils.Utils(profile.cloud_model.constants).moist_static_energy(F_e, profile.z)/1.e3
                        return plot.plot(environment_mse, z, marker='', label='environment')


            elif i == None:
                raise NotImplementedError("Variable not found")
            else:
                profile_data = profile.F[:,i]

            if tephigram is not None:
                z = profile.z
                p = profile.cloud_model.environment.p(z)
                T = profile.F[:,Var.T]
                kwargs = { 'P': p/100., 'T': T-273.15, 'marker': '.'}
                if len(lines) > 0:
                    kwargs['color'] = lines[n_profile].get_color()
                tephigram.plot_temp(**kwargs)

                def ref_plot_func():
                    Te = profile.cloud_model.environment.temp(z)
                    kwargs = { 'P': p/100., 'T': Te-273.15, 'marker': '.', 'color': 'black', 'label': 'environment'}
                    return tephigram.plot_temp(**kwargs)
                plot.title("Tephigram")

            else:
                profile_line = plot.plot(profile_data, profile.z, label=str(profile), marker='.', linestyle='',)
                plot.grid(True)

                if n == 0:
                    lines += profile_line

                if v == 'T':
                    plot.xlabel('temperature [K]')
                    plot.ylabel('height [m]')
                    ref_plot_func = lambda: plot.plot(profile.cloud_model.environment.temp(profile.z), profile.z, marker='', label='environment')
                elif v == 'r':
                    plot.ylabel('height [m]')
                    plot.xlabel('radius [m]')
                    plot.xlim(0., None)
                elif v == 'w':
                    plot.ylabel('height [m]')
                    plot.xlabel('vertical velocity [m/s]')
                elif v == 'q_v':
                    plot.ylabel('height [m]')
                    plot.xlabel('water vapor specific concentration [kg/kg]')
                    d_max = max(max(profile_data), d_max)
                    scale_by_max = True

                    T = profile.F[:,Var.T]
                    z = profile.z
                    p = profile.cloud_model.environment.p(z)
                    q_v__sat = utils.qv_sat(T=T, p=p)
                    color = lines[n_profile].get_color()
                    plot.plot(q_v__sat, z, marker='', color=color, label='')
                elif v == 'q_l':
                    plot.ylabel('height [m]')
                    plot.xlabel('liquid water specific concentration [kg/kg]')
                    d_max = max(max(profile_data), d_max)
                    scale_by_max = True
                elif v == 'q_r':
                    plot.ylabel('height [m]')
                    plot.xlabel('rain water specific concentration [kg/kg]')
                    d_max = max(max(profile_data), d_max)
                    scale_by_max = True
                elif v == 'mse':
                    plot.ylabel('height [m]')
                    plot.xlabel('Moist static energy [kJ]')
                    d_max = max(max(profile_data), d_max)
                else:
                    raise NotImplementedError

        if scale_by_max and d_max != 0.0:
            dx = 0.1*d_max
            plot.xlim(0.-dx,d_max+dx)

        if ref_plot_func is not None:
            ref_lines += ref_plot_func()

        if len(ref_lines) > 0:
            plot.legend(ref_lines, [l.get_label() for l in ref_lines])

    plot.figlegend(lines, [l.get_label() for l in lines], loc = 'lower center', ncol=4, labelspacing=0. )
    plot.grid(True)

    plot.suptitle("Vertical cloud profiles")

    return fig
