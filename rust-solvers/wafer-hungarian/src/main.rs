//! CLI binary for the Hungarian solver.
//!
//! Reads a single-line JSON request on stdin, writes a single-line JSON
//! response on stdout.  Only handles the `hungarian` command.

use wafer_core::io;
use wafer_core::types::{Request, Response};
use wafer_hungarian::hungarian_min_cost;

fn main() {
    let req = match io::read_request() {
        Ok(r) => r,
        Err(e) => {
            let _ = io::write_response(&Response::err(e));
            std::process::exit(1);
        }
    };

    let response = match req {
        Request::Hungarian(h) => match hungarian_min_cost(&h.matrix) {
            Ok((total_cost, assignment)) => Response::ok_hungarian(total_cost, assignment),
            Err(e) => Response::err(e.to_string()),
        },
        other => Response::err(format!(
            "unexpected command '{}'; this binary only handles 'hungarian'",
            match other {
                Request::Hungarian(_) => unreachable!(),
                Request::Derangement(_) => "derangement",
                Request::BatchDerangement(_) => "batch_derangement",
            }
        )),
    };

    if let Err(e) = io::write_response(&response) {
        eprintln!("fatal: {e}");
        std::process::exit(1);
    }
}
