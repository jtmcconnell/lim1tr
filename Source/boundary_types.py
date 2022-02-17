########################################################################################
#                                                                                      #
#  Copyright 2021 National Technology & Engineering Solutions of Sandia, LLC (NTESS).  #
#  Under the terms of Contract DE-NA0003525 with NTESS, the U.S. Government retains    #
#  certain rights in this software.                                                    #
#                                                                                      #
#  This software is released under the license detailed in the file, LICENSE.          #
#                                                                                      #
########################################################################################

from __future__ import division
import numpy as np


class bc_base:
    def apply(self, *args):
        return 0


    def apply_operator(self, *args):
        return 0


class end_bc(bc_base):
    def __init__(self, dx_arr, my_end):
        self.name = 'end'
        self.dx_arr = dx_arr
        self.n_tot = dx_arr.shape[0]
        if my_end == 'Left':
            self.n_ind = 0
            self.k_ind = 0
        elif my_end == 'Right':
            self.n_ind = self.n_tot - 1
            self.k_ind = self.n_tot - 2
        else:
            err_str = 'Unrecognized boundary type {}.'.format(my_end)
            raise ValueError(err_str)


class end_convection(end_bc):
    def set_params(self, h, T):
        self.h_end = h
        self.T_end = T
        self.name += '_convection'


    def apply(self, eqn_sys, mat_man):
        '''Adds end convection BC terms to system.
        '''
        phi = 2*mat_man.k_arr[self.k_ind]/self.dx_arr[self.n_ind]
        c_end = self.h_end*phi/(self.h_end + phi)
        eqn_sys.LHS_c[self.n_ind] += c_end
        eqn_sys.RHS[self.n_ind] += c_end*self.T_end


    def apply_operator(self, eqn_sys, mat_man, T):
        '''Adds the action of the end convection
        terms on the previous time step to the RHS
        '''
        phi = 2*mat_man.k_arr[self.k_ind]/self.dx_arr[self.n_ind]
        c_end = self.h_end*phi/(self.h_end + phi)
        eqn_sys.RHS[self.n_ind] += c_end*(self.T_end - T[self.n_ind])


class end_flux(end_bc):
    def set_params(self, flux):
        self.flux = flux
        self.name += '_flux'


    def apply(self, eqn_sys, mat_man):
        '''Adds heat flux bc term to end.
        '''
        eqn_sys.RHS[self.n_ind] += self.flux


    def apply_operator(self, eqn_sys, mat_man, T):
        '''Adds action of heat flux bc terms
        on the previous time step to the RHS
        '''
        eqn_sys.RHS[self.n_ind] += self.flux


class end_radiation(end_bc):
    def set_params(self, eps, T):
        self.sigma_eps = 5.67e-8*eps
        self.T_ext_4 = T**4
        self.name += '_radiation'


    def apply(self, eqn_sys, mat_man, T):
        '''Adds end convection BC terms to system.
        '''
        eqn_sys.J_c[self.n_ind] += self.sigma_eps*4*T[self.n_ind]**3
        eqn_sys.F[self.n_ind] += self.sigma_eps*(T[self.n_ind]**4 - self.T_ext_4)


    def apply_operator(self, eqn_sys, mat_man, T):
        '''Adds the action of the end convection
        terms on the previous time step to the RHS
        '''
        eqn_sys.RHS[self.n_ind] -= self.sigma_eps*(T[self.n_ind]**4 - self.T_ext_4)


class ext_bc(bc_base):
    def __init__(self, dx_arr, PA_r):
        self.name = 'ext'
        self.dx_arr = dx_arr
        self.n_tot = dx_arr.shape[0]
        self.PA_r = PA_r


class ext_convection(ext_bc):
    def set_params(self, h, T):
        self.h_ext = h
        self.T_ext = T
        self.name += '_convection'


    def apply(self, eqn_sys, mat_man):
        '''Adds external convection terms
        '''
        for i in range(self.n_tot):
            h_const = self.h_ext*self.dx_arr[i]*self.PA_r

            # LHS
            eqn_sys.LHS_c[i] += h_const

            # RHS
            eqn_sys.RHS[i] += h_const*self.T_ext


    def apply_operator(self, eqn_sys, mat_man, T):
        '''Adds the action of the external convection terms
        on the previous time step to the RHS
        '''
        for i in range(self.n_tot):
            # convection constant
            h_const = self.h_ext*self.dx_arr[i]*self.PA_r

            # RHS
            eqn_sys.RHS[i] += h_const*(self.T_ext - T[i])


class ext_radiation(ext_bc):
    def set_params(self, eps, T):
        self.sigma_eps = 5.67e-8*eps
        self.T_ext_4 = T**4
        self.name += '_radiation'


    def apply(self, eqn_sys, mat_man, T):
        '''Adds end convection BC terms to system.
        '''
        dxPA = self.dx_arr*self.PA_r
        for i in range(self.n_tot):
            eqn_sys.J_c[i] += dxPA[i]*self.sigma_eps*4*T[i]**3
            eqn_sys.F[i] += dxPA[i]*self.sigma_eps*(T[i]**4 - self.T_ext_4)


    def apply_operator(self, eqn_sys, mat_man, T):
        '''Adds the action of the end convection
        terms on the previous time step to the RHS
        '''
        dxPA = self.dx_arr*self.PA_r
        for i in range(self.n_tot):
            eqn_sys.RHS[i] -= dxPA[i]*self.sigma_eps*(T[i]**4 - self.T_ext_4)


class timed_boundary:
    def __init__(self, bc, off_time):
        self.bc = bc
        self.off_time = off_time
        self.bc.name += '_timed'


    def set_time(self, tot_time):
        self.tot_time = tot_time


    def apply(self, *args):
        if self.off_time - self.tot_time > 1e-14:
            self.bc.apply(*args)


    def apply_operator(self, *args):
        if self.off_time - self.tot_time > 1e-14:
            self.bc.apply_operator(*args)
