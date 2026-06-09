//! Max-weight derangement solver.
//!
//! A *derangement* is a permutation where no element maps to itself
//! (`assignment[i] ≠ i`).  This module finds the derangement with **maximum**
//! total weight by reducing the problem to a Hungarian min-cost assignment:
//!
//! 1. Self-loop entries (`weight[i][i]`) are replaced with a huge penalty `M`
//!    so the Hungarian algorithm never selects them.
//! 2. Max-weight is converted to min-cost: `cost[i][j] = max_w - weight[i][j]`.
//! 3. The resulting Hungarian assignment is a max-weight derangement.
//!
//! This is a line-for-line port of the Python reference in
//! `src/wafer_dse/architecture_model/solver/algorithm/derangement.py`.

use wafer_hungarian::{hungarian_min_cost, HungarianError};

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

#[derive(Debug, PartialEq)]
pub enum DerangementError {
    /// Underlying Hungarian solver failed.
    Hungarian(HungarianError),
    /// No derangement exists (e.g. N=1 — the only choice is a self-loop).
    Impossible,
    /// Weight matrix is not square.
    NonSquare { rows: usize, cols: usize },
}

impl std::fmt::Display for DerangementError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            DerangementError::Hungarian(e) => write!(f, "hungarian error: {e}"),
            DerangementError::Impossible => {
                write!(f, "no valid derangement exists; check terminal count ≥ 2")
            }
            DerangementError::NonSquare { rows, cols } => {
                write!(f, "weight must be square (got {rows}×{cols})")
            }
        }
    }
}

impl From<HungarianError> for DerangementError {
    fn from(e: HungarianError) -> Self {
        DerangementError::Hungarian(e)
    }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/// Compute the max-weight derangement for an N×N weight matrix.
///
/// # Arguments
/// * `weight` — N×N matrix. `weight[i][j]` is the reward of assigning row `i`
///   to column `j`.  Must be non-negative (negative values produce correct but
///   potentially unintuitive results due to the `max_w` offset).
///
/// # Returns
/// * `(max_total_weight, assignment)` where `assignment[i] = j` and `j ≠ i`.
///   For N ≤ 1, returns `(0.0, [])` — no valid derangement exists.
///
/// # Errors
/// * `DerangementError::NonSquare` — matrix is not square.
/// * `DerangementError::Impossible` — unexpectedly selected a self-loop
///   (should only happen with degenerate input).
pub fn max_weight_derangement(
    weight: &[Vec<f64>],
) -> Result<(f64, Vec<usize>), DerangementError> {
    let n = weight.len();

    // --- N ≤ 1 short-circuit (matches Python) ---
    if n <= 1 {
        return Ok((0.0, vec![]));
    }

    // --- validate square ---
    for row in weight {
        if row.len() != n {
            return Err(DerangementError::NonSquare {
                rows: n,
                cols: row.len(),
            });
        }
    }

    // --- find max weight (EXACT match to Python: max(max(row) for row in weight)) ---
    let max_w = weight
        .iter()
        .flat_map(|row| row.iter())
        .cloned()
        .fold(f64::NEG_INFINITY, f64::max);

    // --- self-loop penalty (EXACT match to Python formula) ---
    // Python: big = max(1.0, max_w) * (n + 1) * 1e9
    let big = max_w.max(1.0) * (n as f64 + 1.0) * 1e9;

    // --- max-weight → min-cost transformation ---
    let mut cost: Vec<Vec<f64>> = Vec::with_capacity(n);
    for i in 0..n {
        let mut row: Vec<f64> = Vec::with_capacity(n);
        for j in 0..n {
            if i == j {
                row.push(big);
            } else {
                row.push(max_w - weight[i][j]);
            }
        }
        cost.push(row);
    }

    let (_min_cost, assignment) = hungarian_min_cost(&cost)?;

    // --- defensive: verify no self-loops ---
    if assignment.iter().enumerate().any(|(i, &j)| i == j) {
        return Err(DerangementError::Impossible);
    }

    let total: f64 = (0..n).map(|i| weight[i][assignment[i]]).sum();
    Ok((total, assignment))
}

// ===========================================================================
// Tests — exhaustive verification (matching Python test_derangement.py)
// ===========================================================================

#[cfg(test)]
mod tests {
    use super::*;

    /// Generate all derangements of 0..n-1.
    fn derangements(n: usize) -> Vec<Vec<usize>> {
        let mut result = vec![];
        let mut indices: Vec<usize> = (0..n).collect();

        fn permute(
            indices: &mut [usize],
            start: usize,
            result: &mut Vec<Vec<usize>>,
        ) {
            let n = indices.len();
            if start == n {
                // Check it's a derangement
                if indices.iter().enumerate().all(|(i, &j)| i != j) {
                    result.push(indices.to_vec());
                }
                return;
            }
            for i in start..n {
                indices.swap(start, i);
                permute(indices, start + 1, result);
                indices.swap(start, i);
            }
        }

        permute(&mut indices, 0, &mut result);
        result
    }

    fn brute_force_max(weight: &[Vec<f64>]) -> (f64, Vec<usize>) {
        let n = weight.len();
        let mut best_w = -1.0_f64;
        let mut best_perm = vec![];
        for perm in derangements(n) {
            let total: f64 = (0..n).map(|i| weight[i][perm[i]]).sum();
            if total > best_w {
                best_w = total;
                best_perm = perm;
            }
        }
        (best_w, best_perm)
    }

    fn random_weight(n: usize, lo: f64, hi: f64) -> Vec<Vec<f64>> {
        let mut seed: u64 = (n as u64).wrapping_mul(0xCAFEBABE);
        let mut next = || {
            seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            let v = (seed >> 32) as f64 / (u32::MAX as f64);
            lo + v * (hi - lo)
        };
        (0..n)
            .map(|_| (0..n).map(|_| next()).collect())
            .collect()
    }

