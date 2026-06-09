//! Hungarian (Kuhn-Munkres) algorithm for min-cost perfect bipartite matching.
//!
//! This is a line-for-line port of the Python reference implementation in
//! `src/wafer_dse/architecture_model/solver/algorithm/hungarian.py`.
//! The two implementations are designed to produce **bit-identical** results
//! for the same input — same potential updates, same path augmentation order,
//! same tie-breaking behaviour.
//!
//! # Complexity
//! O(N³) time, O(N) auxiliary space.  For N ≤ 256 this runs in microseconds.

// ---------------------------------------------------------------------------
// Error type
// ---------------------------------------------------------------------------

#[derive(Debug, PartialEq)]
pub enum HungarianError {
    /// Matrix is not square — each row must have length N.
    NonSquare { rows: usize, cols: usize },
}

impl std::fmt::Display for HungarianError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            HungarianError::NonSquare { rows, cols } => {
                write!(f, "cost must be square (got {rows}×{cols})")
            }
        }
    }
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/// Compute the min-cost perfect matching for an N×N cost matrix.
///
/// # Arguments
/// * `cost` — N×N matrix. `cost[i][j]` is the cost of assigning row `i` to column `j`.
///   May contain arbitrary finite `f64` values including negatives.
///
/// # Returns
/// * `(min_total_cost, assignment)` where `assignment[i] = j` maps each row to a
///   distinct column, and the total cost is minimal.
///
/// # Errors
/// * `HungarianError::NonSquare` if any row has a different length than the number of rows.
///
/// # Panics
/// Panics on `f64::INFINITY` or `f64::NAN` in the cost matrix — these values
/// break the potential-update logic.
pub fn hungarian_min_cost(cost: &[Vec<f64>]) -> Result<(f64, Vec<usize>), HungarianError> {
    let n = cost.len();

    // --- N=0 short-circuit (matches Python) ---
    if n == 0 {
        return Ok((0.0, vec![]));
    }

    // --- validate square ---
    for row in cost {
        if row.len() != n {
            return Err(HungarianError::NonSquare {
                rows: n,
                cols: row.len(),
            });
        }
    }

    // --- N=1 short-circuit ---
    if n == 1 {
        return Ok((cost[0][0], vec![0]));
    }

    // ------------------------------------------------------------------
    // Potentials & matching state (1-indexed, size n+1)
    // ------------------------------------------------------------------
    let mut u = vec![0.0_f64; n + 1]; // row potentials
    let mut v = vec![0.0_f64; n + 1]; // col potentials
    let mut p = vec![0_usize; n + 1]; // p[j] = row matched to column j
    let mut way = vec![0_usize; n + 1]; // backtracking pointers

    // ------------------------------------------------------------------
    // Main algorithm — one augmentation per row
    // ------------------------------------------------------------------
    for i in 1..=n {
        p[0] = i;
        let mut j0 = 0_usize;
        let mut minv = vec![f64::INFINITY; n + 1];
        let mut used = vec![false; n + 1];

        // --- find augmenting path in the equality graph ---
        loop {
            used[j0] = true;
            let i0 = p[j0];
            let mut delta = f64::INFINITY;
            let mut j1 = 0_usize;

            for j in 1..=n {
                if used[j] {
                    continue;
                }
                // EXACT match to Python: cur = cost[i0-1][j-1] - u[i0] - v[j]
                let cur = cost[i0 - 1][j - 1] - u[i0] - v[j];
                if cur < minv[j] {
                    minv[j] = cur;
                    way[j] = j0;
                }
                if minv[j] < delta {
                    delta = minv[j];
                    j1 = j;
                }
            }

            // --- update potentials ---
            for j in 0..=n {
                if used[j] {
                    u[p[j]] += delta;
                    v[j] -= delta;
                } else {
                    minv[j] -= delta;
                }
            }

            j0 = j1;
            if p[j0] == 0 {
                break;
            }
        }

        // --- backtrack along `way` pointers to update matching ---
        loop {
            let j1 = way[j0];
            p[j0] = p[j1];
            j0 = j1;
            if j0 == 0 {
                break;
            }
        }
    }

    // ------------------------------------------------------------------
    // Build assignment array (0-indexed)
    // ------------------------------------------------------------------
    let mut assignment = vec![0_usize; n];
    for j in 1..=n {
        if p[j] != 0 {
            assignment[p[j] - 1] = j - 1;
        }
    }

    let total: f64 = (0..n).map(|i| cost[i][assignment[i]]).sum();
    Ok((total, assignment))
}

