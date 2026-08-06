"""图 1: 可扩展性。输出: docs/paper/Img/scalability.pdf"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import os

PROJECT = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
OUT = os.path.join(os.path.dirname(__file__), "..")

def main():
    df = pd.read_csv(os.path.join(PROJECT, "outputs", "paper_experiments", "scalability.csv"))
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    colors = {'dragonfly': '#2196F3', 'mesh': '#FF9800', 'kary_ncube': '#4CAF50'}
    for topo in df['topology'].unique():
        s = df[df['topology'] == topo]
        ax1.scatter(s['n_terminals'], s['num_vars'], c=colors.get(topo, '#999'),
                    label=topo, s=60, alpha=0.8, edgecolors='white', linewidth=0.5)
    n_min, n_max = df['n_terminals'].min(), df['n_terminals'].max()
    ax1.plot([n_min, n_max], [n_min**2*30, n_max**2*30], '--', color='gray', alpha=0.5, label=r'$O(N^2)$')
    ax1.set_xlabel('N (terminals)'); ax1.set_ylabel('Number of variables')
    ax1.set_title('LP Variables vs Topology Size'); ax1.legend(fontsize=8); ax1.grid(True, alpha=0.3)
    ax2.scatter(df['num_vars'], df['solve_time_s'],
                c=[colors.get(t, '#999') for t in df['topology']], s=60, alpha=0.8, edgecolors='white', linewidth=0.5)
    for _, r in df.iterrows():
        if r['solve_time_s'] > 5:
            ax2.annotate(r['label'], (r['num_vars'], r['solve_time_s']), fontsize=7, alpha=0.7, xytext=(5,5), textcoords='offset points')
    ax2.set_xlabel('Number of variables'); ax2.set_ylabel('Solve time (s)')
    ax2.set_title('LP Solve Time vs Problem Size')
    ax2.set_xscale('log'); ax2.set_yscale('log'); ax2.grid(True, alpha=0.3)
    plt.tight_layout(); plt.savefig(os.path.join(OUT, "scalability.pdf"), dpi=150, bbox_inches='tight')
    print("  -> scalability.pdf")

if __name__ == "__main__": main()
