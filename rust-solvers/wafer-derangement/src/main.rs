//! CLI binary for the derangement solver.
//!
//! Reads a single-line JSON request on stdin, writes a single-line JSON
//! response on stdout.  Only handles the `derangement` command.

use wafer_core::io;
use wafer_core::types::{Request, Response};
use wafer_derangement::max_weight_derangement;

fn main() {
    let req = match io::read_request() {
        Ok(r) => r,
        Err(e) => {
            let _ = io::write_response(&Response::err(e));
            std::process::exit(1);
        }
    };

    let response = match req {
        Request::Derangement(d) => match max_weight_derangement(&d.matrix) {
            Ok((max_weight, assignment)) => Response::ok_derangement(max_weight, assignment),
            Err(e) => Response::err(e.to_string()),
        },
        other => Response::err(format!(
            "unexpected command '{}'; this binary only handles 'derangement'",
            match other {
                Request::Hungarian(_) => "hungarian",
                Request::Derangement(_) => unreachable!(),
                Request::BatchDerangement(_) => "batch_derangement",
            }
        )),
    };

    if let Err(e) = io::write_response(&response) {
        eprintln!("fatal: {e}");
        std::process::exit(1);
    }
}