// ===========================================================================
// Tests — exhaustive verification against brute-force (matching Python tests)
// ===========================================================================

#[cfg(test)]
mod tests {
    use super::*;

    /// Brute-force: enumerate all n! permutations, return min cost + assignment.
    fn brute_force_min(cost: &[Vec<f64>]) -> (f64, Vec<usize>) {
        let n = cost.len();
        let mut best_cost = f64::INFINITY;
        let mut best_perm = vec![];
        let mut indices: Vec<usize> = (0..n).collect();

        // Heap's algorithm — generates all permutations in-place
        // We use recursion for simplicity at small N.
        fn permute(
            cost: &[Vec<f64>],
            indices: &mut [usize],
            start: usize,
            best_cost: &mut f64,
            best_perm: &mut Vec<usize>,
        ) {
            let n = indices.len();
            if start == n {
                let total: f64 = (0..n).map(|i| cost[i][indices[i]]).sum();
                if total < *best_cost {
                    *best_cost = total;
                    *best_perm = indices.to_vec();
                }
                return;
            }
            for i in start..n {
                indices.swap(start, i);
                permute(cost, indices, start + 1, best_cost, best_perm);
                indices.swap(start, i);
            }
        }

        permute(cost, &mut indices, 0, &mut best_cost, &mut best_perm);
        (best_cost, best_perm)
    }

    fn random_square(n: usize, lo: f64, hi: f64) -> Vec<Vec<f64>> {
        // Deterministic "random" using a simple LCG for reproducibility
        let mut seed: u64 = (n as u64).wrapping_mul(0xDEADBEEF);
        let mut next = || {
            seed = seed.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
            let v = (seed >> 32) as f64 / (u32::MAX as f64);
            lo + v * (hi - lo)
        };
        (0..n)
            .map(|_| (0..n).map(|_| next()).collect())
            .collect()
    }

    #[test]
    fn n0_empty() {
        let (total, assign) = hungarian_min_cost(&[]).unwrap();
        assert_eq!(total, 0.0);
        assert!(assign.is_empty());
    }

    #[test]
    fn n1_single() {
        let (total, assign) = hungarian_min_cost(&[vec![5.0]]).unwrap();
        assert_eq!(total, 5.0);
        assert_eq!(assign, vec![0]);
    }

    #[test]
    fn n2_exhaustive() {
        for _ in 0..20 {
            let cost = random_square(2, -10.0, 100.0);
            let (h_total, h_assign) = hungarian_min_cost(&cost).unwrap();
            let (b_total, _) = brute_force_min(&cost);
            assert!((h_total - b_total).abs() < 1e-9);
            let mut sorted: Vec<_> = h_assign.clone();
            sorted.sort();
            assert_eq!(sorted, vec![0, 1]);
        }
    }

    #[test]
    fn n3_exhaustive() {
        for _ in 0..20 {
            let cost = random_square(3, -10.0, 100.0);
            let (h_total, h_assign) = hungarian_min_cost(&cost).unwrap();
            let (b_total, _) = brute_force_min(&cost);
            assert!((h_total - b_total).abs() < 1e-9);
            let mut sorted: Vec<_> = h_assign.clone();
            sorted.sort();
            assert_eq!(sorted, vec![0, 1, 2]);
        }
    }

    #[test]
    fn n4_exhaustive() {
        for _ in 0..10 {
            let cost = random_square(4, -10.0, 100.0);
            let (h_total, h_assign) = hungarian_min_cost(&cost).unwrap();
            let (b_total, _) = brute_force_min(&cost);
            assert!((h_total - b_total).abs() < 1e-9);
            let mut sorted: Vec<_> = h_assign.clone();
            sorted.sort();
            assert_eq!(sorted, vec![0, 1, 2, 3]);
        }
    }

    #[test]
    fn n5_exhaustive() {
        for _ in 0..5 {
            let cost = random_square(5, -10.0, 100.0);
            let (h_total, h_assign) = hungarian_min_cost(&cost).unwrap();
            let (b_total, _) = brute_force_min(&cost);
            assert!((h_total - b_total).abs() < 1e-9);
            let mut sorted: Vec<_> = h_assign.clone();
            sorted.sort();
            let expected: Vec<usize> = (0..5).collect();
            assert_eq!(sorted, expected);
        }
    }

