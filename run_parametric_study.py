#!/usr/bin/env python3
"""
Run Optus's 3-tier parametric study using optimized MPM (standard mode)
Uses: mpm_optimized.py with use_gimp=False (verified correct, 2-3x faster)
"""

import numpy as np
import pandas as pd
from mpm_optimized import MPM2D_Optimized
import time
import sys

# Load parametric study plan
try:
    df = pd.read_csv('parametric_study_plan.csv')
    print(f"Loaded {len(df)} simulation cases from parametric_study_plan.csv")
except FileNotFoundError:
    print("ERROR: parametric_study_plan.csv not found!")
    print("Run: python3 smart_parametric_study.py first")
    sys.exit(1)

# Results storage
results = []

def run_case(row_idx, row):
    """Run a single parametric case"""
    print(f"\n{'='*70}")
    print(f"CASE {row_idx + 1}/{len(df)}: {row['tier']} - {row['description']}")
    print(f"{'='*70}")

    # Parameters
    su = int(row['su_Pa'])
    width = float(row['width_m'])
    E = float(row['E_Pa'])
    nu = 0.495
    rho = 1600

    # Domain (scaled based on width)
    Lx = max(30, width * 5)
    Ly = max(15, Lx / 2)
    nx = int(row.get('nx', 80))
    ny = int(row.get('ny', 40))

    print(f"  Foundation: {width}m wide")
    print(f"  Soil: su={su/1000:.0f} kPa, E={E/1e6:.1f} MPa")
    print(f"  Grid: {nx}x{ny}")

    t0 = time.time()

    try:
        # Initialize MPM with STANDARD mode (use_gimp=False)
        mpm = MPM2D_Optimized(
            domain_x=[0, Lx],
            domain_y=[0, Ly],
            nx=nx,
            ny=ny,
            su=su,
            E=E,
            nu=nu,
            rho=rho,
            use_gimp=False  # ✅ VERIFIED CORRECT
        )

        # Add soil
        soil_depth = Ly * 0.67
        mpm.add_soil_block([0, Lx], [0, soil_depth], ppc=4)

        # Add foundation
        mpm.add_strip_foundation(
            center_x=Lx/2,
            y_base=soil_depth,
            width=width,
            thickness=0.5,
            density=2500
        )

        # Run simulation
        dt = mpm.timestep()
        rate = float(row.get('rate_m_per_s', 0.0025))
        mpm.foundation_velocity = -rate

        max_steps = int(row.get('max_steps', 8000))
        target_settlement = float(row.get('target_settlement_m', 0.05))

        step = 0
        settlements = []
        loads = []

        while step < max_steps:
            mpm.mpm_step(dt)
            step += 1

            # Track progress
            current_y = np.mean([mpm.particles[i].y for i in mpm.foundation_indices])
            settlement = mpm.foundation_y0 - current_y

            if step % 1000 == 0:
                q = mpm.calculate_bearing_capacity() / 1000
                settlements.append(settlement)
                loads.append(q)
                print(f"    Step {step:4d} | s={settlement*1000:.1f}mm | q={q:.0f} kN/m")

            if settlement >= target_settlement:
                print(f"  ✅ Reached target settlement")
                break

        # Final results
        q_ult = max(loads) if loads else 0
        Nc = (q_ult * 1000) / (su * width) if su > 0 else 0

        elapsed = time.time() - t0

        print(f"\n  Results:")
        print(f"    Q_ultimate: {q_ult:.0f} kN/m")
        print(f"    Nc factor: {Nc:.2f}")
        print(f"    Time: {elapsed:.1f}s")

        return {
            'case_id': row_idx + 1,
            'tier': row['tier'],
            'description': row['description'],
            'su_kPa': su / 1000,
            'width_m': width,
            'E_MPa': E / 1e6,
            'Q_kN': q_ult,
            'Nc': Nc,
            'time_s': elapsed,
            'status': 'success'
        }

    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        return {
            'case_id': row_idx + 1,
            'tier': row['tier'],
            'description': row['description'],
            'status': f'failed: {e}'
        }

# Main execution
print("="*70)
print("PARAMETRIC STUDY - OPTIMIZED MPM (Standard Mode)")
print("="*70)
print(f"Total cases: {len(df)}")
print(f"Method: mpm_optimized.py with use_gimp=False")
print(f"Expected speedup: 2-3x vs mpm_validation.py")
print("="*70)

# Run all cases
for idx, row in df.iterrows():
    result = run_case(idx, row)
    results.append(result)

    # Save intermediate results
    pd.DataFrame(results).to_csv('parametric_results_intermediate.csv', index=False)
    print(f"\n  Progress: {idx+1}/{len(df)} complete ({(idx+1)/len(df)*100:.0f}%)")

# Final save
df_results = pd.DataFrame(results)
df_results.to_csv('parametric_results.csv', index=False)

print(f"\n{'='*70}")
print("PARAMETRIC STUDY COMPLETE!")
print(f"{'='*70}")
print(f"Results saved to: parametric_results.csv")
print(f"Total cases: {len(results)}")
print(f"Successful: {sum(1 for r in results if r['status'] == 'success')}")
print(f"Failed: {sum(1 for r in results if r['status'] != 'success')}")