    // --- exhaustive tests ---

    #[test]
    fn n2_exhaustive() {
        for _ in 0..20 {
            let w = random_weight(2, 0.0, 100.0);
            let (h_total, h_assign) = max_weight_derangement(&w).unwrap();
            let (b_total, _) = brute_force_max(&w);
            assert!((h_total - b_total).abs() < 1e-9);
            assert!(h_assign.iter().enumerate().all(|(i, &j)| i != j));
        }
    }

    #[test]
    fn n3_exhaustive() {
        for _ in 0..20 {
            let w = random_weight(3, 0.0, 100.0);
            let (h_total, h_assign) = max_weight_derangement(&w).unwrap();
            let (b_total, _) = brute_force_max(&w);
            assert!((h_total - b_total).abs() < 1e-9);
            assert!(h_assign.iter().enumerate().all(|(i, &j)| i != j));
        }
    }

    #[test]
    fn n4_exhaustive() {
        for _ in 0..10 {
            let w = random_weight(4, 0.0, 100.0);
            let (h_total, h_assign) = max_weight_derangement(&w).unwrap();
            let (b_total, _) = brute_force_max(&w);
            assert!((h_total - b_total).abs() < 1e-9);
            assert!(h_assign.iter().enumerate().all(|(i, &j)| i != j));
        }
    }

    #[test]
    fn n5_exhaustive() {
        for _ in 0..5 {
            let w = random_weight(5, 0.0, 100.0);
            let (h_total, h_assign) = max_weight_derangement(&w).unwrap();
            let (b_total, _) = brute_force_max(&w);
            assert!((h_total - b_total).abs() < 1e-9);
            assert!(h_assign.iter().enumerate().all(|(i, &j)| i != j));
        }
    }

    #[test]
    fn n6_exhaustive() {
        for _ in 0..3 {
            let w = random_weight(6, 0.0, 100.0);
            let (h_total, h_assign) = max_weight_derangement(&w).unwrap();
            let (b_total, _) = brute_force_max(&w);
            assert!((h_total - b_total).abs() < 1e-9);
            assert!(h_assign.iter().enumerate().all(|(i, &j)| i != j));
        }
    }

    #[test]
    fn n7_exhaustive() {
        let w = random_weight(7, 0.0, 100.0);
        let (h_total, h_assign) = max_weight_derangement(&w).unwrap();
        let (b_total, _) = brute_force_max(&w);
        assert!((h_total - b_total).abs() < 1e-9);
        assert!(h_assign.iter().enumerate().all(|(i, &j)| i != j));
    }

    #[test]
    fn n8_exhaustive() {
        let w = random_weight(8, 0.0, 100.0);
        let (h_total, h_assign) = max_weight_derangement(&w).unwrap();
        let (b_total, _) = brute_force_max(&w);
        assert!((h_total - b_total).abs() < 1e-9);
        assert!(h_assign.iter().enumerate().all(|(i, &j)| i != j));
    }

    // --- constraint & edge case tests ---

    #[test]
    fn n0_empty() {
        let (total, assign) = max_weight_derangement(&[]).unwrap();
        assert_eq!(total, 0.0);
        assert!(assign.is_empty());
    }

    #[test]
    fn n1_empty() {
        let (total, assign) = max_weight_derangement(&[vec![5.0]]).unwrap();
        assert_eq!(total, 0.0);
        assert!(assign.is_empty());
    }

    #[test]
    fn all_zeros() {
        let w = vec![vec![0.0; 4]; 4];
        let (total, assign) = max_weight_derangement(&w).unwrap();
        assert_eq!(total, 0.0);
        assert!(assign.iter().enumerate().all(|(i, &j)| i != j));
    }

    #[test]
    fn constant_weights() {
        let n = 5;
        let w = vec![vec![10.0; n]; n];
        let (total, assign) = max_weight_derangement(&w).unwrap();
        // Any derangement has total = 10.0 * n (all entries are 10.0)
        assert!((total - 10.0 * n as f64).abs() < 1e-9);
        assert!(assign.iter().enumerate().all(|(i, &j)| i != j));
    }

    #[test]
    fn diagonal_only_nonzero() {
        let n = 4;
        let w: Vec<Vec<f64>> = (0..n)
            .map(|i| {
                (0..n)
                    .map(|j| if i == j { 100.0 } else { 0.0 })
                    .collect()
            })
            .collect();
        let (total, assign) = max_weight_derangement(&w).unwrap();
        assert_eq!(total, 0.0);
        assert!(assign.iter().enumerate().all(|(i, &j)| i != j));
    }

    #[test]
    fn non_square_raises() {
        let w = vec![vec![1.0, 2.0], vec![3.0]];
        let err = max_weight_derangement(&w).unwrap_err();
        assert!(matches!(err, DerangementError::NonSquare { .. }));
    }

    #[test]
    fn assignment_is_permutation() {
        for n in [2, 3, 4, 5, 6] {
            let w = random_weight(n, 0.0, 100.0);
            let (_, assign) = max_weight_derangement(&w).unwrap();
            let mut sorted = assign.clone();
            sorted.sort();
            assert_eq!(sorted, (0..n).collect::<Vec<_>>());
        }
    }

    #[test]
    fn total_matches_assignment() {
        for n in [2, 3, 4, 5] {
            let w = random_weight(n, 0.0, 100.0);
            let (total, assign) = max_weight_derangement(&w).unwrap();
            let expected: f64 = (0..n).map(|i| w[i][assign[i]]).sum();
            assert!((total - expected).abs() < 1e-9);
        }
    }
}
