#
#@BEGIN LICENSE
#
# GPU-accelerated density-fitted coupled-cluster, a plugin to:
#
# PSI4: an ab initio quantum chemistry software package
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#@END LICENSE
#


import psi4
from psi4 import core
import os
import re
import psi4.driver.p4util as p4util
from psi4.driver.procrouting import proc_util
import psi4.driver.p4util as p4util

def run_gpu_dfcc(name, **kwargs):
    """Function encoding sequence of PSI module calls for
    a GPU-accelerated DF-CCSD(T) computation.

    >>> energy('df-ccsd(t)')

    """

    lowername = name.lower()
    kwargs = p4util.kwargs_lower(kwargs)
#kwarg = kwargs_lower(kwargs)
    # stash user options
    optstash = p4util.OptionsState(
         ['GPU_DFCC','COMPUTE_TRIPLES'],
         ['GPU_DFCC','DFCC'],
         ['GPU_DFCC','NAT_ORBS'],
         ['SCF','DF_INTS_IO'],
         ['SCF','SCF_TYPE'])

    psi4.core.set_local_option('SCF','DF_INTS_IO', 'SAVE')
    psi4.core.set_local_option('GPU_DFCC','DFCC', True)

    # throw an exception for open-shells
    if (psi4.core.get_option('SCF','REFERENCE') != 'RHF' ):
        raise ValidationError("Error: %s requires \"reference rhf\"." % lowername)

    # override symmetry: TODO!!! until this is fixed, you must include "symmetry c1" in the molecule group
    #molecule = psi4.get_active_molecule()
    #user_pg = molecule.schoenflies_symbol()
    #molecule.reset_point_group('c1')
    #molecule.fix_orientation(1)
    #molecule.update_geometry()
    #if user_pg != 'c1':
    #    psi4.print_out('\n')
    #    psi4.print_out('    <<< WARNING!!! >>>\n')
    #    psi4.print_out('\n')
    #    psi4.print_out('    plugin gpu_dfcc does not make use of molecular symmetry,\n')
    #    psi4.print_out('    further calculations in C1 point group.\n')
    #    psi4.print_out('\n')

    # triples?
    if (lowername == 'gpu-df-ccsd'):
        psi4.core.set_local_option('GPU_DFCC','COMPUTE_TRIPLES', False)
    if (lowername == 'gpu-df-ccsd(t)'):
        psi4.core.set_local_option('GPU_DFCC','COMPUTE_TRIPLES', True)

    # set scf-type to df unless the user wants something else
    if psi4.core.has_option_changed('SCF','SCF_TYPE') == False:
       psi4.core.set_local_option('SCF','SCF_TYPE', 'DF')

    # pick a df basis if the user didn't pick one
    if psi4.core.get_option('GPU_DFCC','DF_BASIS_CC') == '':
       basis   = psi4.core.get_global_option('BASIS')
       dfbasis = corresponding_rifit(basis)

    # psi4 run sequence 
    ref_wfn = kwargs.get('ref_wfn', None)
    if ref_wfn is None:
        ref_wfn = psi4.driver.scf_helper(name, use_c1=True, **kwargs)  # C1 certified
    else:
        if ref_wfn.molecule().schoenflies_symbol() != 'c1':
            raise ValidationError("""  GPU-DFCC does not make use of molecular symmetry: """
                                  """  reference wavefunction must be C1.\n""")

    scf_aux_basis = psi4.core.BasisSet.build(ref_wfn.molecule(), "DF_BASIS_SCF",
                                        psi4.core.get_option("SCF", "DF_BASIS_SCF"),
                                        "JKFIT", psi4.core.get_global_option('BASIS'),
                                        puream=ref_wfn.basisset().has_puream())
    ref_wfn.set_basisset("DF_BASIS_SCF", scf_aux_basis)

    aux_basis = psi4.core.BasisSet.build(ref_wfn.molecule(), "DF_BASIS_CC",
                                        psi4.core.get_global_option("DF_BASIS_CC"),
                                        "RIFIT", psi4.core.get_global_option("BASIS"))
    ref_wfn.set_basisset("DF_BASIS_CC", aux_basis)
    psi4.core.set_local_option('GPU_DFCC','DF_BASIS_CC',aux_basis)



    #aux_basis = psi4.core.BasisSet.build(ref_wfn.molecule(), "DF_BASIS_CC",
    #                                    psi4.core.get_global_option("DF_BASIS_CC"),
    #                                    "RIFIT", psi4.core.get_global_option("BASIS"))
    #ref_wfn.set_basisset("DF_BASIS_CC", aux_basis)

    returnvalue = psi4.core.plugin('gpu_dfcc.so',ref_wfn)

    # restore options
    optstash.restore()

    return returnvalue 

# Integration with driver routines
psi4.driver.procedures['energy']['gpu-df-ccsd(t)'] = run_gpu_dfcc
psi4.driver.procedures['energy']['gpu-df-ccsd']    = run_gpu_dfcc


def exampleFN():
    # Your Python code goes here
    pass
