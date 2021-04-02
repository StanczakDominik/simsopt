#!/usr/bin/env python

import numpy as np
from math import pi
from simsopt.geo.coilcollection import CoilCollection
from simsopt.geo.boozersurface import BoozerSurface
from simsopt.geo.biotsavart import BiotSavart
from simsopt.geo.surfacexyzfourier import SurfaceXYZFourier
from simsopt.geo.surfacerzfourier import SurfaceRZFourier
from simsopt.geo.surfaceobjectives import ToroidalFlux 
from surface_test_helpers import get_ncsx_data,get_surface2, get_exact_surface 
from simsopt.mhd import Vmec

vmec = Vmec("input.test_boozer_surfaces_vmec")

stellsym = False
surfacetype = "SurfaceXYZFourier"

coils, currents, ma = get_ncsx_data()
stellarator = CoilCollection(coils, currents, 3, True)

bs = BiotSavart(stellarator.coils, stellarator.currents)
bs_tf = BiotSavart(stellarator.coils, stellarator.currents)

s = get_surface2(surfacetype,stellsym)
s.fit_to_curve(ma, 0.1)
iota = -0.4


tf = ToroidalFlux(s, bs_tf)
tf_target = 0.05
boozerSurface = BoozerSurface(bs, s, tf, tf_target) 
print("Surface computed using LBFGS and penalised toroidal flux constraint") 
s,iota,message = boozerSurface.minimize_boozer_penalty_constraints_LBFGS(tol = 1e-12, maxiter = 100, constraint_weight = 100., iota = iota)

s,iota,message = boozerSurface.minimize_boozer_penalty_constraints_ls(tol = 1e-12, maxiter = 100, constraint_weight = 100., iota = iota)
print("Toroidal flux is :", tf.J(), "Target toroidal flux is: ", tf_target, "\n")

print("Surface computed using Newton and penalised toroidal flux constraint") 
s, iota,message = boozerSurface.minimize_boozer_penalty_constraints_newton(tol = 1e-11, maxiter = 10, constraint_weight = 100., iota = iota)
print("Toroidal flux is :", tf.J(), "Target toroidal flux is: ", tf_target, "\n")

for tf_target in np.arange(1, 4) * 0.05:
    boozerSurface = BoozerSurface(bs, s, tf, tf_target) 
    s, iota, lm, message = boozerSurface.minimize_boozer_exact_constraints_newton(tol = 1e-11, maxiter = 10,iota = iota)
    xi = np.concatenate( (s.get_dofs(), [iota]) )
    res = boozerSurface.boozer_penalty_constraints(xi, derivatives = 0, scalarize = False)
    print(message)
    print("Toroidal flux is :", tf.J(),\
      "\nTarget toroidal flux is: ", tf_target,\
      "\niota is: ", iota,\
      "\nresidual is: ", np.linalg.norm(res),\
      "\n")
    
    # Matt the SurfaceRZFourier is here:
    sRZ = s.to_RZFourier()
    #sRZ.plot()

    vmec.phiedge = tf_target
    vmec.boundary = sRZ
    vmec.need_to_run_code = True
    iota_vmec = vmec.iota_edge() # This line causes VMEC to run.
    print('Iota from VMEC:', iota_vmec)
    print('G from VMEC:', vmec.wout.bvco[-1])
    # For some reason there is a sign difference in iota from vmec.
    np.testing.assert_allclose(iota, -iota_vmec, atol=0.002, rtol=0)
    # For flux=0.15, diff in iota is 0.00105711, so atol is ~2x this.





