#!/usr/bin/env python3
"""
Simplified Analysis & Visualization Tool
Analyzes experiment results and creates graphs in one streamlined script.

Usage:
    python3 analyze-and-visualize.py <experiment_results_directory>
    
Example:
    python3 analyze-and-visualize.py experiment_results_20251026_144115
"""

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import sys
import json
from datetime import datetime

# Publication-quality graph settings Source:
plt.rcParams['figure.figsize'] = (10, 6)
plt.rcParams['font.size'] = 12
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['axes.labelsize'] = 12
plt.rcParams['axes.titlesize'] = 14
plt.rcParams['xtick.labelsize'] = 11
plt.rcParams['ytick.labelsize'] = 11
plt.rcParams['legend.fontsize'] = 10
plt.rcParams['figure.dpi'] = 150

EXPERIMENT_NAMES = {
    '1_baseline': 'Baseline',
    '2_burst_high': 'Burst High-Tier',
    '3_burst_equal': 'Burst Equal',
    '3_burst_low_heavy': 'Burst Low-Tier',
    '4_saturation': 'Saturation'
}

TIER_COLORS = {
    'hi': '#2E86AB',
    'med': '#F18F01', 
    'low': '#A23B72'
}

def format_name(exp_name):
    """Format experiment name for display"""
    name = exp_name.replace('experiment_', '')
    return EXPERIMENT_NAMES.get(name, name.replace('_', ' ').title())

def load_experiments(results_dir):
    """Load all experiment CSV files"""
    experiments = {}
    
    for exp_dir in sorted(results_dir.glob('experiment_*')):
        # Skip experiment 5 if it exists its breaking eeverything for some reason WHY
        if 'experiment_5' in exp_dir.name:
            continue
        
        csv_file = exp_dir / 'callbacks.csv'
        if csv_file.exists():
            try:
                df = pd.read_csv(csv_file)
                if len(df) > 0:
                    experiments[exp_dir.name] = df
                    print(f"Loaded {exp_dir.name}: {len(df):,} requests")
            except Exception as e:
                print(f"Error loading {exp_dir.name}: {e}")
    
    return experiments

def analyze_experiment(df, exp_name):
    """Calculate statistics for an experiment"""
    latencies = df['Latency to Gateway (ms)']
    
    stats = {
        'experiment': format_name(exp_name),
        'total_requests': len(latencies),
        'mean_ms': latencies.mean(),
        'median_ms': latencies.median(),
        'std_ms': latencies.std(),
        'min_ms': latencies.min(),
        'max_ms': latencies.max(),
        'p50_ms': latencies.quantile(0.50),
        'p90_ms': latencies.quantile(0.90),
        'p95_ms': latencies.quantile(0.95),
        'p99_ms': latencies.quantile(0.99)
    }
    
    # Per-tier statistics
    tier_stats = {}
    for tier in ['hi', 'med', 'low']:
        tier_df = df[df['X-Function-Name'].str.contains(f'-{tier}-tier')]
        if len(tier_df) > 0:
            tier_latencies = tier_df['Latency to Gateway (ms)']
            tier_stats[tier] = {
                'count': len(tier_latencies),
                'mean': tier_latencies.mean(),
                'p95': tier_latencies.quantile(0.95),
                'p99': tier_latencies.quantile(0.99)
            }
    
    return stats, tier_stats

def print_summary(all_stats):
    """Print experiment summary to console"""
    print("\n" + "="*80)
    print("EXPERIMENT RESULTS SUMMARY")
    print("="*80 + "\n")
    
    # Summary table
    print(f"{'Experiment':<20} {'Requests':>10} {'Mean':>8} {'P95':>8} {'P99':>8} {'Std':>8}")
    print("-" * 80)
    
    for stats in all_stats:
        print(f"{stats['experiment']:<20} "
              f"{stats['total_requests']:>10,} "
              f"{stats['mean_ms']:>8.2f} "
              f"{stats['p95_ms']:>8.2f} "
              f"{stats['p99_ms']:>8.2f} "
              f"{stats['std_ms']:>8.2f}")
    
    print("\n" + "="*80 + "\n")

