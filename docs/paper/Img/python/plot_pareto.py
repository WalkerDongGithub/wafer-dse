"""图 3: Pareto 前沿。输出: docs/paper/Img/pareto.pdf"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import os

PROJECT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
OUT = os.path.join(os.path.dirname(__file__), "..")

def main():
    df = pd.read_csv(os.path.join(PROJECT, "outputs", "paper_experiments", "dse_sweep.csv"))
    fig, ax = plt.subplots(figsize=(8, 5.5))
    sizes = df['total_power_w'] / df['total_power_w'].max() * 300 + 50
    sc = ax.scatter(df['total_die_area_mm2'], df['n_terminals'], s=sizes,
                    c=df['t_star'], cmap='RdYlGn', vmin=0, vmax=2,
                    alpha=0.85, edgecolors='#333', linewidth=0.8)
    cbar = plt.colorbar(sc, ax=ax); cbar.set_label(r'$t^*$ (1.0 = non-blocking)')
    for _, r in df.iterrows():
        ax.annotate(r['label'].replace('DF_', ''), (r['total_die_area_mm2'], r['n_terminals']),
                    fontsize=7.5, ha='left', xytext=(5, 3), textcoords='offset points')
    # Pareto frontier
    frontier_n, frontier_a = [], []
    for n in sorted(df['n_terminals'].unique()):
        s = df[df['n_terminals'] == n]
        best = s.loc[s['total_die_area_mm2'].idxmin()]
        frontier_n.append(best['n_terminals']); frontier_a.append(best['total_die_area_mm2'])
    ax.plot(frontier_a, frontier_n, '--', color='#333', lw=1.5, alpha=0.5)
    ax.scatter(frontier_a, frontier_n, marker='*', s=200, color='gold',
              edgecolors='#333', linewidth=0.8, zorder=10, label='Pareto frontier')
    ax.set_xlabel('Total die area (mm²)'); ax.set_ylabel('N (number of terminals)')
    ax.set_title('Dragonfly Design Space: Terminals vs Area\n(All at 800 Gbps, Valiant routing)')
    ax.legend(fontsize=9); ax.grid(True, alpha=0.3)
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "pareto.pdf"), dpi=150, bbox_inches='tight')
    print("  -> pareto.pdf")

if __name__ == "__main__": main()
