"""图 2: B_max vs N。输出: docs/paper/Img/bmax.pdf"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

PROJECT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
OUT = os.path.join(os.path.dirname(__file__), "..")

def main():
    df = pd.read_csv(os.path.join(PROJECT, "outputs", "paper_experiments", "bmax.csv"))
    df = df[df['topology'].str.startswith('DF')].sort_values('n_terminals')
    fig, ax = plt.subplots(figsize=(9, 5.5))
    x = df['n_terminals'].values
    ax.plot(x, df['B_max_geom_Gbps'].values, 'o-', color='#E53935', lw=2, ms=8,
            label=r'$B_{\max}^{\mathrm{geom}}$ (bump budget)')
    ax.plot(x, df['B_max_thermal_Gbps'].values, 's--', color='#1E88E5', lw=2, ms=8,
            label=r'$B_{\max}^{\mathrm{thermal}}$ (cooling limit)')
    for _, r in df.iterrows():
        ax.annotate(f"{r['B_max_Gbps']/1000:.0f}K", (r['n_terminals'], r['B_max_Gbps']),
                    fontsize=7.5, ha='center', va='bottom', xytext=(0, 6), textcoords='offset points')
    ax.axhline(y=800, color='gray', linestyle=':', alpha=0.4, lw=1)
    ax.annotate('800 Gbps target', (x[-1], 800), fontsize=9, color='gray', va='bottom', ha='right')
    ax.fill_between(x, df['B_max_geom_Gbps'].values, df['B_max_thermal_Gbps'].values, alpha=0.06, color='blue')
    ax.set_xlabel('N (number of terminals)'); ax.set_ylabel(r'$B_{\max}$ (Gbps)')
    ax.set_title(r'Physical Bandwidth Ceiling: $B_{\max}$ vs Topology Size')
    ax.set_yscale('log'); ax.legend(); ax.grid(True, alpha=0.3, which='both')
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "bmax.pdf"), dpi=150, bbox_inches='tight')
    print("  -> bmax.pdf")

if __name__ == "__main__": main()