def create_overview_graph(experiments, output_dir):
    """Main comparison graph with Mean, P95, P99"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    exp_names = []
    means = []
    p95s = []
    p99s = []
    
    for exp_name, df in sorted(experiments.items()):
        latencies = df['Latency to Gateway (ms)']
        exp_names.append(format_name(exp_name))
        means.append(latencies.mean())
        p95s.append(latencies.quantile(0.95))
        p99s.append(latencies.quantile(0.99))
    
    x = np.arange(len(exp_names))
    width = 0.25
    
    ax.bar(x - width, means, width, label='Mean', alpha=0.85, color='#2E86AB')
    ax.bar(x, p95s, width, label='P95', alpha=0.85, color='#F18F01')
    ax.bar(x + width, p99s, width, label='P99', alpha=0.85, color='#A23B72')
    
    ax.set_xlabel('Experiment Pattern')
    ax.set_ylabel('Latency (ms)')
    ax.set_title('Router-to-Gateway Latency Comparison')
    ax.set_xticks(x)
    ax.set_xticklabels(exp_names, rotation=30, ha='right')
    ax.legend()
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'overview_latency_comparison.png', dpi=200, bbox_inches='tight')
    print(f"Created: overview_latency_comparison.png")
    plt.close()

def create_cdf_graph(experiments, output_dir):
    """Cumulative Distribution Function for all experiments"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']
    
    for i, (exp_name, df) in enumerate(sorted(experiments.items())):
        latencies = df['Latency to Gateway (ms)'].sort_values()
        cdf = np.arange(1, len(latencies) + 1) / len(latencies)
        ax.plot(latencies, cdf, label=format_name(exp_name), 
                linewidth=2, alpha=0.8, color=colors[i % len(colors)])
    
    ax.set_xlabel('Latency (ms)')
    ax.set_ylabel('Cumulative Probability')
    ax.set_title('Latency CDF Across All Experiments')
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='lower right')
    ax.set_xlim(left=0)
    
    plt.tight_layout()
    plt.savefig(output_dir / 'cdf_all_experiments.png', dpi=200, bbox_inches='tight')
    print(f"Created: cdf_all_experiments.png")
    plt.close()

def create_boxplot(experiments, output_dir):
    """Box plot showing distribution for each experiment"""
    fig, ax = plt.subplots(figsize=(12, 6))
    
    data = []
    labels = []
    
    for exp_name, df in sorted(experiments.items()):
        data.append(df['Latency to Gateway (ms)'])
        labels.append(format_name(exp_name))
    
    bp = ax.boxplot(data, labels=labels, patch_artist=True, 
                     showfliers=False, widths=0.6)
    
    # Color the boxes
    for patch, color in zip(bp['boxes'], ['#2E86AB', '#A23B72', '#F18F01', '#C73E1D', '#6A994E']):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax.set_ylabel('Latency (ms)')
    ax.set_title('Latency Distribution by Experiment')
    ax.grid(axis='y', alpha=0.3, linestyle='--')
    plt.xticks(rotation=30, ha='right')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'boxplot_comparison.png', dpi=200, bbox_inches='tight')
    print(f"Created: boxplot_comparison.png")
    plt.close()