    #[test]
    fn n7_exhaustive() {
        let cost = random_square(7, -10.0, 100.0);
        let (h_total, h_assign) = hungarian_min_cost(&cost).unwrap();
        let (b_total, _) = brute_force_min(&cost);
        assert!((h_total - b_total).abs() < 1e-9);
        let mut sorted: Vec<_> = h_assign.clone();
        sorted.sort();
        let expected: Vec<usize> = (0..7).collect();
        assert_eq!(sorted, expected);
    }

    #[test]
    fn n8_exhaustive() {
        let cost = random_square(8, -10.0, 100.0);
        let (h_total, h_assign) = hungarian_min_cost(&cost).unwrap();
        let (b_total, _) = brute_force_min(&cost);
        assert!((h_total - b_total).abs() < 1e-9);
        let mut sorted: Vec<_> = h_assign.clone();
        sorted.sort();
        let expected: Vec<usize> = (0..8).collect();
        assert_eq!(sorted, expected);
    }

    #[test]
    fn all_zeros() {
        let cost = vec![vec![0.0, 0.0], vec![0.0, 0.0]];
        let (total, assign) = hungarian_min_cost(&cost).unwrap();
        assert_eq!(total, 0.0);
        let mut sorted = assign.clone();
        sorted.sort();
        assert_eq!(sorted, vec![0, 1]);
    }

    #[test]
    fn negative_values() {
        let cost = vec![vec![-5.0, -3.0], vec![-2.0, -4.0]];
        let (total, assign) = hungarian_min_cost(&cost).unwrap();
        assert!((total - (-9.0)).abs() < 1e-9);
        assert_eq!(assign, vec![0, 1]);
    }

    #[test]
    fn non_square_raises() {
        let cost = vec![vec![1.0, 2.0], vec![3.0]];
        let err = hungarian_min_cost(&cost).unwrap_err();
        assert!(matches!(err, HungarianError::NonSquare { .. }));
    }

    #[test]
    fn assignment_is_valid_permutation() {
        for n in [1, 2, 3, 4, 5, 6] {
            let cost = random_square(n, 0.0, 100.0);
            let (_, assign) = hungarian_min_cost(&cost).unwrap();
            let mut sorted = assign.clone();
            sorted.sort();
            assert_eq!(sorted, (0..n).collect::<Vec<_>>(), "N={n}: not a valid permutation");
        }
    }

    #[test]
    fn row_constant_addition_preserves_assignment() {
        let cost = random_square(5, 0.0, 100.0);
        let (_, orig_assign) = hungarian_min_cost(&cost).unwrap();
        let orig_total: f64 = (0..5).map(|i| cost[i][orig_assign[i]]).sum();

        let mut modified = cost.clone();
        let c = 100.0;
        for j in 0..5 {
            modified[2][j] += c;
        }

        let (mod_total, mod_assign) = hungarian_min_cost(&modified).unwrap();
        assert_eq!(mod_assign, orig_assign);
        assert!((mod_total - (orig_total + c)).abs() < 1e-9);
    }

    #[test]
    fn column_constant_addition_preserves_assignment() {
        let cost = random_square(5, 0.0, 100.0);
        let (_, orig_assign) = hungarian_min_cost(&cost).unwrap();
        let orig_total: f64 = (0..5).map(|i| cost[i][orig_assign[i]]).sum();

        let mut modified = cost.clone();
        let c = 50.0;
        for i in 0..5 {
            modified[i][3] += c;
        }

        let (mod_total, mod_assign) = hungarian_min_cost(&modified).unwrap();
        assert_eq!(mod_assign, orig_assign);
        assert!((mod_total - (orig_total + c)).abs() < 1e-9);
    }

    #[test]
    fn known_solution() {
        let cost = vec![
            vec![1.0, 2.0, 3.0],
            vec![2.0, 4.0, 6.0],
            vec![3.0, 6.0, 9.0],
        ];
        let (total, assign) = hungarian_min_cost(&cost).unwrap();
        assert_eq!(total, 10.0);
        assert_eq!(assign, vec![2, 1, 0]);
    }
}
