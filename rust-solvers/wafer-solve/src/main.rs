//! Unified CLI entry-point for all wafer solver algorithms.
//!
//! ## Protocol
//!
//! Single-line JSON request on stdin → single-line JSON response on stdout.
//! The `command` field dispatches to the correct solver.
//!
//! ## Commands
//!
//! | Command              | Solver               | Batch? |
//! |----------------------|----------------------|--------|
//! | `hungarian`          | wafer-hungarian      | single |
//! | `derangement`        | wafer-derangement    | single |
//! | `batch_derangement`  | wafer-derangement    | batch  |
//!
//! This is the binary that Python's `rust_backend.py` invokes via subprocess.

use wafer_core::io;
use wafer_core::types::{DerangementResult, Request, Response};

fn main() {
    let req = match io::read_request() {
        Ok(r) => r,
        Err(e) => {
            let _ = io::write_response(&Response::err(e));
            std::process::exit(1);
        }
    };

    let response = match req {
        // --- hungarian (single matrix) ---
        Request::Hungarian(h) => {
            match wafer_hungarian::hungarian_min_cost(&h.matrix) {
                Ok((total_cost, assignment)) => Response::ok_hungarian(total_cost, assignment),
                Err(e) => Response::err(e.to_string()),
            }
        }

        // --- derangement (single matrix) ---
        Request::Derangement(d) => {
            match wafer_derangement::max_weight_derangement(&d.matrix) {
                Ok((max_weight, assignment)) => Response::ok_derangement(max_weight, assignment),
                Err(e) => Response::err(e.to_string()),
            }
        }

        // --- batch derangement (multiple matrices — primary hot path) ---
        Request::BatchDerangement(b) => {
            let mut results: Vec<DerangementResult> =
                Vec::with_capacity(b.matrices.len());

            for matrix in &b.matrices {
                match wafer_derangement::max_weight_derangement(matrix) {
                    Ok((max_weight, assignment)) => {
                        results.push(DerangementResult {
                            max_weight,
                            assignment,
                        });
                    }
                    Err(e) => {
                        let _ = io::write_response(&Response::err(e.to_string()));
                        std::process::exit(1);
                    }
                }
            }

            Response::ok_batch(results)
        }
    };

    if let Err(e) = io::write_response(&response) {
        eprintln!("fatal: {e}");
        std::process::exit(1);
    }
}