def create_tier_comparison(experiments, output_dir):
    """Compare tier performance across experiments"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # P95 comparison
    exp_names = []
    hi_p95 = []
    med_p95 = []
    low_p95 = []
    
    for exp_name, df in sorted(experiments.items()):
        exp_names.append(format_name(exp_name))
        
        for tier, data_list in [('hi', hi_p95), ('med', med_p95), ('low', low_p95)]:
            tier_df = df[df['X-Function-Name'].str.contains(f'-{tier}-tier')]
            if len(tier_df) > 0:
                data_list.append(tier_df['Latency to Gateway (ms)'].quantile(0.95))
            else:
                data_list.append(0)
    
    x = np.arange(len(exp_names))
    width = 0.25
    
    ax1.bar(x - width, hi_p95, width, label='High-Tier', alpha=0.85, color=TIER_COLORS['hi'])
    ax1.bar(x, med_p95, width, label='Med-Tier', alpha=0.85, color=TIER_COLORS['med'])
    ax1.bar(x + width, low_p95, width, label='Low-Tier', alpha=0.85, color=TIER_COLORS['low'])
    
    ax1.set_xlabel('Experiment')
    ax1.set_ylabel('P95 Latency (ms)')
    ax1.set_title('P95 Latency by Tier')
    ax1.set_xticks(x)
    ax1.set_xticklabels(exp_names, rotation=30, ha='right')
    ax1.legend()
    ax1.grid(axis='y', alpha=0.3, linestyle='--')
    
    # P99 comparison
    hi_p99 = []
    med_p99 = []
    low_p99 = []
    
    for exp_name, df in sorted(experiments.items()):
        for tier, data_list in [('hi', hi_p99), ('med', med_p99), ('low', low_p99)]:
            tier_df = df[df['X-Function-Name'].str.contains(f'-{tier}-tier')]
            if len(tier_df) > 0:
                data_list.append(tier_df['Latency to Gateway (ms)'].quantile(0.99))
            else:
                data_list.append(0)
    
    ax2.bar(x - width, hi_p99, width, label='High-Tier', alpha=0.85, color=TIER_COLORS['hi'])
    ax2.bar(x, med_p99, width, label='Med-Tier', alpha=0.85, color=TIER_COLORS['med'])
    ax2.bar(x + width, low_p99, width, label='Low-Tier', alpha=0.85, color=TIER_COLORS['low'])
    
    ax2.set_xlabel('Experiment')
    ax2.set_ylabel('P99 Latency (ms)')
    ax2.set_title('P99 Latency by Tier')
    ax2.set_xticks(x)
    ax2.set_xticklabels(exp_names, rotation=30, ha='right')
    ax2.legend()
    ax2.grid(axis='y', alpha=0.3, linestyle='--')
    
    plt.tight_layout()
    plt.savefig(output_dir / 'tier_comparison.png', dpi=200, bbox_inches='tight')
    print(f"Created: tier_comparison.png")
    plt.close()

def save_json_summary(all_stats, all_tier_stats, output_dir):
    """Save statistics to JSON file"""
    summary = {
        'generated': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'experiments': []
    }
    
    for stats, tier_stats in zip(all_stats, all_tier_stats):
        exp_data = {
            'name': stats['experiment'],
            'overall': stats,
            'tiers': tier_stats
        }
        summary['experiments'].append(exp_data)
    
    output_file = output_dir / 'summary_statistics.json'
    with open(output_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Created: summary_statistics.json")

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 analyze-and-visualize.py <experiment_results_directory>")
        print("\nExample:")
        print("  python3 analyze-and-visualize.py experiment_results_20251026_144115")
        sys.exit(1)
    
    results_dir = Path(sys.argv[1])
    
    if not results_dir.exists():
        print(f"Error: Directory not found: {results_dir}")
        sys.exit(1)
    
    print(f"\n{'='*80}")
    print(f"Multi-Tier FaaS Analysis & Visualization")
    print(f"{'='*80}\n")
    print(f"Results Directory: {results_dir}")
    print(f"Analysis Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load experiments
    print("Loading experiment data...")
    experiments = load_experiments(results_dir)
    
    if not experiments:
        print("No experiment data found!")
        sys.exit(1)
    
    print(f"\n Loaded {len(experiments)} experiments\n")
    
    # Analyze each experiment
    print("Analyzing experiments...")
    all_stats = []
    all_tier_stats = []
    
    for exp_name, df in experiments.items():
        stats, tier_stats = analyze_experiment(df, exp_name)
        all_stats.append(stats)
        all_tier_stats.append(tier_stats)
    
    print_summary(all_stats)
    output_dir = results_dir / 'graphs'
    output_dir.mkdir(exist_ok=True)
    print(f"Creating graphs in: {output_dir}\n")
    print("Generating visualizations...")
    create_overview_graph(experiments, output_dir)
    create_cdf_graph(experiments, output_dir)
    create_boxplot(experiments, output_dir)
    create_tier_comparison(experiments, output_dir)
    print("\nSaving statistics...")
    save_json_summary(all_stats, all_tier_stats, output_dir)
    
    print(f"\n{'='*80}")
    print(f"Output location: {output_dir}")
    print(f"\nGenerated files:")
    print(f"  • overview_latency_comparison.png - Main results")
    print(f"  • cdf_all_experiments.png - Cumulative distribution")
    print(f"  • boxplot_comparison.png - Distribution view")
    print(f"  • tier_comparison.png - Per-tier analysis")
    print(f"  • summary_statistics.json - Raw statistics\n")

if __name__ == '__main__':
    main()
